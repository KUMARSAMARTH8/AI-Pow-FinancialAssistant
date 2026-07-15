from transformers import pipeline
from functools import lru_cache
from loguru import logger

INTENT_LABELS = [
    "expense_concern",
    "loan_inquiry",
    "fraud_alert",
    "investment_query",
    "budget_planning",
    "general_question",
]


@lru_cache(maxsize=1)
def load_classifier():
    logger.info("Loading intent classifier model...")

    try:
        clf = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1  # CPU (use 0 if GPU available)
        )
        logger.info("Intent classifier ready")
        return clf

    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise


def classify_intent(text: str) -> dict:
    if not text.strip():
        return {
            "intent": "general_question",
            "confidence": 0.0,
            "all_scores": {}
        }

    clf = load_classifier()

    try:
        result = clf(
            text,
            candidate_labels=INTENT_LABELS,
            multi_label=False
        )

        return {
            "intent": result["labels"][0],
            "confidence": round(result["scores"][0], 3),
            "all_scores": {
                label: round(score, 3)
                for label, score in zip(result["labels"], result["scores"])
            },
        }

    except Exception as e:
        logger.error(f"Classification error: {e}")
        return {
            "intent": "general_question",
            "confidence": 0.0,
            "all_scores": {}
        }