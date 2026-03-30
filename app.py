import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objects as go

st.set_page_config(page_title="AI Stock Dashboard", layout="wide")

# 🎛️ Sidebar
st.sidebar.title("⚙️ Settings")

ticker = st.sidebar.selectbox(
    "Select Asset",
    ["AAPL", "TSLA", "GOOGL", "MSFT", "BTC-USD", "ETH-USD", "RELIANCE.NS"]
)

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-01-01"))

st.title("📈 AI Stock Prediction Dashboard")
st.markdown("### Real-time stock analysis with AI-powered insights 🚀")

# 📊 Fetch data
data = yf.download(ticker, start=start_date, end=end_date)

# Fix multi-index issue
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

if data.empty:
    st.error("No data found.")
else:
    # 📌 Metrics
    current_price = data["Close"].iloc[-1]
    prev_price = data["Close"].iloc[-2]

    change = current_price - prev_price
    percent_change = (change / prev_price) * 100

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Current Price", f"${current_price:.2f}")
    col2.metric("📊 Change", f"{change:.2f}", f"{percent_change:.2f}%")
    col3.metric("📦 Volume", int(data["Volume"].iloc[-1]))

    # 📈 Price chart
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Raw Data")
        st.write(data.tail())

    with col2:
        st.subheader("📈 Closing Price")
        st.line_chart(data["Close"])

    # 📊 Moving averages
    data["MA50"] = data["Close"].rolling(50).mean()
    data["MA200"] = data["Close"].rolling(200).mean()

    st.subheader("📊 Moving Averages")
    st.line_chart(data[["Close", "MA50", "MA200"]].dropna())

    # 🟢 Signals
    data["Signal"] = (data["MA50"] > data["MA200"]).astype(int)

    st.subheader("🟢 Buy/Sell Signals")
    st.write(data[["Close", "MA50", "MA200", "Signal"]].tail())

    # 🧠 Trend Insight
    if data["MA50"].iloc[-1] > data["MA200"].iloc[-1]:
        st.success("📈 Bullish Trend (Buy Signal)")
    else:
        st.error("📉 Bearish Trend (Sell Signal)")

    # 📊 Candlestick Chart
    st.subheader("🕯️ Candlestick Chart")

    fig = go.Figure(data=[go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 🤖 Prediction
    data = data.dropna()

    X = np.arange(len(data)).reshape(-1, 1)
    y = data["Close"].values

    model = LinearRegression()
    model.fit(X, y)

    future = np.array([[len(data) + i] for i in range(10)])
    predictions = model.predict(future)

    future_dates = pd.date_range(start=data.index[-1], periods=10)

    pred_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted Price": predictions
    })

    st.subheader("🤖 Next 10 Days Prediction")
    st.line_chart(pred_df.set_index("Date"))

    # 📥 Download button
    st.download_button(
        label="📥 Download Data as CSV",
        data=data.to_csv(),
        file_name=f"{ticker}_data.csv",
        mime="text/csv"
    )