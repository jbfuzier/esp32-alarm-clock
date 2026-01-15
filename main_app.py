"""
Main Application for ESP32 Alarm Clock
Orchestrates all modules: WiFi, NTP, LED control, Storage, Web server
"""
import asyncio
try:
    import network
    import ntptime
    from machine import RTC
    MICROPYTHON = True
except ImportError:
    MICROPYTHON = False
    print("Warning: Not running on MicroPython, some features may not work")

import time
import config
from led_control import LEDController
from storage import Storage
from web_server import AsyncHTTPServer


class AlarmClockApp:
    """
    Main application class that coordinates all modules
    """
    
    def __init__(self):
        """Initialize all components"""
        print("Initializing ESP32 Alarm Clock...")
        
        # Initialize LED controller
        self.led_controller = LEDController(
            pin=config.LED_PIN,
            num_leds=config.LED_COUNT,
            max_brightness=config.DEFAULT_MAX_BRIGHTNESS
        )
        
        # Initialize storage
        self.storage = Storage()
        
        # Initialize web server
        self.web_server = AsyncHTTPServer(
            host=config.WEB_SERVER_HOST,
            port=config.WEB_SERVER_PORT
        )
        self.web_server.set_app(self)
        
        # WiFi and time sync status
        self.wifi_connected = False
        self.time_synced = False
        
        # Track triggered alarms (for one-time alarms)
        self.triggered_alarms = set()
        
        # RTC for time tracking
        if MICROPYTHON:
            self.rtc = RTC()
        else:
            self.rtc = None
        
        print("Initialization complete")
    
    async def connect_to_wifi(self):
        """
        Connect to WiFi with retry logic
        
        Returns:
            bool: True if connected, False otherwise
        """
        if not MICROPYTHON:
            print("[Simulation] WiFi connection skipped (not on MicroPython)")
            self.wifi_connected = True
            return True
        
        print(f"Connecting to WiFi: {config.SSID}")
        
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        for attempt in range(config.RETRY_ATTEMPTS):
            try:
                if not wlan.isconnected():
                    print(f"Attempt {attempt + 1}/{config.RETRY_ATTEMPTS}")
                    wlan.connect(config.SSID, config.PASSWORD)
                    
                    # Wait for connection
                    retry_count = 0
                    while not wlan.isconnected() and retry_count < 10:
                        await asyncio.sleep(1)
                        retry_count += 1
                    
                    if wlan.isconnected():
                        print(f"Connected! IP: {wlan.ifconfig()[0]}")
                        self.wifi_connected = True
                        return True
                else:
                    print(f"Already connected! IP: {wlan.ifconfig()[0]}")
                    self.wifi_connected = True
                    return True
                
            except Exception as e:
                print(f"WiFi connection error: {e}")
            
            if attempt < config.RETRY_ATTEMPTS - 1:
                print(f"Retrying in {config.INTERVAL} seconds...")
                await asyncio.sleep(config.INTERVAL)
        
        print("Failed to connect to WiFi")
        self.wifi_connected = False
        
        # Blink error on LED
        await self.led_controller.error_blink(config.ERROR_BLINK_INTERVAL)
        
        return False
    
    async def sync_time_ntp(self):
        """
        Synchronize time with NTP server with retry logic
        
        Returns:
            bool: True if synchronized, False otherwise
        """
        if not MICROPYTHON:
            print("[Simulation] NTP sync skipped (not on MicroPython)")
            self.time_synced = True
            return True
        
        if not self.wifi_connected:
            print("Cannot sync time: WiFi not connected")
            return False
        
        print(f"Synchronizing time with NTP server: {config.NTP_SERVER}")
        
        for attempt in range(config.RETRY_ATTEMPTS):
            try:
                print(f"Attempt {attempt + 1}/{config.RETRY_ATTEMPTS}")
                ntptime.host = config.NTP_SERVER
                ntptime.settime()
                
                # Apply timezone offset
                current_time = time.localtime()
                print(f"Time synchronized: {current_time[3]:02d}:{current_time[4]:02d}:{current_time[5]:02d}")
                
                self.time_synced = True
                return True
                
            except Exception as e:
                print(f"NTP sync error: {e}")
            
            if attempt < config.RETRY_ATTEMPTS - 1:
                print(f"Retrying in {config.INTERVAL} seconds...")
                await asyncio.sleep(config.INTERVAL)
        
        print("Failed to synchronize time")
        self.time_synced = False
        
        # Blink error on LED
        await self.led_controller.error_blink(config.ERROR_BLINK_INTERVAL)
        
        return False
    
    def _get_current_time(self):
        """
        Get current time
        
        Returns:
            tuple: (hour, minute, weekday) or None if not available
        """
        try:
            if MICROPYTHON and self.rtc:
                # MicroPython RTC.datetime(): (year, month, day, weekday, hour, minute, second, subsecond)
                # weekday: 0=Monday through 6=Sunday
                dt = self.rtc.datetime()
                hour = dt[4]
                minute = dt[5]
                weekday = dt[3]
            else:
                # Standard Python time.localtime()
                # tm_wday: 0=Monday through 6=Sunday
                lt = time.localtime()
                hour = lt[3]
                minute = lt[4]
                weekday = lt[6]
            
            return (hour, minute, weekday)
        except Exception as e:
            print(f"Error getting current time: {e}")
            return None
    
    def _should_trigger_alarm(self, alarm, current_hour, current_minute, current_weekday):
        """
        Check if an alarm should be triggered
        
        Args:
            alarm: Alarm dictionary
            current_hour: Current hour (0-23)
            current_minute: Current minute (0-59)
            current_weekday: Current weekday (0=Monday, 6=Sunday)
            
        Returns:
            bool: True if alarm should trigger
        """
        # Check if alarm is enabled
        if not alarm.get('enabled', False):
            return False
        
        # Parse alarm time
        try:
            alarm_time = alarm['time'].split(':')
            alarm_hour = int(alarm_time[0])
            alarm_minute = int(alarm_time[1])
        except:
            print(f"Invalid alarm time format: {alarm.get('time')}")
            return False
        
        # Check if time matches
        if alarm_hour != current_hour or alarm_minute != current_minute:
            return False
        
        # Check alarm type
        alarm_type = alarm.get('type', 'recurring')
        
        if alarm_type == 'recurring':
            # Check if current day is in the alarm's days
            days = alarm.get('days', [])
            if current_weekday not in days:
                return False
        elif alarm_type == 'one-time':
            # Check if already triggered
            alarm_id = alarm.get('id')
            if alarm_id in self.triggered_alarms:
                return False
        
        return True
    
    async def _trigger_alarm(self, alarm):
        """
        Trigger an alarm with LED ramp effect
        
        Args:
            alarm: Alarm dictionary
        """
        alarm_id = alarm.get('id')
        alarm_time = alarm.get('time', 'unknown')
        
        print(f"Triggering alarm {alarm_id} at {alarm_time}")
        
        # Get alarm parameters
        max_brightness = alarm.get('max_brightness', config.DEFAULT_MAX_BRIGHTNESS)
        ramp_duration = alarm.get('ramp_duration', config.DEFAULT_RAMP_DURATION)
        color_temp = alarm.get('color_temp', 50)
        
        # Perform LED ramp
        try:
            await self.led_controller.ramp_brightness(
                start_brightness=0,
                end_brightness=max_brightness,
                temperature=color_temp,
                duration_minutes=ramp_duration
            )
            
            print(f"Alarm {alarm_id} complete")
            
            # Mark as triggered for one-time alarms
            if alarm.get('type') == 'one-time':
                self.triggered_alarms.add(alarm_id)
                
        except Exception as e:
            print(f"Error triggering alarm: {e}")
    
    async def _trigger_alarm_wrapper(self, alarm):
        """
        Wrapper for alarm triggering to handle exceptions
        
        Args:
            alarm: Alarm dictionary
        """
        try:
            await self._trigger_alarm(alarm)
        except Exception as e:
            print(f"Error in alarm task for alarm {alarm.get('id')}: {e}")
    
    async def check_alarms(self):
        """
        Continuously monitor and trigger alarms
        """
        print("Starting alarm monitoring...")
        
        last_check_minute = -1
        alarm_tasks = []
        
        while True:
            try:
                # Clean up completed tasks
                alarm_tasks = [task for task in alarm_tasks if not task.done()]
                
                # Get current time
                time_info = self._get_current_time()
                if not time_info:
                    await asyncio.sleep(config.ALARM_CHECK_INTERVAL)
                    continue
                
                current_hour, current_minute, current_weekday = time_info
                
                # Only check once per minute
                if current_minute == last_check_minute:
                    await asyncio.sleep(config.ALARM_CHECK_INTERVAL)
                    continue
                
                last_check_minute = current_minute
                
                # Load alarms
                alarms = self.storage.load_alarms()
                
                # Check each alarm
                for alarm in alarms:
                    if self._should_trigger_alarm(alarm, current_hour, current_minute, current_weekday):
                        # Trigger alarm with error handling wrapper
                        task = asyncio.create_task(self._trigger_alarm_wrapper(alarm))
                        alarm_tasks.append(task)
                
            except Exception as e:
                print(f"Error in alarm check: {e}")
            
            await asyncio.sleep(config.ALARM_CHECK_INTERVAL)
    
    async def run(self):
        """
        Main entry point - start all tasks
        """
        print("Starting ESP32 Alarm Clock application...")
        
        # Connect to WiFi
        await self.connect_to_wifi()
        
        # Sync time if WiFi connected
        if self.wifi_connected:
            await self.sync_time_ntp()
        
        # Start all tasks concurrently
        try:
            await asyncio.gather(
                self.check_alarms(),
                self.web_server.start(),
            )
        except KeyboardInterrupt:
            print("Application stopped by user")
        except Exception as e:
            print(f"Application error: {e}")
        finally:
            print("Shutting down...")
            self.web_server.stop()


# Entry point for MicroPython
async def main():
    """Main entry point"""
    app = AlarmClockApp()
    await app.run()


# Auto-start when imported
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
