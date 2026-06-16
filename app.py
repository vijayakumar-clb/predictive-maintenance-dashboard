import streamlit as st
import paho.mqtt.client as mqtt
import sqlite3
import json
import pandas as pd
import time
import threading
from datetime import datetime

# --- Configuration Constants ---
DB_NAME = "maintenance_data.db"
# Replace these with your exact HiveMQ credentials from your terminal setup
MQTT_BROKER = "e17bb346f90b432a9d629ddf306a9b11.s1.eu.hivemq.cloud" 
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

# --- Background MQTT Client Listener ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload_data = json.loads(msg.payload.decode("utf-8"))
        # Parse out your NodeMCU payload value: {"vibration": X}
        vibration_val = int(payload_data.get("vibration", 0))
        
        # Log data directly into SQLite
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO vibration_logs (vibration_status) VALUES (?)", (vibration_val,))
        conn.commit()
        conn.close()
    except Exception as e:
        pass

def start_mqtt_loop():
    client = mqtt.Client()
    client.tls_set() # Mandatory TLS for HiveMQ Cloud connections
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"MQTT Connection Error: {e}")

# Initialize the background broker thread once per app lifecycle
if "mqtt_thread" not in st.session_state:
    st.session_state.mqtt_thread = threading.Thread(target=start_mqtt_loop, daemon=True)
    st.session_state.mqtt_thread.start()

# --- Read Data for Analytics Display ---
def fetch_historical_data():
    conn = sqlite3.connect(DB_NAME)
    # Pull the last 50 data frames to avoid UI lagging
    df = pd.read_sql_query("SELECT timestamp, vibration_status FROM vibration_logs ORDER BY id DESC LIMIT 50", conn)
    conn.close()
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.iloc[::-1].reset_index(drop=True) # Read oldest to newest left-to-right
    return df

# Get latest frame state
data_df = fetch_historical_data()

# --- Dashboard Layout Panels ---
if not data_df.empty:
    latest_row = data_df.iloc[-1]
    current_status = int(latest_row['vibration_status'])
    last_update_time = latest_row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

    # 1. Analytics KPI Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Last Recorded Signal State", value="⚠️ HIGH VIBRATION" if current_status == 1 else "✅ STABLE")
    with col2:
        # Analytics Calculation: Duty percentage of runtime stress anomalies
        total_samples = len(data_df)
        anomaly_samples = data_df['vibration_status'].sum()
        stress_percentage = (anomaly_samples / total_samples) * 100 if total_samples > 0 else 0
        st.metric(label="Machine Stress Factor (Anomaly %)", value=f"{stress_percentage:.1f} %")
    with col3:
        st.metric(label="Last Data Sync Timestamp", value=str(last_update_time))

    # 2. Predictive Analytics Rule Engine & Status Banners
    st.markdown("#### 🚨 Predictive Diagnostics Analysis")
    if current_status == 1:
        st.error("### CRITICAL ANOMALY ALERT: Structural vibration thresholds exceeded! Maintenance required immediately.")
    elif stress_percentage > 40:
        st.warning("### PREDICTIVE WARNING: Frequent microscopic vibration spikes observed over last 50 samples. Check machine alignment soon.")
    else:
        st.success("### SYSTEM HEALTHY: Machine telemetry indicates normal operation within standard baselines.")

    # 3. Telemetry Visualizer Graph
    st.markdown("#### 📊 Real-Time Time-Series Analytics")
    # Clean display mapping for line charts
    chart_data = data_df.copy()
    chart_data = chart_data.set_index('timestamp')
    st.line_chart(chart_data['vibration_status'], height=300)

    # 4. Raw Historical Log Matrix
    with st.expander("📂 Inspect Raw SQLite Historical Log Data"):
        st.dataframe(data_df, use_container_width=True)
else:
    st.info("🔄 Awaiting incoming telemetry stream payload from NodeMCU hardware via HiveMQ...")

# Autorefresh the script view page every 2 seconds for continuous updating
time.sleep(2)
st.rerun()
