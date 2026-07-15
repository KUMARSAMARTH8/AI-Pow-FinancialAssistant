import spacy
import re
from functools import lru_cache
from typing import Dict, List, Optional


@lru_cache(maxsize=1)
def load_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        raise RuntimeError(
            "spaCy model not found. Run: python -m spacy download en_core_web_sm"
        )


AMOUNT_PATTERN = re.compile(
    r"(?:Rs\.?|INR|USD|\$|₹)?\s?(\d{1,3}(?:,\d{2,3})*)(?:\s?(?:lakh|crore|k|thousand))?",
    re.IGNORECASE,
)

TIMEFRAMES = {
    "last month": "previous_month",
    "this month": "current_month",
    "last week": "previous_week",
    "last 30 days": "last_30_days",
    "last year": "previous_year",
}

CATEGORIES = {
    "food": ["food", "restaurant", "groceries", "swiggy", "zomato"],
    "rent": ["rent", "apartment", "pg", "housing"],
    "transport": ["uber", "ola", "petrol", "fuel", "metro"],
    "entertainment": ["netflix", "movie", "gaming", "spotify"],
    "medical": ["hospital", "medicine", "doctor", "pharmacy"],
}


def extract_entities(text: str) -> Dict:
    nlp = load_nlp()
    doc = nlp(text.lower())

    result = {
        "amounts": [],
        "timeframe": None,
        "category": None,
        "raw": text,
    }

    # Extract amounts
    for match in AMOUNT_PATTERN.finditer(text):
        value = _normalize(match.group())
        if value > 0:
            result["amounts"].append({
                "raw": match.group().strip(),
                "value": value
            })

    # Extract timeframe
    lower_text = text.lower()
    for phrase, canon in TIMEFRAMES.items():
        if phrase in lower_text:
            result["timeframe"] = canon
            break

    # Extract category
    for cat, keywords in CATEGORIES.items():
        if any(k in lower_text for k in keywords):
            result["category"] = cat
            break

    return result


def _normalize(raw: str) -> float:
    try:
        raw = re.sub(r"[₹$]|rs\.?|inr", "", raw.lower())
        raw = raw.replace(",", "").strip()

        multiplier = 1

        if "crore" in raw:
            multiplier = 10_000_000
            raw = raw.replace("crore", "")
        elif "lakh" in raw:
            multiplier = 100_000
            raw = raw.replace("lakh", "")
        elif "k" in raw:
            multiplier = 1_000
            raw = raw.replace("k", "")
        elif "thousand" in raw:
            multiplier = 1_000
            raw = raw.replace("thousand", "")

        return float(raw.strip()) * multiplier

    except Exception:
        return 0.0