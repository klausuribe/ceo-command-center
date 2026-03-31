"""Main AI engine — Claude API integration with caching and error handling."""

import json
from typing import Any

import anthropic
from loguru import logger

from config.settings import ANTHROPIC_API_KEY, COMPANY_NAME
from config.ai_config import MODEL, MAX_TOKENS
from ai.cache_manager import get_cached, set_cache
from analytics.kpi_calculator import all_kpis


class AIEngine:
    """Central AI engine for CEO Command Center."""

    def __init__(self) -> None:
        if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "sk-ant-xxxxxxxxxxxxx":
            logger.warning("ANTHROPIC_API_KEY not configured — AI features disabled")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = MODEL
        self.max_tokens = MAX_TOKENS

    @property
    def is_available(self) -> bool:
        return self.client is not None

    def call_claude(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> tuple[str, int]:
        """Call Claude API. Returns (response_text, tokens_used).

        Raises RuntimeError if API is not configured.
        """
        if not self.is_available:
            raise RuntimeError("Claude API key not configured. Set ANTHROPIC_API_KEY in .env")

        sys_prompt = system or (
            f"Eres el analista financiero ejecutivo de {COMPANY_NAME}. "
            "Responde siempre en español. Sé directo, usa números específicos. "
            "No seas genérico. Usa bullets para organizar la información."
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                system=sys_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            logger.info(f"Claude API call: {tokens} tokens used")
            return text, tokens
        except anthropic.RateLimitError:
            logger.warning("Claude API rate limited — retrying in 5s")
            import time
            time.sleep(5)
            return self.call_claude(prompt, system, max_tokens)
        except anthropic.APIConnectionError as e:
            logger.error(f"Claude API connection error: {e}")
            raise RuntimeError(f"No se pudo conectar a la API de Claude: {e}")
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise

    def analyze_module(
        self,
        module: str,
        data: dict[str, Any],
        prompt_template: str,
        use_cache: bool = True,
    ) -> str:
        """Generate AI analysis for a module with caching.

        Args:
            module: Module name (sales, receivables, etc.)
            data: Data dict to include in the prompt
            prompt_template: Prompt template with {data} placeholder
            use_cache: Whether to use cache
        """
        # Check cache first
        if use_cache:
            cached = get_cached(module, "narrative", data)
            if cached:
                return cached

        # Build prompt with data
        data_json = json.dumps(data, default=str, ensure_ascii=False, indent=2)
        prompt = prompt_template.replace("{data}", data_json)
        prompt = prompt.replace("{company_name}", COMPANY_NAME)

        text, tokens = self.call_claude(prompt)

        # Cache the response
        cost = tokens * 0.000003  # Approximate cost per token for Sonnet
        set_cache(module, "narrative", data, prompt, text, tokens, cost)

        return text

    def morning_briefing(self, period: str | None = None) -> str:
        """Generate the executive morning briefing."""
        kpis = all_kpis(period)

        # Check cache
        cached = get_cached("home", "briefing", kpis)
        if cached:
            return cached

        prompt = (
            f"Eres el analista financiero ejecutivo de {COMPANY_NAME}. "
            "Basándote en estos datos del día de hoy, genera un briefing ejecutivo "
            "de máximo 300 palabras para el CEO. "
            "Prioriza: (1) alertas críticas, (2) oportunidades, (3) tendencias.\n\n"
            f"DATOS:\n{json.dumps(kpis, default=str, ensure_ascii=False, indent=2)}\n\n"
            "Responde en español, tono profesional pero directo. Usa bullets para alertas."
        )

        text, tokens = self.call_claude(prompt)
        cost = tokens * 0.000003
        set_cache("home", "briefing", kpis, prompt, text, tokens, cost)
        return text


# Singleton instance
_engine: AIEngine | None = None


def get_engine() -> AIEngine:
    """Return singleton AIEngine instance."""
    global _engine
    if _engine is None:
        _engine = AIEngine()
    return _engine
