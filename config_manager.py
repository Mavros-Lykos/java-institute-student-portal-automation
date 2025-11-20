import json
import os
import base64
from datetime import datetime, timedelta

class ConfigManager:
    def __init__(self, config_file="credentials.json"):
        self.config_file = config_file
        self.data = self.load_data()
    
    def load_data(self):
        """Load data from JSON file or create new structure"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    # Ensure all required keys exist
                    if 'users' not in data:
                        data['users'] = []
                    if 'cached_classes' not in data:
                        data['cached_classes'] = []
                    if 'settings' not in data:
                        data['settings'] = {'theme': 'dark'}
                    return data
            except:
                return self.create_default_structure()
        else:
            return self.create_default_structure()
    
    def create_default_structure(self):
        """Create default data structure"""
        return {
            "users": [],
            "cached_classes": [],
            "settings": {
                "theme": "dark"
            }
        }
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    # ==================== Encryption ====================
    
    def encrypt_password(self, password):
        """Simple base64 encryption for password"""
        return base64.b64encode(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password):
        """Decrypt base64 encrypted password"""
        try:
            return base64.b64decode(encrypted_password.encode()).decode()
        except:
            return encrypted_password  # Return as-is if not encrypted
    
    # ==================== User Management ====================
    
    def get_all_users(self):
        """Get all saved users"""
        return self.data.get('users', [])
    
    def get_user(self, user_id):
        """Get specific user by ID"""
        for user in self.data.get('users', []):
            if user['id'] == user_id:
                return user
        return None
    
    def add_user(self, user_data):
        """Add new user with encrypted password"""
        # Encrypt password before saving
        user_data['password'] = self.encrypt_password(user_data['password'])
        user_data['created_at'] = datetime.now().isoformat()
        user_data['last_used'] = datetime.now().isoformat()
        
        self.data['users'].append(user_data)
        
        # Add site URL to history if not present
        self.add_site_url(user_data['site_url'])
        
        self.save_data()
    
    def update_user(self, user_data):
        """Update existing user"""
        # Encrypt password if it's not already encrypted
        if 'password' in user_data:
            # Check if password looks like base64 (simple check)
            try:
                base64.b64decode(user_data['password'])
            except:
                # Not encrypted, so encrypt it
                user_data['password'] = self.encrypt_password(user_data['password'])
        
        user_data['last_used'] = datetime.now().isoformat()
        
        # Find and update user
        for i, user in enumerate(self.data['users']):
            if user['id'] == user_data['id']:
                self.data['users'][i] = user_data
                break
        
        # Add site URL to history if not present
        if 'site_url' in user_data:
            self.add_site_url(user_data['site_url'])
        
        self.save_data()
    
    def delete_user(self, user_id):
        """Delete user by ID"""
        self.data['users'] = [u for u in self.data['users'] if u['id'] != user_id]
        
        # Also delete cached classes for this user
        self.data['cached_classes'] = [
            c for c in self.data['cached_classes'] 
            if c.get('user_id') != user_id
        ]
        
        self.save_data()
    
    # ==================== Site URL Management ====================
    
    def get_site_urls(self):
        """Get list of previously used site URLs"""
        if 'site_urls' not in self.data['settings']:
            self.data['settings']['site_urls'] = []
        
        # Extract unique URLs from users
        urls = set(self.data['settings']['site_urls'])
        for user in self.data['users']:
            if 'site_url' in user:
                urls.add(user['site_url'])
        
        return sorted(list(urls))
    
    def add_site_url(self, url):
        """Add site URL to history"""
        if 'site_urls' not in self.data['settings']:
            self.data['settings']['site_urls'] = []
        
        if url not in self.data['settings']['site_urls']:
            self.data['settings']['site_urls'].append(url)
            self.save_data()
    
    # ==================== Cache Management ====================
    
    def cache_class(self, class_data):
        """Cache a class link for 24 hours"""
        now = datetime.now()
        expires = now + timedelta(days=1)
        
        cache_entry = {
            'user_id': class_data['user_id'],
            'class_name': class_data['class_name'],
            'class_time': class_data['class_time'],
            'date': now.strftime("%Y-%m-%d"),
            'zoom_link': class_data['zoom_link'],
            'cached_at': now.isoformat(),
            'expires_at': expires.isoformat()
        }
        
        # Check if entry already exists (same user, date, class name)
        existing_index = -1
        for i, cached in enumerate(self.data['cached_classes']):
            if (cached['user_id'] == class_data['user_id'] and 
                cached['date'] == cache_entry['date'] and
                cached['class_name'] == class_data['class_name']):
                existing_index = i
                break
        
        if existing_index >= 0:
            # Update existing entry
            self.data['cached_classes'][existing_index] = cache_entry
        else:
            # Add new entry
            self.data['cached_classes'].append(cache_entry)
        
        # Clean up expired entries
        self.cleanup_expired_cache()
        
        self.save_data()
    
    def get_cached_classes(self, user_id=None):
        """Get cached classes, optionally filtered by user"""
        if user_id:
            return [c for c in self.data['cached_classes'] if c['user_id'] == user_id]
        return self.data['cached_classes']
    
    def get_valid_cached_classes(self):
        """Get only non-expired cached classes for today"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        valid_classes = []
        for cached in self.data['cached_classes']:
            try:
                expires_at = datetime.fromisoformat(cached['expires_at'])
                # Only include if not expired and is today's class
                if expires_at > now and cached['date'] == today:
                    valid_classes.append(cached)
            except:
                continue
        
        return valid_classes
    
    def cleanup_expired_cache(self):
        """Remove expired cached classes"""
        now = datetime.now()
        
        self.data['cached_classes'] = [
            cached for cached in self.data['cached_classes']
            if datetime.fromisoformat(cached['expires_at']) > now
        ]
    
    def delete_cached_class(self, cache_index):
        """Delete a specific cached class by index"""
        if 0 <= cache_index < len(self.data['cached_classes']):
            del self.data['cached_classes'][cache_index]
            self.save_data()
    
    # ==================== Settings Management ====================
    
    def get_theme(self):
        """Get current theme setting"""
        return self.data['settings'].get('theme', 'dark')
    
    def set_theme(self, theme):
        """Set theme (dark or light)"""
        self.data['settings']['theme'] = theme
        self.save_data()
    
    def get_setting(self, key, default=None):
        """Get a setting value"""
        return self.data['settings'].get(key, default)
    
    def set_setting(self, key, value):
        """Set a setting value"""
        self.data['settings'][key] = value
        self.save_data()