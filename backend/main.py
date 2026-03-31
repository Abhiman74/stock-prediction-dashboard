from fastapi import FastAPI
import yfinance as yf
import numpy as np
from sklearn.linear_model import LinearRegression

app = FastAPI()

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    data = yf.download(ticker, start="2020-01-01", end="2024-01-01")

    if data.empty:
        return {"error": "No data found"}

    # Fix multi-index
    if hasattr(data.columns, "levels"):
        data.columns = data.columns.get_level_values(0)

    data = data.dropna()

    # ---------- INDICATORS ----------
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()
    data["Signal"] = (data["MA50"] > data["MA200"]).astype(int)

    # ---------- RSI ----------
    delta = data["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / loss
    data["RSI"] = 100 - (100 / (1 + rs))

    # ---------- MACD ----------
    exp1 = data["Close"].ewm(span=12, adjust=False).mean()
    exp2 = data["Close"].ewm(span=26, adjust=False).mean()

    data["MACD"] = exp1 - exp2
    data["Signal_Line"] = data["MACD"].ewm(span=9, adjust=False).mean()

    # ---------- ML ----------
    X = np.arange(len(data)).reshape(-1, 1)
    y = data["Close"].values

    model = LinearRegression()
    model.fit(X, y)

    future = np.array([[len(data) + i] for i in range(10)])
    predictions = model.predict(future)

    # ---------- SMART SIGNAL ----------
    latest = data.iloc[-1]

    score = 0
    reasons = []

    # MA trend
    if latest["MA50"] > latest["MA200"]:
        score += 1
        reasons.append("Uptrend (MA50 > MA200)")
    else:
        score -= 1
        reasons.append("Downtrend (MA50 < MA200)")

    # RSI
    if latest["RSI"] < 30:
        score += 1
        reasons.append("RSI oversold (<30)")
    elif latest["RSI"] > 70:
        score -= 1
        reasons.append("RSI overbought (>70)")

    # MACD
    if latest["MACD"] > latest["Signal_Line"]:
        score += 1
        reasons.append("MACD bullish crossover")
    else:
        score -= 1
        reasons.append("MACD bearish crossover")

    # Final decision
    final_signal = 1 if score > 0 else 0

    # Confidence (0 to 1)
    confidence = abs(score) / 3

    # Explanation
    explanation = f"Decision Score: {score}/3 → " + " | ".join(reasons)
    # ---------- CLEAN DATA FOR JSON ----------
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.fillna(0)

    # ---------- RETURN ----------
    return {
        "latest_price": float(data["Close"].iloc[-1]),
        "signal": final_signal,
        "confidence": float(confidence),
        "prediction": [float(x) for x in predictions],
        "explanation": explanation,
        "history": data.reset_index().to_dict(orient="list")
    }