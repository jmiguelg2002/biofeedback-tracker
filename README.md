📊 Biofeedback Tracker

A real-time biofeedback application that monitors physiological signals (e.g., heart rate, HRV, stress) from a mobile device or simulated input. It integrates with 5G Network APIs (NEF/PCF) to dynamically adjust QoS policies and trigger emergency alerts in case of critical stress.

🧠 Features

📡 Real-Time Data Monitoring (heart rate, HRV, stress)

🧈 Mood Classification: Focused, Distracted, Stressed, Critical

🧠 Stress Peak Detection with timeline

🌋 QoS Policy Integration via NEF/PCF mock APIs

🚨 911 Emergency Trigger when stress exceeds critical threshold

📀 Session Logging into SQLite and CSV export

🎤 Voice Summary: Spoken feedback using TTS (Text-to-Speech)

🎶 Optional voice input with Whisper (coming soon)

📝 User Notes for emotional context

🚧 Architecture Overview

+-------------------+       +------------------+      +-------------------+
|   Mobile Device   | <---> | Streamlit Client | ---> |   Biofeedback DB  |
| (Sensors/Voice AI)|       |  (app.py)        |      |   (SQLite, CSV)   |
+-------------------+       +------------------+      +-------------------+
        |                            |
        |                            v
        |                    +------------------+
        |                    |  NEF/PCF Mock API|
        |                    | (QoS + Emergency)|
        |                    +------------------+
        |                            |
        |                            v
        |                   🚨 Notify Emergency (911)

🚀 How to Run

Clone the Repo

git clone https://github.com/jmiguelg2002/biofeedback-tracker.git
cd biofeedback-tracker

Install Requirements

pip install -r requirements.txt

Run NEF Mock API

cd nef-api
uvicorn mock_api:app --reload

Run the Biofeedback Tracker App

streamlit run app.py

🧪 Test Scenarios

Simulate a session by selecting a user and app.

Observe how QoS policy changes based on stress.

If stress > 95, emergency alert is triggered and sent to NEF.

Receive voice feedback at the end of session.

📁 Project Structure

biofeedback-tracker/
├── app.py                    # Main Streamlit app
├── db.py                     # SQLite ORM with SQLAlchemy
├── nef-api/
│   └── mock_api.py           # Mock NEF/PCF Policy and Emergency endpoint
├── requirements.txt
└── README.md

📦 Dependencies

streamlit

requests

sqlalchemy

pyttsx3 (TTS)

whisper (optional, voice input)

sounddevice, numpy (for recording)

🔐 Emergency Policy

Critical stress (stress > 95) triggers a POST to NEF API:

{
  "user_id": "user_001",
  "app_id": "work",
  "stress": 98,
  "emergency": true
}

📄 License

MIT License © 2025 Jose Miguel Gomez
