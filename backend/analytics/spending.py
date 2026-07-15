import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from backend.db.mongo import get_collection


# ===================== SPENDING ANALYSIS =====================

async def get_spending_analysis(user_id: str, period: str = "current_month") -> dict:
    try:
        col = get_collection("transactions")
        start, end = _date_range(period)

        cursor = col.find(
            {
                "user_id": user_id,
                "date": {"$gte": start, "$lte": end},
                "transaction_type": "debit",
            },
            projection={"_id": 0, "amount": 1, "category": 1, "date": 1, "merchant": 1},
        )

        docs = await cursor.to_list(length=10_000)

        # ❗ FIX 1: Always return consistent structure
        if not docs:
            return {
                "total_spent": 0,
                "by_category": {},
                "daily_trend": [],
                "daily_average": 0,
                "transaction_count": 0,
                "vs_previous_period_pct": 0,
                "period": period,
            }

        df = pd.DataFrame(docs)

        # ❗ FIX 2: Safe column handling
        if "date" not in df.columns or "amount" not in df.columns:
            return {
                "total_spent": 0,
                "by_category": {},
                "daily_trend": [],
                "daily_average": 0,
                "transaction_count": 0,
                "vs_previous_period_pct": 0,
                "period": period,
            }

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date", "amount"])

        df["day"] = df["date"].dt.date

        # ---------------- CATEGORY ----------------
        by_category = (
            df.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
            .round(2)
            .to_dict()
        )

        # ---------------- DAILY TREND ----------------
        daily = df.groupby("day")["amount"].sum().reset_index()
        daily.columns = ["date", "spent"]
        daily["date"] = daily["date"].astype(str)

        daily["moving_avg"] = (
            daily["spent"].rolling(7, min_periods=1).mean().round(2)
        )

        total_spent = float(df["amount"].sum())

        # ---------------- PREVIOUS PERIOD ----------------
        prev_start, prev_end = _previous_period_range(start, end)

        prev_cursor = col.find(
            {
                "user_id": user_id,
                "date": {"$gte": prev_start, "$lte": prev_end},
                "transaction_type": "debit",
            },
            projection={"amount": 1},
        )

        prev_docs = await prev_cursor.to_list(length=10_000)

        prev_total = sum(float(d.get("amount", 0)) for d in prev_docs) if prev_docs else 0

        pct_change = (
            ((total_spent - prev_total) / prev_total) * 100
            if prev_total > 0
            else 0
        )

        return {
            "total_spent": round(total_spent, 2),
            "by_category": by_category,
            "daily_trend": daily.to_dict(orient="records"),
            "daily_average": round(total_spent / max(1, (end - start).days), 2),
            "transaction_count": len(df),
            "vs_previous_period_pct": round(pct_change, 2),
            "period": period,
        }

    except Exception as e:
        # ❗ FIX 3: Never crash backend
        return {
            "total_spent": 0,
            "by_category": {},
            "daily_trend": [],
            "daily_average": 0,
            "transaction_count": 0,
            "vs_previous_period_pct": 0,
            "period": period,
            "error": str(e),
        }


# ===================== DATE HELPERS =====================

def _date_range(period: str) -> Tuple[datetime, datetime]:
    now = datetime.utcnow()

    ranges = {
        "current_month": (
            now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            now,
        ),
        "previous_month": (
            _prev_month_start(now),
            now.replace(day=1) - timedelta(seconds=1),
        ),
        "last_30_days": (now - timedelta(days=30), now),
        "last_90_days": (now - timedelta(days=90), now),
    }

    return ranges.get(period, ranges["current_month"])


def _prev_month_start(now: datetime) -> datetime:
    first_day_current = now.replace(day=1)
    last_day_prev = first_day_current - timedelta(days=1)
    return last_day_prev.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _previous_period_range(start: datetime, end: datetime) -> Tuple[datetime, datetime]:
    delta = end - start
    prev_end = start - timedelta(seconds=1)
    prev_start = prev_end - delta
    return prev_start, prev_end


# ===================== ANOMALY DETECTION =====================

async def detect_anomalies(user_id: str) -> List[Dict]:
    try:
        col = get_collection("transactions")

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        cursor = col.find(
            {
                "user_id": user_id,
                "date": {"$gte": thirty_days_ago},
                "transaction_type": "debit",
            },
            projection={"amount": 1, "category": 1, "date": 1, "merchant": 1, "_id": 0},
        )

        docs = await cursor.to_list(length=5_000)

        if len(docs) < 5:
            return []

        df = pd.DataFrame(docs)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["amount"])

        anomalies = []

        for category, group in df.groupby("category"):
            if len(group) < 3:
                continue

            mean = group["amount"].mean()
            std = group["amount"].std()

            if std == 0 or np.isnan(std):
                continue

            z_scores = np.abs((group["amount"] - mean) / std)

            for idx, row in group[z_scores > 2.0].iterrows():
                anomalies.append({
                    "category": category,
                    "amount": float(row["amount"]),
                    "merchant": row.get("merchant", "Unknown"),
                    "date": str(row["date"].date()) if pd.notnull(row["date"]) else "",
                    "z_score": round(float(z_scores.loc[idx]), 2),
                    "category_avg": round(float(mean), 2),
                })

        return sorted(anomalies, key=lambda x: x["z_score"], reverse=True)

    except Exception:
        return []