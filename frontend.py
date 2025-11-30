import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000/api"
SELECTED_ATHLETE_ID = 1


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
elif page == "🧠 AI Prevention":
    st.title("🧠 AI Injury Prevention Advisor")

    latest = get_latest_session()
    if not latest:
        st.warning("No athlete or session data found.")
        st.stop()

    st.markdown(
        f"Analyzing **{latest['name']}**'s current workload using real ML predictions."
    )

    payload = {
        "athlete": SELECTED_ATHLETE_ID,
        "heart_rate": latest["heart_rate"],
        "duration_minutes": latest.get("duration_minutes", 60.0),
        "calories_burned": latest["calories_burned"],
        "calculated_intensity": latest["intensity"],
        "strain_score": latest["strain_score"],
        "sleep_hours": latest["sleep_hours"],
        "steps": latest["steps"],
        "fatigue_level": latest.get("fatigue_level", 0),
    }

    try:
        resp = requests.post(f"{BASE_URL}/predict/", json=payload, timeout=15)
        if resp.status_code in (200, 201):
            result = resp.json()
            risk_score = float(result.get("probability", 0.0))
            risk_level = result.get("risk_level", "low")

            st.metric("Injury Risk Score (ML)", f"{risk_score * 100:.1f}%")

            if risk_level == "high" or risk_score > 0.7:
                st.error("🚨 High Risk — rest and recovery recommended.")
                st.write(
                    "• Reduce workload immediately.\n• Increase sleep.\n• Consult athletic trainer.")
            elif risk_level == "medium" or risk_score > 0.4:
                st.warning("⚠️ Moderate Risk — monitor and adjust intensity.")
                st.write(
                    "• Hydrate well.\n• Avoid sudden workload spikes.\n• Prioritize recovery.")
            else:
                st.success("✅ Low Risk — Good to Train")
                st.write(
                    "• Maintain balanced intensity.\n• Warm-up properly.\n• Monitor biomechanics.")
        else:
            st.error(f"Backend error: {resp.status_code}")
    except Exception as e:
        st.error(f"Could not contact backend: {e}")


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
