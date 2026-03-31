import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="AI Stock Dashboard", layout="wide")

# ---------- SIDEBAR ----------
st.sidebar.title("⚙️ Settings")
# Quick select (optional)
popular = ["AAPL", "TSLA", "MSFT", "BTC-USD"]
choice = st.sidebar.selectbox("Quick Select", popular)

# Custom input (main)
ticker = st.sidebar.text_input(
    "Or enter any stock / crypto",
    value=choice
).upper()

st.title("📈 AI Stock Dashboard (Pro)")
st.caption("Full Stack • FastAPI + AI Insights 🚀")

# ---------- API ----------
try:
    res = requests.get(f"http://127.0.0.1:8000/stock/{ticker}")
    data = res.json()

    if "error" in data:
        st.error(data["error"])

    else:
        # ---------- METRICS ----------
        col1, col2 = st.columns(2)

        col1.metric("💰 Price", round(data["latest_price"], 2))

        signal_text = "BUY 📈" if data["signal"] == 1 else "SELL 📉"
        col2.metric("Signal", signal_text)

        st.markdown("---")

        # ---------- DATA ----------
        df = pd.DataFrame(data["history"])

        # ---------- MAIN CHART ----------
        st.subheader("📊 Smart Stock Chart")

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3]
        )

        st.subheader("📉 RSI Indicator")

        fig_rsi = go.Figure()

        fig_rsi.add_trace(go.Scatter(
            y=df["RSI"],
            name="RSI",
            line=dict(color="purple")
        ))

        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")

        fig_rsi.update_layout(template="plotly_dark")

        st.plotly_chart(fig_rsi, use_container_width=True)

        st.subheader("📊 MACD Indicator")

        fig_macd = go.Figure()

        fig_macd.add_trace(go.Scatter(
            y=df["MACD"],
            name="MACD",
            line=dict(color="blue")
        ))

        fig_macd.add_trace(go.Scatter(
            y=df["Signal_Line"],
            name="Signal Line",
            line=dict(color="orange")
        ))

        fig_macd.update_layout(template="plotly_dark")

        st.plotly_chart(fig_macd, use_container_width=True)

        # ---------- CANDLESTICK ----------
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        ), row=1, col=1)

        # ---------- MOVING AVERAGES ----------
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["MA50"],
            name="MA50",
            line=dict(color="blue")
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["MA200"],
            name="MA200",
            line=dict(color="orange")
        ), row=1, col=1)

        # ---------- BUY/SELL ----------
        buy_points = df[df["Signal"] == 1]
        sell_points = df[df["Signal"] == 0]

        fig.add_trace(go.Scatter(
            x=buy_points.index,
            y=buy_points["Close"],
            mode="markers",
            marker=dict(color="green", size=7),
            name="Buy"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=sell_points.index,
            y=sell_points["Close"],
            mode="markers",
            marker=dict(color="red", size=7),
            name="Sell"
        ), row=1, col=1)

        # ---------- PREDICTION ----------
        future_x = list(range(len(df), len(df) + len(data["prediction"])))

        fig.add_trace(go.Scatter(
            x=future_x,
            y=data["prediction"],
            name="Prediction",
            line=dict(color="cyan", dash="dash")
        ), row=1, col=1)

        # ---------- VOLUME ----------
        fig.add_trace(go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            opacity=0.4
        ), row=2, col=1)

        # ---------- LAYOUT ----------
        fig.update_layout(
            template="plotly_dark",
            height=750,
            title="📊 AI Stock Analysis",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # ---------- AI PREDICTION (SMOOTH VIEW) ----------
        st.subheader("🤖 AI Prediction Trend")

        history_close = df["Close"].tolist()
        full_series = history_close + data["prediction"]

        st.line_chart(full_series)

        # ---------- AI EXPLANATION ----------
        st.subheader("🧠 AI Insight")

        if data["signal"] == 1:
            st.success("📈 BUY SIGNAL\n\n" + data["explanation"])
        else:
            st.error("📉 SELL SIGNAL\n\n" + data["explanation"])

except:
    st.error("⚠️ Backend not running")