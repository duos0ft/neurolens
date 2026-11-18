from datetime import datetime

from pydantic import BaseModel, Field

from app.ai.capabilities.sentiment_analysis import SentimentLabel


class SentimentAnalysisResponse(BaseModel):
    label: SentimentLabel
    confidence: float = Field(ge=0, le=1)
    model: str
    analyzed_at: datetime
