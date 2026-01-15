"""
LED Controller for ESP32 Alarm Clock
MicroPython compatible LED control with NeoPixel support
"""
import asyncio
try:
    from machine import Pin
    import neopixel
    NEOPIXEL_AVAILABLE = True
except ImportError:
    NEOPIXEL_AVAILABLE = False
    print("Warning: NeoPixel not available, running in fallback mode")

import config


class LEDController:
    """
    Controls WS2812B LED strip via NeoPixel
    Supports brightness ramping, color temperature control, and various effects
    """
    
    def __init__(self, pin, num_leds, max_brightness=100):
        """
        Initialize LED Controller
        
        Args:
            pin: GPIO pin number for LED data line
            num_leds: Number of LEDs in the strip
            max_brightness: Maximum brightness (0-100%)
        """
        self.pin_num = pin
        self.num_leds = num_leds
        self.max_brightness = max_brightness
        self.current_brightness = 0
        self.current_temperature = 50
        self.is_on = False
        self.current_rgb = (0, 0, 0)
        
        if NEOPIXEL_AVAILABLE:
            try:
                self.pin = Pin(pin, Pin.OUT)
                self.pixels = neopixel.NeoPixel(self.pin, num_leds)
                self.fallback_mode = False
            except Exception as e:
                print(f"Failed to initialize NeoPixel: {e}")
                self.fallback_mode = True
        else:
            self.fallback_mode = True
            
    def _cct_to_rgb(self, temperature):
        """
        Convert color temperature (0-100) to RGB
        0 = Warm White (3000K): RGB(255, 200, 150)
        100 = Cold White (6500K): RGB(255, 255, 255)
        Linear interpolation between values
        
        Args:
            temperature: Color temperature (0-100)
            
        Returns:
            tuple: RGB values (r, g, b)
        """
        warm_r, warm_g, warm_b = config.WARM_WHITE_RGB
        cold_r, cold_g, cold_b = config.COLD_WHITE_RGB
        
        # Linear interpolation
        ratio = temperature / 100.0
        r = int(warm_r + (cold_r - warm_r) * ratio)
        g = int(warm_g + (cold_g - warm_g) * ratio)
        b = int(warm_b + (cold_b - warm_b) * ratio)
        
        return (r, g, b)
    
    def _apply_brightness(self, rgb, brightness):
        """
        Apply brightness to RGB values
        
        Args:
            rgb: tuple of (r, g, b)
            brightness: brightness level (0-100)
            
        Returns:
            tuple: RGB with brightness applied
        """
        factor = brightness / 100.0
        return tuple(int(c * factor) for c in rgb)
    
    async def set_color(self, brightness, temperature):
        """
        Set LED color based on brightness and temperature (async)
        
        Args:
            brightness: Brightness level (0-100)
            temperature: Color temperature (0-100)
        """
        self.current_brightness = brightness
        self.current_temperature = temperature
        self.is_on = brightness > 0
        
        # Get base RGB from temperature
        base_rgb = self._cct_to_rgb(temperature)
        
        # Apply brightness
        self.current_rgb = self._apply_brightness(base_rgb, brightness)
        
        if not self.fallback_mode:
            try:
                for i in range(self.num_leds):
                    self.pixels[i] = self.current_rgb
                self.pixels.write()
            except Exception as e:
                print(f"Error setting color: {e}")
        else:
            print(f"[Fallback] Set color: brightness={brightness}, temp={temperature}, rgb={self.current_rgb}")
        
        await asyncio.sleep(0)
    
    def set_color_sync(self, brightness, temperature):
        """
        Set LED color based on brightness and temperature (synchronous)
        
        Args:
            brightness: Brightness level (0-100)
            temperature: Color temperature (0-100)
        """
        self.current_brightness = brightness
        self.current_temperature = temperature
        self.is_on = brightness > 0
        
        # Get base RGB from temperature
        base_rgb = self._cct_to_rgb(temperature)
        
        # Apply brightness
        self.current_rgb = self._apply_brightness(base_rgb, brightness)
        
        if not self.fallback_mode:
            try:
                for i in range(self.num_leds):
                    self.pixels[i] = self.current_rgb
                self.pixels.write()
            except Exception as e:
                print(f"Error setting color: {e}")
        else:
            print(f"[Fallback] Set color sync: brightness={brightness}, temp={temperature}, rgb={self.current_rgb}")
    
    async def ramp_brightness(self, start_brightness, end_brightness, temperature, duration_minutes):
        """
        Ramp brightness from start to end over specified duration
        
        Args:
            start_brightness: Starting brightness (0-100)
            end_brightness: Ending brightness (0-100)
            temperature: Color temperature to use (0-100)
            duration_minutes: Duration of ramp in minutes
        """
        duration_seconds = duration_minutes * 60
        steps = max(duration_seconds, 1)  # At least 1 step
        step_delay = duration_seconds / steps
        
        for step in range(steps + 1):
            # Calculate current brightness using linear interpolation
            ratio = step / steps
            current_brightness = start_brightness + (end_brightness - start_brightness) * ratio
            
            # Set the color
            await self.set_color(current_brightness, temperature)
            
            # Wait before next step
            if step < steps:
                await asyncio.sleep(step_delay)
    
    async def pulse(self, brightness, temperature, pulse_count, interval_ms):
        """
        Pulse effect - turn on and off repeatedly
        
        Args:
            brightness: Peak brightness (0-100)
            temperature: Color temperature (0-100)
            pulse_count: Number of pulses
            interval_ms: Interval between pulses in milliseconds
        """
        interval_sec = interval_ms / 1000.0
        
        for _ in range(pulse_count):
            # Turn on
            await self.set_color(brightness, temperature)
            await asyncio.sleep(interval_sec / 2)
            
            # Turn off
            await self.set_color(0, temperature)
            await asyncio.sleep(interval_sec / 2)
    
    async def error_blink(self, interval_ms=500):
        """
        Error indication - blink red
        
        Args:
            interval_ms: Blink interval in milliseconds
        """
        interval_sec = interval_ms / 1000.0
        
        # Blink red 5 times
        for _ in range(5):
            # Turn on red
            self.current_rgb = (255, 0, 0)
            if not self.fallback_mode:
                try:
                    for i in range(self.num_leds):
                        self.pixels[i] = (255, 0, 0)
                    self.pixels.write()
                except Exception as e:
                    print(f"Error in error_blink: {e}")
            else:
                print(f"[Fallback] Error blink ON")
            
            await asyncio.sleep(interval_sec)
            
            # Turn off
            self.current_rgb = (0, 0, 0)
            if not self.fallback_mode:
                try:
                    for i in range(self.num_leds):
                        self.pixels[i] = (0, 0, 0)
                    self.pixels.write()
                except Exception as e:
                    print(f"Error in error_blink: {e}")
            else:
                print(f"[Fallback] Error blink OFF")
            
            await asyncio.sleep(interval_sec)
    
    async def rainbow_effect(self, brightness, speed_ms):
        """
        Rainbow color cycling effect
        
        Args:
            brightness: Brightness level (0-100)
            speed_ms: Speed of color change in milliseconds
        """
        speed_sec = speed_ms / 1000.0
        
        # Simple rainbow: cycle through hue
        colors = [
            (255, 0, 0),    # Red
            (255, 127, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (75, 0, 130),   # Indigo
            (148, 0, 211),  # Violet
        ]
        
        for color in colors:
            # Apply brightness to color
            adjusted_color = self._apply_brightness(color, brightness)
            self.current_rgb = adjusted_color
            
            if not self.fallback_mode:
                try:
                    for i in range(self.num_leds):
                        self.pixels[i] = adjusted_color
                    self.pixels.write()
                except Exception as e:
                    print(f"Error in rainbow_effect: {e}")
            else:
                print(f"[Fallback] Rainbow effect: {adjusted_color}")
            
            await asyncio.sleep(speed_sec)
    
    def get_current_state(self):
        """
        Get current LED state
        
        Returns:
            dict: Current state with brightness, temperature, is_on, rgb
        """
        return {
            'brightness': self.current_brightness,
            'temperature': self.current_temperature,
            'is_on': self.is_on,
            'rgb': self.current_rgb
        }
