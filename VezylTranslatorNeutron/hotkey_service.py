"""
Unified Hotkey Service for VezylTranslator
Consolidated hotkey management and system integration
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import keyboard


class HotkeyService:
    """Unified hotkey management service"""
    
    def __init__(self):
        self.hotkey_ids = {}  # Dictionary to store hotkey IDs
        self.is_active = False
    
    # === Core Hotkey Operations ===
    
    def register_hotkey(self, name, hotkey_str, callback):
        """Register a hotkey with name, key combination, and callback"""
        self.unregister_hotkey(name)
        
        try:
            # Register hotkey without system-wide suppression
            hotkey_id = keyboard.add_hotkey(hotkey_str, callback, suppress=False)
            self.hotkey_ids[name] = hotkey_id
            print(f"Registered hotkey '{name}': {hotkey_str}")
            return True
        except Exception as e:
            print(f"Failed to register hotkey '{name}' ({hotkey_str}): {e}")
            self.hotkey_ids[name] = None
            return False
    
    def unregister_hotkey(self, name):
        """Unregister a hotkey by name"""
        try:
            if name in self.hotkey_ids and self.hotkey_ids[name]:
                keyboard.remove_hotkey(self.hotkey_ids[name])
                self.hotkey_ids[name] = None
                return True
        except Exception as e:
            print(f"Error unregistering hotkey '{name}': {e}")
        return False
    
    def unregister_all_hotkeys(self):
        """Unregister all registered hotkeys"""
        try:
            for name in list(self.hotkey_ids.keys()):
                self.unregister_hotkey(name)
            print("All hotkeys unregistered successfully")
            return True
        except Exception as e:
            print(f"Error unregistering all hotkeys: {e}")
            return False
    
    # === System Integration ===
    
    def start_hotkey_system(self, translator_instance, main_window_instance, toggle_clipboard_callback):
        """Initialize all hotkey listeners using configured hotkeys"""
        
        # Check if hotkeys are enabled in config
        if not getattr(translator_instance, 'enable_hotkeys', False):
            print("Hotkeys disabled in configuration")
            return False
        
        try:
            # Homepage hotkey
            success1 = self.register_hotkey(
                "homepage",
                translator_instance.hotkey,
                lambda: main_window_instance.show_and_fill_homepage()
            )
            
            # Clipboard toggle hotkey
            success2 = self.register_hotkey(
                "clipboard",
                translator_instance.clipboard_hotkey,
                toggle_clipboard_callback
            )
            
            if success1 and success2:
                self.is_active = True
                print("All hotkeys registered successfully")
                return True
            else:
                print("Some hotkeys failed to register")
                return False
                
        except Exception as e:
            print(f"Error registering hotkeys: {e}")
            return False
    
    def stop_hotkey_system(self):
        """Stop and unregister all hotkey listeners"""
        try:
            self.unregister_hotkey("homepage")
            self.unregister_hotkey("clipboard")
            self.is_active = False
            print("All hotkeys unregistered successfully")
            return True
        except Exception as e:
            print(f"Error unregistering hotkeys: {e}")
            return False
    
    def toggle_hotkey_system(self, translator_instance, main_window_instance, toggle_clipboard_callback, enable=None):
        """Toggle hotkey system on/off or set to specific state"""
        if translator_instance is None:
            print("Translator instance not initialized")
            return False
        
        # If enable is None, toggle current state
        if enable is None:
            enable = not getattr(translator_instance, 'enable_hotkeys', False)
        
        # Update translator instance
        translator_instance.enable_hotkeys = enable
        
        # Save to config if config system is available
        try:
            # Try to save configuration
            if hasattr(translator_instance, 'save_config'):
                translator_instance.save_config()
            else:
                print("Config save method not available")
        except Exception as e:
            print(f"Error saving hotkey config: {e}")
        
        # Apply changes
        if enable:
            result = self.start_hotkey_system(translator_instance, main_window_instance, toggle_clipboard_callback)
            print(f"Hotkeys {'enabled' if result else 'failed to enable'}")
            return result
        else:
            result = self.stop_hotkey_system()
            print(f"Hotkeys {'disabled' if result else 'failed to disable'}")
            return result
    
    # === State Management ===
    
    def get_registered_hotkeys(self):
        """Get list of currently registered hotkeys"""
        return {name: hotkey_id for name, hotkey_id in self.hotkey_ids.items() if hotkey_id is not None}
    
    def is_hotkey_registered(self, name):
        """Check if a specific hotkey is registered"""
        return name in self.hotkey_ids and self.hotkey_ids[name] is not None
    
    def get_system_status(self):
        """Get current hotkey system status"""
        return {
            'is_active': self.is_active,
            'registered_count': len([h for h in self.hotkey_ids.values() if h is not None]),
            'total_slots': len(self.hotkey_ids),
            'registered_hotkeys': list(self.get_registered_hotkeys().keys())
        }
    
    # === Cleanup ===
    
    def cleanup(self):
        """Cleanup hotkey service resources"""
        self.unregister_all_hotkeys()
        self.hotkey_ids.clear()
        self.is_active = False


# === Legacy Function Support ===
# For backward compatibility with existing code

_hotkey_service = HotkeyService()

def register_hotkey(name, hotkey_str, callback):
    """Legacy wrapper for registering hotkey"""
    return _hotkey_service.register_hotkey(name, hotkey_str, callback)

def unregister_hotkey(name):
    """Legacy wrapper for unregistering hotkey"""
    return _hotkey_service.unregister_hotkey(name)

def start_hotkey_system(translator_instance, main_window_instance, toggle_clipboard_callback):
    """Legacy wrapper for starting hotkey system"""
    return _hotkey_service.start_hotkey_system(translator_instance, main_window_instance, toggle_clipboard_callback)

def stop_hotkey_system():
    """Legacy wrapper for stopping hotkey system"""
    return _hotkey_service.stop_hotkey_system()

def toggle_hotkey_system(translator_instance, main_window_instance, toggle_clipboard_callback, enable=None):
    """Legacy wrapper for toggling hotkey system"""
    return _hotkey_service.toggle_hotkey_system(translator_instance, main_window_instance, toggle_clipboard_callback, enable)


# === Public API ===
__all__ = ['HotkeyService', 'register_hotkey', 'unregister_hotkey', 'start_hotkey_system', 
           'stop_hotkey_system', 'toggle_hotkey_system']
