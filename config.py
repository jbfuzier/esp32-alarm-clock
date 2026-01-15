# ESP32 Alarm Clock Configuration
# WiFi and Hardware Settings

# WiFi Configuration
WIFI_SSID = "your_ssid"
WIFI_PASSWORD = "your_password"

# GPIO Pin Configuration
LED_PIN = 5          # GPIO pin for NeoPixel LED strip
BUTTON_ACK_PIN = 4   # Alarm acknowledgment button
BUTTON_ONOFF_PIN = 0 # Manual light on/off toggle
BUTTON_PLUS_PIN = 2  # Brightness increase button
BUTTON_MINUS_PIN = 15 # Brightness decrease button

# LED Configuration
LED_COUNT = 30       # Number of LEDs in the strip
LED_BRIGHTNESS_MAX = 255  # Maximum brightness value
LED_BRIGHTNESS_DEFAULT = 100  # Default brightness on first turn-on (0-100%)

# NTP Configuration
NTP_SERVER = "pool.ntp.org"
NTP_RETRY_ATTEMPTS = 10  # Number of retry attempts
NTP_RETRY_INTERVAL = 30  # Seconds between retries
NTP_TIMEOUT = 300  # 5 minutes in seconds before giving up and blinking error

# Timezone Configuration
TIMEZONE = "Europe/Paris"  # Default timezone
UTC_OFFSET = 1  # Winter UTC+1 (will be auto-adjusted for DST)
DST_ENABLED = True

# Error Signal (LED blink if NTP fails)
ERROR_BLINK_INTERVAL = 500  # milliseconds

# Web Server Configuration
WEB_SERVER_PORT = 80
WEB_SERVER_HOST = "0.0.0.0"

# Settings Storage
SETTINGS_FILE = "settings.json"
ALARMS_FILE = "alarms.json"