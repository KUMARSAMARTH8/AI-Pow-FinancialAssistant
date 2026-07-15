from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class IntentType(str, Enum):
    expense_concern = "expense_concern"
    loan_inquiry = "loan_inquiry"
    fraud_alert = "fraud_alert"
    investment_query = "investment_query"
    budget_planning = "budget_planning"
    general_question = "general_question"


class Transaction(BaseModel):
    user_id: str
    amount: float
    category: str
    description: str
    date: datetime
    merchant: Optional[str] = None
    transaction_type: str = "debit"

    # avoid mutable default
    tags: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    user_id: str
    message: str


# ✅ FIX: Proper sentiment schema
class Sentiment(BaseModel):
    sentiment: str
    confidence: float
    urgency: str


class ChatResponse(BaseModel):
    intent: IntentType
    confidence: float

    # more flexible typing
    entities: Dict[str, Any]

    # ✅ FIXED
    sentiment: Sentiment

    response_text: str

    chart_data: Optional[Dict] = None

    alerts: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)