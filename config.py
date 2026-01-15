# Configuration parameters for ESP32 Alarm Clock

# LED configuration
LED_PIN = 2  # Example GPIO pin for LED
LED_BRIGHTNESS = 255  # Brightness level (0-255)

# WiFi configuration
WIFI_SSID = 'your_wifi_ssid'
WIFI_PASSWORD = 'your_wifi_password'

# NTP configuration
NTP_SERVER = 'pool.ntp.org'
NTP_UPDATE_INTERVAL = 3600  # Update time every hour

# Alarm configuration
ALARM_TIME = '07:00'  # Default alarm time (HH:MM)
ALARM_ENABLED = True  # Set to False to disable the alarm