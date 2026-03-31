---
name: ai-engine-builder
description: >
  Build AI-powered features using the Anthropic Claude API for business analysis,
  anomaly detection, forecasting, alerts, and chat. Use this skill whenever creating
  or editing anything in the ai/ directory, working with prompts, Claude API calls,
  the chat engine, anomaly detection, or AI-generated analysis. Triggers on "AI",
  "Claude API", "analysis", "prompt", "chat engine", "anomaly", "forecast", "alert",
  "morning briefing", or any AI-related feature.
---

# AI Engine Builder — Claude API Integration

Build all AI features following these patterns for consistent, cost-effective Claude API usage.

## Claude API Call Pattern

```python
import anthropic
from config.settings import ANTHROPIC_API_KEY, AI_MODEL

class AIEngine:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = AI_MODEL  # claude-sonnet-4-20250514

    def _call_claude(self, system_prompt: str, user_content: str,
                     max_tokens: int = 2000) -> str:
        """Core API call with error handling and cost tracking."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}]
            )
            return response.content[0].text
        except anthropic.APIError as e:
            return f"Error de IA: {str(e)}"
        except Exception as e:
            return f"Error inesperado: {str(e)}"
```

## Prompt Template Pattern

Every prompt file in `ai/prompts/` follows this structure:

```python
# ai/prompts/sales_prompts.py

def get_analysis_prompt(data: dict, period: str) -> tuple[str, str]:
    """Returns (system_prompt, user_content) tuple."""

    system_prompt = """Eres el analista de inteligencia de negocios del CEO Command Center.
    REGLAS:
    1. Responde SIEMPRE en español
    2. Usa datos específicos (números, %, nombres)
    3. Sé directo — no rellenes con texto genérico
    4. Estructura tu respuesta con las secciones solicitadas
    5. Máximo 400 palabras por análisis"""

    user_content = f"""Analiza los datos de ventas del periodo {period}.

    DATOS:
    {json.dumps(data, ensure_ascii=False, indent=2)}

    GENERA:
    1. **DIAGNÓSTICO** (qué pasó y por qué — máx 100 palabras)
    2. **ANOMALÍAS** (cambios inusuales detectados)
    3. **OPORTUNIDADES** (potencial sub-explotado)
    4. **RIESGOS** (concentración, dependencias)
    5. **ACCIONES** (3-5 recomendaciones concretas)"""

    return system_prompt, user_content
```

## Cache Pattern — Critical for Cost Control

```python
import hashlib
import json
from datetime import datetime, timedelta

class AICache:
    def __init__(self, db):
        self.db = db

    def _hash_data(self, data) -> str:
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def get(self, module: str, analysis_type: str, data: dict) -> str | None:
        data_hash = self._hash_data(data)
        row = self.db.execute(
            """SELECT response FROM ai_analysis_cache
               WHERE module=? AND analysis_type=? AND data_hash=?
               AND is_valid=1 AND expires_at > ?""",
            (module, analysis_type, data_hash, datetime.now().isoformat())
        ).fetchone()
        return row[0] if row else None

    def set(self, module: str, analysis_type: str, data: dict,
            response: str, ttl_hours: int = 4):
        data_hash = self._hash_data(data)
        expires = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        self.db.execute(
            """INSERT INTO ai_analysis_cache
               (module, analysis_type, data_hash, response, expires_at, is_valid)
               VALUES (?, ?, ?, ?, ?, 1)""",
            (module, analysis_type, data_hash, response, expires)
        )
        self.db.commit()
```

ALWAYS check cache before calling Claude API. ALWAYS cache responses after receiving them.

## Chat Engine Pattern

```python
def chat(self, user_message: str, module: str, history: list) -> str:
    """Process a chat message with full context."""
    # 1. Load relevant data for current module
    context = self._load_module_context(module)

    # 2. Build messages with history (keep last 10 exchanges)
    messages = []
    for msg in history[-20:]:  # Last 10 exchanges = 20 messages
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": user_message})

    # 3. Call Claude with context in system prompt
    system = f"""Eres el asistente de BI del CEO Command Center.
    Módulo activo: {module}
    Datos actuales: {json.dumps(context, ensure_ascii=False)}

    REGLAS:
    - Responde con datos específicos
    - Si el usuario da un supuesto, confirma y explica impacto
    - Si no tienes datos para responder, dilo claramente"""

    response = self.client.messages.create(
        model=self.model,
        max_tokens=1500,
        system=system,
        messages=messages
    )
    return response.content[0].text
```

## Data Compression for Prompts

NEVER send raw DataFrames. Compress data to key metrics:

```python
def compress_for_prompt(df, module):
    """Reduce data to what the AI actually needs."""
    if module == 'sales':
        return {
            'total_revenue': float(df['subtotal'].sum()),
            'total_profit': float(df['gross_profit'].sum()),
            'avg_margin': float(df['margin_pct'].mean()),
            'top_5_products': df.groupby('product_name')['subtotal']
                .sum().nlargest(5).to_dict(),
            'top_5_customers': df.groupby('customer_name')['subtotal']
                .sum().nlargest(5).to_dict(),
            'daily_trend': df.groupby('date_id')['subtotal']
                .sum().tail(30).to_dict(),
        }
```

## Cost Tracking

Log every API call:
```python
tokens_in = response.usage.input_tokens
tokens_out = response.usage.output_tokens
cost = (tokens_in * 0.003 + tokens_out * 0.015) / 1000  # Sonnet pricing
```

## Testing AI Features

After implementing any AI feature, test with:
```bash
python -c "
from ai.engine import AIEngine
engine = AIEngine()
# Quick test with minimal data
result = engine._call_claude(
    'Responde OK si recibes este mensaje.',
    'Test de conexión.'
)
print(f'API Response: {result[:100]}')
print('✅ Claude API connection works')
"
```
