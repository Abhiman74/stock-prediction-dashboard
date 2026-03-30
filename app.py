import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Stock Dashboard", layout="wide")

st.title("📈 AI Stock Prediction Dashboard")

# Input
ticker = st.text_input("Enter Stock Ticker", "AAPL")

# Fetch data
data = yf.download(ticker, start="2020-01-01", end="2024-01-01")

if data.empty:
    st.error("No data found. Try AAPL, TSLA, BTC-USD")
else:
    st.subheader("Raw Data")
    st.write(data.tail())

    # 📊 Moving Averages
    data["MA50"] = data["Close"].rolling(window=50).mean()
    data["MA200"] = data["Close"].rolling(window=200).mean()

    st.subheader("📊 Moving Averages")
    st.line_chart(data[["Close", "MA50", "MA200"]])

    # 🟢 Buy/Sell Signals
    data["Signal"] = 0
    data.loc[50:, "Signal"] = (
        data["MA50"][50:] > data["MA200"][50:]
    ).astype(int)

    st.subheader("🟢 Buy/Sell Signals (1 = Buy, 0 = Sell)")
    st.write(data[["Close", "MA50", "MA200", "Signal"]].tail())

    # 🤖 Simple Prediction
    data = data.dropna()

    X = np.arange(len(data)).reshape(-1, 1)
    y = data["Close"].values

    model = LinearRegression()
    model.fit(X, y)

    future = np.array([[len(data) + i] for i in range(10)])
    predictions = model.predict(future)

    st.subheader("🤖 Next 10 Days Prediction")
    st.write(predictions)