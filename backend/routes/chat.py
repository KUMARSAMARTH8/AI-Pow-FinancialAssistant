from fastapi import APIRouter, HTTPException
from backend.db.models import ChatRequest, ChatResponse, Sentiment, IntentType
from backend.nlp.orchestrator import analyze_message
from backend.analytics.spending import get_spending_analysis, detect_anomalies
from backend.db.mongo import get_collection
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):

    # ---------------- VALIDATION ----------------
    if not req.message or len(req.message.strip()) < 3:
        raise HTTPException(status_code=400, detail="Message too short")

    try:
        # ---------------- NLP ----------------
        nlp = analyze_message(req.message) or {}

        # ✅ SAFE INTENT ENUM
        raw_intent = nlp.get("intent", "general_question")
        try:
            intent = IntentType(raw_intent)
        except Exception:
            intent = IntentType.general_question

        # ---------------- SENTIMENT ----------------
        sentiment_data = nlp.get("sentiment") or {}

        sentiment = Sentiment(
            sentiment=str(sentiment_data.get("sentiment", "neutral")),
            confidence=float(sentiment_data.get("confidence") or 0.0),
            urgency=str(sentiment_data.get("urgency", "low")),
        )

        # ---------------- ROUTE ----------------
        response = await _route_intent(intent.value, req.user_id, nlp)

        # ---------------- LOGGING ----------------
        try:
            col = get_collection("conversations")
            await col.insert_one({
                "user_id": req.user_id,
                "message": req.message,
                "intent": intent.value,
                "timestamp": datetime.utcnow()
            })
        except Exception as db_err:
            logger.warning(f"MongoDB logging failed: {db_err}")

        # ---------------- FINAL RESPONSE ----------------
        return ChatResponse(
            intent=intent,
            confidence=float(nlp.get("confidence") or 0.0),
            entities=nlp.get("entities") or {},
            sentiment=sentiment,
            **response
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail="Internal server error in chat processing"
        )


# ---------------- INTENT ROUTER ----------------
async def _route_intent(intent: str, user_id: str, nlp: dict) -> dict:

    if intent == "expense_concern":
        # ✅ FIX 1: SAFE TIMEFRAME
        period = (nlp.get("entities") or {}).get("timeframe") or "current_month"

        try:
            analysis = await get_spending_analysis(user_id, period)
            anomalies = await detect_anomalies(user_id)
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            analysis = {"total_spent": 0, "by_category": {}, "daily_trend": []}
            anomalies = []

        categories = list(analysis.get("by_category", {}).keys())
        top_cat = categories[0] if categories else "Unknown"

        # ✅ FIX 2: SAFE STRING HANDLING
        safe_period = period.replace('_', ' ') if isinstance(period, str) else "current month"

        response_text = (
            f"For {safe_period}, your total spending is "
            f"₹{analysis.get('total_spent', 0):,.0f}. "
            f"Top category: {top_cat}."
        )

        return {
            "response_text": response_text,
            "chart_data": {
                "type": "spending",
                "category_chart": analysis.get("by_category", {}),
                "trend_chart": analysis.get("daily_trend", [])
            },
            "alerts": [
                f"Unusual ₹{a.get('amount', 0):,.0f} at {a.get('merchant', 'Unknown')}"
                for a in anomalies[:3]
            ],
            "suggestions": [
                "Review subscriptions",
                "Set category budget limits"
            ],
        }

    # ---------------- DEFAULT ----------------
    return {
        "response_text": "I can help analyze your spending, trends, and alerts.",
        "chart_data": None,
        "alerts": [],
        "suggestions": [
            "Show my monthly spending",
            "Analyze my categories",
            "Check unusual transactions"
        ]
    }