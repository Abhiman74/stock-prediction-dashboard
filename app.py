import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import defaultdict

st.set_page_config(page_title="AI Stock Dashboard", layout="wide")

# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None


# ---------- FAKE DATABASE ----------


# ---------- LOGIN ----------
if not st.session_state.logged_in:
    st.markdown("## 🔐 AI Stock Dashboard Login")
    st.caption("Login to access your AI-powered trading dashboard")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            res = requests.post(
                "http://127.0.0.1:8000/login",
                params={
                    "username": username,
                    "password": password
                }
            )

            data = res.json()

            if "error" not in data:
                st.session_state.logged_in = True
                st.session_state.user = data["username"]
                st.success("Logged in successfully 🚀")
                st.rerun()
            else:
                st.error("Invalid credentials ❌")

        except Exception:
            st.error("⚠️ Backend not running")

    st.stop()

# ---------- SIDEBAR ----------
st.sidebar.title("⚙️ Settings")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

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

# Add to watchlist (DB)
if st.sidebar.button("Add to Watchlist"):
    try:
        requests.post(
            "http://127.0.0.1:8000/watchlist/add",
            params={
                "username": st.session_state.user,
                "ticker": ticker
            }
        )
        st.sidebar.success("Added!")
    except Exception:
        st.sidebar.error("Failed to add")

# Fetch watchlist from DB
try:
    res = requests.get(
        f"http://127.0.0.1:8000/watchlist/{st.session_state.user}"
    )

    watchlist = res.json()

    for stock in watchlist:
        st.sidebar.write(f"• {stock}")

except Exception:
    st.sidebar.error("Failed to load watchlist")

st.sidebar.markdown("---")
st.sidebar.subheader("💼 Portfolio")

buy_price = st.sidebar.number_input("Buy Price", min_value=0.0, step=1.0)
quantity = st.sidebar.number_input("Quantity", min_value=1.0, step=1.0)

# Add to portfolio
if st.sidebar.button("Add to Portfolio"):
    try:
        requests.post(
            "http://127.0.0.1:8000/portfolio/add",
            params={
                "username": st.session_state.user,
                "ticker": ticker,
                "buy_price": buy_price,
                "quantity": quantity
            }
        )
        st.sidebar.success("Added to portfolio!")
    except Exception:
        st.sidebar.error("Failed to add portfolio item")

# Fetch portfolio
try:
    res = requests.get(
        f"http://127.0.0.1:8000/portfolio/{st.session_state.user}"
    )

    portfolio = res.json()
    
    grouped = defaultdict(lambda: {"total_qty":0, "total_cost":0})

    for item in portfolio:
        qty = float(item.get("quantity", 1))
        grouped[item["ticker"]]["total_qty"] += qty
        grouped[item["ticker"]]["total_cost"] += item["buy_price"] * qty

    for ticker_key, data in grouped.items():
        try:
            res_price = requests.get(f"http://127.0.0.1:8000/stock/{ticker_key}")
            price_data = res_price.json()

            current_price = price_data.get("latest_price", 0)

            avg_price = data["total_cost"] / data["total_qty"]
            profit = (current_price - avg_price) * data["total_qty"]

            col1, col2 = st.sidebar.columns([3,1])

            col1.write(
                f"{ticker_key} | Qty: {data['total_qty']} | Avg: {round(avg_price,2)} | P/L: {round(profit,2)}"
            )

            if col2.button("❌", key=f"delete_{ticker_key}"):
                try:
                    requests.post(
                        "http://127.0.0.1:8000/portfolio/delete",
                        params={
                            "username": st.session_state.user,
                            "ticker": ticker_key
                        }
                    )
                    st.success("Deleted successfully")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Delete error: {e}")

        except Exception:
            st.sidebar.write(ticker_key)

    # ---------- PORTFOLIO ANALYTICS ----------
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Portfolio Analytics")

    total_invested = 0
    total_current = 0
    total_profit = 0

    for ticker_key, data in grouped.items():
        try:
            res_price = requests.get(f"http://127.0.0.1:8000/stock/{ticker_key}")
            price_data = res_price.json()

            current_price = price_data.get("latest_price", 0)

            qty = data["total_qty"]
            avg_price = data["total_cost"] / qty

            invested = avg_price * qty
            current = current_price * qty
            profit = current - invested

            total_invested += invested
            total_current += current
            total_profit += profit

        except Exception:
            continue

    # Returns %
    if total_invested > 0:
        returns = (total_profit / total_invested) * 100
    else:
        returns = 0

    st.sidebar.write(f"💰 Invested: {round(total_invested,2)}")
    st.sidebar.write(f"📈 Current: {round(total_current,2)}")
    st.sidebar.write(f"📊 Profit: {round(total_profit,2)}")
    st.sidebar.write(f"📉 Return: {round(returns,2)}%")

    try:
        st.sidebar.bar_chart([total_invested, total_current])
    except Exception:
        pass

except Exception:
    st.sidebar.error("Failed to load portfolio")

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

except Exception:
    st.error("⚠️ Backend not running")