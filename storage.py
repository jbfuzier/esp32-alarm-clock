import json
import os

class Storage:
    def __init__(self, filename='storage.json'):
        self.filename = filename
        self.data = self.load_data()

    def load_data(self):
        if not os.path.exists(self.filename):
            return {'alarms': [], 'settings': {}}
        with open(self.filename, 'r') as f:
            return json.load(f)

    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)

    def add_alarm(self, alarm):
        self.data['alarms'].append(alarm)
        self.save_data()

    def remove_alarm(self, alarm_index):
        if 0 <= alarm_index < len(self.data['alarms']):
            del self.data['alarms'][alarm_index]
            self.save_data()

    def update_setting(self, key, value):
        self.data['settings'][key] = value
        self.save_data()

    def get_alarms(self):
        return self.data['alarms']

    def get_settings(self):
        return self.data['settings']