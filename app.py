import json
import os
import time
from typing import Any, Dict, Optional, Tuple

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

from prompts import SYSTEM_PROMPT
from schema import SupportResponse

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL_CANDIDATES = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "openai/gpt-oss-120b:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-3-27b-it:free",
]


def safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """Parse model output as JSON, with a fallback extraction pass."""
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return None
        return None


def model_to_dict(model: SupportResponse) -> Dict[str, Any]:
    """Support both Pydantic v1 and v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def build_note(payload: Dict[str, Any]) -> str:
    if payload.get("needs_human"):
        return "Note: This case should be reviewed by a human support agent."
    return "Note: No human escalation needed."


def infer_intent_from_text(user_text: str) -> Optional[str]:
    """Deterministic fallback for common support patterns."""
    text = user_text.lower().strip()

    if "store credit" in text or "credit instead" in text:
        return "store_credit"

    if "exchange" in text or "wrong size" in text or "استبدال" in user_text:
        return "exchange"

    escalation_markers = [
        "terrible service",
        "late delivery",
        "very upset",
        "angry",
        "after 30 days",
    ]
    if any(marker in text for marker in escalation_markers):
        return "escalate"

    # Policy-like questions with time windows are safer to escalate.
    if "return" in text and "day" in text:
        return "escalate"

    if "not working" in text or "doesn't work" in text or "does not work" in text:
        return "refund"

    return None


def process_input(user_text: str) -> Tuple[str, str]:
    try:
        if not os.getenv("OPENROUTER_API_KEY"):
            payload = {
                "intent": None,
                "needs_human": True,
                "error": "Missing OPENROUTER_API_KEY in .env",
            }
            return json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
            ), build_note(payload)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ]

        errors = []
        for model_name in MODEL_CANDIDATES:
            for _ in range(2):
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=0.2,
                        response_format={"type": "json_object"},
                    )
                except Exception as e:
                    err_text = str(e)
                    errors.append(f"{model_name}: {err_text}")
                    if "429" in err_text:
                        time.sleep(1.2)
                    continue

                raw = (response.choices[0].message.content or "").strip()
                data = safe_json_parse(raw)

                if data:
                    try:
                        validated = SupportResponse(**data)
                        fallback_intent = infer_intent_from_text(user_text)
                        if fallback_intent:
                            validated.intent = fallback_intent
                            if fallback_intent == "escalate":
                                validated.needs_human = True
                        if not validated.image_analysis:
                            validated.image_analysis = None
                        # Low confidence should always trigger human escalation.
                        # This keeps uncertain cases from being auto-resolved.
                        if validated.confidence < 0.65:
                            validated.needs_human = True
                        payload = model_to_dict(validated)
                        return (
                            json.dumps(payload, indent=2, ensure_ascii=False),
                            build_note(payload),
                        )
                    except Exception:
                        pass

                messages.append(
                    {"role": "system", "content": "Return STRICT valid JSON only."}
                )

        inferred_intent = infer_intent_from_text(user_text)
        payload = {
            "intent": inferred_intent,
            "needs_human": True,
            "error": "All model attempts failed",
            "details": errors[-3:],
        }
        return json.dumps(payload, indent=2, ensure_ascii=False), build_note(payload)

    except Exception as e:
        payload = {"intent": None, "needs_human": True, "error": str(e)}
        return json.dumps(payload, indent=2, ensure_ascii=False), build_note(payload)


demo = gr.Interface(
    fn=process_input,
    inputs=gr.Textbox(label="Customer Message"),
    outputs=[
        gr.Code(label="Structured JSON Output"),
        gr.Textbox(label="Escalation Note"),
    ],
    title="Smart Multilingual Support Assistant",
)

if __name__ == "__main__":
    demo.launch()
