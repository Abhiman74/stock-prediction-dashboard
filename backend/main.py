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

    # ---------- AI EXPLANATION ----------
    signal = int(data["Signal"].iloc[-1])

    if signal == 1:
        explanation = "MA50 is above MA200 → Uptrend detected → BUY signal 📈"
    else:
        explanation = "MA50 is below MA200 → Downtrend detected → SELL signal 📉"

    # ---------- CLEAN DATA FOR JSON ----------
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.fillna(0)

    # ---------- RETURN ----------
    return {
    "latest_price": float(data["Close"].iloc[-1]),
    "signal": signal,
    "prediction": [float(x) for x in predictions],
    "explanation": explanation,
    "history": data.reset_index().to_dict(orient="list")
}