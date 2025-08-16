"""
Unified Tray Service for VezylTranslator
Consolidated system tray management and integration
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import threading
import os
import time
from PIL import Image
from pystray import Icon, MenuItem, Menu
from VezylTranslatorNeutron.constant import RESOURCES_DIR


class TrayService:
    """Unified system tray management service"""
    
    def __init__(self):
        self.tray_icon_instance = None
        self.is_running = False
        self.tray_thread = None
    
    # === Tray Icon Management ===
    
    def get_tray_instance(self):
        """Get current tray icon instance"""
        return self.tray_icon_instance
    
    def safe_show_homepage_from_tray(self):
        """Safely show homepage from tray icon with main window recreation if needed"""
        try:
            # Try to get main window using global context first
            import VezylTranslator
            if hasattr(VezylTranslator, 'get_or_create_main_window'):
                main_window = VezylTranslator.get_or_create_main_window()
                if main_window is not None:
                    # Reset shutdown flag if exists
                    if hasattr(main_window, '_shutting_down'):
                        main_window._shutting_down = False
                    main_window.show_and_fill_homepage()
                    return True
            
            print("Could not get main window from global context for tray")
            return False
        except Exception as e:
            print(f"Failed to show homepage from tray: {e}")
            return False
    
    # === Tray Initialization ===
    
    def start_tray_icon(self, software_name, get_windows_theme_func, toggle_clipboard_func, 
                       show_homepage_func, on_quit_func, menu_texts):
        """Start system tray icon in background thread"""
        
        def on_tray_left_click(icon):
            """Handle tray icon left click"""
            toggle_clipboard_func()
        
        def on_homepage_callback(icon, item):
            """Handle homepage menu item click"""
            # Try safe homepage function first
            if self.safe_show_homepage_from_tray():
                return
            
            # Fallback to original method if safe method fails
            try:
                show_homepage_func()
            except Exception as e:
                print(f"Fallback homepage method also failed: {e}")
        
        def on_quit_callback(icon, item):
            """Handle quit menu item click"""
            on_quit_func(icon, item)
        
        def create_and_run_tray():
            """Create and run tray icon"""
            try:
                # Get icon path based on main script location
                base_dir = os.path.dirname(os.path.abspath(os.sys.argv[0]))
                icon_path = os.path.join(base_dir, RESOURCES_DIR, "logo.ico")
                icon_path_dark = os.path.join(base_dir, RESOURCES_DIR, "logo_black.ico")
                
                # Choose icon based on Windows theme
                if get_windows_theme_func() == "dark":
                    icon_image = Image.open(icon_path)
                else:
                    icon_image = Image.open(icon_path_dark)
                
                # Create tray menu
                menu = Menu(
                    MenuItem(menu_texts["toggle_clipboard_translate"], on_tray_left_click, default=True),
                    Menu.SEPARATOR,
                    MenuItem(menu_texts["open_homepage"], on_homepage_callback),
                    MenuItem(menu_texts["quit"], on_quit_callback)
                )
                
                # Create tray icon
                icon = Icon(
                    software_name,
                    icon_image,
                    software_name,
                    menu=menu
                )
                
                # Store instance reference
                self.tray_icon_instance = icon
                self.is_running = True
                
                # Run tray icon (blocks until stopped)
                icon.run()
                
            except Exception as e:
                print(f"Error starting tray icon: {e}")
                import sys
                sys.excepthook(*sys.exc_info())
            finally:
                self.is_running = False
        
        # Start tray in background thread
        self.tray_thread = threading.Thread(target=create_and_run_tray, daemon=True)
        self.tray_thread.start()
        
        # Wait briefly for initialization
        time.sleep(0.5)
        
        return self.tray_icon_instance is not None
    
    def stop_tray_icon(self):
        """Stop tray icon and cleanup"""
        if self.tray_icon_instance:
            try:
                self.tray_icon_instance.stop()
                self.tray_icon_instance = None
                self.is_running = False
                print("Tray icon stopped successfully")
                return True
            except Exception as e:
                print(f"Error stopping tray icon: {e}")
                return False
        return True
    
    # === Icon Management ===
    
    def update_tray_icon(self, icon_path):
        """Update tray icon image"""
        if not self.tray_icon_instance:
            print("No tray icon instance available for update")
            return False
        
        try:
            if os.path.exists(icon_path):
                print(f"Loading new icon from: {icon_path}")
                new_icon = Image.open(icon_path)
                
                # Update icon
                self.tray_icon_instance.icon = new_icon
                
                # Force icon refresh using the pystray recommended method
                try:
                    # Try to refresh the icon through visibility toggle
                    original_visible = self.tray_icon_instance.visible
                    if original_visible:
                        self.tray_icon_instance.visible = False
                        time.sleep(0.05)
                        self.tray_icon_instance.visible = True
                    print(f"Successfully updated tray icon: {os.path.basename(icon_path)}")
                except Exception as refresh_error:
                    print(f"Icon updated but refresh failed: {refresh_error}")
                
                return True
            else:
                print(f"Icon file does not exist: {icon_path}")
                return False
                
        except Exception as e:
            print(f"Error updating tray icon: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def update_icon_for_clipboard_state(self, clipboard_enabled, get_windows_theme_func):
        """Update icon based on clipboard watcher state"""
        if not self.tray_icon_instance:
            print("No tray instance available for clipboard state update")
            return False
        
        try:
            # Get base directory for icon paths
            base_dir = os.path.dirname(os.path.abspath(os.sys.argv[0]))
            
            # Choose appropriate icon
            if not clipboard_enabled:
                icon_path = os.path.join(base_dir, RESOURCES_DIR, "logo_red.ico")
                expected_state = "DISABLED (red)"
            else:
                theme = get_windows_theme_func()
                if theme == "dark":
                    icon_path = os.path.join(base_dir, RESOURCES_DIR, "logo.ico")
                    expected_state = "ENABLED (white for dark theme)"
                else:
                    icon_path = os.path.join(base_dir, RESOURCES_DIR, "logo_black.ico")
                    expected_state = "ENABLED (black for light theme)"
            
            print(f"Clipboard watcher state: {expected_state}")
            print(f"Selected icon path: {icon_path}")
            
            # Verify icon file exists before attempting update
            if not os.path.exists(icon_path):
                print(f"ERROR: Icon file not found: {icon_path}")
                # Try fallback to default icon
                fallback_path = os.path.join(base_dir, RESOURCES_DIR, "logo.ico")
                if os.path.exists(fallback_path):
                    print(f"Using fallback icon: {fallback_path}")
                    icon_path = fallback_path
                else:
                    print("No fallback icon available")
                    return False
            
            return self.update_tray_icon(icon_path)
            
        except Exception as e:
            print(f"Error updating icon for clipboard state: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # === Status and Cleanup ===
    
    def is_tray_running(self):
        """Check if tray icon is currently running"""
        return self.is_running and self.tray_icon_instance is not None
    
    def get_tray_status(self):
        """Get current tray service status"""
        return {
            'is_running': self.is_running,
            'has_instance': self.tray_icon_instance is not None,
            'thread_active': self.tray_thread is not None and self.tray_thread.is_alive()
        }
    
    def cleanup(self):
        """Cleanup tray service resources"""
        self.stop_tray_icon()
        if self.tray_thread and self.tray_thread.is_alive():
            self.tray_thread.join(timeout=2.0)
        self.tray_thread = None


# === Legacy Function Support ===
# For backward compatibility with existing code

_tray_service = TrayService()

def get_tray_icon_instance():
    """Legacy wrapper for getting tray icon instance"""
    return _tray_service.get_tray_instance()

def safe_show_homepage_from_tray():
    """Legacy wrapper for safe homepage show"""
    return _tray_service.safe_show_homepage_from_tray()

def run_tray_icon_in_thread(software_name, get_windows_theme, toggle_clipboard_watcher, 
                           show_homepage, on_quit, menu_texts):
    """Legacy wrapper for running tray icon"""
    success = _tray_service.start_tray_icon(
        software_name, get_windows_theme, toggle_clipboard_watcher,
        show_homepage, on_quit, menu_texts
    )
    print(f"Tray service started: {success}, Instance available: {_tray_service.get_tray_instance() is not None}")
    return success


# === Public API ===
__all__ = ['TrayService', 'get_tray_icon_instance', 'safe_show_homepage_from_tray', 
           'run_tray_icon_in_thread']
