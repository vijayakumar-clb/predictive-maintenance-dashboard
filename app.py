import streamlit as st
import paho.mqtt.client as mqtt
import sqlite3
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="IIoT Predictive Maintenance Panel", 
    layout="wide"
)

st.title("🏭 Industry 4.0 Real-Time Machine Health Monitor")
st.markdown("Automated edge telemetry capture, anomaly alerting, and multi-day data persistence.")

# --- 2. Automatically Refresh the Page Every 2 Seconds ---
# This safely triggers a clean rerun of the script, updating data without ID duplication errors.
st_autorefresh(interval=2000, key="vibration_data_refresh")

DB_NAME = "cloud_factory.db"

# --- 3. SQL Database Setup ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS logs 
                    (timestamp TEXT, vibration_intensity INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. Persistent MQTT Background Client ---
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs VALUES (?, ?, ?)", 
                       (current_time, int(payload['vibration_intensity']), payload['status']))
        conn.commit()
        conn.close()
    except Exception as e:
        pass

if 'mqtt_connected' not in st.session_state:
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set("admin1", "Vk@217959") 
    client.tls_set() 
    client.on_message = on_message
    
    try:
        client.connect("e17bb346f90b432a9d6298ddf306a9b1.s1.eu.hivemq.cloud", 8883, 60)
        client.subscribe("factory/machine1/vibration")
        client.loop_start()
        st.session_state['mqtt_connected'] = True
    except Exception as e:
        st.error(f"Failed to connect to cloud broker: {e}")

# --- 5. Data Fetching ---
def get_historical_data(limit=100):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(f"SELECT * FROM logs ORDER BY timestamp DESC LIMIT {limit}", conn)
    conn.close()
    if not df.empty:
        df = df.iloc[::-1] # Order oldest to newest for visual timelines
    return df

# --- 6. Render Layout ---
df_logs = get_historical_data(limit=100)

if not df_logs.empty:
    latest_record = df_logs.iloc[-1]
    machine_status = latest_record['status']
    
    # 🚨 Live Alert Banner
    if machine_status == "ANOMALY":
        st.error(f"⚠️ CRITICAL FAULT WARNING: High vibration detected at {latest_record['timestamp']}! Inspect machine bearing immediately.")
    else:
        st.success("🟢 SYSTEM STATE HEALTHY: Normal rotational harmonics detected.")
    
    st.markdown("### 📈 Live Telemetry Summary")
    
    # Metric KPI Display
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Vibration Pulse Count", f"{int(latest_record['vibration_intensity'])} Shakes / 5s")
    col2.metric("System Evaluation Status", str(machine_status))
    col3.metric("Last Data Update Time", str(latest_record['timestamp'].split(" ")[1]))
    
    st.markdown("---")
    
    # Interactive Timeline Visualization Chart
    fig = px.line(
        df_logs, 
        x='timestamp', 
        y='vibration_intensity', 
        title="Continuous Machine Vibe Frequency Log Trend",
        markers=True
    )
    fig.update_traces(line_color='#FF4B4B' if machine_status == "ANOMALY" else '#00CC96')
    fig.update_layout(xaxis_title="Time Logged", yaxis_title="Pulses (Intensity)")
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw Data Log Table View for daily audits
    with st.expander("📋 View Daily Data Log Table"):
        st.dataframe(df_logs[['timestamp', 'vibration_intensity', 'status']].tail(20), use_container_width=True)
        
else:
    st.info("📡 Connecting to live stream... Shaking your hardware sensor will push data immediately.")
