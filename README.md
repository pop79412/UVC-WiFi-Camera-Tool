# UVC-WiFi-Camera-Tool
UVC-WiFi-Camera-Tool: A Python-based GUI for hardware validation via Serial/WiFi, featuring ISP tuning (AE/Gain), Day/Night mode switching, and integrated PotPlayer video preview.

## 🌟 Key Features

### 1. Hybrid Communication Control
- **Serial (UART) Master**: Automatically detects USB serial port (UART port) to send hardware commands.
- **WiFi Automation**: Configure SSID/Password via serial and automatically retrieve/save the device IP address for network testing.

### 2. Image Signal Processor (ISP) Tuning
- **AE Control**: Toggle between Auto and Manual Exposure modes.
- **Precision Adjustment**: Real-time Shutter and Gain modification.
- **Status Monitoring**: Fetch and display current hardware sensor values instantly.

### 3. Lighting & Day/Night Mode
- **ICR Switch**: Toggle Infrared Cut Filter via single clicks.
- **IRLED Dimming**: Adjustable Duty Cycle (0-100%) for Night Mode validation.

### 4. Smart Video Integration
- **PotPlayer Linkage**: 
    - Auto-launch **RTSP** streams (WiFi mode) or **UVC** capture (USB mode).
    - Intelligent window management: Automatically brings PotPlayer to the front and triggers snapshots (Ctrl+E).
- **Auto-Discovery**: Scans Windows Registry to find your local PotPlayer installation.

## 🛠 Prerequisites

- **Python**: 3.x
- **Hardware**: USB-to-UART bridge (connected to your target device).
- **Software**: [PotPlayer](https://potplayer.daum.net/) (highly recommended for the video preview features).

## 📦 Installation

1. **Clone the Repo**:
   git clone https://github.com/pop79412/UVC-WiFi-Camera-Tool.git && cd UVC-WiFi-Camera-Tool
2. **Install Dependencies**:
   pip install pyserial pyautogui pygetwindow
## 🚀 Quick Start
1. **Connect Hardware**: Connect your camera device to the computer via a USB-to-UART bridge.
2. **Launch the Application**: python UVC-WiFi-Camera-Tool.py
3. **Initialize Connection**:
   UVC mode: Click UVC button go to UVC mode and click potplayer preview.
   WIFI mode: Filled in SSID and PASSWD connect to wifi and click potplayer preview.
4. **Testing**:
   Testing with AE settings or Daynightmode switch or manual commit typing
