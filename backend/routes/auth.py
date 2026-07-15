from fastapi import APIRouter, HTTPException
from passlib.context import CryptContext

from backend.db.mongo import get_collection
from backend.auth.jwt import create_access_token

router = APIRouter()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


@router.post("/register")
async def register(user: dict):

    users = get_collection("users")

    existing = await users.find_one(
        {"email": user["email"]}
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = pwd_context.hash(
        user["password"]
    )

    user_doc = {
        "name": user["name"],
        "email": user["email"],
        "password": hashed_password
    }

    result = await users.insert_one(user_doc)

    return {
        "message": "User created",
        "user_id": str(result.inserted_id)
    }


@router.post("/login")
async def login(credentials: dict):

    users = get_collection("users")

    user = await users.find_one(
        {"email": credentials["email"]}
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not pwd_context.verify(
        credentials["password"],
        user["password"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {
            "sub": str(user["_id"]),
            "email": user["email"]
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }