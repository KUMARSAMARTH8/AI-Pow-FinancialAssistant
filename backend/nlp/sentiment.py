from transformers import pipeline
from functools import lru_cache
from loguru import logger


# ---------------- LOAD MODEL (CACHED) ----------------
@lru_cache(maxsize=1)
def load_sentiment():
    try:
        logger.info("Loading sentiment model...")
        model = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english",
            device=-1,  # CPU (use 0 if GPU available)
        )
        logger.info("Sentiment model ready")
        return model
    except Exception as e:
        logger.error(f"Error loading sentiment model: {e}")
        return None   # ❗ prevent crash


# ---------------- ANALYZE ----------------
def analyze_sentiment(text: str) -> dict:

    # ---------------- EMPTY INPUT ----------------
    if not text or not text.strip():
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "urgency": "low",
        }

    try:
        model = load_sentiment()

        # ❗ MODEL LOAD FAILURE SAFE
        if model is None:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "urgency": "low",
            }

        # limit input length (avoid transformer crash)
        result = model(text[:512])[0] if text else {}

        label = str(result.get("label", "neutral")).lower()
        score = float(result.get("score", 0.0))

        # ---------------- URGENCY LOGIC ----------------
        if label == "negative":
            if score > 0.90:
                urgency = "high"
            elif score > 0.75:
                urgency = "medium"
            else:
                urgency = "low"
        else:
            urgency = "low"

        return {
            "sentiment": label,
            "confidence": round(score, 3),
            "urgency": urgency,
        }

    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")

        # ❗ ALWAYS RETURN SAFE STRUCTURE
        return {
            "sentiment": "neutral",
            "confidence": 0.0,
            "urgency": "low",
        }