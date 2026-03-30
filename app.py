import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="AI Stock Dashboard", layout="wide")

# 🎛️ Sidebar
st.sidebar.title("⚙️ Settings")

ticker = st.sidebar.text_input("Enter Stock Ticker", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-01-01"))

st.title("📈 AI Stock Prediction Dashboard")

# Fetch data
data = yf.download(ticker, start=start_date, end=end_date)

# Fix multi-index columns (important)
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

if data.empty:
    st.error("No data found. Try AAPL, TSLA, BTC-USD")
else:
    # 📊 Layout
    col1, col2 = st.columns(2)

    # 📄 Raw Data
    with col1:
        st.subheader("📄 Raw Data")
        st.write(data.tail())

    # 📈 Price Chart
    with col2:
        st.subheader("📈 Closing Price")
        st.line_chart(data["Close"])

    # 📊 Moving Averages
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()

    st.subheader("📊 Moving Averages")
    st.line_chart(data[["Close", "MA50", "MA200"]].dropna())

    # 🟢 Signals
    data["Signal"] = 0
    data["Signal"] = (data["MA50"] > data["MA200"]).astype(int)

    st.subheader("🟢 Buy/Sell Signals")
    st.write(data[["Close", "MA50", "MA200", "Signal"]].tail())

    # 🤖 Prediction
    data = data.dropna()

    X = np.arange(len(data)).reshape(-1, 1)
    y = data["Close"].values

    model = LinearRegression()
    model.fit(X, y)

    future = np.array([[len(data) + i] for i in range(10)])
    predictions = model.predict(future)

    st.subheader("🤖 Next 10 Days Prediction")
    st.write(predictions)