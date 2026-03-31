# 📈 AI Stock Prediction Dashboard

A full-stack AI-powered stock analysis dashboard built using **FastAPI, Streamlit, and Machine Learning**.

---

## 🚀 Features

- 📊 Candlestick charts (like Zerodha)
- 📉 Moving Averages (MA50, MA200)
- 📈 RSI Indicator
- 📊 MACD Indicator
- 🔥 Buy/Sell Signals based on trend crossover
- 🤖 AI-based price prediction (Linear Regression)
- 🧠 AI explanation for trading decisions

---

## 🧠 How It Works

- Historical stock data is fetched using **Yahoo Finance API**
- Technical indicators (MA, RSI, MACD) are calculated
- A **Linear Regression model** predicts future prices
- Buy/Sell signals are generated using trend crossover logic
- Results are visualized using interactive charts

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit  
- **Backend:** FastAPI  
- **ML:** Scikit-learn  
- **Data:** yfinance  
- **Visualization:** Plotly  

---

## ⚙️ Setup Instructions

### 1. Clone the repo
```bash
git clone https://github.com/Abhiman74/stock-prediction-dashboard.git
cd stock-prediction-dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run backend
cd backend
uvicorn main:app --reload

# 5. Run frontend (open new terminal)
cd ..
source venv/bin/activate
streamlit run app.py
