import streamlit as st
import paho.mqtt.client as mqtt
import sqlite3
import json
import pandas as pd
import time
import threading

# --- Configuration Constants ---
DB_NAME = "maintenance_data.db"
MQTT_BROKER = "e17bb346f90b432a9d6298ddf306a9b1.s1.eu.hivemq.cloud" 
MQTT_PORT = 8883
MQTT_USER = "vijay123"
MQTT_PASS = "Vk@217959"
MQTT_TOPIC = "machine/vibration"

# --- Page Config & UI Setup ---
st.set_page_config(page_title="IIoT Predictive Maintenance", layout="wide", page_icon="⚙️")
st.title("⚙️ Industrial IoT Predictive Maintenance System")
st.markdown("### Real-Time Machine Telemetry & Predictive Analytics Dashboard")

# --- SQLite Database Initialization ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vibration_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            vibration_status INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Background MQTT Client Listener (Paho v2.x Compatible) ---
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode("utf-8").strip()
        vibration_val = 0
        
        # Safe Parse System: Tries to read JSON first, falls back to raw integer text
        try:
            payload_data = json.loads(raw_payload)
            if isinstance(payload_data, dict):
                vibration_val = int(payload_data.get("vibration", 0))
            else:
                vibration_val = int(payload_data)
        except Exception:
            vibration_val = int(float(raw_payload))
        
        # Log data directly into SQLite instance
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO vibration_logs (vibration_status) VALUES (?)", (vibration_val,))
        conn.commit()
        conn.close()
    except Exception as e:
        pass

def start_mqtt_loop():
    # FIXED: Added CallbackAPIVersion declaration to satisfy paho-mqtt v2.x requirements
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.tls_set() # Enforce mandatory TLS handshake for secure HiveMQ Cloud clusters
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        pass

# Initialize the background broker thread safely once per session lifecycle
if "mqtt_thread" not in st.session_state:
    st.session_state.mqtt_thread = threading.Thread(target=start_mqtt_loop, daemon=True)
    st.session_state.mqtt_thread.start()

# --- Read Data for Analytics Display ---
def fetch_historical_data():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT timestamp, vibration_status FROM vibration_logs ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.iloc[::-1].reset_index(drop=True) # Sort oldest to newest left-to-right
    return df

# Get latest dataframe entries
data_df = fetch_historical_data()

# --- Dashboard Layout Panels ---
if not data_df.empty:
    latest_row = data_df.iloc[-1]
    current_status = int(latest_row['vibration_status'])
    last_update_time = latest_row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

    # 1. Analytics KPI Progress Metric Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Last Recorded Signal State", value="⚠️ HIGH VIBRATION" if current_status == 1 else "✅ STABLE")
    with col2:
        total_samples = len(data_df)
        anomaly_samples = (data_df['vibration_status'] == 1).sum()
        stress_percentage = (anomaly_samples / total_samples) * 100 if total_samples > 0 else 0
        st.metric(label="Machine Stress Factor (Anomaly %)", value=f"{stress_percentage:.1f} %")
    with col3:
        st.metric(label="Last Data Sync Timestamp", value=str(last_update_time))

    # 2. Predictive Analytics Status Warning Blocks
    st.markdown("#### 🚨 Predictive Diagnostics Analysis")
    if current_status == 1:
        st.error("### CRITICAL ANOMALY ALERT: Structural vibration thresholds exceeded! Mechanical fatigue detected.")
    elif stress_percentage > 35:
        st.warning("### PREDICTIVE WARNING: Repeated vibration spikes observed over historical timeline window. Schedule check soon.")
    else:
        st.success("### SYSTEM HEALTHY: Machine telemetry indicates normal baseline operation within design limits.")

    # 3. Telemetry Visualizer Linear Chart
    st.markdown("#### 📊 Real-Time Time-Series Analytics")
    chart_data = data_df.copy()
    chart_data = chart_data.set_index('timestamp')
    st.line_chart(chart_data['vibration_status'], height=300)

    # 4. Raw Historical Matrix View
    with st.expander("📂 Inspect Raw SQLite Historical Log Data"):
        st.dataframe(data_df, use_container_width=True)
else:
    st.info("🔄 Awaiting incoming telemetry stream payload from NodeMCU hardware via HiveMQ... Ensure your hardware is actively publishing.")

# Autorefresh the page views every 2 seconds automatically
time.sleep(2)
st.rerun()
