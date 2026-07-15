import pandas as pd
import numpy as np

from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

from backend.db.mongo import get_collection


async def forecast_expenses(
    user_id: str,
    days: int = 30
):
    col = get_collection("transactions")

    cursor = col.find(
        {
            "user_id": user_id,
            "transaction_type": "debit"
        },
        projection={
            "_id": 0,
            "amount": 1,
            "date": 1
        }
    ).sort("date", 1)

    docs = await cursor.to_list(length=10000)

    if len(docs) < 7:
        return {
            "forecast": [],
            "message": "Need at least 7 transactions"
        }

    df = pd.DataFrame(docs)

    df["date"] = pd.to_datetime(df["date"])

    daily = (
        df.groupby(
            df["date"].dt.date
        )["amount"]
        .sum()
        .reset_index()
    )

    daily.columns = ["date", "spent"]

    daily["day_number"] = np.arange(
        len(daily)
    )

    X = daily[["day_number"]]
    y = daily["spent"]

    model = LinearRegression()

    model.fit(X, y)

    future_days = np.arange(
        len(daily),
        len(daily) + days
    ).reshape(-1, 1)

    predictions = model.predict(
        future_days
    )

    forecast = []

    last_date = daily["date"].max()

    for i, amount in enumerate(predictions):

        forecast.append(
            {
                "date": str(
                    last_date +
                    timedelta(days=i + 1)
                ),
                "predicted_spending":
                    round(
                        max(0, float(amount)),
                        2
                    )
            }
        )

    return {
        "forecast": forecast,
        "predicted_total": round(
            float(np.sum(predictions)),
            2
        ),
        "days": days
    }