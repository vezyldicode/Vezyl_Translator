"""
 * Program: Vezyl Translator
 * Version: 1.5.2
 * Author: Tuan Viet Nguyen
 * Website: https://github.com/vezyldicode
 * Date:  Mai 24, 2025
 * Description: 
 * 
 * This code is copyrighted by Tuan Viet Nguyen.
 * You may not use, distribute, or modify this code without the author's permission.
"""

# Import the new application core
from VezylTranslatorProton.app import main as app_main

# Legacy support - maintain compatibility
from VezylTranslatorProton.app import get_app_instance, VezylTranslatorApp

# Backward compatibility class
class Translator(VezylTranslatorApp):
    """Legacy Translator class for backward compatibility"""
    
    def __init__(self):
        super().__init__()
        # Maintain legacy attributes for compatibility
        self.Is_icon_showing = self.is_icon_showing
        self.load_config = self.reload_config



# Global variables for backward compatibility
language_interface, theme_interface = "", ""
main_window_instance = None
translator_instance = None
tmp_clipboard = ""
tray_icon_instance = None


def update_main_window_instance(new_window):
    """Update the global main window instance - legacy support"""
    global main_window_instance
    main_window_instance = new_window
    return new_window


def get_or_create_main_window():
    """Get existing main window or create new one if needed - legacy support"""
    global main_window_instance, translator_instance
    app = get_app_instance()
    if app and app.main_window:
        main_window_instance = app.main_window
        return main_window_instance
    return None


def safe_show_homepage():
    """Safely show homepage - legacy support"""
    app = get_app_instance()
    if app and app.main_window:
        try:
            app.main_window.show_and_fill_homepage()
            return True
        except Exception as e:
            print(f"Error showing homepage: {e}")
    return False


def toggle_clipboard_watcher():
    """Toggle clipboard watcher - legacy support"""
    app = get_app_instance()
    if app:
        from VezylTranslatorProton.clipboard_module import toggle_clipboard_watcher as unified_toggle
        unified_toggle(app)


def start_hotkey_listener():
    """Start hotkey listener - legacy support"""
    app = get_app_instance()
    if app:
        return app.start_hotkey_system()
    return False


def stop_hotkey_listener():
    """Stop hotkey listener - legacy support"""
    app = get_app_instance()
    if app:
        return app.stop_hotkey_system()
    return False


def main():
    """Main entry point - delegates to new app system"""
    # Set up global variables for backward compatibility
    global translator_instance, main_window_instance
    
    # Run the new app system
    app_main()


def on_homepage(icon, item):
    """Legacy tray callback"""
    safe_show_homepage()


def on_quit(icon, item):
    """Legacy quit callback"""
    app = get_app_instance()
    if app:
        try:
            if app.main_window and hasattr(app.main_window, 'translation_executor'):
                app.main_window.translation_executor.shutdown(wait=False)
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        try:
            from VezylTranslatorProton.clipboard_module import clear_format_cache
            clear_format_cache()
        except ImportError:
            pass
    
    icon.stop()
    import os
    os._exit(0)


if __name__ == "__main__":
    main()