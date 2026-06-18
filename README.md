# 🏭 Industry 4.0 Real-Time Machine Health Monitor

An Industrial IoT (IIoT) Predictive Maintenance Dashboard built with **Streamlit**, **MQTT**, and **SQLite3**. This system captures real-time edge telemetry (vibration data), logs it into a local database pipeline, dynamically evaluates system health, and visualizes trends using interactive graphics.

## 🚀 Key Features
* **Real-Time Telemetry Streaming:** Integrates a background MQTT client subscribing to secure HiveMQ Cloud brokers over TLS.
* **Edge Persistence Pipeline:** Multi-day historical log archiving using a lightweight SQLite3 embedded relational engine.
* **Automated Dashboard Interactivity:** Embedded UI background self-refresh loops every 2 seconds without full-page reloads.
* **Intelligent Threat Visuals:** Dynamically swaps status metrics and alters chart trends visually to highlight structural anomalies instantly.

---

## 🛠️ System Architecture

1. **Hardware / Data Source:** Edge node streams vibration data packet payloads via MQTT.
2. **Cloud Broker:** HiveMQ Cloud processes and routes secure encrypted traffic over Port 8883.
3. **Database Layer:** Local SQLite3 instance preserves system state log history safely.
4. **Presentation Web Server:** Streamlit and Plotly display sub-second operational metrics.

---

## 💻 Tech Stack & Dependencies
* **Language:** Python
* **Web Framework:** Streamlit, Streamlit Autorefresh
* **MQTT Client:** Paho MQTT (v2 Callback Architecture)
* **Data & Analytics:** Pandas, Plotly Express
* **Database Engine:** SQLite3

---

## ⚙️ Setup and Installation

### 1. Prerequisites
Ensure you have Python installed on your Linux machine. Install all required dependencies via terminal:
```bash
pip install streamlit paho-mqtt pandas plotly streamlit-autorefresh
