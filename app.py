
import streamlit as st
import time
import uuid
import pandas as pd
import requests
from db import SessionLocal, BiofeedbackLog
from datetime import datetime
import random

# --- Constants ---
DEFAULT_DURATION = 120
APP_OPTIONS = ["work", "gaming", "social", "messages"]
MOCK_API_URL = "https://nef-api.onrender.com/get_policy"
#SES_URL = "http://localhost:8081/validate"
SES_URL = "https://mock-ses.onrender.com/validate" 

QOS_MAPPING = {
    "Policy-Gold": "High",
    "Policy-Silver": "Medium",
    "Policy-Bronze": "Low"
}

def map_policy_to_qos(policy):
    return QOS_MAPPING.get(policy, "Unknown")

def get_policy_from_nef(user_id, app_id, stress=None):
    try:
        params = {"user_id": user_id, "app_id": app_id}
        if stress is not None:
            params["stress"] = stress
        response = requests.get(MOCK_API_URL, params=params, timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print("NEF/PCF API call failed:", e)
    return {"policy": "Policy-Silver", "bandwidth": 50, "latency": 50}

def generate_mock_data():
    return {
        "heart_rate": random.randint(60, 100),
        "hrv": random.randint(20, 80),
        "stress": random.randint(30, 100)
    }

def determine_state(stress, hrv):
    if stress > 95:
        return "Critical"
    elif stress > 80:
        return "Stressed"
    elif hrv < 30:
        return "Distracted"
    elif stress < 40 and hrv > 50:
        return "Focused"
    else:
        return "Normal"

def summarize_session(df):
    avg_hr = df["heart_rate"].mean()
    avg_hrv = df["hrv"].mean()
    avg_stress = df["stress"].mean()
    avg_bw = df["bandwidth"].mean()
    avg_latency = df["latency"].mean()
    status = determine_state(avg_stress, avg_hrv)
    max_hr = df["heart_rate"].max()
    min_hr = df["heart_rate"].min()
    max_stress = df["stress"].max()
    min_hrv = df["hrv"].min()
    return avg_hr, avg_hrv, avg_stress, avg_bw, avg_latency, status, max_hr, min_hr, max_stress, min_hrv

# --- SES Authentication ---
def authenticate_with_ses(imsi):
    try:
        response = requests.post(SES_URL, json={"imsi": imsi}, timeout=2)
        if response.status_code == 200:
            return response.json().get("user_id")
    except Exception as e:
        st.error(f"SES authentication failed: {e}")
    return None

# --- Streamlit UI ---
st.set_page_config(page_title="Biofeedback Tracker", layout="wide")
st.title("📈 Real-Time Biofeedback Tracker")

# Input IMSI
imsi_input = st.text_input("Enter IMSI to Authenticate", max_chars=20, help="Example: 714011002222222")

authenticated_user = None
if imsi_input:
    authenticated_user = authenticate_with_ses(imsi_input)
    if authenticated_user:
        st.success(f"✅ Authenticated as {authenticated_user}")
    else:
        st.error("❌ Authentication failed. Please check IMSI.")

if authenticated_user:
    app_id = st.selectbox("Select Application", APP_OPTIONS)
    duration = st.slider("Session Duration (seconds)", 10, 600, DEFAULT_DURATION)

    if 'pause_state' not in st.session_state:
        st.session_state.pause_state = False
    if 'data_log' not in st.session_state:
        st.session_state.data_log = []
    if 'stress_peaks' not in st.session_state:
        st.session_state.stress_peaks = []
    if 'max_stress_seen' not in st.session_state:
        st.session_state.max_stress_seen = 0
    if 'session_active' not in st.session_state:
        st.session_state.session_active = False

    if st.button("Start Session"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.end_time = time.time() + duration
        st.session_state.data_log = []
        st.session_state.stress_peaks = []
        st.session_state.max_stress_seen = 0
        st.session_state.pause_state = False
        st.session_state.session_active = True

    if st.button("Pause/Resume"):
        st.session_state.pause_state = not st.session_state.pause_state

    if st.session_state.get('session_active', False) and time.time() < st.session_state.end_time:
        session = SessionLocal()
        placeholder = st.empty()

        while time.time() < st.session_state.end_time:
            if st.session_state.pause_state:
                time.sleep(0.5)
                continue

            now = datetime.utcnow()
            data = generate_mock_data()
            nef_data = get_policy_from_nef(authenticated_user, app_id, data["stress"])
            policy = nef_data["policy"]
            bandwidth = nef_data["bandwidth"]
            latency = nef_data["latency"]
            qos_level = map_policy_to_qos(policy)
            state = determine_state(data["stress"], data["hrv"])

            if data["stress"] > st.session_state.max_stress_seen:
                st.session_state.max_stress_seen = data["stress"]
                if data["stress"] > 95:
                    st.session_state.stress_peaks.append({"time": now, "stress": data["stress"]})

            if state == "Critical":
                st.error("🚨 Critical stress detected! Emergency escalation triggered.")
                with open("emergency_contact_log.txt", "a") as f:
                    f.write(f"{now} - {authenticated_user} - {app_id} - Critical stress\n")

            log = BiofeedbackLog(
                session_id=st.session_state.session_id,
                user_id=authenticated_user,
                app_id=app_id,
                heart_rate=int(data["heart_rate"]),
                hrv=int(data["hrv"]),
                stress=int(data["stress"]),
                state=state,
                qos_level=qos_level,
                bandwidth=float(bandwidth),
                latency=float(latency),
                policy=policy,
                timestamp=now
            )
            session.add(log)
            session.commit()

            st.session_state.data_log.append({
                "time": now,
                **data,
                "bandwidth": bandwidth,
                "latency": latency,
                "state": state,
                "qos": qos_level
            })

            df = pd.DataFrame(st.session_state.data_log)
            with placeholder.container():
                st.subheader(f"Live Session - {authenticated_user} ({app_id})")
                st.line_chart(df.set_index("time")[["heart_rate", "hrv", "stress"]], height=400)
                st.metric("Current State", state)
                st.metric("QoS Level", qos_level)

                if st.session_state.stress_peaks:
                    st.write("### 🧠 Stress Peaks Timeline")
                    peak_df = pd.DataFrame(st.session_state.stress_peaks)
                    st.dataframe(peak_df.set_index("time"))

            time.sleep(1)

        df = pd.DataFrame(st.session_state.data_log)
        avg_hr, avg_hrv, avg_stress, avg_bw, avg_latency, status, max_hr, min_hr, max_stress, min_hrv = summarize_session(df)
        st.subheader("📝 Session Summary")
        st.write(f"**Session ID:** {st.session_state.session_id}")
        st.metric("Average Heart Rate", f"{avg_hr:.2f} bpm")
        st.metric("Average HRV", f"{avg_hrv:.2f}")
        st.metric("Average Stress", f"{avg_stress:.2f}")
        st.metric("Average Bandwidth", f"{avg_bw:.2f} Mbps")
        st.metric("Average Latency", f"{avg_latency:.2f} ms")
        st.metric("Overall Status", status)
        st.write(f"👤 IMSI: `{imsi_input}` | 🧾 Mapped User ID: `{authenticated_user}` | 📱 App: `{app_id}` | 📊 QoS Policy: `{policy}`")

        df["time"] = df["time"].astype(str)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Session Data as CSV",
            data=csv,
            file_name=f"biofeedback_session_{st.session_state.session_id}.csv",
            mime='text/csv',
        )

        session.close()
        st.session_state.session_active = False
