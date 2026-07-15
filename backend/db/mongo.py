# backend/db/mongo.py

import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Global client
_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    global _client

    if _client is None:
        uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")

        _client = AsyncIOMotorClient(
            uri,
            maxPoolSize=10,
            serverSelectionTimeoutMS=5000,
        )

        logger.info(f"MongoDB client created: {uri}")

    return _client


def get_db():
    db_name = os.getenv("DATABASE_NAME", "financial_assistant")
    return get_client()[db_name]


def get_collection(name: str):
    return get_db()[name]


async def create_indexes():
    """Run once at startup to ensure fast queries."""
    col = get_collection("transactions")

    await col.create_index([("user_id", 1), ("date", -1)])
    await col.create_index([("user_id", 1), ("category", 1)])

    logger.info("MongoDB indexes created")


async def close_client():
    """Gracefully close MongoDB connection (on shutdown)."""
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB client closed")