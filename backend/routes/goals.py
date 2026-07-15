from fastapi import APIRouter
from backend.db.mongo import get_collection

router = APIRouter()

@router.post("/")
async def create_goal(goal: dict):

    col = get_collection("goals")

    result = await col.insert_one(goal)

    return {
        "goal_id": str(result.inserted_id)
    }


@router.get("/{user_id}")
async def get_goals(user_id: str):

    col = get_collection("goals")

    cursor = col.find({"user_id": user_id})

    goals = []

    async for g in cursor:
        g["_id"] = str(g["_id"])
        goals.append(g)

    return goals