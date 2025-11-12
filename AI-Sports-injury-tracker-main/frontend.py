import streamlit as st
import pandas as pd
import datetime
import requests
import random
import plotly.express as px
from typing import Dict
from streamlit_calendar import calendar

if "data_initialized" not in st.session_state:
    # Default simulated single-day data
    st.session_state.wearable_data = {
        "heart_rate": 82,
        "fatigue_level": 4,
        "sleep_hours": 7.5,
        "steps": 8300,
        "calories_burned": 520,
    }

    # Generate 14 days of mock historical data
    today = pd.Timestamp.today()
    st.session_state.historical_data = pd.DataFrame({
        "Date": pd.date_range(end=today, periods=14),
        "Heart Rate": [random.randint(70, 90) for _ in range(14)],
        "Sleep Hours": [round(random.uniform(6, 8.5), 1) for _ in range(14)],
        "Steps": [random.randint(6000, 11000) for _ in range(14)],
        "Calories Burned": [random.randint(400, 600) for _ in range(14)],
    })

    st.session_state.events = []
    st.session_state.user_profile = {
        "name": "Athlete One",
        "age": 25,
        "sport": "Soccer",
        "training_goal": "Injury Prevention & Performance",
    }

    st.session_state.data_initialized = True

# Utility Functions

BASE_URL = "http://127.0.0.1:8000/api"

SELECTED_ATHLETE_ID = 1  # Liam Johnson


@st.cache_data(ttl=15)
def get_all_athletes():
    try:
        r = requests.get(f"{BASE_URL}/athletes/")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def fetch_backend_data(athlete_id=SELECTED_ATHLETE_ID):
    """Fetch athlete data directly from the Django backend."""
    try:
        response = requests.get(
            f"{BASE_URL}/athletes/{athlete_id}/", timeout=10)
        if response.status_code == 200:
            athlete = response.json()

            # Print debug info to verify structure
            # st.write("ahahah Backend athlete response:", athlete)

            # adapt to your backend's actual field names
            return {
                "name": athlete.get("name") or athlete.get("athlete_name") or athlete.get("full_name") or f"Athlete {athlete_id}",
                "heart_rate": athlete.get("heart_rate", 0),
                "sleep_hours": athlete.get("sleep_hours", 0),
                "steps": athlete.get("steps", 0),
                "calories_burned": athlete.get("calories_burned", 0),
                "fatigue_level": athlete.get("fatigue_level", 0),
                "sport": athlete.get("sport", "N/A"),
                "team": athlete.get("team", "N/A"),
                "age": athlete.get("age", 0),
                "experience_years": athlete.get("experience_years", 0),
            }
        else:
            st.error(f"⚠️ Backend returned status {response.status_code}")
            st.write(response.text)
            return {}
    except Exception as e:
        st.error(f"❌ Could not connect to backend: {e}")
        return {}


def compute_local_metrics(data: Dict) -> Dict:
    hr = data.get("heart_rate", 80)
    fatigue = data.get("fatigue_level", 4)
    sleep = data.get("sleep_hours", 7)
    steps = data.get("steps", 8000)

    risk_score = min(1, ((hr - 60) / 100 + fatigue / 10 - sleep / 15))
    risk_score = max(0, round(risk_score, 2))

    strain_score = min(1, ((steps / 10000) + (hr / 200)) / 2)
    strain_score = max(0, round(strain_score, 2))

    return {"risk_level": risk_score, "strain_level": strain_score}


def generate_local_ai_advice(data: Dict) -> Dict:
    metrics = compute_local_metrics(data)
    risk_score = metrics["risk_level"]
    hr, fatigue, sleep = data["heart_rate"], data["fatigue_level"], data["sleep_hours"]

    if risk_score > 0.7 or hr > 160 or fatigue > 8:
        advice = [
            "Your heart rate and fatigue suggest overtraining.",
            "Take a recovery day and hydrate well.",
            "Avoid intense sessions until metrics stabilize.",
        ]
    elif risk_score > 0.4 or sleep < 6 or fatigue > 6:
        advice = [
            "You’re moderately fatigued—consider a lighter workout.",
            "Prioritize sleep and hydration tonight.",
            "Mobility or low-impact cardio is ideal today.",
        ]
    else:
        advice = [
            "Metrics look good—you're ready to train.",
            "Stick to your plan and monitor recovery.",
            "Keep syncing your wearable for better insights.",
        ]
    return {"risk_score": risk_score, "advice": advice}


# Sidebar Navigation


st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["🏠 Dashboard", "📅 Calendar", "🧠 AI Prevention",
        "⌚ Wearable Devices", "👤 Profile"],
)

# Sidebar athlete selector
# athletes = requests.get(f"{BASE_URL}/athletes/").json()
# athlete_options = [f"{a['id']} — {a['name']}" for a in athletes]
# selected_option = st.sidebar.selectbox("Athlete", athlete_options)
# selected_athlete = int(selected_option.split("—")[0].strip())

# Dashboard

if page == "🏠 Dashboard":
    st.title("📊 Athlete Health Dashboard")

    # Try backend first
    wearable_data = fetch_backend_data()
    if not wearable_data:
        st.warning("No athlete data found.")
        st.stop()

    # Display core athlete info
    st.markdown(f"### 🏅 {wearable_data['name']} ({wearable_data['sport']})")

    # Primary performance metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("❤️ Heart Rate", f"{wearable_data['heart_rate']:.1f} bpm")
    col2.metric("💤 Sleep Hours", f"{wearable_data['sleep_hours']:.1f}")
    col3.metric("🔥 Calories Burned", f"{wearable_data['calories_burned']:.2f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("🏃 Steps", int(wearable_data["steps"]))

    # Fetch latest prediction for this athlete
    try:
        r = requests.get(
            f"{BASE_URL}/predictions/latest/{SELECTED_ATHLETE_ID}/", timeout=10)
        if r.status_code == 200:
            pred = r.json()
            risk_pct = float(pred["predicted_probability"]) * 100.0
            strain_pct = float(pred["strain_score"]) * 100.0
            col5.metric("⚠️ Risk Level", f"{risk_pct:.1f}%")
            col6.metric("💪 Strain Level", f"{strain_pct:.1f}%")
        else:
            col5.metric("⚠️ Risk Level", "—")
            col6.metric("💪 Strain Level", "—")
            st.info("No prediction yet. Open ‘AI Prevention’ and run a prediction.")
    except Exception as e:
        col5.metric("⚠️ Risk Level", "—")
        col6.metric("💪 Strain Level", "—")
        st.warning(f"Could not load latest prediction: {e}")

    st.divider()
    st.subheader("📈 Performance Trends")

    # Plot historical charts
    hist = st.session_state.historical_data

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(px.line(hist, x="Date", y="Heart Rate",
                        title="Heart Rate Trend"), use_container_width=True)
        st.plotly_chart(px.bar(hist, x="Date", y="Steps",
                        title="Daily Steps"), use_container_width=True)
    with col_b:
        st.plotly_chart(px.bar(hist, x="Date", y="Sleep Hours",
                        title="Sleep Duration"), use_container_width=True)
        st.plotly_chart(px.line(hist, x="Date", y="Calories Burned",
                        title="Calories Burned Trend"), use_container_width=True)

# AI Prevention Page

elif page == "🧠 AI Prevention":
    st.title("🧠 AI Injury Prevention Advisor")

    # pull current athlete metrics from backend
    data = fetch_backend_data()

    # compute strain/intensity locally to send to backend
    hr = float(data["heart_rate"])
    steps = int(data["steps"])
    strain = round(((steps / 10000.0) + (hr / 200.0)) / 2.0, 2)
    intensity = round((hr / 200.0) + (steps / 12000.0), 2)

    payload = {
        "athlete": SELECTED_ATHLETE_ID,
        "heart_rate": hr,
        "duration_minutes": 60.0,
        "calories_burned": float(data["calories_burned"]),
        "calculated_intensity": intensity,
        "strain_score": strain,
        "sleep_hours": float(data["sleep_hours"]),
        "steps": steps,
        "fatigue_level": int(data.get("fatigue_level", 0)),
    }

    try:
        resp = requests.post(f"{BASE_URL}/predict/", json=payload, timeout=15)
        if resp.status_code in (200, 201):
            res = resp.json()
            risk_score = float(res.get("score", 0.0))
            risk_level = res.get("risk_level", "low")
            st.metric("Injury Risk Score", f"{risk_score*100:.1f}%")

            if risk_level == "high" or risk_score > 0.7:
                st.error("🚨 High Risk — rest and recovery recommended.")
            elif risk_level == "medium" or risk_score > 0.4:
                st.warning("⚠️ Moderate Risk — reduce intensity.")
            else:
                st.success("✅ Low Risk — safe to train.")

            st.subheader("Personalized Training Advice")
            tips = {
                "high": [
                    "Take a recovery day and hydrate well.",
                    "Avoid intense sessions until metrics stabilize.",
                ],
                "medium": [
                    "Consider a lighter workout today.",
                    "Prioritize sleep and hydration tonight.",
                ],
                "low": [
                    "Metrics look good—you're ready to train.",
                    "Stick to your plan and monitor recovery.",
                ],
            }
            for tip in tips[risk_level]:
                st.write(f"- {tip}")
        else:
            st.error(f"Backend AI error: HTTP {resp.status_code}")
            st.write(resp.text)
    except Exception as e:
        st.error(f"Could not contact backend: {e}")

   # if st.button("Send Data to Backend"):

   # pass

# ------------------------------------------------------------
elif page == "📜 Prediction History":
    st.title("📜 Prediction History")
    try:
        resp = requests.get("http://127.0.0.1:8000/api/predictions/")
        if resp.status_code == 200:
            history = resp.json()
            df = pd.DataFrame(history)
            st.dataframe(
                df[["athlete_name", "risk_level", "strain_score", "created_at"]])
        else:
            st.warning("No prediction data found.")
    except Exception as e:
        st.error(f"Error fetching history: {e}")

# Calendar

elif page == "📅 Calendar":
    st.title("📅 Training & Recovery Calendar")

    st.subheader("Add Event")
    event_title = st.text_input("Event Title")
    event_date = st.date_input("Event Date", datetime.date.today())

    if st.button("Add Event"):
        st.session_state.events.append(
            {"title": event_title, "start": str(event_date), "end": str(event_date)})
        st.success(f"Event '{event_title}' added!")

    st.subheader("Your Calendar")
    calendar(events=st.session_state.events)

# Wearable Devices

elif page == "⌚ Wearable Devices":
    st.title("⌚ Connected Wearables")

    st.markdown("**Currently Connected:**")
    devices = ["Fitbit Charge 5", "Apple Watch Series 8"]
    for d in devices:
        st.write(f"- {d}")

# ---------------------------------------------

if st.button("Send Data to Backend"):
    try:
        payload = {
            "athlete": SELECTED_ATHLETE_ID,
            "heart_rate": st.session_state.wearable_data["heart_rate"],
            "duration_minutes": random.uniform(30, 90),
            "calories_burned": st.session_state.wearable_data["calories_burned"],
            "calculated_intensity": 0.5,
            "strain_score": 0.5,
            "sleep_hours": st.session_state.wearable_data.get("sleep_hours", random.uniform(6, 9)),
            "steps": st.session_state.wearable_data.get("steps", random.randint(1000, 12000)),
            "fatigue_level": st.session_state.wearable_data.get("fatigue_level", random.randint(3, 8)),
        }

        response = requests.post(f"{BASE_URL}/predict/", json=payload)
        if response.status_code in [200, 201]:
            st.success("✅ Data sent successfully!")
            st.session_state.wearable_data = fetch_backend_data(
                SELECTED_ATHLETE_ID)
            st.rerun()
        else:
            st.error(f"❌ Failed to send data. Status: {response.status_code}")
            st.write(response.text)
    except Exception as e:
        st.error(f"⚠️ Error sending data: {e}")


# Profile
elif page == "👤 Profile":
    st.title("👤 User Profile")

    try:
        # Get ONE athlete
        # (Liam Johnson)
        response = requests.get(f"{BASE_URL}/athletes/1/")
        if response.status_code == 200:
            athlete = response.json()
            st.markdown(f"### 🏅 {athlete['name']}")
            st.write(f"**Sport:** {athlete['sport']}")
            st.write(f"**Team:** {athlete['team']}")
            st.write(f"**Age:** {athlete['age']}")
            st.write(
                f"**Experience (years):** {athlete['experience_years']:.1f}")
            st.write(f"**Heart Rate:** {athlete['heart_rate']} bpm")
            st.write(f"**Sleep Hours:** {athlete['sleep_hours']}")
            st.write(f"**Steps:** {athlete['steps']}")
            st.write(f"**Fatigue Level:** {athlete['fatigue_level']}")
        else:
            st.warning("⚠️ Could not load athlete from backend.")
    except Exception as e:
        st.error(f"Error loading athlete profile: {e}")
