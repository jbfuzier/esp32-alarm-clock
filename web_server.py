import uasyncio as asyncio
import ujson
from machine import Pin

class SimpleWebServer:
    def __init__(self):
        self.alarms = []
        self.lights = []
        self.settings = {}

    async def handle_request(self, request):
        # Simulated request handling logic
        response = {'status': 'success'}
        return ujson.dumps(response)

    async def get_alarms(self):
        return ujson.dumps(self.alarms)

    async def add_alarm(self, alarm):
        self.alarms.append(alarm)
        return ujson.dumps({'status': 'alarm added'})

    async def manage_lights(self, light_status):
        self.lights.append(light_status)
        return ujson.dumps({'status': 'lights updated'})

    async def update_settings(self, new_settings):
        self.settings.update(new_settings)
        return ujson.dumps({'status': 'settings updated'})

    async def serve(self):
        while True:
            # Simulate waiting for requests
            await asyncio.sleep(1)

# Usage
# server = SimpleWebServer()
# asyncio.run(server.serve())