from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from loguru import logger

import os
import time

# ---------------- LOAD ENV ----------------
load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ---------------- IMPORTS ----------------
from backend.db.mongo import create_indexes

from backend.routes import (
    chat,
    analyze,
    alerts,
    transactions,
    history,
    goals,
    risk,
    auth,
    forecast
)

# ---------------- LIFESPAN ----------------
@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting AI Financial Assistant...")

    try:
        await create_indexes()
        logger.success("MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Database startup failed: {e}")

    yield

    logger.info("Server shutting down")

# ---------------- APP ----------------
app = FastAPI(
    title="AI Financial Assistant",
    description="NLP Powered Personal Finance Analytics Platform",
    version="1.1.0",
    lifespan=lifespan
)

# ---------------- CORS ----------------
origins = ["*"]

if ENVIRONMENT == "production":
    origins = [
        "https://your-vercel-app.vercel.app"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------- REQUEST LOGGER ----------------
@app.middleware("http")
async def log_requests(request: Request, call_next):

    start_time = time.time()

    response = await call_next(request)

    process_time = round(
        (time.time() - start_time) * 1000,
        2
    )

    logger.info(
        f"{request.method} "
        f"{request.url.path} "
        f"Status={response.status_code} "
        f"Time={process_time}ms"
    )

    return response

# ---------------- HEALTH CHECK ----------------
@app.get("/health")
async def health():

    return {
        "status": "healthy",
        "environment": ENVIRONMENT
    }

# ---------------- ROUTES ----------------
app.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

app.include_router(
    analyze.router,
    prefix="/analyze",
    tags=["Analytics"]
)

app.include_router(
    alerts.router,
    prefix="/alerts",
    tags=["Alerts"]
)

app.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["Transactions"]
)

app.include_router(
    history.router,
    prefix="/history",
    tags=["History"]
)

app.include_router(
    goals.router,
    prefix="/goals",
    tags=["Goals"]
)

app.include_router(
    risk.router,
    prefix="/risk",
    tags=["Risk"]
)

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# ----------- NEW: FORECAST ROUTE -----------
app.include_router(
    forecast.router,
    prefix="/forecast",
    tags=["Forecast"]
)

# ---------------- GLOBAL ERROR HANDLER ----------------
@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    logger.error(f"Unhandled Exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal Server Error"
        }
    )

# ---------------- DEBUG ROUTES ----------------
if ENVIRONMENT != "production":
    print("\nRegistered Routes:")
    for route in app.routes:
        methods = getattr(route, "methods", None)
        print(f"{route.path} -> {methods}")

# ---------------- FRONTEND ----------------
# KEEP THIS LAST
app.mount(
    "/",
    StaticFiles(
        directory="frontend",
        html=True
    ),
    name="frontend"
)