from fastapi import APIRouter
from backend.analytics.spending import get_spending_analysis

router = APIRouter()


@router.get("/{user_id}")
async def analyze(user_id: str, period: str = "current_month"):
    return await get_spending_analysis(user_id, period)

from backend.analytics.spending import (
    get_spending_analysis
)

@router.get("/weekly/{user_id}")
async def weekly(user_id: str):

    data = await get_spending_analysis(
        user_id,
        "current_week"
    )

    return {
        "weekly_total": data["total_spent"]
    }


@router.get("/monthly/{user_id}")
async def monthly(user_id: str):

    current = await get_spending_analysis(
        user_id,
        "current_month"
    )

    previous = await get_spending_analysis(
        user_id,
        "previous_month"
    )

    return {
        "current": current["total_spent"],
        "previous": previous["total_spent"]
    }
