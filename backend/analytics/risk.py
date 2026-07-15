from backend.analytics.spending import detect_anomalies, get_spending_analysis


async def calculate_risk_score(user_id: str) -> dict:
    anomalies = await detect_anomalies(user_id)
    analysis = await get_spending_analysis(user_id, "current_month")

    # 1. Anomaly score
    anomaly_score = min(25, len(anomalies) * 5)

    # 2. Trend score
    trend = analysis.get("vs_previous_period_pct", 0) or 0
    trend_score = min(25, max(0, trend / 2)) if trend > 0 else 0

    # 3. Category risk
    HIGH_RISK_CATEGORIES = {"gambling", "crypto", "unknown"}

    by_category = analysis.get("by_category", {})
    risky_spend = sum(v for k, v in by_category.items() if k in HIGH_RISK_CATEGORIES)

    total_spent = analysis.get("total_spent", 1) or 1
    category_score = min(25, (risky_spend / total_spent) * 100)

    # Final score
    total_score = anomaly_score + trend_score + category_score

    level = (
        "low" if total_score < 30
        else "medium" if total_score < 60
        else "high"
    )

    return {
        "score": round(total_score),
        "level": level,
        "anomaly_count": len(anomalies),
    }