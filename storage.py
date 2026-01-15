import json
import os

class Storage:
    def __init__(self, filename='data.json'):
        self.filename = filename
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                self.data = json.load(file)

    def save(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=4)

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    async def get_async(self, key):
        # Simulating async operation with asyncio.sleep
        import asyncio
        await asyncio.sleep(0)  # Simulate async behavior
        return self.get(key)

    async def set_async(self, key, value):
        await asyncio.sleep(0)  # Simulate async behavior
        self.set(key, value)
