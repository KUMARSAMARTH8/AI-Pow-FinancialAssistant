from fastapi import APIRouter, HTTPException
from backend.db.mongo import get_collection
from datetime import datetime
from bson import ObjectId

router = APIRouter()


@router.post("/")
async def add_transaction(transaction: dict):

    col = get_collection("transactions")

    transaction["created_at"] = datetime.utcnow()

    result = await col.insert_one(transaction)

    return {
        "message": "Transaction added",
        "id": str(result.inserted_id)
    }


@router.get("/{user_id}")
async def get_transactions(user_id: str):

    col = get_collection("transactions")

    cursor = col.find(
        {"user_id": user_id}
    ).sort("date", -1)

    transactions = []

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        transactions.append(doc)

    return transactions


@router.delete("/{transaction_id}")
async def delete_transaction(transaction_id: str):

    col = get_collection("transactions")

    result = await col.delete_one(
        {"_id": ObjectId(transaction_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return {"message": "Deleted"}