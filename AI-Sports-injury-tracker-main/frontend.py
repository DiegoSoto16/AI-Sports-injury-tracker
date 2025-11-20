import streamlit as st
import pandas as pd
import datetime
import requests
import random
import numpy as np
import tensorflow as tf
from pathlib import Path
import plotly.express as px
from streamlit_calendar import calendar

# Must use Python 3.10.0 for Tensorflow

BASE_URL = "http://127.0.0.1:8000/api"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.athlete_id = None
    st.session_state.athlete_name = None

def login_user(username: str):
    """Validate username using backend athlete list."""
    try:
        r = requests.get(f"{BASE_URL}/athletes/")
        if r.status_code == 200:
            athletes = r.json()
            for a in athletes:
                if a["name"].lower() == username.lower():
                    st.session_state.logged_in = True
                    st.session_state.athlete_id = a["id"]
                    st.session_state.athlete_name = a["name"]
                    return True
    except Exception as e:
        st.error(f"Backend error: {e}")
    return False

def show_login_page():
    st.title("🔐 Athlete Login")
    username = st.text_input("Enter your athlete name:")
    if st.button("Login"):
        if login_user(username):
            st.rerun()
        else:
            st.error("Invalid athlete name or not found.")

if not st.session_state.logged_in:
    show_login_page()
    st.stop()

ATHLETE_ID = st.session_state.athlete_id

MODEL_PATH = Path("backend/ml_models/injury_model.h5")

data = pd.read_csv('injury_data.csv')

MAX_VALUES = {
    "heart_rate": data["heart_rate"].max(),
    "duration_minutes": data["duration_minutes"].max(),
    "calories_burned": data["calories_burned"].max(),
    "calculated_intensity": data["calculated_intensity"].max(),
    "strain_score": data["strain_score"].max()
}

@st.cache_resource
def load_kesar_model():
    """Load Keras model safely."""
    if MODEL_PATH.exists():
        try:
            return tf.keras.models.load_model(str(MODEL_PATH))
        except Exception as e:
            st.error(f"TF model load failed: {e}")
    return None

def preprocess_features(data_dict):
    """Apply SAME normalization used during training: X / max(X)."""
    feature_order = [
        "heart_rate",
        "duration_minutes",
        "calories_burned",
        "calculated_intensity",
        "strain_score"
    ]

    raw = np.array([data_dict[f] for f in feature_order], dtype=float)
    normalized = np.array([
        raw[i] / MAX_VALUES[f] if MAX_VALUES[f] != 0 else raw[i]
        for i, f in enumerate(feature_order)
    ])
    return normalized.reshape(1, -1)

def keras_predict(data_dict):
    """Run model prediction if available."""
    model = load_kesar_model()
    if model is None:
        return None
    x = preprocess_features(data_dict)
    pred = model.predict(x, verbose=0)
    return float(pred[0][0])  # sigmoid output

if "data_initialized" not in st.session_state:
    today = pd.Timestamp.today()

    st.session_state.historical_data = pd.DataFrame({
        "Date": pd.date_range(end=today, periods=14),
        "Heart Rate": [random.randint(70, 95) for _ in range(14)],
        "Sleep Hours": [round(random.uniform(6, 8.5), 1) for _ in range(14)],
        "Steps": [random.randint(6000, 12000) for _ in range(14)],
        "Calories Burned": [random.randint(400, 650) for _ in range(14)],
    })

    st.session_state.events = []
    st.session_state.data_initialized = True

# BACKEND DATA FETCH
def fetch_backend_data(athlete_id):
    try:
        r = requests.get(f"{BASE_URL}/athletes/{athlete_id}/")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Backend contact error: {e}")
    return {}


# SIDEBAR
st.sidebar.title("Navigation")
st.sidebar.markdown(f"**Logged in as:** {st.session_state.athlete_name}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.athlete_id = None
    st.session_state.athlete_name = None
    st.rerun()

PAGE = st.sidebar.radio(
    "Go to",
    ["🏠 Dashboard", "📅 Calendar", "🧠 AI Prevention", "⌚ Wearable Devices", "👤 Profile"]
)


# DASHBOARD
if PAGE == "🏠 Dashboard":
    st.title("📊 Athlete Dashboard")

    data = fetch_backend_data(ATHLETE_ID)

    if not data:
        st.warning("No backend data found.")
        st.stop()

    st.subheader(f"{data['name']} — {data.get('sport', 'N/A')}")

    col1, col2, col3 = st.columns(3)
    col1.metric("❤️ Heart Rate", f"{data['heart_rate']} bpm")
    col2.metric("💤 Sleep Hours", f"{data['sleep_hours']}")
    col3.metric("🔥 Calories Burned", f"{data['calories_burned']}")

    col4, col5, col6 = st.columns(3)
    col4.metric("🏃 Steps", f"{data['steps']}")

    # Try backend prediction
    try:
        r = requests.get(f"{BASE_URL}/predictions/latest/{ATHLETE_ID}/")
        if r.status_code == 200:
            pred = r.json()
            col5.metric("⚠️ Risk Level", f"{float(pred['predicted_probability'])*100:.1f}%")
            col6.metric("💪 Strain Level", f"{float(pred['strain_score'])*100:.1f}%")
        else:
            col5.metric("⚠️ Risk Level", "—")
            col6.metric("💪 Strain Level", "—")
    except:
        col5.metric("⚠️ Risk Level", "—")
        col6.metric("💪 Strain Level", "—")

    st.divider()
    st.subheader("📈 Performance Trends")

    hist = st.session_state.historical_data

    st.plotly_chart(px.line(hist, x="Date", y="Heart Rate", title="Heart Rate Trend"), use_container_width=True)
    st.plotly_chart(px.bar(hist, x="Date", y="Steps", title="Daily Steps"), use_container_width=True)
    st.plotly_chart(px.bar(hist, x="Date", y="Sleep Hours", title="Sleep Duration"), use_container_width=True)
    st.plotly_chart(px.line(hist, x="Date", y="Calories Burned", title="Calories Burned Trend"), use_container_width=True)

# AI PREVENTION
elif PAGE == "🧠 AI Prevention":
    st.title("🧠 AI Injury Prevention (Keras Model Ready)")

    data = fetch_backend_data(ATHLETE_ID)

    # Compute intensity & strain for now (until your CSV defines real values)
    intensity = round((data["heart_rate"] / 200) + (data["steps"] / 12000), 2)
    strain = round(((data["steps"] / 10000) + (data["heart_rate"] / 200)) / 2, 2)

    feature_set = {
        "heart_rate": float(data["heart_rate"]),
        "duration_minutes": 60.0,
        "calories_burned": float(data["calories_burned"]),
        "calculated_intensity": intensity,
        "strain_score": strain
    }

    # Try TensorFlow model first
    risk = keras_predict(feature_set)

    if risk is not None:
        st.metric("Injury Risk (Neural Network)", f"{risk*100:.1f}%")
    else:
        # Fallback formula
        fallback = round((intensity + strain) / 2, 2)
        st.warning("Keras Model Missing → Using fallback formula.")
        st.metric("Injury Risk (Fallback)", f"{fallback*100:.1f}%")
        risk = fallback

    # Advice Text
    st.subheader("Personalized Training Advice")
    if risk > 0.7:
        st.error("🚨 High Risk — rest and recovery recommended.")
    elif risk > 0.4:
        st.warning("⚠️ Moderate Risk — reduce intensity.")
    else:
        st.success("✅ Low Risk — safe to train today.")

# CALENDAR
elif PAGE == "📅 Calendar":
    st.title("📅 Training & Recovery Calendar")

    event_title = st.text_input("Event Title")
    event_date = st.date_input("Event Date", datetime.date.today())

    if st.button("Add Event"):
        st.session_state.events.append(
            {"title": event_title, "start": str(event_date), "end": str(event_date)}
        )
        st.success("Event added.")

    st.subheader("Your Calendar")
    calendar(events=st.session_state.events)

# WEARABLE DEVICES
elif PAGE == "⌚ Wearable Devices":
    st.title("⌚ Wearable Devices")
    st.write("- Fitbit Charge 5")
    st.write("- Apple Watch Series 8")

# PROFILE
elif PAGE == "👤 Profile":
    st.title("👤 Athlete Profile")

    data = fetch_backend_data(ATHLETE_ID)
    if data:
        st.write(f"**Name:** {data['name']}")
        st.write(f"**Sport:** {data['sport']}")
        st.write(f"**Team:** {data['team']}")
        st.write(f"**Age:** {data['age']}")
        st.write(f"**Experience Years:** {data['experience_years']}")
        st.write(f"**Heart Rate:** {data['heart_rate']}")
        st.write(f"**Sleep Hours:** {data['sleep_hours']}")
        st.write(f"**Steps:** {data['steps']}")
        st.write(f"**Fatigue Level:** {data['fatigue_level']}")
