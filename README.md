# 🎮 CHROMA REFLEX: Pro F1 Edition

**Chroma Reflex** is a hardware-integrated reaction time game that tests your reflexes using a custom controller. Inspired by F1 racing starts, players must hit a Piezo sensor to initiate a light sequence, wait for the lights to go out, and physically hit the correct color button as fast as possible.

![Status](https://img.shields.io/badge/Status-Complete-green)
![Python](https://img.shields.io/badge/Python-3.x-blue)
![Arduino](https://img.shields.io/badge/Hardware-Arduino-teal)

## ✨ Features

* **F1 Style Start:** A tension-building 5-light countdown sequence triggered by physical impact.
* **Physical Controller:** Uses a Piezo sensor for impact detection and arcade buttons for input.
* **DSP Signal Processing:** Implements a Low-Pass Filter and Envelope Detector on the Arduino to clean noisy sensor data.
* **Precision Timing:** Measures reaction time down to the millisecond.
* **Visual Feedback:** Instant on-screen "CORRECT" or "WRONG" badges with color-coded cues.
* **Session Tally:** Displays a full scoreboard of all 5 rounds with average reaction time at the end.

## 🛠️ Tech Stack

### Software
* **Python 3.x:** Core game logic and UI.
* **Pygame:** Rendering engine for graphics and window management.
* **PySerial:** Handles USB communication between the computer and Arduino.

### Hardware
* **Arduino Uno/Nano:** Microcontroller brain.
* **Piezo Sensor:** Detects physical taps/hits to start rounds.
* **3x Push Buttons:** Inputs for Red, Green, and Blue targets.
* **LED:** Visual indicator for tap registration.
* **1MΩ Resistor:** Applied to Piezo for signal stability.

---

## 🔌 Hardware Setup

### Wiring Diagram

| Component | Arduino Pin | Notes |
| :--- | :--- | :--- |
| **Piezo (+) Red** | `A0` | Connect in parallel with 1MΩ Resistor |
| **Piezo (-) Black** | `GND` | Connect in parallel with 1MΩ Resistor |
| **Red Button** | `D2` | One leg to Pin 2, other to GND |
| **Green Button** | `D3` | One leg to Pin 3, other to GND |
| **Blue Button** | `D4` | One leg to Pin 4, other to GND |
| **LED (+) Anode** | `D8` | Series with 220Ω resistor |
| **LED (-) Cathode** | `GND` | |

> **⚠️ Important:** The Piezo sensor creates voltage spikes. The **1MΩ resistor** across the Piezo legs is critical to drain the voltage and prevent false triggers.

---

## 🚀 Installation & Usage

### 1. Arduino Setup
1.  Open `ChromaReflex_Arduino.ino` in the Arduino IDE.
2.  Connect your Arduino via USB.
3.  Select your Board and Port.
4.  **Upload** the code.
5.  *Optional:* Open Serial Monitor (9600 baud) to test buttons and tap sensitivity. Close it before running Python.

### 2. Python Setup
1.  Ensure Python is installed.
2.  Install dependencies:
    ```bash
    pip install pygame pyserial
    ```
3.  Open the Python script (`color_game.py`).
4.  **Edit the COM Port:** Find this line and change it to your Arduino's port (e.g., `COM3`, `/dev/ttyUSB0`):
    ```python
    SERIAL_PORT = 'COM6' 
    ```
5.  Run the game:
    ```bash
    python color_game.py
    ```

---

## 🕹️ How to Play

1.  **Start:** Press **SPACEBAR** or **Click Mouse** on the title screen.
2.  **Initiate:** The screen will say "HIT PIEZO". Slap/Tap the piezo sensor.
3.  **Countdown:** 5 Red Lights will turn on sequentially. **Wait!**
4.  **React:** When the lights go **OFF** and the Color appears, press the matching physical button immediately.
    * **Correct:** Green Badge + Time logged.
    * **Wrong:** Red Badge + 1 second penalty.
5.  **Next Round:** Press **Spacebar** to confirm the result and ready the Piezo for the next round.
6.  **Finish:** After 5 rounds, view your session tally and Average Time. Press **'R'** to restart.

---

## 🐛 Troubleshooting

* **"Arduino Not Found":** Check if the `SERIAL_PORT` variable in Python matches the port in Arduino IDE. Close the Arduino Serial Monitor before running the game.
* **Piezo not detecting:** Lower the `threshold` variable in the Arduino code (e.g., from 80 to 50).
* **Piezo triggering itself:** Increase the `threshold` variable or ensure the 1MΩ resistor is connected securely.
* **Buttons not working:** Ensure you are using `INPUT_PULLUP` logic (button connects Pin to Ground).

---

## 📜 License
This project is open-source. Feel free to modify the code for your own custom controllers or game modes.
