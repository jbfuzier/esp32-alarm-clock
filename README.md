# ESP32 Alarm Clock

A complete MicroPython-based alarm clock implementation for ESP32 with LED wake-up light, web interface, and REST API.

## Features

- 🌅 **Wake-up Light**: Gradual LED brightness ramping simulates natural sunrise
- ⏰ **Multiple Alarms**: Support for recurring (day-based) and one-time alarms
- 🌡️ **Color Temperature Control**: Adjustable from warm white (3000K) to cold white (6500K)
- 🌐 **Web Interface**: REST API for remote control and configuration
- 💾 **Persistent Storage**: JSON-based alarm and settings storage
- 📡 **WiFi & NTP**: Automatic time synchronization
- 🎨 **LED Effects**: Pulse, rainbow, and error indication effects

## Hardware Requirements

- **ESP32 Development Board** (any variant with WiFi)
- **WS2812B LED Strip** (60 LEDs recommended)
- **Power Supply**: 5V for LED strip (sufficient amperage for your LED count)
- **Jumper Wires**: For connections
- **Breadboard**: Optional, for prototyping

### Wiring

| ESP32 Pin | Connection |
|-----------|------------|
| GPIO 25   | LED Strip Data Line |
| GND       | LED Strip Ground |
| 5V        | LED Strip Power (via external power supply) |

⚠️ **Important**: Use an external 5V power supply for the LED strip. ESP32's 5V pin may not provide sufficient current.

## Software Requirements

- **MicroPython** (v1.19 or later) flashed on ESP32
- **Required Libraries**:
  - `neopixel` (built-in with MicroPython)
  - `asyncio` (uasyncio in MicroPython)
  - `network` (built-in)
  - `ntptime` (built-in)

## Installation

### 1. Flash MicroPython

```bash
# Install esptool
pip install esptool

# Erase flash
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash

# Flash MicroPython firmware
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-*.bin
```

### 2. Upload Code

Using `ampy` or `rshell`:

```bash
# Install ampy
pip install adafruit-ampy

# Upload files
ampy --port /dev/ttyUSB0 put config.py
ampy --port /dev/ttyUSB0 put led_control.py
ampy --port /dev/ttyUSB0 put storage.py
ampy --port /dev/ttyUSB0 put web_server.py
ampy --port /dev/ttyUSB0 put main_app.py
ampy --port /dev/ttyUSB0 put index.html
```

### 3. Configure WiFi

Edit `config.py` before uploading:

```python
SSID = 'your_wifi_network'
PASSWORD = 'your_wifi_password'
```

### 4. Run Application

The application starts automatically if you rename `main_app.py` to `main.py`:

```bash
ampy --port /dev/ttyUSB0 mv main_app.py main.py
```

Or run manually via REPL:

```python
import main_app
```

## Configuration

All configuration is in `config.py`:

```python
# WiFi Settings
SSID = 'your_wifi_ssid'
PASSWORD = 'your_wifi_password'

# NTP Settings
NTP_SERVER = 'pool.ntp.org'
RETRY_ATTEMPTS = 3
INTERVAL = 5

# LED Settings
LED_PIN = 25              # GPIO pin for LED data
LED_COUNT = 60            # Number of LEDs
WARM_WHITE_RGB = (255, 200, 150)  # 3000K
COLD_WHITE_RGB = (255, 255, 255)  # 6500K

# Alarm Defaults
DEFAULT_RAMP_DURATION = 30  # minutes
DEFAULT_MAX_BRIGHTNESS = 80  # percent

# Storage
ALARMS_FILE = 'alarms.json'
SETTINGS_FILE = 'settings.json'

# Web Server
WEB_SERVER_PORT = 80
WEB_SERVER_HOST = '0.0.0.0'

# Timezone
TIMEZONE_OFFSET = '+1'  # UTC offset
```

## REST API

Once running, the web server listens on port 80.

### Alarms

#### Get All Alarms
```http
GET /api/alarms
```

**Response:**
```json
[
  {
    "id": 0,
    "time": "07:00",
    "type": "recurring",
    "days": [0, 1, 2, 3, 4],
    "max_brightness": 80,
    "ramp_duration": 30,
    "color_temp": 50,
    "enabled": true
  }
]
```

#### Create Alarm
```http
POST /api/alarms
Content-Type: application/json

{
  "time": "07:00",
  "type": "recurring",
  "days": [0, 1, 2, 3, 4],
  "max_brightness": 80,
  "ramp_duration": 30,
  "color_temp": 50,
  "enabled": true
}
```

#### Update Alarm
```http
PATCH /api/alarms/0
Content-Type: application/json

{
  "time": "07:30",
  "enabled": true
}
```

#### Delete Alarm
```http
DELETE /api/alarms/0
```

### Lights

#### Get Light State
```http
GET /api/lights
```

**Response:**
```json
{
  "brightness": 80,
  "temperature": 50,
  "is_on": true,
  "rgb": [204, 181, 161]
}
```

#### Set Light State
```http
POST /api/lights
Content-Type: application/json

{
  "brightness": 80,
  "temperature": 50
}
```

### Settings

#### Get Settings
```http
GET /api/settings
```

#### Update Settings
```http
PATCH /api/settings
Content-Type: application/json

{
  "timezone": 1,
  "brightness": 85
}
```

## Alarm Structure

### Recurring Alarm
```json
{
  "time": "07:00",          // HH:MM format
  "type": "recurring",
  "days": [0, 1, 2, 3, 4],  // 0=Monday, 6=Sunday
  "max_brightness": 80,     // 0-100%
  "ramp_duration": 30,      // minutes
  "color_temp": 50,         // 0=warm, 100=cold
  "enabled": true
}
```

### One-Time Alarm
```json
{
  "time": "14:30",
  "type": "one-time",
  "max_brightness": 70,
  "ramp_duration": 5,
  "color_temp": 60,
  "enabled": true
}
```

## LED Effects

The `LEDController` class provides several effects:

- **Brightness Ramping**: Smooth transition from 0% to target over time
- **Pulse**: Rhythmic on/off pattern
- **Rainbow**: Color cycling effect
- **Error Blink**: Red blinking for error indication

## Architecture

### Modules

1. **config.py**: Configuration constants
2. **led_control.py**: LED controller with effects
3. **storage.py**: JSON-based persistent storage
4. **web_server.py**: Async HTTP REST API server
5. **main_app.py**: Application orchestrator

### Flow

```
main_app.py
├── WiFi Connection (with retry)
├── NTP Time Sync (with retry)
├── Alarm Monitoring Loop
│   ├── Check current time
│   ├── Load alarms from storage
│   ├── Match alarms to current time
│   └── Trigger LED ramp effect
└── Web Server
    ├── REST API endpoints
    └── Integration with LEDController & Storage
```

## Troubleshooting

### WiFi Connection Fails
- Verify SSID and password in `config.py`
- Check WiFi signal strength
- LED will blink red on connection failure

### Time Not Syncing
- Ensure WiFi is connected
- Verify NTP server is reachable
- Check firewall settings

### LEDs Not Working
- Verify wiring (GPIO 25 → Data, GND → Ground)
- Check power supply (5V, sufficient amperage)
- Ensure LED_COUNT matches your strip
- System works in fallback mode without physical LEDs

### Web Server Not Accessible
- Get ESP32 IP from serial output
- Check firewall/router settings
- Verify port 80 is not blocked

## Development & Testing

### Run Tests (on development machine)

```bash
# Syntax check
python3 -m py_compile *.py

# Run unit tests
PYTHONPATH=. python3 tests/test_modules.py

# Run demonstration
PYTHONPATH=. python3 demo_system.py
```

### Simulation Mode

The code includes fallback modes for development without hardware:
- LED operations print to console
- WiFi/NTP operations are simulated
- Time functions use system clock

## License

This project is open source. See LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions

Enjoy your ESP32 Alarm Clock! 🌅