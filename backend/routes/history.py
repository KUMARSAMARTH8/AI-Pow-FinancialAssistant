from fastapi import APIRouter
from backend.db.mongo import get_collection

router = APIRouter()

@router.get("/{user_id}")
async def get_history(
    user_id: str,
    category: str | None = None
):

    query = {"user_id": user_id}

    if category:
        query["category"] = category

    col = get_collection("transactions")

    cursor = col.find(query).sort("date", -1)

    data = []

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        data.append(doc)

    return data