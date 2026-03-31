import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="AI Stock Dashboard", layout="wide")

# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

# ---------- FAKE DATABASE ----------
users = {
    "admin": "1234",
    "abhiman": "pass"
}

# ---------- LOGIN ----------
if not st.session_state.logged_in:
    st.markdown("## 🔐 AI Stock Dashboard Login")
    st.caption("Login to access your AI-powered trading dashboard")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.session_state.user = username
            st.success("Logged in successfully")
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ---------- SIDEBAR ----------
st.sidebar.title("⚙️ Settings")

# ---------- QUICK SELECT ----------
popular = ["AAPL", "TSLA", "MSFT", "BTC-USD", "ETH-USD"]
choice = st.sidebar.selectbox("🔥 Quick Select", popular)

# ---------- CUSTOM INPUT ----------
ticker = st.sidebar.text_input(
    "🔍 Enter Stock / Crypto",
    value=choice
).upper()

# ---------- WATCHLIST ----------
st.sidebar.subheader("⭐ Watchlist")

if st.sidebar.button("Add to Watchlist"):
    if ticker not in st.session_state.watchlist:
        st.session_state.watchlist.append(ticker)

if st.sidebar.button("Clear Watchlist"):
    st.session_state.watchlist = []

for stock in st.session_state.watchlist:
    st.sidebar.write(f"• {stock}")

# ---------- OPTIONS ----------
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Chart Settings")

show_rsi = st.sidebar.checkbox("Show RSI", True)
show_macd = st.sidebar.checkbox("Show MACD", True)
show_ma = st.sidebar.checkbox("Show Moving Averages", True)

# ---------- AI SETTINGS ----------
st.sidebar.subheader("🤖 AI Settings")
days = st.sidebar.slider("Prediction Days", 5, 30, 10)

# ---------- THEME ----------
st.sidebar.subheader("🎨 Theme")
dark_mode = st.sidebar.toggle("🌙 Dark Mode", True)

theme = "plotly_dark" if dark_mode else "plotly_white"

# ---------- APPLY UI THEME ----------
if not dark_mode:
    st.markdown("""
        <style>
        .stApp {
            background-color: white;
            color: black;
        }
        </style>
    """, unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("📈 AI Stock Dashboard (Pro)")
st.caption(f"Welcome {st.session_state.user} 👋 | Full Stack • FastAPI + AI 🚀")

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

        df = pd.DataFrame(data["history"])

        # ---------- RSI ----------
        if show_rsi:
            st.subheader("📉 RSI Indicator")

            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(y=df["RSI"], name="RSI"))

            fig_rsi.add_hline(y=70)
            fig_rsi.add_hline(y=30)

            fig_rsi.update_layout(template=theme)
            st.plotly_chart(fig_rsi, use_container_width=True)

        # ---------- MACD ----------
        if show_macd:
            st.subheader("📊 MACD Indicator")

            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(y=df["MACD"], name="MACD"))
            fig_macd.add_trace(go.Scatter(y=df["Signal_Line"], name="Signal"))

            fig_macd.update_layout(template=theme)
            st.plotly_chart(fig_macd, use_container_width=True)

        # ---------- MAIN CHART ----------
        st.subheader("📊 Smart Stock Chart")

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3]
        )

        # Candlestick
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        ), row=1, col=1)

        # Moving averages
        if show_ma:
            fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="MA50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], name="MA200"), row=1, col=1)

        # Buy/Sell
        buy = df[df["Signal"] == 1]
        sell = df[df["Signal"] == 0]

        fig.add_trace(go.Scatter(x=buy.index, y=buy["Close"], mode="markers", name="Buy"), row=1, col=1)
        fig.add_trace(go.Scatter(x=sell.index, y=sell["Close"], mode="markers", name="Sell"), row=1, col=1)

        # Prediction
        future_x = list(range(len(df), len(df) + len(data["prediction"])))

        fig.add_trace(go.Scatter(
            x=future_x,
            y=data["prediction"],
            name="Prediction",
            line=dict(dash="dash")
        ), row=1, col=1)

        # Volume
        fig.add_trace(go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            opacity=0.4
        ), row=2, col=1)

        fig.update_layout(
            template=theme,
            height=750,
            title="📊 AI Stock Analysis",
            xaxis_rangeslider_visible=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # ---------- PREDICTION ----------
        st.subheader("🤖 AI Prediction Trend")
        full_series = df["Close"].tolist() + data["prediction"]
        st.line_chart(full_series)

        # ---------- AI INSIGHT ----------
        st.subheader("🧠 AI Insight")

        if data["signal"] == 1:
            st.success("📈 BUY SIGNAL\n\n" + data["explanation"])
        else:
            st.error("📉 SELL SIGNAL\n\n" + data["explanation"])

except:
    st.error("⚠️ Backend not running")