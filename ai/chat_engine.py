"""Conversational chat engine with context loading and assumption management."""

import json
import uuid
from datetime import datetime
from typing import Any

from loguru import logger

from config.settings import COMPANY_NAME
from config.ai_config import MODEL, MAX_TOKENS
from database.db_manager import execute_sql, query_df
from analytics.kpi_calculator import all_kpis, sales_kpis, receivables_kpis, payables_kpis
from ai.prompts.chat_prompts import CHAT_SYSTEM, INTENT_DETECTION


class ChatEngine:
    """AI chat engine with business data context."""

    def __init__(self, engine: Any) -> None:
        """Initialize with an AIEngine instance."""
        self.ai = engine
        self.session_id = str(uuid.uuid4())[:8]

    def process_message(
        self,
        user_message: str,
        chat_history: list[dict] | None = None,
        active_module: str | None = None,
    ) -> str:
        """Process a user message and return AI response.

        Args:
            user_message: The user's message
            chat_history: List of {"role": ..., "content": ...} dicts
            active_module: Currently active dashboard module
        """
        if not self.ai.is_available:
            return ("⚠️ La API de Claude no está configurada. "
                    "Configura ANTHROPIC_API_KEY en el archivo .env para habilitar el chat.")

        # Step 1: Detect intent
        intent = self._detect_intent(user_message)
        logger.info(f"Chat intent: {intent}")

        # Step 2: Load relevant context
        context = self._load_context(intent, active_module)

        # Step 3: Get active assumptions
        assumptions = self._get_assumptions()

        # Step 4: Build system prompt
        system = CHAT_SYSTEM.replace("{company_name}", COMPANY_NAME)
        system = system.replace("{context_data}", json.dumps(context, default=str, ensure_ascii=False, indent=2))
        system = system.replace("{active_assumptions}", json.dumps(assumptions, default=str, ensure_ascii=False))

        # Step 5: Build messages
        messages = []
        if chat_history:
            # Keep last 10 messages for context window
            for msg in chat_history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})

        # Step 6: Call Claude
        try:
            response = self.ai.client.messages.create(
                model=self.ai.model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=messages,
            )
            text = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens

            # Step 7: Save to chat history
            self._save_message("user", user_message, active_module, 0)
            self._save_message("assistant", text, active_module, tokens)

            # Step 8: If assumption, save it
            if intent == "assumption":
                self._save_assumption(user_message)

            return text

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"❌ Error al procesar tu pregunta: {e}"

    def _detect_intent(self, message: str) -> str:
        """Classify user intent using simple heuristics (saves API calls)."""
        msg = message.lower()
        if any(w in msg for w in ["asume", "supón", "considera que", "asumí", "supongamos"]):
            return "assumption"
        if any(w in msg for w in ["qué pasa si", "qué pasaría", "what if", "simula"]):
            return "whatif"
        if any(w in msg for w in ["compara", "vs", "versus", "diferencia entre"]):
            return "comparison"
        if any(w in msg for w in ["recomienda", "sugiere", "qué debo", "qué hago"]):
            return "recommendation"
        return "question"

    def _load_context(self, intent: str, module: str | None) -> dict:
        """Load relevant business data based on intent and module."""
        # Always include high-level KPIs
        context: dict[str, Any] = {}

        if module == "sales" or module is None:
            context["sales"] = sales_kpis()
        if module == "receivables" or module is None:
            context["receivables"] = receivables_kpis()
        if module == "payables" or module is None:
            context["payables"] = payables_kpis()

        # For general questions or no module, include everything
        if module is None:
            context = all_kpis()

        return context

    def _get_assumptions(self) -> list[dict]:
        """Get active user assumptions."""
        df = query_df(
            "SELECT description, impact_type, impact_value, impact_pct, module "
            "FROM config_assumptions WHERE is_active = 1"
        )
        return df.to_dict("records")

    def _save_message(self, role: str, content: str, module: str | None, tokens: int) -> None:
        """Persist chat message to database."""
        try:
            execute_sql(
                "INSERT INTO chat_history (session_id, role, content, module_context, tokens_used) "
                "VALUES (:sid, :role, :content, :module, :tokens)",
                {
                    "sid": self.session_id,
                    "role": role,
                    "content": content,
                    "module": module,
                    "tokens": tokens,
                },
            )
        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")

    def _save_assumption(self, message: str) -> None:
        """Save a user assumption to config_assumptions."""
        try:
            execute_sql(
                "INSERT INTO config_assumptions (module, description, is_active, created_by) "
                "VALUES (:module, :desc, 1, 'chat')",
                {"module": "general", "desc": message},
            )
            logger.info(f"Saved assumption: {message[:50]}...")
        except Exception as e:
            logger.error(f"Failed to save assumption: {e}")

    def get_history(self) -> list[dict]:
        """Get chat history for current session."""
        df = query_df(
            "SELECT role, content, created_at FROM chat_history "
            "WHERE session_id = :sid ORDER BY created_at",
            {"sid": self.session_id},
        )
        return df.to_dict("records")
