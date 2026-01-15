try:
    from neopixel import NeoPixel, Color
    import machine
    import uasyncio as asyncio
except ImportError:
    # Fallback mode
    class NeoPixel:
        def __init__(self, *args, **kwargs):
            pass

        def fill(self, color):
            pass

class LEDController:
    def __init__(self, pin, num_leds):
        self.leds = NeoPixel(pin, num_leds)

    async def ramp_brightness(self, target_brightness, duration):
        current_brightness = self.leds.brightness
        step = (target_brightness - current_brightness) / (duration * 1000 / 10)
        while current_brightness != target_brightness:
            current_brightness += step
            self.set_brightness(int(current_brightness))
            await asyncio.sleep(0.01)

    async def set_color_temperature(self, cct, duration):
        warm_white = (255, 200, 150)
        cold_white = (255, 255, 255)
        r = warm_white[0] + (cold_white[0] - warm_white[0]) * (cct / 100)
        g = warm_white[1] + (cold_white[1] - warm_white[1]) * (cct / 100)
        b = warm_white[2] + (cold_white[2] - warm_white[2]) * (cct / 100)
        self.set_color((int(r), int(g), int(b)))

    async def pulse_effect(self, intensity, duration):
        for _ in range(int(duration * 2)):
            self.set_brightness(intensity)
            await asyncio.sleep(0.5)
            self.set_brightness(0)
            await asyncio.sleep(0.5)

    async def error_blinking(self, times, duration):
        for _ in range(times):
            self.set_color((255, 0, 0))  # Red for error
            await asyncio.sleep(duration)  # Blink duration
            self.set_color((0, 0, 0))
            await asyncio.sleep(duration)

    def sync_set_brightness(self, target_brightness, duration):
        current_brightness = self.leds.brightness
        step = (target_brightness - current_brightness) / (duration * 1000 / 10)
        while current_brightness != target_brightness:
            current_brightness += step
            self.set_brightness(int(current_brightness))
            time.sleep(0.01)

    def sync_set_color_temperature(self, cct, duration):
        warm_white = (255, 200, 150)
        cold_white = (255, 255, 255)
        r = warm_white[0] + (cold_white[0] - warm_white[0]) * (cct / 100)
        g = warm_white[1] + (cold_white[1] - warm_white[1]) * (cct / 100)
        b = warm_white[2] + (cold_white[2] - warm_white[2]) * (cct / 100)
        self.set_color((int(r), int(g), int(b)))

    def set_brightness(self, brightness):
        # Set the brightness for all LEDs
        self.leds.brightness = brightness
        self.leds.write()

    def set_color(self, color):
        # Set color for all LEDs
        self.leds.fill(color)
        self.leds.write()