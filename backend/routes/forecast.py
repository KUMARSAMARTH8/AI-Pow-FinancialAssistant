from fastapi import APIRouter

from backend.analytics.forecast import (
    forecast_expenses
)

router = APIRouter()


@router.get("/{user_id}")
async def forecast(
    user_id: str,
    days: int = 30
):
    return await forecast_expenses(
        user_id,
        days
    )