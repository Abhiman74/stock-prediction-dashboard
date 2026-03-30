import streamlit as st
import yfinance as yf
import pandas as pd

st.title("📈 Stock Prediction Dashboard")

# Input
ticker = st.text_input("Enter Stock Ticker", "AAPL")

# Fetch data
data = yf.download(ticker, start="2020-01-01", end="2024-01-01")

if data.empty:
    st.error("No data found. Try AAPL, TSLA, BTC-USD")
else:
    st.subheader("Raw Data")
    st.write(data.tail())

    st.subheader("Closing Price Chart")
    st.line_chart(data["Close"])