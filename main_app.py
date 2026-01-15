import asyncio
import machine
import network
import ntptime
import time

# Configuration Variables
SSID = 'your_wifi_ssid'
PASSWORD = 'your_wifi_password'
ALARM_HOUR = 7
ALARM_MINUTE = 0
LED_PIN = 2

# Initialize LED
led = machine.Pin(LED_PIN, machine.Pin.OUT)

# Connect to Wi-Fi
async def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        await asyncio.sleep(1)
    print('Connected to Wi-Fi:', wlan.ifconfig())

# Synchronize time with NTP server
async def sync_time():
    ntptime.settime()
    print('Time synchronized')

# Alarm checking logic
async def check_alarm():
    while True:
        current_time = time.localtime()
        if current_time[3] == ALARM_HOUR and current_time[4] == ALARM_MINUTE:
            led.on()  # Turn on LED
            await asyncio.sleep(60)  # Alarm lasts for 60 seconds
            led.off()  # Turn off LED
        await asyncio.sleep(30)  # Check every 30 seconds

# Storage management (simulated)
async def storage_management():
    # Placeholder for actual storage management code
    while True:
        print('Storage management routine running')
        await asyncio.sleep(600)  # Run every 10 minutes

# Main function to run coroutines
async def main():
    await connect_to_wifi()
    await sync_time()
    await asyncio.gather(check_alarm(), storage_management())

# Start the application
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print('Program stopped')
