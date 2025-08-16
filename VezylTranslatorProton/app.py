"""
Application Core Module for VezylTranslator
Manages application lifecycle, initialization, and main components
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import sys
import traceback
import os
import subprocess
import time
import threading
import winreg
from datetime import datetime
from typing import Optional, Callable, Dict, Any

import customtkinter as ctk
from VezylTranslatorNeutron import constant
import VezylTranslatorProton.locale_module as _


class CrashHandler:
    """Handles application crashes and error reporting"""
    
    @staticmethod
    def setup_crash_handler():
        """Setup global exception handler"""
        sys.excepthook = CrashHandler._handle_exception
    
    @staticmethod
    def _handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Handle clipboard errors gracefully - don't crash app
        if any(keyword in error_msg.lower() for keyword in [
            'pyperclipwindowsexception', 'openclipboard', 'clipboard',
            'access denied', 'sharing violation'
        ]):
            print("Clipboard access error - continuing normal operation")
            print(f"Error details: {exc_value}")
            
            # Log clipboard error for debugging
            try:
                with open("clipboard_errors.log", "a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Clipboard Error: {exc_value}\n")
            except:
                pass
            
            return  # Don't crash on clipboard errors
        
        # Check if we're in startup mode
        in_startup_mode = any('--startup-dir' in arg for arg in sys.argv if isinstance(arg, str))

        # Use simpler error handling during startup
        if in_startup_mode:
            try:
                temp_log = os.path.join(os.environ.get('TEMP', ''), 'VezylTranslator_startup_error.log')
                with open(temp_log, 'w', encoding='utf-8') as f:
                    f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(error_msg)
                    f.write("\n\nApplication will retry normal start later.\n")
            except:
                pass
            os._exit(1)
        
        # Normal crash handling for non-startup mode
        try:
            subprocess.Popen([
                "VezylTranslatorCrashHandler.exe",
                error_msg,
                constant.SOFTWARE,
                constant.SOFTWARE_VERSION
            ])
        except Exception:
            try:
                with open("crash.log", "w", encoding="utf-8") as f:
                    f.write(error_msg)
            except:
                pass
        os._exit(1)


class StartupManager:
    """Manages Windows startup integration"""
    
    @staticmethod
    def set_startup(enable: bool) -> bool:
        """Enable/disable Windows startup for the application"""
        app_name = "VezylTranslator"
        
        # Get current application directory
        app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        
        # Get correct executable path (works with both .py and .exe)
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            script_path = os.path.abspath(sys.argv[0])
            python_exe = sys.executable
            if 'python.exe' in python_exe.lower():
                pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
                if os.path.exists(pythonw_exe):
                    exe_path = f'"{pythonw_exe}" "{script_path}"'
                else:
                    exe_path = f'"{python_exe}" "{script_path}"'
            else:
                exe_path = f'"{python_exe}" "{script_path}"'
        
        # For startup registry entry
        if not exe_path.startswith('"'):
            quoted_path = f'"{exe_path}"'
        else:
            quoted_path = exe_path
        
        quoted_path = f'{quoted_path} --app-dir="{app_dir}"'
        
        # Windows Registry method
        try:
            reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, reg_path, 0, 
                winreg.KEY_READ | winreg.KEY_SET_VALUE
            ) as key:
                if enable:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, quoted_path)
                    print(f"Added {app_name} to startup with path: {quoted_path}")
                    
                    # Verify entry
                    try:
                        value, _ = winreg.QueryValueEx(key, app_name)
                        if value == quoted_path:
                            print(f"Successfully verified {app_name} in registry")
                            return True
                    except Exception as e:
                        print(f"Registry verification error: {e}")
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                        return True
                    except FileNotFoundError:
                        return True  # Nothing to delete
        except Exception as e:
            print(f"Registry startup method failed: {e}")
        
        return False


class VezylTranslatorApp:
    """Main application class that manages the entire VezylTranslator lifecycle"""
    
    def __init__(self):
        print(f"{constant.SOFTWARE}. version {constant.SOFTWARE_VERSION} - Copyright © 2025 by Vezyl")
        
        # Initialize core components
        self.config_file = constant.DEFAULT_CONFIG_FILE
        self._load_config()
        
        # Application state
        self.is_icon_showing = False
        self.clipboard_watcher_enabled = True
        self.main_window = None
        self.clipboard_thread = None
        
        # Create hidden root window
        self.root = ctk.CTk()
        self.root.withdraw()
        
        # Setup startup integration
        StartupManager.set_startup(self.start_at_startup)
        
        # Load locale after config is loaded
        _.load_locale(self.interface_language)
    
    def _load_config(self):
        """Load configuration from file using new config manager"""
        from VezylTranslatorProton.config import get_config_manager
        
        # Get config manager and load app config
        self.config_manager = get_config_manager()
        self.app_config = self.config_manager.load_app_config()
        
        # Map config values to instance attributes for backward compatibility
        self.interface_language = self.app_config.interface_language
        self.start_at_startup = self.app_config.start_at_startup
        self.show_homepage_at_startup = self.app_config.show_homepage_at_startup
        self.always_show_transtale = self.app_config.always_show_transtale
        self.enable_ctrl_tracking = self.app_config.enable_ctrl_tracking
        self.enable_hotkeys = self.app_config.enable_hotkeys
        self.save_translate_history = self.app_config.save_translate_history
        self.auto_save_after = self.app_config.auto_save_after
        self.icon_size = self.app_config.icon_size
        self.icon_dissapear_after = self.app_config.icon_dissapear_after
        self.popup_dissapear_after = self.app_config.popup_dissapear_after
        self.max_length_on_popup = self.app_config.max_length_on_popup
        self.max_history_items = self.app_config.max_history_items
        self.hotkey = self.app_config.hotkey
        self.clipboard_hotkey = self.app_config.clipboard_hotkey
        self.dest_lang = self.app_config.dest_lang
        self.font = self.app_config.font
        self.default_fonts = self.app_config.default_fonts
        self.lang_display = self.app_config.lang_display
        self.translation_model = self.app_config.translation_model
        self.translation_models = self.app_config.translation_models
        
        # Initialize translation engine after all config is loaded
        self._init_translation_engine()
        
        # Ensure startup setting is consistent
        StartupManager.set_startup(self.start_at_startup)
    
    def _init_translation_engine(self):
        """Initialize translation engine and update available models"""
        try:
            from VezylTranslatorProton.translator import get_translation_engine
            self.translation_engine = get_translation_engine()
            
            # Update available translation models from engine
            available_models = self.translation_engine.get_available_models()
            if available_models:
                self.translation_models = available_models
                # Update config with current models
                self.app_config.translation_models = self.translation_models
            
            # Set default model if current one is not available
            if self.translation_model not in self.translation_models:
                if available_models:
                    self.translation_model = next(iter(available_models.keys()))
                    self.app_config.translation_model = self.translation_model
                    self.translation_engine.set_default_model(self.translation_model)
                    
            print(f"Translation engine initialized with {len(self.translation_models)} models")
        except Exception as e:
            print(f"Error initializing translation engine: {e}")
    
    def reload_config(self):
        """Reload configuration from file"""
        self._load_config()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        if hasattr(self, 'config_manager') and hasattr(self, 'app_config'):
            # Update app_config with current instance values
            self.app_config.interface_language = self.interface_language
            self.app_config.start_at_startup = self.start_at_startup
            self.app_config.show_homepage_at_startup = self.show_homepage_at_startup
            self.app_config.always_show_transtale = self.always_show_transtale
            self.app_config.enable_ctrl_tracking = self.enable_ctrl_tracking
            self.app_config.enable_hotkeys = self.enable_hotkeys
            self.app_config.save_translate_history = self.save_translate_history
            self.app_config.auto_save_after = self.auto_save_after
            self.app_config.icon_size = self.icon_size
            self.app_config.icon_dissapear_after = self.icon_dissapear_after
            self.app_config.popup_dissapear_after = self.popup_dissapear_after
            self.app_config.max_length_on_popup = self.max_length_on_popup
            self.app_config.max_history_items = self.max_history_items
            self.app_config.hotkey = self.hotkey
            self.app_config.clipboard_hotkey = self.clipboard_hotkey
            self.app_config.dest_lang = self.dest_lang
            self.app_config.font = self.font
            self.app_config.default_fonts = self.default_fonts
            self.app_config.lang_display = self.lang_display
            self.app_config.translation_model = self.translation_model
            self.app_config.translation_models = self.translation_models
            
            return self.config_manager.save_app_config(self.app_config)
        return False
    
    def get_config_manager(self):
        """Get the config manager instance"""
        return getattr(self, 'config_manager', None)
    
    def show_popup(self, text: str, x: int, y: int):
        """Show popup notification"""
        from VezylTranslatorElectron.popup_manager import show_popup_safe
        from VezylTranslatorProton.utils import get_client_preferences
        
        language_interface, theme_interface = get_client_preferences()
        
        show_popup_safe(
            self, text, x, y,
            self.main_window,
            language_interface,
            theme_interface,
            _
        )
    
    def show_icon(self, text: str, x: int, y: int):
        """Show icon notification"""
        from VezylTranslatorElectron.popup_manager import show_icon_safe
        from VezylTranslatorProton.utils import get_client_preferences
        
        language_interface, theme_interface = get_client_preferences()
        
        show_icon_safe(
            self, text, x, y,
            self.main_window,
            language_interface,
            theme_interface,
            _
        )
    
    def initialize_main_window(self):
        """Initialize the main GUI window"""
        from VezylTranslatorElectron.gui import MainWindow
        from VezylTranslatorProton.utils import get_client_preferences
        
        language_interface, theme_interface = get_client_preferences()
        
        self.main_window = MainWindow(
            self,
            language_interface,
            theme_interface,
            _
        )
        return self.main_window
    
    def start_clipboard_watcher(self):
        """Start clipboard monitoring thread"""
        from VezylTranslatorProton.clipboard_module import clipboard_watcher
        
        if not self.main_window:
            print("Cannot start clipboard watcher: Main window not initialized")
            return
        
        self.clipboard_thread = threading.Thread(
            target=clipboard_watcher,
            args=(
                self,
                self.main_window,
                self.always_show_transtale,
                self.show_popup,
                self.show_icon,
                self.main_window.show_and_fill_homepage
            ),
            daemon=True
        )
        self.clipboard_thread.start()
        print("Clipboard watcher started")
    
    def start_hotkey_system(self) -> bool:
        """Initialize hotkey system"""
        try:
            from VezylTranslatorProton.hotkey_manager_module import register_hotkey
            from VezylTranslatorProton.clipboard_module import toggle_clipboard_watcher as unified_toggle_clipboard_watcher
        except ImportError as e:
            print(f"Failed to import hotkey modules: {e}")
            return False
        
        if not getattr(self, 'enable_hotkeys', False):
            print("Hotkeys disabled in configuration")
            return False
        
        if not self.main_window:
            print("Cannot start hotkeys: Main window not initialized")
            return False
        
        try:
            # Register homepage hotkey
            success1 = register_hotkey(
                "homepage",
                self.hotkey,
                lambda: self.main_window.show_and_fill_homepage()
            )
            
            # Register clipboard toggle hotkey  
            success2 = register_hotkey(
                "clipboard",
                self.clipboard_hotkey,
                lambda: unified_toggle_clipboard_watcher(self)
            )
            
            if success1 and success2:
                print("Hotkeys registered successfully")
                return True
            else:
                print("Some hotkeys failed to register")
                return False
                
        except Exception as e:
            print(f"Error registering hotkeys: {e}")
            return False
    
    def stop_hotkey_system(self) -> bool:
        """Stop hotkey system"""
        try:
            from VezylTranslatorProton.hotkey_manager_module import unregister_hotkey
        except ImportError as e:
            print(f"Failed to import hotkey modules: {e}")
            return False
        
        try:
            unregister_hotkey("homepage")
            unregister_hotkey("clipboard")
            print("Hotkeys unregistered successfully")
            return True
        except Exception as e:
            print(f"Error unregistering hotkeys: {e}")
            return False
    
    def start_tray_icon(self):
        """Start system tray icon"""
        from VezylTranslatorProton.tray_module import run_tray_icon_in_thread
        from VezylTranslatorProton.utils import get_windows_theme
        from VezylTranslatorProton.clipboard_module import toggle_clipboard_watcher as unified_toggle_clipboard_watcher
        
        def safe_show_homepage():
            """Safely show homepage with main window recreation if needed"""
            if self.main_window is not None:
                try:
                    # Reset shutdown flag if exists
                    if hasattr(self.main_window, '_shutting_down'):
                        self.main_window._shutting_down = False
                        
                    # Ensure translation executor is available
                    if hasattr(self.main_window, 'gui_controller'):
                        if not hasattr(self.main_window.gui_controller, 'translation_executor') or self.main_window.gui_controller.translation_executor is None:
                            self.main_window.gui_controller._ensure_translation_executor()
                            
                    self.main_window.show_and_fill_homepage()
                    return True
                except Exception as e:
                    print(f"Error showing homepage: {e}")
            
            return False
        
        def on_quit(icon, item):
            """Cleanup resources before quitting"""
            try:
                # Cleanup main window ThreadPool if available
                if self.main_window and hasattr(self.main_window, 'translation_executor'):
                    self.main_window.translation_executor.shutdown(wait=False)
            except Exception as e:
                print(f"Cleanup error: {e}")
            
            try:
                # Cleanup clipboard cache
                from VezylTranslatorProton.clipboard_module import clear_format_cache
                clear_format_cache()
            except ImportError:
                pass
            
            icon.stop()
            os._exit(0)
        
        menu_texts = _._("menu_tray")
        run_tray_icon_in_thread(
            constant.SOFTWARE,
            get_windows_theme,
            lambda: unified_toggle_clipboard_watcher(self),
            safe_show_homepage,
            on_quit,
            menu_texts
        )
    
    def run(self):
        """Main application run method"""
        startup_start = time.time()
        
        # Apply startup optimizations
        try:
            from VezylTranslatorProton.startup_optimizer import optimize_imports, finish_startup_optimization
            fast_startup_enabled = optimize_imports()
            if fast_startup_enabled:
                print("[FastStartup] Fast startup mode activated")
        except ImportError:
            print("Startup optimizer not available")
            fast_startup_enabled = False
        except Exception as e:
            print(f"Startup optimizer error: {e}")
            fast_startup_enabled = False
        
        print(f"Initial startup took: {time.time() - startup_start:.3f}s")
        
        # Apply performance optimizations
        try:
            from VezylTranslatorProton.performance_patches import apply_all_optimizations
            apply_all_optimizations()
        except ImportError:
            print("Performance patches not available")
        except Exception as e:
            print(f"Failed to apply performance optimizations: {e}")
        
        # Initialize GUI
        gui_start = time.time()
        self.initialize_main_window()
        print(f"GUI initialized: {time.time() - gui_start:.3f}s")
        print(f"Total startup time: {time.time() - startup_start:.3f}s")
        
        # Start clipboard watcher
        self.start_clipboard_watcher()
        
        # Start hotkey system
        hotkey_success = self.start_hotkey_system()
        if hotkey_success:
            print("Hotkey system initialized")
        else:
            print("Hotkey system disabled or failed")
        
        # Show window if configured
        if self.show_homepage_at_startup:
            # Ensure window is visible
            self.main_window.deiconify()
            self.main_window.lift()
            self.main_window.focus_force()
            
            # Add a delayed show as backup
            self.main_window.after(1000, lambda: self._ensure_window_visible())
            
            # Finish startup optimization after window is shown
            if fast_startup_enabled:
                self.main_window.after(2000, lambda: finish_startup_optimization())
        else:
            self.main_window.withdraw()
            
            # Finish startup optimization for hidden startup
            if fast_startup_enabled:
                self.main_window.after(3000, lambda: finish_startup_optimization())
        
        # Start tray icon
        self.start_tray_icon()
        
        # Run main loop
        self.main_window.mainloop()
    
    def _ensure_window_visible(self):
        """Ensure main window is visible"""
        if self.show_homepage_at_startup and self.main_window:
            self.main_window.deiconify()
            self.main_window.lift()
            self.main_window.focus_force()
            self.main_window.update()


# Global application instance
app_instance: Optional[VezylTranslatorApp] = None


def get_app_instance() -> Optional[VezylTranslatorApp]:
    """Get the global application instance"""
    return app_instance


def create_app() -> VezylTranslatorApp:
    """Create and return the application instance"""
    global app_instance
    if app_instance is None:
        app_instance = VezylTranslatorApp()
    return app_instance


def main():
    """Main entry point for the application"""
    # Setup crash handler first
    CrashHandler.setup_crash_handler()
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='VezylTranslator')
    parser.add_argument('--app-dir', help='Application directory path')
    parser.add_argument('--quiet-startup', action='store_true', help='Start silently')
    args, unknown = parser.parse_known_args()
    
    # Change to the application directory if specified
    if args.app_dir and os.path.exists(args.app_dir):
        try:
            os.chdir(args.app_dir)
            print(f"Changed working directory to: {args.app_dir}")
        except Exception as e:
            print(f"Failed to set working directory: {e}")
    
    # Create and run application
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
