import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000/api"
SELECTED_ATHLETE_ID = 9


# ------------------------------------------------------------
# BACKEND FETCHING
# ------------------------------------------------------------
def get_latest_session(athlete_id: int = SELECTED_ATHLETE_ID):
    try:
        res = requests.get(
            f"{BASE_URL}/athletes/{athlete_id}/latest_session/", timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Backend error {res.status_code} on latest_session")
            return {}
    except Exception as e:
        st.error(f"❌ Could not reach backend: {e}")
        return {}


def get_session_history(athlete_id: int = SELECTED_ATHLETE_ID):
    try:
        res = requests.get(
            f"{BASE_URL}/athletes/{athlete_id}/history/", timeout=10)
        if res.status_code == 200:
            return res.json()
        else:
            return []
    except Exception:
        return []


# ------------------------------------------------------------
# SIDEBAR NAVIGATION
# ------------------------------------------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["🏠 Dashboard", "🧠 AI Prevention", "⌚ Wearable Devices", "👤 Profile"]
)


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.athlete_id = None
    st.session_state.athlete_name = None
# ---------------login----


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
# -------------
# ------------------------------------------------------------
# PAGE: DASHBOARD
# ------------------------------------------------------------
if page == "🏠 Dashboard":
    st.title("📊 Athlete Health Dashboard")

    latest = get_latest_session()
    if not latest:
        st.warning("No athlete or session data found.")
        st.stop()

    st.markdown(f"### 🏅 {latest['name']} ({latest['sport']})")

    col1, col2, col3 = st.columns(3)
    col1.metric("❤️ Heart Rate", f"{latest['heart_rate']:.1f} bpm")
    col2.metric("💤 Sleep Hours", f"{latest['sleep_hours']:.2f}")
    col3.metric("🔥 Calories Burned", f"{latest['calories_burned']:.0f}")

    col4, col5, col6 = st.columns(3)
    col4.metric("🏃 Steps", int(latest["steps"]))
    col5.metric("⚡ Intensity", f"{latest['intensity']:.2f}")
    col6.metric("💪 Strain Score", f"{latest['strain_score']:.2f}")

    try:
        r = requests.get(
            f"{BASE_URL}/predictions/latest/{SELECTED_ATHLETE_ID}/",
            timeout=10,
        )
        if r.status_code == 200:
            pred = r.json()
            risk_pct = float(pred["predicted_probability"]) * 100.0
            # 0–10 scale from backend
            strain_idx = float(pred["strain_score"])

            st.subheader("⚠️ Latest ML Risk Assessment")
            c1, c2 = st.columns(2)
            c1.metric("Injury Risk (ML)", f"{risk_pct:.1f}%")
            c2.metric("Strain Index (0–10)", f"{strain_idx:.2f}")
        else:
            st.info(
                "No ML prediction recorded yet. "
                "Visit the **AI Prevention** tab to run one."
            )
    except Exception as e:
        st.warning(f"Could not load latest prediction: {e}")

    st.divider()
    st.subheader("📈 Performance Trends")

    history = get_session_history()
    if not history:
        st.info("No historical data available.")
        st.stop()

    df = pd.DataFrame(history)
    date_key = next(k for k in df.columns if "date" in k.lower())

    df[date_key] = pd.to_datetime(df[date_key])
    df = df.sort_values(date_key)
    df = df.rename(columns={date_key: "session_date"})

    colA, colB = st.columns(2)
    with colA:
        st.plotly_chart(px.line(df, x="session_date", y="heart_rate",
                                title="Heart Rate Over Time"),
                        use_container_width=True)
        st.plotly_chart(px.bar(df, x="session_date", y="steps",
                               title="Steps Per Session"),
                        use_container_width=True)

    with colB:
        st.plotly_chart(px.bar(df, x="session_date", y="sleep_hours",
                               title="Sleep Duration"),
                        use_container_width=True)
        st.plotly_chart(px.line(df, x="session_date", y="calories_burned",
                                title="Calories Burned Trend"),
                        use_container_width=True)


# ------------------------------------------------------------
# PAGE: AI PREVENTION
# ------------------------------------------------------------
# ------------------------------------------------------------
# PAGE: AI PREVENTION
# ------------------------------------------------------------
elif page == "🧠 AI Prevention":
    st.title("🧠 AI Injury Prevention Advisor")

    latest = get_latest_session()
    if not latest:
        st.warning("No athlete or session data found.")
        st.stop()

    st.markdown(
        f"Using **{latest['name']}**'s most recent sessions "
        "to generate an AI-enhanced injury prediction."
    )

    # --------------------------------------------------
    # 1) LOAD TRAINING HISTORY FROM BACKEND
    #    -> /athletes/<id>/history/
    # --------------------------------------------------
    history = []
    try:
        hist_resp = requests.get(
            f"{BASE_URL}/athletes/{SELECTED_ATHLETE_ID}/history/",
            timeout=10,
        )
        if hist_resp.status_code == 200:
            history = hist_resp.json()
        else:
            st.warning("Could not load training history.")
    except Exception as e:
        st.error(f"Could not load training history: {e}")

    # --------------------------------------------------
    # 2) COMPUTE ACWR ON STRAIN SCORE
    # --------------------------------------------------
    def compute_acwr(sessions):
        """
        Acute: last 3 sessions (most recent)
        Chronic: last 7 sessions (training base)
        sessions is ordered oldest -> newest by the backend,
        so we take the last ones here.
        """
        if len(sessions) < 4:
            return None

        # Take up to last 7, reversed so newest first
        recent = list(sessions)[-7:]
        recent = list(reversed(recent))

        acute_sessions = recent[:3]
        chronic_sessions = recent[:7]

        acute = sum(s["strain_score"]
                    for s in acute_sessions) / len(acute_sessions)
        chronic = sum(s["strain_score"]
                      for s in chronic_sessions) / len(chronic_sessions)

        if chronic <= 0:
            return None

        return round(acute / chronic, 2)

    acwr = compute_acwr(history) if history else None

    # --------------------------------------------------
    # 3) SHOW ACWR + SIMPLE RECOMMENDATION
    # --------------------------------------------------
    st.subheader("Training Load Ratio (ACWR)")
    if acwr is None:
        st.info("Not enough load history to compute ACWR yet.")
    else:
        st.metric("ACWR", acwr)
        if acwr < 0.8:
            st.warning(
                "⚠️ Undertraining — consider gradually increasing volume.")
            acwr_note = (
                "Load is lower than your chronic baseline. "
                "You may be underprepared for sudden spikes."
            )
        elif acwr <= 1.3:
            st.success("💪 Optimal Load Zone — safe progression.")
            acwr_note = "Training load is in the sweet spot relative to recent history."
        elif acwr <= 1.6:
            st.warning("⚠️ High Load — increased injury risk.")
            acwr_note = (
                "Recent load is noticeably higher than your base. "
                "Reduce volume or intensity over the next few sessions."
            )
        else:
            st.error("🚨 Load Spike — VERY HIGH injury risk.")
            acwr_note = (
                "Large spike above your chronic load. Rest or low-intensity work is recommended."
            )

        st.markdown(
            f"**Recommendation:** {acwr_note}"
        )

    # --------------------------------------------------
    # 4) BUILD PAYLOAD FOR ML PREDICTION
    # --------------------------------------------------
    payload = {
        "athlete": SELECTED_ATHLETE_ID,
        "heart_rate": float(latest["heart_rate"]),
        "calories_burned": float(latest["calories_burned"]),
        "calculated_intensity": float(latest["intensity"]),
        "strain_score": float(latest["strain_score"]),
        "sleep_hours": float(latest["sleep_hours"]),
        "steps": int(latest["steps"]),
    }

    # --------------------------------------------------
    # 5) CALL BACKEND /predict/  (CREATE_PREDICTION)
    # --------------------------------------------------
    try:
        resp = requests.post(
            f"{BASE_URL}/predict/",
            json=payload,
            timeout=15,
        )
        if resp.status_code == 200:
            result = resp.json()
            prob = float(result.get("probability", 0.0))
            risk_level = result.get("risk_level", "low")
            backend_acwr = result.get("acwr", None)

            st.subheader("AI Injury Risk (ML + workload)")
            st.metric("Risk", f"{prob * 100:.1f}%")

            # Combine ML risk + ACWR    for a short message
            if risk_level == "high" or prob > 0.7:
                st.error("❌ High AI risk — avoid intense training today.")
            elif risk_level == "medium":
                st.warning(
                    "⚠️ Moderate AI risk — train with caution and monitor fatigue.")
            else:
                st.success(" Low AI risk — safe to train.")

            with st.expander("Show full prediction details"):
                st.json(result)
        else:
            st.error(f"Backend error: {resp.status_code}")
    except Exception as e:
        st.error(f"Prediction failed: {e}")


# ------------------------------------------------------------
# PAGE: WEARABLES
# ------------------------------------------------------------
elif page == "⌚ Wearable Devices":
    st.title("⌚ Connected Wearables")
    st.write("- Fitbit Charge 5")
    st.write("- Apple Watch Series 8")


# ------------------------------------------------------------
# PAGE: PROFILE
# ------------------------------------------------------------
elif page == "👤 Profile":
    st.title("👤 Athlete Profile")

    latest = get_latest_session()
    if not latest:
        st.warning("No athlete or session data found.")
        st.stop()

    st.markdown(f"### 🏅 {latest['name']}")
    st.write(f"**Sport:** {latest['sport']}")
    st.write(f"**Team:** {latest['team']}")
    st.write(f"**Age:** {latest['age']}")
    st.write(f"**Experience:** {latest['experience_years']} years")

    st.divider()
    st.subheader("📊 Averages from Last 5 Sessions")

    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Heart Rate", f"{latest['avg_heart_rate']:.1f} bpm")
    c2.metric("Avg Sleep Hours", f"{latest['avg_sleep_hours']:.2f}")
    c3.metric("Avg Steps", f"{latest['avg_steps']:.0f}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Avg Calories", f"{latest['avg_calories_burned']:.0f}")
    c5.metric("Avg Intensity", f"{latest['avg_intensity']:.2f}")
    c6.metric("Avg Strain", f"{latest['avg_strain']:.2f}")

    st.info("These metrics help guide safe workload progression and recovery.")
