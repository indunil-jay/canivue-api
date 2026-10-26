
#include <WiFi.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

Adafruit_MPU6050 mpu;

// ESP32 creates its own Wi-Fi network
const char* ssid = "CanineSensor21";
const char* password = "Collar2026";

WiFiServer server(5000);

const unsigned long SAMPLE_INTERVAL_MS = 10;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);

  if (!mpu.begin()) {
    Serial.println("MPU6050 connection failed");
    while (true) {
      delay(10);
    }
  }
  
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_1000_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_44_HZ);

  Serial.println("Sensor configuration updated");
  Serial.println("Accelerometer: +/-8g");
  Serial.println("Gyroscope: +/-1000 deg/s");


  Serial.println("MPU6050 Ready");

  // Start ESP32 Wi-Fi hotspot
  WiFi.mode(WIFI_AP);

  if (!WiFi.softAP(ssid, password)) {
    Serial.println("Wi-Fi AP failed");
    while (true) {
      delay(1000);
    }
  }

  server.begin();

  Serial.println("Wi-Fi Ready");
  Serial.print("Network: ");
  Serial.println(ssid);
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());
}

void loop() {
  WiFiClient client = server.available();

  if (!client) {
    delay(10);
    return;
  }

  Serial.println("Laptop connected");

  unsigned long lastSampleMs = millis();

  while (client.connected()) {
    unsigned long now = millis();

    if (now - lastSampleMs >= SAMPLE_INTERVAL_MS) {
      lastSampleMs = now;

      sensors_event_t a, g, temp;
      mpu.getEvent(&a, &g, &temp);

      char data[160];

      snprintf(
        data, sizeof(data),
        "%lu,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f\n",
        now,
        a.acceleration.x,
        a.acceleration.y,
        a.acceleration.z,
        g.gyro.x,
        g.gyro.y,
        g.gyro.z
      );

      client.print(data);
    } else {
      delay(1);
    }
  }

  client.stop();
  Serial.println("Laptop disconnected");
}

