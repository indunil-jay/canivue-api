# Behavioural (Sensor) Model

Trains a hybrid 1D-CNN-LSTM (or temporal Transformer) over fixed-length
windows of six-axis IMU data (Ax, Ay, Az, Gx, Gy, Gz) from the ESP32/MPU6050
collar (proposal §5.7.2). Serves a future
`app/features/behavioural_analysis/infrastructure/ml/engine.py`.

- **Windowing**: raw streams are cut into fixed windows (e.g. 10s at
  50–100Hz) in `dataset.py` before batching — this is the same "windowing"
  step the serving-side preprocessing must replicate exactly at inference
  time, so keep the window/stride constants in one place and import them
  from both `dataset.py` and the eventual serving `preprocessing.py`.
- **Sensor-quality gating**: packet-loss, signal clipping, and sampling-rate
  consistency (proposal §5.7.2) should be computed the same way here as in
  serving so training data quality matches what the model sees live.
- **Labels**: `Normal movement, Resting, Walking, Running, Excessive
  scratching, Head shaking, Limping/gait abnormality, Reduced activity` — see
  `dataset.py::BEHAVIOUR_LABELS`.
- **Data**: 30–50 dogs, repeated sessions, video-synchronized behaviour
  labels (proposal Table 4) — not committed to the repo (`.gitignore`'s
  `datasets/` entry).

## Usage (once real data is wired in)

```bash
pip install -r requirements-ml.txt   # from repo root
python -m ml.behavioural.train --data-dir /path/to/sensor_sessions --epochs 30 \
    --out model_registry/behavioural/cnn_lstm_v1.pt
```

## Model versions

| Version | Trained on | Notes |
|---|---|---|
| _(none yet)_ | — | Follow `ml/vision/train.py` as the worked reference for this training loop's shape. |

# Behaviour Sensor Module

## Adaptive Multimodal AI System for Canine Disease Detection and Progression Risk Prediction

**Project:** Final-Year Software Engineering Project  
**Group:** Group 21  
**Module:** Behaviour Sensor Module  
**Hardware:** ESP32 and MPU6050  
**Programming Languages:** C++ (Arduino), Python

## 1. Module Overview

The Behaviour Sensor Module collects motion data using an MPU6050 inertial measurement unit (IMU) connected to an ESP32 microcontroller.

The module measures acceleration along three axes and angular velocity along three axes. The ESP32 processes these measurements and transmits them wirelessly to a laptop using Wi-Fi.

A Python application receives the sensor measurements and saves them as CSV files. These files will support the development and evaluation of machine learning models for canine behaviour classification.

The intended behaviour classes include:

- Resting
- Walking
- Running
- Scratching
- Head shaking

The current implementation focuses on sensor communication, wireless data transmission, CSV recording, and initial signal validation.

## 2. System Architecture

The data collection process follows this workflow:

1. The MPU6050 measures acceleration and angular velocity.
2. The ESP32 reads the six sensor measurements through I2C.
3. The ESP32 creates a Wi-Fi access point.
4. The laptop connects to the ESP32 Wi-Fi network.
5. The Python logger receives sensor measurements through a TCP connection.
6. The logger saves the received measurements in CSV format.
7. Python scripts validate and analyse the collected sensor data.
8. The validated and appropriately labelled data will be prepared for machine learning.

## 3. Hardware Requirements

The current prototype uses:

- ESP32 development board with a compatible USB-to-UART interface
- MPU6050 sensor module
- USB data cable
- Laptop running Windows
- Arduino IDE
- Python 3
- Wi-Fi support on the laptop

A separate Wi-Fi module is not required because the ESP32 has built-in Wi-Fi.

The current prototype uses USB for power during bench testing. Portable power and a suitable collar enclosure are required before collecting data from freely moving dogs.

## 4. Hardware Connections

Connect the MPU6050 to the ESP32 as follows:

| MPU6050 Pin | ESP32 Pin |
|---|---|
| VCC | 3.3V |
| GND | GND |
| SDA | GPIO 21 |
| SCL | GPIO 22 |

Disconnect power before changing the wiring.

## 5. Software Configuration

### 5.1 Arduino IDE

Install Arduino IDE and add the ESP32 board package through Boards Manager.

Select the appropriate ESP32 board and the COM port associated with the USB-to-UART device.

Install the following libraries through Arduino IDE Library Manager:

- Adafruit MPU6050
- Adafruit Unified Sensor

Install any additional dependencies requested by the library manager.

### 5.2 Sensor Configuration

The current firmware uses the following settings:

| Parameter | Setting |
|---|---|
| Sensor | MPU6050 |
| Accelerometer range | ±8g |
| Gyroscope range | ±1000°/s |
| Filter bandwidth | 44 Hz |
| Target sampling frequency | 100 Hz |
| Sampling interval | 10 ms |
| Communication interface | I2C |

The actual sampling frequency and data quality should be verified for each recording session.

### 5.3 Wi-Fi Configuration

The firmware configures the ESP32 as a Wi-Fi access point.

| Parameter | Development setting |
|---|---|
| SSID | CanineSensor21 |
| TCP server port | 5000 |
| Default access-point IP | 192.168.4.1 |
| Data transport | TCP over Wi-Fi |

The Wi-Fi password is defined in the firmware. Configure credentials appropriately for local testing and do not commit real passwords or other secrets to a shared repository.

## 6. Repository Structure

The recommended module structure is:

```text
behaviour-sensor/
├── README.md
├── firmware/
│   └── esp32_wifi_sensor/
│       └── esp32_wifi_sensor.ino
└── data-logger/
    ├── wifi_sensor_logger.py
    ├── validate_csv.py
    ├── analyze_sensor_data.py
    └── requirements.txt
```

The firmware directory contains the ESP32 program. The data-logger directory contains the Python recording, validation, and analysis scripts.

Generated CSV recordings should be stored separately from the source code and excluded from Git commits unless the project team approves their inclusion.

## 7. Python Environment Setup

Open a terminal in the `data-logger` directory.

Install the required dependency:

```bash
py -m pip install -r requirements.txt
```

The `requirements.txt` file should contain:

```text
pyserial
```

The wireless logger uses Python's standard library. PySerial is required for USB serial logging if that functionality is also used.

## 8. Running the ESP32 Firmware

1. Connect the ESP32 to the laptop using a USB data cable.
2. Open `esp32_wifi_sensor.ino` in Arduino IDE.
3. Select the appropriate ESP32 board and COM port.
4. Upload the firmware.
5. Open Serial Monitor at 115200 baud to inspect startup and debugging messages.
6. Confirm that the MPU6050 initializes and the Wi-Fi access point starts.

Once the firmware is uploaded, the ESP32 stores it in flash memory and can run it again whenever power is restored.

## 9. Wireless CSV Data Collection

### Step 1: Power the ESP32

Connect the ESP32 to USB power during bench testing.

### Step 2: Connect to the Wi-Fi network

Connect the laptop to `CanineSensor21` using the configured development password.

The network provides local connectivity and does not require Internet access.

### Step 3: Start the Python logger

From the `data-logger` directory, run:

```bash
py wifi_sensor_logger.py
```

The current test script records for approximately 30 seconds.

### Step 4: Verify the recording

The logger creates a timestamped CSV file, for example:

```text
wifi_bench_20261025_131302.csv
```

The exact filename depends on the recording date and time.

The current bench-test logger uses the label `unverified_motion`. This label indicates that the recording is for engineering testing rather than a verified canine behaviour observation.

## 10. CSV Data Format

The CSV file contains the following columns:

| Column | Description | Unit |
|---|---|---|
| `timestamp_ms` | ESP32 elapsed-time timestamp | Milliseconds |
| `ax` | X-axis acceleration | m/s² |
| `ay` | Y-axis acceleration | m/s² |
| `az` | Z-axis acceleration | m/s² |
| `gx` | X-axis angular velocity | rad/s |
| `gy` | Y-axis angular velocity | rad/s |
| `gz` | Z-axis angular velocity | rad/s |
| `behaviour` | Recording label | Text |

Example:

```csv
timestamp_ms,ax,ay,az,gx,gy,gz,behaviour
100,0.12345,0.23456,9.76543,0.01234,0.02345,0.03456,unverified_motion
110,0.12456,0.23123,9.77123,0.01123,0.02567,0.03245,unverified_motion
```

The values above are illustrative examples, not actual measurements.

The timestamp is generated by the ESP32. It represents elapsed device time rather than the recording's calendar date and time.

## 11. CSV Validation

The validation script checks the expected columns, numeric values, sample count, timestamp progression, recording duration, and approximate sampling frequency.

Run:

```bash
py validate_csv.py
```

The initial wireless bench test produced the following results:

| Validation item | Result |
|---|---|
| Recording duration | 29.99 seconds |
| Valid samples | 3,000 |
| Invalid rows | 0 |
| Reported sampling rate | 100.00 Hz |
| Timestamp gaps greater than 30 ms | 0 |
| Label | `unverified_motion` |

These results confirm that the initial wireless recording was successfully received and formatted.

## 12. Sensor Signal Analysis

The analysis script calculates the minimum, maximum, mean, and standard deviation for each sensor axis.

Run:

```bash
py analyze_sensor_data.py
```

Update the filename variable in the script to analyse a different CSV recording.

Initial controlled tests showed:

- Low measurement variation when the sensor remained stationary.
- Greater acceleration and gyroscope variation during manual movement.
- A stationary acceleration magnitude close to gravitational acceleration.
- A small nonzero stationary gyroscope offset.

These results provide preliminary evidence that the sensor responds to physical movement. Further calibration and testing are required before collecting research data.

## 13. Testing Summary

The following engineering tests have been completed:

- ESP32 and MPU6050 communication.
- Arduino firmware upload and execution.
- USB serial sensor data logging.
- Python CSV generation.
- CSV format and timestamp validation.
- ESP32 Wi-Fi access-point initialization.
- Wireless TCP sensor data transmission.
- Wireless CSV recording.
- Stationary and manual movement signal analysis.
- Initial sensor measurement-range verification using ±8g and ±1000°/s settings.

The initial USB and wireless recordings achieved a reported sampling rate of 100 Hz during the tested sessions.

These results apply to the tested bench configuration and do not establish performance during long-duration or real-world canine activity.

## 14. Current Limitations

The current implementation has the following limitations:

- The prototype does not yet have a dedicated portable battery system or completed collar enclosure.
- The current wireless logger does not buffer sensor readings locally when the Wi-Fi connection is lost.
- The initial bench recordings are not a verified canine behaviour dataset.
- Behaviour labels require independent verification before use in model training.
- Long-duration sampling, packet loss, battery life, and performance across different dogs remain to be evaluated.
- Sensor calibration, timestamp synchronization, and data quality checks require further development.

## 15. Next Development Tasks

The planned next steps are:

1. Improve the data logger to capture dog IDs, session IDs, recording metadata, and verified labels.
2. Implement safe portable power and secure collar mounting.
3. Collect sensor data from dogs performing naturally occurring behaviours.
4. Verify behaviour labels using synchronized video or direct observation.
5. Preprocess sensor data and segment it into time-series windows.
6. Train a baseline behaviour classification model.
7. Develop and evaluate the proposed 1D-CNN-LSTM model.
8. Evaluate generalization using dog-level training, validation, and test splits.
9. Integrate behaviour predictions with the wider multimodal AI system.

## 16. Research and Safety Note

The Behaviour Sensor Module supports preliminary canine activity recognition and health monitoring research. Its predictions must not be treated as a veterinary diagnosis.

Collect dog movement data only with appropriate owner consent and safe equipment placement. Do not induce scratching, head shaking, or distress to generate training samples.

Before deployment, evaluate data quality, model performance, animal safety, privacy, and the limitations of the collected dataset.
