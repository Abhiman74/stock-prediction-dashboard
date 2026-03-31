from fastapi import FastAPI, Depends
import yfinance as yf
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Input
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine
from backend.db_models import User, Base
from backend.auth_utils import hash_password, verify_password

app = FastAPI()

# Create DB tables
Base.metadata.create_all(bind=engine)
# DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/signup")
def signup(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if user:
        return {"error": "User already exists"}

    new_user = User(
        username=username,
        password=hash_password(password)
    )

    db.add(new_user)
    db.commit()

    return {"message": "User created successfully"}


@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password):
        return {"error": "Invalid credentials"}

    return {
        "message": "Login successful",
        "username": user.username
    }
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

    # ---------- LSTM MODEL ----------
    close_data = data["Close"].values.reshape(-1, 1)

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(close_data)

    sequence_length = 60
    X_lstm, y_lstm = [], []

    for i in range(sequence_length, len(scaled_data)):
        X_lstm.append(scaled_data[i-sequence_length:i])
        y_lstm.append(scaled_data[i])

    X_lstm = np.array(X_lstm)
    y_lstm = np.array(y_lstm)

    # ---------- MODEL ----------
    model = Sequential([
        Input(shape=(X_lstm.shape[1], 1)),
        LSTM(50, return_sequences=True),
        LSTM(50),
        Dense(25),
        Dense(1)
    ])

    model.compile(optimizer="adam", loss="mean_squared_error")

    # Train
    model.fit(X_lstm, y_lstm, epochs=3, batch_size=32, verbose=0)

    # ---------- FUTURE PREDICTION ----------
    last_sequence = scaled_data[-sequence_length:]
    future_preds = []

    current_sequence = last_sequence.copy()

    for _ in range(10):
        reshaped = current_sequence.reshape(1, sequence_length, 1)
        pred = model.predict(reshaped, verbose=0)

        future_preds.append(pred[0][0])

        current_sequence = np.vstack([current_sequence[1:], pred])

    # Convert back
    future_preds = scaler.inverse_transform(np.array(future_preds).reshape(-1, 1))
    predictions = future_preds.flatten().tolist()

    # ---------- SMART SIGNAL ----------
    latest = data.iloc[-1]

    score = 0
    reasons = []

    # MA
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

    final_signal = 1 if score > 0 else 0

    # ---------- CONFIDENCE ----------
    confidence = abs(score) / 3

    current_price = float(data["Close"].iloc[-1])
    predicted_price = float(predictions[-1])

    price_confidence = abs(predicted_price - current_price) / current_price

    if price_confidence < 0.02:
        confidence_level = "Low"
    elif price_confidence < 0.05:
        confidence_level = "Medium"
    else:
        confidence_level = "High"

    # ---------- EXPLANATION ----------
    if final_signal == 1 and confidence_level != "Low":
        explanation = f"Strong BUY 📈 | Confidence: {confidence_level} | " + " | ".join(reasons)
    elif final_signal == 1:
        explanation = f"Weak BUY ⚠️ | Confidence: {confidence_level}"
    elif final_signal == 0 and confidence_level != "Low":
        explanation = f"Strong SELL 📉 | Confidence: {confidence_level} | " + " | ".join(reasons)
    else:
        explanation = f"Weak SELL ⚠️ | Confidence: {confidence_level}"

    # ---------- CLEAN DATA ----------
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.fillna(0)

    # ---------- RETURN ----------
    return {
        "latest_price": current_price,
        "signal": final_signal,
        "confidence": confidence_level,
        "prediction": [float(x) for x in predictions],
        "explanation": explanation,
        "history": data.reset_index().to_dict(orient="list")
    }