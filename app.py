import streamlit as st
import paho.mqtt.client as mqtt
import sqlite3
import pandas as pd
import plotly.express as px
import json
from datetime import datetime

# Streamlit Page Setup
st.set_page_config(page_title="IIoT Predictive Maintenance", layout="wide")
st.title("🏭 Cloud Industry 4.0 Machine Health Monitor")
st.markdown("Predictive maintenance tracking via secure MQTT and digital vibration metrics.")

DB_NAME = "cloud_factory.db"

# Initialize Local Storage Database inside Streamlit Server Instance
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS logs 
                    (timestamp TEXT, vibration REAL, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Callback logic when data hits HiveMQ Cloud
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs VALUES (?, ?, ?)", 
                       (datetime.now().strftime('%H:%M:%S'), payload['vibration_intensity'], payload['status']))
        conn.commit()
        conn.close()
    except Exception as e:
        pass

# Maintain a persistent background MQTT thread across Streamlit reruns
if 'mqtt_connected' not in st.session_state:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set("admin1", "Vk@217959") 
    client.tls_set() # Activates required TLS encryption for port 8883
    client.on_message = on_message
    
    client.connect("e17bb346f90b432a9d6298ddf306a9b1.s1.eu.hivemq.cloud", 8883, 60)
    client.subscribe("factory/machine1/vibration")
    client.loop_start()
    st.session_state['mqtt_connected'] = True

# Read past history trends from local SQLite
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql_query("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 50", conn)
conn.close()

if not df.empty:
    df = df.iloc[::-1] # Sort chronologically for timeline display
    
    # Industrial Layout Design: Main UI KPI Cards
    col1, col2 = st.columns(2)
    col1.metric("Latest Vibration Frequency", f"{int(df.iloc[-1]['vibration'])} Pulses / 5s")
    
    status_val = df.iloc[-1]['status']
    if status_val == "ANOMALY":
        col2.error(f"⚠️ Critical System Anomaly Detected")
    else:
        col2.success(f"✅ Machine Operation Stable")
    
    st.markdown("---")
    
    # Render Interactive Plotly Trend Graphic
    fig = px.line(df, x='timestamp', y='vibration', title="Vibration Frequency Intensity (Historical Log Graph)")
    fig.update_traces(line_color='#29B5E8' if status_val == "NORMAL" else '#FF4B4B')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("🔄 System Online. Awaiting automated telemetry updates from NodeMCU Edge Device...")

if st.button("🔄 Refresh Telemetry Dashboard"):
    st.rerun()
