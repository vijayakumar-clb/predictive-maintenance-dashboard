#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>

// Update with your actual Mobile Hotspot credentials
const char* ssid = "Vijay";
const char* password = "12121212";

// Your exact HiveMQ Cloud Configurations
const char* mqtt_server = "e17bb346f90b432a9d6298ddf306a9b1.s1.eu.hivemq.cloud"; 
const int mqtt_port = 8883; 
const char* mqtt_user = "admin1";
const char* mqtt_pass = "Vk@217959";

WiFiClientSecure espClient;
PubSubClient client(espClient);

const int VIBRATION_PIN = D5; // Digital Out (DO) pin connected here
unsigned long last_check_time = 0;
int vibration_pulse_count = 0;
int last_sensor_state = HIGH;
const int ANOMALY_THRESHOLD = 40; 

void setup() {
  Serial.begin(115200);
  pinMode(VIBRATION_PIN, INPUT);
  setup_wifi();
  
  // Skip certificate validation for lightweight TLS execution on ESP8266
  espClient.setInsecure(); 
  client.setServer(mqtt_server, mqtt_port);
}

void setup_wifi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) { 
    delay(500); 
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting TLS MQTT connection...");
    if (client.connect("NodeMCU_Vibration", mqtt_user, mqtt_pass)) {
      Serial.println("Connected Securely to HiveMQ!");
    } else {
      Serial.print("Failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) { reconnect(); }
  client.loop();

  // Pulse counting loop for digital 0/1 sensor transitions
  int current_state = digitalRead(VIBRATION_PIN);
  if (current_state != last_sensor_state) {
    if (current_state == LOW) { 
      vibration_pulse_count++;
    }
    last_sensor_state = current_state;
  }

  // Calculate frequency every 5 seconds window
  if (millis() - last_check_time > 5000) {
    String status = (vibration_pulse_count > ANOMALY_THRESHOLD) ? "ANOMALY" : "NORMAL";
    String payload = "{\"vibration_intensity\":" + String(vibration_pulse_count) + ",\"status\":\"" + status + "\"}";
    
    Serial.print("Publishing Payload: ");
    Serial.println(payload);
    
    client.publish("factory/machine1/vibration", payload.c_str());
    
    vibration_pulse_count = 0;
    last_check_time = millis();
  }
}