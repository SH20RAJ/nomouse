import json
import os
from pathlib import Path

class Settings:
    def __init__(self):
        # Default settings
        self.defaults = {
            'enabled': True,
            'start_minimized': False,
            'start_on_boot': False,
            'smoothing_slow': 0.5,
            'smoothing_fast': 0.8,
            'scroll_sensitivity': 5,
            'camera_index': 0
        }
        
        # Current settings
        self.current = self.defaults.copy()
        
        # Settings file path
        self.settings_dir = self._get_settings_dir()
        self.settings_file = os.path.join(self.settings_dir, 'settings.json')
        
        # Load settings if file exists
        self.load()
    
    def _get_settings_dir(self):
        """Get the settings directory based on the OS"""
        home = Path.home()
        
        if os.name == 'nt':  # Windows
            settings_dir = os.path.join(home, 'AppData', 'Local', 'NoMouse')
        else:  # macOS and Linux
            settings_dir = os.path.join(home, '.config', 'nomouse')
        
        # Create directory if it doesn't exist
        os.makedirs(settings_dir, exist_ok=True)
        
        return settings_dir
    
    def load(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.current.update(loaded_settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.current, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key, default=None):
        """Get a setting value"""
        return self.current.get(key, default)
    
    def set(self, key, value):
        """Set a setting value and save"""
        self.current[key] = value
        self.save()
    
    def reset(self):
        """Reset settings to defaults"""
        self.current = self.defaults.copy()
        self.save()
    
    def get_all(self):
        """Get all settings"""
        return self.current.copy()
