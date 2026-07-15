from fastapi import APIRouter
from backend.analytics.risk import calculate_risk_score

router = APIRouter()

@router.get("/{user_id}")
async def get_risk(user_id: str):

    score = await calculate_risk_score(user_id)

    level = "Low"

    if score > 70:
        level = "High"
    elif score > 40:
        level = "Medium"

    return {
        "score": score,
        "level": level
    }