import machine
import network
import ntptime
import socket
from time import sleep

# Wi-Fi Credentials
SSID = 'your_SSID'
PASSWORD = 'your_PASSWORD'

# Alarm variables
define_alarms = []

# NTP Server settings
NTP_SERVER = 'pool.ntp.org'

# Function to connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    while not wlan.isconnected():
        sleep(1)
    print('Connected to Wi-Fi:', wlan.ifconfig())

# Function to get the current time
def get_ntp_time():
    ntptime.settime()  # Set the time based on NTP
    print('Time synchronized with NTP')

# Function to handle button presses
def button_handler(pin):
    # Your button handling logic here
    print('Button Pressed!')
    # E.g., set alarm, snooze

# Setting up button
button_pin = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
button_pin.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_handler)

# Function to start web server
def start_web_server():
    addr = socket.getaddrinfo('0.0.0.0', 80)[0]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    print('Listening on:', addr)
    while True:
        cl, addr = s.accept()
        print('Client connected from', addr)
        request = cl.recv(1024)
        cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
        cl.send('<h1>ESP32 Alarm Clock</h1>')
        cl.close()

# Main script execution
if __name__ == '__main__':
    connect_wifi()
    get_ntp_time()
    start_web_server()  
    # Add alarm handling logic here
