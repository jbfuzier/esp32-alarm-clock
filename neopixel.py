import asyncio
import neopixel
import machine

class NeoPixelControl:
    def __init__(self, pin, num_pixels):
        self.pixel_pin = machine.Pin(pin)
        self.num_pixels = num_pixels
        self.pixels = neopixel.NeoPixel(self.pixel_pin, self.num_pixels)

    async def set_color(self, r, g, b):
        for i in range(self.num_pixels):
            self.pixels[i] = (r, g, b)
        self.pixels.write()

    async def set_warm_white(self, brightness=255):
        r = int(255 * (brightness / 255))
        g = int(224 * (brightness / 255))
        b = int(204 * (brightness / 255))
        await self.set_color(r, g, b)

    async def set_cold_white(self, brightness=255):
        r = int(255 * (brightness / 255))
        g = int(255 * (brightness / 255))
        b = int(255 * (brightness / 255))
        await self.set_color(r, g, b)

    async def cycle_colors(self):
        while True:
            await self.set_warm_white()
            await asyncio.sleep(1)
            await self.set_cold_white()
            await asyncio.sleep(1)

# Example usage:
# async def main():
#     control = NeoPixelControl(pin=5, num_pixels=8)
#     await control.cycle_colors()
# 
# asyncio.run(main())