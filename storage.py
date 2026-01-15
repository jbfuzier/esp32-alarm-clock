"""
Storage Management for ESP32 Alarm Clock
Handles alarm and settings persistence with JSON files
"""
import asyncio
try:
    import ujson as json
except ImportError:
    import json
    
try:
    import uos as os
except ImportError:
    import os

import config


class Storage:
    """
    Manages persistent storage for alarms and settings
    Separate files for alarms.json and settings.json
    """
    
    def __init__(self):
        """Initialize storage with default files"""
        self.alarms_file = config.ALARMS_FILE
        self.settings_file = config.SETTINGS_FILE
        self.next_alarm_id = 0
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Create default files if they don't exist"""
        # Initialize alarms file
        if not self._file_exists(self.alarms_file):
            self.save_alarms([])
        
        # Initialize settings file with defaults
        if not self._file_exists(self.settings_file):
            default_settings = {
                'timezone': 1,
                'brightness': 80,
                'temperature': 50,
                'light_enabled': True
            }
            self.save_settings(default_settings)
    
    def _file_exists(self, filename):
        """Check if file exists"""
        try:
            os.stat(filename)
            return True
        except OSError:
            return False
    
    def _validate_alarm(self, alarm_dict):
        """
        Validate alarm data
        
        Args:
            alarm_dict: Alarm dictionary to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check required fields
        required_fields = ['time', 'type', 'enabled']
        for field in required_fields:
            if field not in alarm_dict:
                return False, f"Missing required field: {field}"
        
        # Validate time format (HH:MM)
        time_str = alarm_dict['time']
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                return False, "Time must be in HH:MM format"
            hour = int(parts[0])
            minute = int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return False, "Invalid time values"
        except (ValueError, AttributeError):
            return False, "Invalid time format"
        
        # Validate brightness (0-100)
        if 'max_brightness' in alarm_dict:
            brightness = alarm_dict['max_brightness']
            if not (0 <= brightness <= 100):
                return False, "Brightness must be between 0 and 100"
        
        # Validate days array (for recurring alarms)
        if alarm_dict['type'] == 'recurring':
            if 'days' not in alarm_dict:
                return False, "Recurring alarms must have 'days' array"
            days = alarm_dict['days']
            if not isinstance(days, list):
                return False, "'days' must be an array"
            for day in days:
                if not (0 <= day <= 6):
                    return False, "Day values must be between 0-6 (Mon-Sun)"
        
        return True, None
    
    # Synchronous alarm operations
    
    def load_alarms(self):
        """
        Load alarms from file (synchronous)
        
        Returns:
            list: List of alarm dictionaries
        """
        try:
            with open(self.alarms_file, 'r') as f:
                alarms = json.load(f)
                
            # Update next_alarm_id
            if alarms:
                max_id = max(alarm.get('id', 0) for alarm in alarms)
                self.next_alarm_id = max_id + 1
                
            return alarms
        except Exception as e:
            print(f"Error loading alarms: {e}")
            return []
    
    def save_alarms(self, alarms):
        """
        Save alarms to file (synchronous)
        
        Args:
            alarms: List of alarm dictionaries
        """
        try:
            with open(self.alarms_file, 'w') as f:
                json.dump(alarms, f)
        except Exception as e:
            print(f"Error saving alarms: {e}")
    
    def load_settings(self):
        """
        Load settings from file (synchronous)
        
        Returns:
            dict: Settings dictionary
        """
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            # Return defaults
            return {
                'timezone': 1,
                'brightness': 80,
                'temperature': 50,
                'light_enabled': True
            }
    
    def save_settings(self, settings):
        """
        Save settings to file (synchronous)
        
        Args:
            settings: Settings dictionary
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def add_alarm(self, alarm_dict):
        """
        Add a new alarm (synchronous)
        
        Args:
            alarm_dict: Alarm data (without id)
            
        Returns:
            tuple: (success, alarm_dict_with_id or error_message)
        """
        # Validate alarm
        is_valid, error = self._validate_alarm(alarm_dict)
        if not is_valid:
            return False, error
        
        # Load existing alarms
        alarms = self.load_alarms()
        
        # Assign new ID
        alarm_dict['id'] = self.next_alarm_id
        self.next_alarm_id += 1
        
        # Add to list
        alarms.append(alarm_dict)
        
        # Save
        self.save_alarms(alarms)
        
        return True, alarm_dict
    
    def update_alarm(self, alarm_id, alarm_data):
        """
        Update an existing alarm (synchronous)
        
        Args:
            alarm_id: ID of alarm to update
            alarm_data: New alarm data
            
        Returns:
            tuple: (success, updated_alarm or error_message)
        """
        # Validate alarm data
        is_valid, error = self._validate_alarm(alarm_data)
        if not is_valid:
            return False, error
        
        # Load alarms
        alarms = self.load_alarms()
        
        # Find and update alarm
        for i, alarm in enumerate(alarms):
            if alarm.get('id') == alarm_id:
                # Preserve ID
                alarm_data['id'] = alarm_id
                alarms[i] = alarm_data
                self.save_alarms(alarms)
                return True, alarm_data
        
        return False, "Alarm not found"
    
    def delete_alarm(self, alarm_id):
        """
        Delete an alarm (synchronous)
        
        Args:
            alarm_id: ID of alarm to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Load alarms
        alarms = self.load_alarms()
        
        # Find and remove alarm
        for i, alarm in enumerate(alarms):
            if alarm.get('id') == alarm_id:
                alarms.pop(i)
                self.save_alarms(alarms)
                return True
        
        return False
    
    def get_alarm(self, alarm_id):
        """
        Get a single alarm (synchronous)
        
        Args:
            alarm_id: ID of alarm to retrieve
            
        Returns:
            dict or None: Alarm dictionary or None if not found
        """
        alarms = self.load_alarms()
        
        for alarm in alarms:
            if alarm.get('id') == alarm_id:
                return alarm
        
        return None
    
    # Asynchronous versions
    
    async def load_alarms_async(self):
        """Load alarms asynchronously"""
        await asyncio.sleep(0)
        return self.load_alarms()
    
    async def save_alarms_async(self, alarms):
        """Save alarms asynchronously"""
        await asyncio.sleep(0)
        self.save_alarms(alarms)
    
    async def load_settings_async(self):
        """Load settings asynchronously"""
        await asyncio.sleep(0)
        return self.load_settings()
    
    async def save_settings_async(self, settings):
        """Save settings asynchronously"""
        await asyncio.sleep(0)
        self.save_settings(settings)
    
    async def add_alarm_async(self, alarm_dict):
        """Add alarm asynchronously"""
        await asyncio.sleep(0)
        return self.add_alarm(alarm_dict)
    
    async def update_alarm_async(self, alarm_id, alarm_data):
        """Update alarm asynchronously"""
        await asyncio.sleep(0)
        return self.update_alarm(alarm_id, alarm_data)
    
    async def delete_alarm_async(self, alarm_id):
        """Delete alarm asynchronously"""
        await asyncio.sleep(0)
        return self.delete_alarm(alarm_id)
    
    async def get_alarm_async(self, alarm_id):
        """Get alarm asynchronously"""
        await asyncio.sleep(0)
        return self.get_alarm(alarm_id)
    
    def get_storage_info(self):
        """
        Get storage information
        
        Returns:
            dict: Storage info with file sizes
        """
        info = {}
        
        try:
            stat = os.stat(self.alarms_file)
            info['alarms_file_size'] = stat[6]  # Size is at index 6
        except:
            info['alarms_file_size'] = 0
        
        try:
            stat = os.stat(self.settings_file)
            info['settings_file_size'] = stat[6]
        except:
            info['settings_file_size'] = 0
        
        return info
