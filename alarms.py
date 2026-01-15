import network
import ntptime
from machine import RTC
import time

class AlarmClock:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.rtc = RTC()
        self.alarms = []

    def connect_wifi(self):
        station = network.WLAN(network.STA_IF)
        station.active(True)
        station.connect(self.ssid, self.password)
        while not station.isconnected():
            time.sleep(1)
        print("Connected to WiFi:", station.ifconfig())

    def synchronize_time(self):
        ntptime.settime()
        print("Time synchronized with NTP server.")
    
    def set_alarm(self, hour, minute):
        alarm_time = (hour, minute)
        self.alarms.append(alarm_time)
        print(f"Alarm set for {hour:02}:{minute:02}.")
    
    def check_alarms(self):
        current_time = self.rtc.datetime()
        current_hour = current_time[4]
        current_minute = current_time[5]
        
        if (current_hour, current_minute) in self.alarms:
            print("Alarm ringing!")
            # Here you could add code to sound a buzzer or turn on an LED

if __name__ == "__main__":
    ssid = "your_wifi_ssid"
    password = "your_wifi_password"
    
    alarm_clock = AlarmClock(ssid, password)
    alarm_clock.connect_wifi()
    alarm_clock.synchronize_time()
    
    # Example: Set an alarm for 10:30
    alarm_clock.set_alarm(10, 30)
    
    while True:
        alarm_clock.check_alarms()
        time.sleep(60)