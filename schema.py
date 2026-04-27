from typing import Optional

from pydantic import BaseModel, Field


class SupportResponse(BaseModel):
    intent: Optional[str] = Field(
        None, description="refund, exchange, store_credit, escalate or null"
    )
    urgency: Optional[str] = Field(None, description="low, medium, high or null")
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str
    image_analysis: Optional[str] = Field(None, description="damaged, wrong_item, or null")
    suggested_reply_en: str
    suggested_reply_ar: str
    needs_human: bool
