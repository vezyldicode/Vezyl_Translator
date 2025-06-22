"""
 * Program: Vezyl Translator
 * Version: 1.0.0 beta
 * Author: Tuan Viet Nguyen
 * Website: https://github.com/vezyldicode
 * Date:  Mai 24, 2025
 * Description: 
 * 
 * This code is copyrighted by Tuan Viet Nguyen.
 * You may not use, distribute, or modify this code without the author's permission.
"""
from VezylTranslatorNeutron import constant
import sys
import traceback
import os
import subprocess


def external_crash_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Check if we're in startup mode by checking command line args
    in_startup_mode = any('--startup-dir' in arg for arg in sys.argv if isinstance(arg, str))
    
    # Use a simpler error handling approach during startup
    if in_startup_mode:
        try:
            # Try to log to user's temp directory which should always be writable
            temp_log = os.path.join(os.environ.get('TEMP', ''), 'VezylTranslator_startup_error.log')
            with open(temp_log, 'w', encoding='utf-8') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(error_msg)
                f.write("\n\nApplication will retry normal start later.\n")
        except:
            pass  # If even this fails, just silently exit
        # Exit silently without showing console window
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
        # If crash handler fails, try to show a simple message
        try:
            with open("crash.log", "w", encoding="utf-8") as f:
                f.write(error_msg)
        except:
            pass
    os._exit(1)

sys.excepthook = external_crash_handler

import winsound
import customtkinter as ctk
import threading
import time
import json
import base64
import winreg  # Thêm import này ở đầu file
from datetime import datetime
from PIL import Image  # pip install pillow
from pystray import Icon, MenuItem, Menu
import keyboard
import toml
import VezylTranslatorProton.locale_module  as _
from VezylTranslatorProton.file_flow import (
    pad, 
    unpad, 
    encrypt_aes, 
    decrypt_aes, 
    get_aes_key)
from VezylTranslatorProton.hotkey_manager_module import (
    register_hotkey, 
    unregister_hotkey)
from VezylTranslatorProton.tray_module import run_tray_icon_in_thread, get_tray_icon_instance
from VezylTranslatorProton.clipboard_module import clipboard_watcher, get_clipboard_text, set_clipboard_text
from VezylTranslatorProton.config_module import load_config, save_config, get_default_config
from VezylTranslatorProton.utils import (
    get_windows_theme, 
    show_confirm_popup, 
    get_client_preferences, 
    ensure_local_dir, 
    search_entries
)
from VezylTranslatorProton.translate_module import translate_with_model
from VezylTranslatorProton.history_module import (
    write_log_entry,
    read_history_entries,
    delete_history_entry,
    delete_all_history_entries
)
from VezylTranslatorProton.favorite_module import (
    write_favorite_entry,
    read_favorite_entries,
    delete_favorite_entry,
    delete_all_favorite_entries,
    update_favorite_note
)
from VezylTranslatorElectron.gui import MainWindow
from VezylTranslatorElectron.popup_manager import show_popup_safe, show_icon_safe

class Translator:
    def __init__(self):
        print(f"{constant.SOFTWARE}. version {constant.SOFTWARE_VERSION} - Copyright © 2025 by Vezyl")
        # Load config
        self.config_file = "config/general.json"
        self.load_config()
        self.Is_icon_showing = False
        self.clipboard_watcher_enabled = True
        # Load locale
        locales_dir = os.path.join("resources", "locales")
        _.load_locale(self.interface_language, locales_dir)

        self.root = ctk.CTk()
        self.root.withdraw()
        # --- Thêm xử lý khởi động cùng Windows ---
        self.set_startup(self.start_at_startup)

    def set_startup(self, enable):
        """
        Bật/tắt khởi động cùng Windows cho phần mềm.
        """
        app_name = "VezylTranslator"
        
        # Get current application directory
        app_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        
        # Get correct executable path (works with both .py and .exe)
        if getattr(sys, 'frozen', False):
            # Running as compiled .exe
            exe_path = sys.executable
        else:
            # Running as script
            script_path = os.path.abspath(sys.argv[0])
            python_exe = sys.executable
            # Try to use pythonw instead of python
            if 'python.exe' in python_exe.lower():
                pythonw_exe = python_exe.replace('python.exe', 'pythonw.exe')
                if os.path.exists(pythonw_exe):
                    exe_path = f'"{pythonw_exe}" "{script_path}"'
                else:
                    exe_path = f'"{python_exe}" "{script_path}"'
            else:
                exe_path = f'"{python_exe}" "{script_path}"'
        
        # For startup registry entry - always use quoted path for reliability
        if not exe_path.startswith('"'):
            quoted_path = f'"{exe_path}"'
        else:
            quoted_path = exe_path
        
        # Add the current directory as startup parameter
        quoted_path = f'{quoted_path} --app-dir="{app_dir}"'
        
        # Try multiple startup methods in order of preference
        success = False
        
        # Method 1: Windows Registry
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
                            success = True
                    except Exception as e:
                        print(f"Registry verification error: {e}")
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                        success = True
                    except FileNotFoundError:
                        success = True  # Nothing to delete
        except Exception as e:
            print(f"Registry startup method failed: {e}")
        
        return success

    def load_config(self):

        """load file config"""
        default_config = get_default_config()
        config = load_config(self.config_file, default_config)
        self.interface_language = config.get('interface_language')
        self.start_at_startup = config.get('start_at_startup')
        self.show_homepage_at_startup = config.get('show_homepage_at_startup')
        self.always_show_transtale = config.get('always_show_transtale')
        self.save_translate_history = config.get('save_translate_history')
        self.auto_save_after = config.get('auto_save_after')
        self.icon_size = config.get('icon_size')
        self.icon_dissapear_after = config.get('icon_dissapear_after')
        self.popup_dissapear_after = config.get('popup_dissapear_after')
        self.max_length_on_popup = config.get('max_length_on_popup')
        self.max_history_items = config.get('max_history_items')
        self.hotkey = config.get('hotkey')
        self.clipboard_hotkey = config.get('clipboard_hotkey')
        self.dest_lang = config.get('dest_lang')
        self.font = config.get('font')
        self.default_fonts = config.get('default_fonts')
        self.lang_display = config.get('lang_display')
        # --- Đảm bảo trạng thái khởi động cùng Windows đúng với config ---
        self.set_startup(self.start_at_startup)
    
    def show_popup(self, text, x, y):
        show_popup_safe(
            self, text, x, y,
            main_window_instance,
            language_interface,
            theme_interface,
            _
        )

    def show_icon(self, text, x, y):
        show_icon_safe(
            self, text, x, y,
            main_window_instance,
            language_interface,
            theme_interface,
            _
        )



language_interface, theme_interface = "", ""

main_window_instance = None  # Biến toàn cục lưu MainWindow
translator_instance = None   # Biến toàn cục lưu Translator
tmp_clipboard = ""
tray_icon_instance = None   # Biến toàn cục lưu instance của Translator


def toggle_clipboard_watcher():
    global translator_instance

    if translator_instance is not None:
        translator_instance.clipboard_watcher_enabled = not getattr(translator_instance, "clipboard_watcher_enabled", True)
        state = "ON" if translator_instance.clipboard_watcher_enabled else "OFF"
        print(f"Clipboard watcher toggled: {state}")

        # Phát âm thanh thông báo
        if translator_instance.clipboard_watcher_enabled:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            winsound.MessageBeep(winsound.MB_ICONHAND)

        # Đổi icon tray theo trạng thái
        tray_icon = get_tray_icon_instance()
        if tray_icon is not None:
            try:
                if not translator_instance.clipboard_watcher_enabled:
                    new_icon = Image.open("resources/logo_red.ico")
                else:
                    if get_windows_theme() == "dark":
                        new_icon = Image.open("resources/logo.ico")
                    else:
                        new_icon = Image.open("resources/logo_black.ico")
                tray_icon.icon = new_icon
                # Force the icon to refresh by toggling visibility
                tray_icon.visible = False
                time.sleep(0.1)
                tray_icon.visible = True
                print(f"Icon updated to {'red' if not translator_instance.clipboard_watcher_enabled else 'normal'}")
            except Exception as e:
                print(f"Error updating icon: {e}")
        else:
            print("Tray icon instance is not initialized, cannot update icon.")

def start_hotkey_listener():
    """Initialize all hotkey listeners using the configured hotkeys."""
    global translator_instance

    # Hotkey mở homepage
    register_hotkey(
        "homepage",
        translator_instance.hotkey,
        lambda: main_window_instance.show_and_fill_homepage()
    )

    # Hotkey bật/tắt clipboard watcher
    register_hotkey(
        "clipboard",
        translator_instance.clipboard_hotkey,
        toggle_clipboard_watcher
    )
    

def main():
    # Parse command line arguments first
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
    
    # # Create required directories FIRST
    # ensure_required_directories()


    global language_interface, theme_interface, translator_instance, main_window_instance
    language_interface, theme_interface = get_client_preferences()
    # Continue with normal startup...
    global translator_instance, main_window_instance
    translator_instance = Translator()
    main_window_instance = MainWindow(
    translator_instance,
    language_interface,
    theme_interface,
    _
)
    translator_instance.main_window = main_window_instance
    translator_instance.clipboard_thread = threading.Thread(
        target=clipboard_watcher,
        args=(
            translator_instance,
            main_window_instance,
            translator_instance.always_show_transtale,
            translator_instance.show_popup,
            translator_instance.show_icon,
            main_window_instance.show_and_fill_homepage
        ),
        daemon=True
    )
    translator_instance.clipboard_thread.start()

    start_hotkey_listener()

    if translator_instance.show_homepage_at_startup:
        # Ensure window is visible with multiple approaches
        main_window_instance.deiconify()
        main_window_instance.lift()
        main_window_instance.focus_force()
        
        # Add a delayed show as backup to ensure window appears
        main_window_instance.after(1000, lambda: ensure_window_visible())
    else:
        main_window_instance.withdraw()

    def ensure_window_visible():
        if translator_instance.show_homepage_at_startup:
            main_window_instance.deiconify()
            main_window_instance.lift()
            main_window_instance.focus_force()
            main_window_instance.update()
            
    # Khởi động tray icon
    menu_texts = _._("menu_tray")
    run_tray_icon_in_thread(
        constant.SOFTWARE,
        get_windows_theme,
        toggle_clipboard_watcher,
        main_window_instance.show_and_fill_homepage,
        on_quit,
        menu_texts
    )

    # Chạy mainloop của MainWindow (main thread)
    main_window_instance.mainloop()

def on_homepage(icon, item):
    global main_window_instance
    if main_window_instance is not None:
        try:
            main_window_instance.after(0, main_window_instance.show_and_fill_homepage)
        except Exception as e:
            print(f"Loi hien thi cua so chinh: {e}")
            sys.excepthook(*sys.exc_info())
    else:
        print("Cua so chinh chua duoc khoi tao")

def on_quit(icon, item):
    icon.stop()
    os._exit(0)

if __name__ == "__main__":
    main()

# def ensure_required_directories():
#     """Create all required directories for the application"""
#     dirs = [
#         "config", 
#         "resources",
#         "resources/locales",
#         "logs",
#         "temp"
#     ]
#     for directory in dirs:
#         try:
#             os.makedirs(directory, exist_ok=True)
#         except:
#             # For startup, we'll continue even if some directories can't be created
#             pass