import streamlit as st
import time
import uuid
import pandas as pd
import requests
from db import SessionLocal, BiofeedbackLog
from datetime import datetime
import random

st.set_page_config(page_title="Biofeedback Tracker", layout="wide")

# --- Constants ---
DEFAULT_DURATION = 120
USER_OPTIONS = ["user_001", "user_002", "user_abc"]
APP_OPTIONS = ["work", "gaming", "social", "messages"]

MOCK_API_URL = "https://nef-api.onrender.com/get_policy"  # ← update this to your public URL

QOS_MAPPING = {
    "Policy-Gold": "High",
    "Policy-Silver": "Medium",
    "Policy-Bronze": "Low"
}

def map_policy_to_qos(policy):
    return QOS_MAPPING.get(policy, "Unknown")

def get_policy_from_nef(user_id, app_id):
    try:
        response = requests.get(
            MOCK_API_URL,
            params={"user_id": user_id, "app_id": app_id},
            timeout=2
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print("NEF/PCF API call failed:", e)
    return {"policy": "Policy-Silver", "bandwidth": 50, "latency": 50}

def generate_mock_data():
    return {
        "heart_rate": random.randint(60, 100),
        "hrv": random.randint(20, 80),
        "stress": random.randint(30, 90)
    }

def determine_state(stress, hrv):
    if stress > 80:
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

# --- Streamlit UI ---
st.title("📈 Real-Time Biofeedback Tracker")

user_id = st.selectbox("Select User", USER_OPTIONS)
app_id = st.selectbox("Select Application", APP_OPTIONS)
duration = st.slider("Session Duration (seconds)", 10, 600, DEFAULT_DURATION)

note = st.text_area("Optional Note for This Session", placeholder="E.g. Feeling anxious today, testing after workout...")

if 'pause_state' not in st.session_state:
    st.session_state.pause_state = False
if 'data_log' not in st.session_state:
    st.session_state.data_log = []
if 'session_active' not in st.session_state:
    st.session_state.session_active = False

if st.button("Start Session"):
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.end_time = time.time() + duration
    st.session_state.data_log = []
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
        nef_data = get_policy_from_nef(user_id, app_id)
        policy = nef_data["policy"]
        bandwidth = nef_data["bandwidth"]
        latency = nef_data["latency"]
        qos_level = map_policy_to_qos(policy)
        state = determine_state(data["stress"], data["hrv"])

        log = BiofeedbackLog(
            session_id=st.session_state.session_id,
            user_id=user_id,
            app_id=app_id,
            heart_rate=int(data["heart_rate"]),
            hrv=int(data["hrv"]),
            stress=int(data["stress"]),
            state=state,
            qos_level=qos_level,
            bandwidth=float(bandwidth),
            latency=float(latency),
            policy=policy,
            note=note,
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
            st.subheader(f"Live Session - {user_id} ({app_id})")
            st.line_chart(df.set_index("time")["heart_rate"], height=300, use_container_width=True)
            st.line_chart(df.set_index("time")["hrv"], height=300, use_container_width=True)
            st.line_chart(df.set_index("time")["stress"], height=300, use_container_width=True)
            st.metric("Current State", state)
            st.metric("QoS Level", qos_level)

        time.sleep(1)

    # Session Summary
    df = pd.DataFrame(st.session_state.data_log)
    avg_hr, avg_hrv, avg_stress, avg_bw, avg_latency, status, max_hr, min_hr, max_stress, min_hrv = summarize_session(df)
    st.subheader("📝 Session Summary")
    st.write(f"**Session ID:** {st.session_state.session_id}")
    st.write(f"**User Note:** {note}")
    st.metric("Average Heart Rate", f"{avg_hr:.2f} bpm")
    st.metric("Min Heart Rate", f"{min_hr:.2f} bpm")
    st.metric("Max Heart Rate", f"{max_hr:.2f} bpm")
    st.metric("Average HRV", f"{avg_hrv:.2f}")
    st.metric("Min HRV", f"{min_hrv:.2f}")
    st.metric("Average Stress", f"{avg_stress:.2f}")
    st.metric("Max Stress", f"{max_stress:.2f}")
    st.metric("Average Bandwidth", f"{avg_bw:.2f} Mbps")
    st.metric("Average Latency", f"{avg_latency:.2f} ms")
    st.metric("Overall Status", status)
    
    # CSV Download
    df["time"] = df["time"].astype(str)  # convert datetime to string for CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
    label="📥 Download Session Data as CSV",
    data=csv,
    file_name=f"biofeedback_session_{st.session_state.session_id}.csv",
    mime='text/csv',
    )


    session.close()
    st.session_state.session_active = False
