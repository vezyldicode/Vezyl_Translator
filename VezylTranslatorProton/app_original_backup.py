"""
Application Core Module for VezylTranslator - Phase 9A Consolidated
Manages application lifecycle, initialization, and unified controller logic
Consolidated: GUIController + TranslationController + TabController
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
import tkinter as tk
from datetime import datetime
from typing import Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import customtkinter as ctk
from VezylTranslatorNeutron import constant
from VezylTranslatorElectron.helpers import get_windows_theme, search_entries, ensure_local_dir, show_confirm_popup
from VezylTranslatorProton.translator import get_translation_engine
from VezylTranslatorProton.storage import (
    write_log_entry, read_history_entries, delete_history_entry, delete_all_history_entries,
    read_favorite_entries, delete_favorite_entry, delete_all_favorite_entries,
    update_favorite_note, write_favorite_entry
)
from VezylTranslatorNeutron.clipboard_service import set_clipboard_text
import VezylTranslatorProton.locale_module as _


# === CRASH HANDLER ===

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


# === STARTUP MANAGER ===

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
            exe_path = os.path.join(app_dir, "VezylTranslator.exe")
            if not os.path.exists(exe_path):
                exe_path = os.path.join(app_dir, "VezylTranslator.py")
        
        startup_command = f'"{exe_path}" --startup-dir'
        
        try:
            # Use winreg to access registry
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, startup_command)
                winreg.CloseKey(key)
                print(f"Startup enabled: {startup_command}")
                return True
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    winreg.CloseKey(key)
                    print("Startup disabled")
                    return True
                except FileNotFoundError:
                    winreg.CloseKey(key)
                    print("Startup entry not found (already disabled)")
                    return True
                    
        except Exception as e:
            print(f"Error managing startup: {e}")
            return False


# === CONSOLIDATED APPLICATION CORE ===

class ApplicationCore:
    """
    Consolidated Application Core with integrated controllers
    Combines: GUIController + TranslationController + TabController functionality
    """
    
    def __init__(self):
        # Application state
        self.main_window = None
        self.translator = None
        self.language_interface = None
        self.theme_interface = None
        self._ = _
        
        # GUI Controller state
        self.translation_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="gui_translate")
        self.pending_translations = {}
        self._shutting_down = False
        self.ctrl_pressed = False
        self.active_mousewheel_handlers = []
        self.is_fullscreen = False
        self.width = 900
        self.height = 600
        
        # Translation Controller state
        self.auto_save_state = {"saved": False, "timer_id": None, "last_content": ""}
        
        print("ApplicationCore initialized with consolidated controllers")
    
    # === POPUP MANAGEMENT ===
    
    def show_popup_safe(self, text, x, y):
        """Show popup safely with client preferences"""
        from VezylTranslatorElectron.popup_manager import show_popup_safe
        from VezylTranslatorElectron.helpers import get_client_preferences
        
        language_interface, theme_interface = get_client_preferences()
        
        show_popup_safe(
            self, text, x, y,
            self.main_window,
            language_interface,
            theme_interface,
            _
        )
    
    def show_icon_safe(self, text, x, y):
        """Show icon safely with client preferences"""
        from VezylTranslatorElectron.popup_manager import show_icon_safe
        from VezylTranslatorElectron.helpers import get_client_preferences
        
        language_interface, theme_interface = get_client_preferences()
        
        show_icon_safe(
            self, text, x, y,
            self.main_window,
            language_interface,
            theme_interface,
            _
        )
    
    def initialize_main_window(self):
        """Initialize main window with preferences"""
        from VezylTranslatorElectron.main_window import MainWindow
        from VezylTranslatorElectron.helpers import get_client_preferences
        
        language_interface, theme_interface = get_client_preferences()
        
        self.main_window = MainWindow(
            self,
            language_interface,
            theme_interface,
            _
        )
        return self.main_window
    
    # === GUI CONTROLLER METHODS ===
    
    def get_window_config(self):
        """Get window configuration"""
        return {
            'title': f"{constant.SOFTWARE_NAME} {constant.SOFTWARE_VERSION}",
            'width': self.width,
            'height': self.height,
            'icon_path': self._get_icon_path(),
            'resizable': True
        }
    
    def _get_icon_path(self):
        """Get appropriate icon based on system theme"""
        theme = get_windows_theme()
        if theme == "dark":
            return os.path.join(constant.RESOURCES_DIR, "logo.ico")
        else:
            return os.path.join(constant.RESOURCES_DIR, "logo_black.ico")
    
    def get_navigation_config(self):
        """Get navigation bar configuration"""
        return [
            (os.path.join(constant.RESOURCES_DIR, "logo.png"), "Trang chủ"),
            (os.path.join(constant.RESOURCES_DIR, "history.png"), "Lịch sử"),
            (os.path.join(constant.RESOURCES_DIR, "favorite.png"), "Yêu thích"),
            (os.path.join(constant.RESOURCES_DIR, "settings.png"), "Cài đặt")
        ]
    
    def translate_async(self, widget_id, translate_function):
        """Execute translation asynchronously using ThreadPool"""
        if self._shutting_down:
            print("Translation skipped: Application shutting down")
            return None
            
        if not hasattr(self, 'translation_executor') or self.translation_executor._shutdown:
            print("Translation executor unavailable or shutdown")
            return None
            
        # Cancel pending translation for this widget
        if widget_id in self.pending_translations:
            try:
                self.pending_translations[widget_id].cancel()
            except:
                pass
            
        try:
            future = self.translation_executor.submit(translate_function)
            self.pending_translations[widget_id] = future
            
            def on_complete(fut):
                self.pending_translations.pop(widget_id, None)
                try:
                    fut.result()
                except Exception as e:
                    print(f"Translation error: {e}")
                    
            future.add_done_callback(on_complete)
            return future
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                print("Translation executor has been shutdown")
                return None
            else:
                raise
    
    def cancel_translation(self, widget_id):
        """Cancel translation for specific widget"""
        if widget_id in self.pending_translations:
            try:
                self.pending_translations[widget_id].cancel()
            except:
                pass
            self.pending_translations.pop(widget_id, None)
    
    def setup_ctrl_tracking(self, window):
        """Setup or disable Ctrl key tracking"""
        # Unbind all Ctrl events first
        window.unbind_all('<Control_L>')
        window.unbind_all('<Control_R>')
        window.unbind_all('<KeyRelease-Control_L>')
        window.unbind_all('<KeyRelease-Control_R>')
        
        # Only bind if explicitly enabled
        if getattr(self.translator, 'enable_ctrl_tracking', False):
            window.bind_all('<Control_L>', self._ctrl_down)
            window.bind_all('<Control_R>', self._ctrl_down)
            window.bind_all('<KeyRelease-Control_L>', self._ctrl_up)
            window.bind_all('<KeyRelease-Control_R>', self._ctrl_up)
            print("Ctrl tracking enabled (may cause system delays)")
        else:
            print("Ctrl tracking disabled (recommended for performance)")
    
    def _ctrl_down(self, event=None):
        self.ctrl_pressed = True

    def _ctrl_up(self, event=None):
        self.ctrl_pressed = False
    
    def add_mousewheel_handler(self, canvas, handler_func):
        """Add mousewheel handler and track it for cleanup"""
        self.active_mousewheel_handlers.append((canvas, handler_func))
        canvas.bind_all("<MouseWheel>", handler_func)
        
    def cleanup_mousewheel_handlers(self):
        """Clean up all tracked mousewheel handlers"""
        for canvas, handler_func in self.active_mousewheel_handlers:
            try:
                if canvas.winfo_exists():
                    canvas.unbind_all("<MouseWheel>")
            except:
                pass
        self.active_mousewheel_handlers.clear()

    def safe_mousewheel_handler(self, canvas):
        """Create a safe mousewheel handler for a canvas"""
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        return _on_mousewheel
    
    def toggle_fullscreen(self, window):
        self.is_fullscreen = not self.is_fullscreen
        window.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, window):
        self.is_fullscreen = False
        window.attributes("-fullscreen", False)
    
    # === TRANSLATION CONTROLLER METHODS ===
    
    def create_translation_function(self, text, src_lang, dest_lang, dest_text_widget, 
                                   src_lang_combo=None, lang_display=None, write_history=True):
        """Create a translation function for async execution"""
        def do_translate():
            if not text.strip():
                # Clear destination if source is empty
                if dest_text_widget:
                    dest_text_widget.after(0, lambda: self._update_dest_text(dest_text_widget, ""))
                return
            
            try:
                # Perform translation using new engine
                engine = get_translation_engine()
                result = engine.translate(
                    text, src_lang, dest_lang, 
                    self.translator.translation_model
                )
                translated = result.to_dict()  # Convert to old format for compatibility
                
                if translated and dest_text_widget:
                    # Extract text from translation result
                    translated_text = translated.get("text", "") if isinstance(translated, dict) else str(translated)
                    detected_src = translated.get("src", src_lang) if isinstance(translated, dict) else src_lang
                    
                    # Update source language combo if auto-detect was used
                    if src_lang == "auto" and src_lang_combo and lang_display and detected_src != "auto":
                        detected_display = lang_display.get(detected_src, detected_src)
                        src_lang_combo.after(0, lambda: src_lang_combo.set(detected_display))
                    
                    # Update UI in main thread
                    dest_text_widget.after(0, lambda: self._update_dest_text(dest_text_widget, translated_text))
                    
                    # Write to history if enabled
                    if write_history and getattr(self.translator, 'save_translate_history', True):
                        try:
                            ensure_local_dir(constant.LOCAL_DIR)
                            # Update constant.last_translated_text for consistency
                            constant.last_translated_text = translated_text
                            write_log_entry(
                                translated_text,  # last_translated_text
                                detected_src,     # src_lang  
                                dest_lang,        # dest_lang
                                "homepage",       # source
                                constant.TRANSLATE_LOG_FILE,  # log_file
                                self.language_interface,      # language_interface
                                self.theme_interface           # theme_interface
                            )
                        except Exception as e:
                            print(f"Error writing history: {e}")
                
            except Exception as e:
                print(f"Translation error: {e}")
                if dest_text_widget:
                    error_msg = f"Lỗi dịch: {str(e)}"  # Capture error message immediately
                    dest_text_widget.after(0, lambda msg=error_msg: self._update_dest_text(dest_text_widget, msg))
        
        return do_translate
    
    def _update_dest_text(self, dest_text_widget, text):
        """Update destination text widget safely"""
        try:
            if dest_text_widget.winfo_exists():
                dest_text_widget.configure(state="normal")
                dest_text_widget.delete("1.0", "end")
                dest_text_widget.insert("1.0", text)
                dest_text_widget.configure(state="disabled")
        except Exception as e:
            print(f"Error updating destination text: {e}")
    
    def create_reverse_translation_function(self, src_text_widget, dest_text_widget, 
                                          src_lang_combo, dest_lang_combo, lang_display):
        """Create reverse translation function"""
        def reverse_translate():
            try:
                # Get current values
                src_text = src_text_widget.get("1.0", "end").strip()
                dest_text_widget.configure(state="normal")
                dest_text = dest_text_widget.get("1.0", "end").strip()
                dest_text_widget.configure(state="disabled")
                
                if not dest_text:
                    return
                
                # Swap languages
                src_lang_display = src_lang_combo.get()
                dest_lang_display = dest_lang_combo.get()
                
                # Don't reverse if source is auto-detect
                if src_lang_display == self._._("home")["auto_detect"]:
                    return
                
                # Swap combobox values
                src_lang_combo.set(dest_lang_display)
                dest_lang_combo.set(src_lang_display)
                
                # Swap text content
                src_text_widget.delete("1.0", "end")
                src_text_widget.insert("1.0", dest_text)
                
                # Trigger translation
                src_text_widget.edit_modified(True)
                src_text_widget.event_generate("<<Modified>>")
                
            except Exception as e:
                print(f"Error in reverse translation: {e}")
        
        return reverse_translate
    
    def setup_auto_save(self, src_text_widget):
        """Setup auto-save functionality for source text"""
        def save_last_translated_text():
            text = src_text_widget.get("1.0", "end").strip()
            if text:
                constant.last_translated_text = text
                self.auto_save_state["saved"] = True
        
        def start_auto_save_timer():
            if self.auto_save_state["timer_id"]:
                src_text_widget.after_cancel(self.auto_save_state["timer_id"])
            self.auto_save_state["timer_id"] = src_text_widget.after(
                self.translator.auto_save_after, save_last_translated_text
            )
        
        def reset_auto_save():
            self.auto_save_state["saved"] = False
            self.auto_save_state["last_content"] = src_text_widget.get("1.0", "end").strip()
            start_auto_save_timer()
        
        def on_src_text_key(event):
            current = src_text_widget.get("1.0", "end").strip()
            if not self.auto_save_state["saved"]:
                reset_auto_save()
            elif current != self.auto_save_state["last_content"]:
                reset_auto_save()
            
            # Save immediately on Enter
            if event.keysym == "Return" and not self.auto_save_state["saved"]:
                save_last_translated_text()
        
        # Bind events
        src_text_widget.bind("<KeyRelease>", on_src_text_key)
        
        # Initialize auto-save state
        reset_auto_save()
        
        return {
            'save_function': save_last_translated_text,
            'reset_function': reset_auto_save,
            'on_key_function': on_src_text_key
        }
    
    def create_debounced_text_change_handler(self, src_text_widget, translation_callback, delay=300):
        """Create debounced text change handler"""
        def debounce_text_change(*args):
            if hasattr(debounce_text_change, "after_id") and debounce_text_change.after_id:
                src_text_widget.after_cancel(debounce_text_change.after_id)
            debounce_text_change.after_id = src_text_widget.after(delay, translation_callback)
        
        debounce_text_change.after_id = None
        return debounce_text_change
    
    def get_language_from_display(self, display_value, lang_display, auto_detect_text):
        """Convert display language to language code"""
        if display_value == auto_detect_text:
            return "auto"
        else:
            return next((k for k, v in lang_display.items() if v == display_value), "auto")
    
    def fill_last_translated_text(self, src_text_widget):
        """Fill source text with last translated text if available"""
        if constant.last_translated_text:
            try:
                src_text_widget.delete("1.0", "end")
                src_text_widget.insert("1.0", constant.last_translated_text)
                # Reset modification flag
                src_text_widget.edit_modified(False)
            except Exception as e:
                print(f"Error filling last translated text: {e}")
    
    # === TAB CONTROLLER METHODS ===
    
    def get_history_data(self, search_keyword="", max_items=30):
        """Get filtered and limited history data"""
        log_file = constant.TRANSLATE_LOG_FILE
        history = read_history_entries(log_file, self.language_interface, self.theme_interface)
        
        if search_keyword:
            filtered = search_entries(history, search_keyword, ["last_translated_text", "translated_text"])
        else:
            filtered = history
        
        # Limit items for performance
        return list(reversed(filtered[-max_items:]))
    
    def get_favorite_data(self, search_keyword="", max_items=30):
        """Get filtered and limited favorite data"""
        log_file = constant.FAVORITE_LOG_FILE
        favorites = read_favorite_entries(log_file, self.language_interface, self.theme_interface)
        
        if search_keyword:
            filtered = search_entries(favorites, search_keyword, ["original_text", "translated_text", "note"])
        else:
            filtered = favorites
        
        # Limit items for performance
        return list(reversed(filtered[-max_items:]))
    
    def delete_history_entry_by_data(self, time_str, last_translated_text, refresh_callback):
        """Delete history entry and refresh UI"""
        try:
            delete_history_entry(
                constant.TRANSLATE_LOG_FILE,
                self.language_interface,
                self.theme_interface,
                time_str,
                last_translated_text
            )
            refresh_callback()
        except Exception as e:
            print(f"Error deleting history entry: {e}")
    
    def delete_all_history_entries_with_confirm(self, parent, refresh_callback):
        """Delete all history entries with confirmation"""
        show_confirm_popup(
            parent=parent,
            title=self._._("confirm_popup")["title"],
            message=self._._("history")["menu"]["delete_confirm"],
            on_confirm=lambda: (
                ensure_local_dir(constant.LOCAL_DIR),
                delete_all_history_entries(constant.TRANSLATE_LOG_FILE),
                refresh_callback()
            ),
            width=420,
            height=180,
            _=self._
        )
    
    def delete_favorite_entry_by_data(self, time_str, original_text, refresh_callback):
        """Delete favorite entry and refresh UI"""
        try:
            delete_favorite_entry(
                constant.FAVORITE_LOG_FILE, 
                self.language_interface, 
                self.theme_interface, 
                time_str, 
                original_text
            )
            refresh_callback()
        except Exception as e:
            print(f"Error deleting favorite entry: {e}")
    
    def delete_all_favorite_entries_with_confirm(self, parent, refresh_callback):
        """Delete all favorite entries with confirmation"""
        show_confirm_popup(
            parent=parent,
            title=self._._("confirm_popup")["title"],
            message=self._._("favorite")["menu"]["delete_confirm"],
            on_confirm=lambda: (
                ensure_local_dir(constant.LOCAL_DIR),
                delete_all_favorite_entries(constant.FAVORITE_LOG_FILE),
                refresh_callback()
            ),
            width=420,
            height=180,
            _=self._
        )
    
    def update_favorite_note_by_data(self, entry_time, new_note, refresh_callback):
        """Update favorite note and refresh UI"""
        try:
            update_favorite_note(
                constant.FAVORITE_LOG_FILE, 
                self.language_interface, 
                self.theme_interface, 
                entry_time, 
                new_note
            )
            refresh_callback()
        except Exception as e:
            print(f"Error updating favorite note: {e}")
    
    def add_to_favorites(self, original_text, translated_text, src_lang, dest_lang, note=""):
        """Add entry to favorites"""
        try:
            ensure_local_dir(constant.LOCAL_DIR)
            write_favorite_entry(
                constant.FAVORITE_LOG_FILE,
                self.language_interface,
                self.theme_interface,
                original_text,
                translated_text,
                src_lang,
                dest_lang,
                note
            )
            return True
        except Exception as e:
            print(f"Error adding to favorites: {e}")
            return False
    
    def copy_text_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            set_clipboard_text(text)
            return True
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            return False
    
    def create_history_context_menu_handler(self, parent, time_str, content, src_lang, dest_lang, item, refresh_callback, open_in_homepage_callback):
        """Create context menu handler for history entries"""
        def show_context_menu(event):
            menu = tk.Menu(parent, tearoff=0)
            
            # Add to favorites option
            menu.add_command(
                label=self._._("history")["menu"]["add_to_favorites"], 
                command=lambda: (
                    self.add_to_favorites(content, item.get("translated_text", ""), src_lang, dest_lang),
                    print("Added to favorites")
                )
            )
            
            # Copy options
            menu.add_command(
                label=self._._("history")["menu"]["copy_original"], 
                command=lambda: self.copy_text_to_clipboard(content)
            )
            menu.add_command(
                label=self._._("history")["menu"]["copy_translated"], 
                command=lambda: self.copy_text_to_clipboard(item.get("translated_text", ""))
            )
            
            menu.add_separator()
            
            # Delete options
            menu.add_command(
                label=self._._("history")["menu"]["delete"], 
                command=lambda: self.delete_history_entry_by_data(time_str, content, refresh_callback)
            )
            menu.add_command(
                label=self._._("history")["menu"]["delete_all"], 
                command=lambda: self.delete_all_history_entries_with_confirm(parent, refresh_callback)
            )
            
            menu.tk_popup(event.x_root, event.y_root)
        
        return show_context_menu
    
    def create_favorite_context_menu_handler(self, parent, time_str, original_text, refresh_callback):
        """Create context menu handler for favorite entries"""
        def show_context_menu(event):
            menu = tk.Menu(parent, tearoff=0)
            
            # Copy options
            menu.add_command(
                label=self._._("favorite")["menu"]["copy_original"], 
                command=lambda: self.copy_text_to_clipboard(original_text)
            )
            
            menu.add_separator()
            
            # Delete options
            menu.add_command(
                label=self._._("favorite")["menu"]["delete"], 
                command=lambda: self.delete_favorite_entry_by_data(time_str, original_text, refresh_callback)
            )
            menu.add_command(
                label=self._._("favorite")["menu"]["delete_all"], 
                command=lambda: self.delete_all_favorite_entries_with_confirm(parent, refresh_callback)
            )
            
            menu.tk_popup(event.x_root, event.y_root)
        
        return show_context_menu
    
    def create_double_click_handler(self, src_lang, dest_lang, content, open_in_homepage_callback):
        """Create double-click handler for entries"""
        def on_double_click(event):
            open_in_homepage_callback(src_lang, dest_lang, content)
        
        return on_double_click
    
    def create_hover_effect_handlers(self, frame, normal_color="#23272f", hover_color="#181a20"):
        """Create hover effect handlers for frames"""
        def on_enter(event):
            frame.configure(fg_color=hover_color)
        
        def on_leave(event):
            frame.configure(fg_color=normal_color)
        
        return on_enter, on_leave
    
    def group_entries_by_date(self, entries):
        """Group entries by date for display"""
        grouped = []
        last_date = None
        
        for item in entries:
            time_str = item.get("time", "")
            date_str = time_str.split(" ")[0] if time_str else ""
            
            show_date = False
            if date_str != last_date:
                show_date = True
                last_date = date_str
            
            grouped.append({
                'item': item,
                'date_str': date_str,
                'show_date': show_date
            })
        
        return grouped
    
    # === SYSTEM INTEGRATION ===
    
    def run_tray_and_system_integration(self):
        """Initialize tray icon and system integration"""
        from VezylTranslatorNeutron.tray_service import run_tray_icon_in_thread
        from VezylTranslatorElectron.helpers import get_windows_theme
        from VezylTranslatorNeutron.clipboard_service import toggle_clipboard_watcher as unified_toggle_clipboard_watcher
        
        def safe_show_homepage():
            """Safely show homepage with main window recreation if needed"""
            if self.main_window is not None:
                try:
                    # Reset shutdown flag if exists
                    if hasattr(self.main_window, '_shutting_down'):
                        self.main_window._shutting_down = False
                    
                    self.main_window.deiconify()
                    self.main_window.lift()
                    self.main_window.focus_force()
                    self.main_window.show_tab("Trang chủ")
                    print("Main window restored successfully")
                except Exception as e:
                    print(f"Error showing main window: {e}")
                    try:
                        # If main window is corrupted, try to recreate it
                        self.main_window.destroy()
                        self.main_window = None
                        print("Destroyed corrupted main window")
                        
                        # Recreate main window
                        self.initialize_main_window()
                        self.main_window.show_tab("Trang chủ")
                        print("Recreated main window successfully")
                    except Exception as e2:
                        print(f"Failed to recreate main window: {e2}")
                        # Fallback: create a simple message window
                        self._create_fallback_window()
            else:
                try:
                    self.initialize_main_window()
                    self.main_window.show_tab("Trang chủ")
                except Exception as e:
                    print(f"Error creating main window: {e}")
                    self._create_fallback_window()
        
        def safe_toggle_clipboard():
            """Safely toggle clipboard watcher"""
            unified_toggle_clipboard_watcher()
        
        def safe_exit_application():
            """Safely exit the application"""
            self.cleanup()
            os._exit(0)
        
        # Get theme for icon selection
        theme = get_windows_theme()
        icon_path = constant.LOGO_BLACK_FILE if theme == "light" else constant.LOGO_FILE
        
        # Menu items for tray
        menu_items = [
            ("Hiện trang chủ", safe_show_homepage),
            ("Bật/Tắt clipboard", safe_toggle_clipboard),
            ("---", None),
            ("Thoát", safe_exit_application)
        ]
        
        # Start tray icon in separate thread
        run_tray_icon_in_thread(
            icon_path=icon_path,
            tooltip="Vezyl Translator",
            menu_items=menu_items
        )
        print("System tray integration started")
    
    def _create_fallback_window(self):
        """Create a fallback error window"""
        try:
            fallback = ctk.CTkToplevel()
            fallback.title("Vezyl Translator - Lỗi")
            fallback.geometry("400x200")
            
            label = ctk.CTkLabel(
                fallback, 
                text="Có lỗi xảy ra với cửa sổ chính.\nVui lòng khởi động lại ứng dụng.",
                justify="center"
            )
            label.pack(expand=True)
            
            button = ctk.CTkButton(
                fallback, 
                text="Thoát", 
                command=lambda: os._exit(0)
            )
            button.pack(pady=10)
            
            fallback.lift()
            fallback.focus_force()
            
        except Exception as e:
            print(f"Failed to create fallback window: {e}")
    
    # === APPLICATION LIFECYCLE ===
    
    def run(self):
        """Run the application"""
        print(f"{constant.SOFTWARE_NAME}. version {constant.SOFTWARE_VERSION} - Copyright © 2025 by Vezyl")
        
        # Setup crash handler
        CrashHandler.setup_crash_handler()
        
        # Initialize translator engine
        try:
            from VezylTranslatorProton.translator import get_translation_engine
            self.translator = get_translation_engine()
            print("Translation engine initialized")
        except Exception as e:
            print(f"Error initializing translator: {e}")
            return False
        
        # Apply optimizations
        try:
            from VezylTranslatorElectron.helpers import optimize_startup, finish_startup
            optimize_startup()
            fast_startup_enabled = True
            print("[FastStartup] Fast startup mode activated")
        except ImportError:
            print("Startup optimizer not available")
            fast_startup_enabled = False
        except Exception as e:
            print(f"Startup optimizer error: {e}")
            fast_startup_enabled = False
        
        # Apply performance optimizations
        try:
            from VezylTranslatorElectron.helpers import apply_performance_optimizations
            apply_performance_optimizations()
        except ImportError:
            print("Performance patches not available")
        except Exception as e:
            print(f"Failed to apply performance optimizations: {e}")
        
        # Initialize GUI
        gui_start = time.time()
        self.initialize_main_window()
        gui_time = time.time() - gui_start
        
        total_time = time.time() - gui_start
        print(f"GUI initialized: {gui_time:.3f}s")
        print(f"Total startup time: {total_time:.3f}s")
        
        # Start system integration
        self.run_tray_and_system_integration()
        
        # Start services
        try:
            from VezylTranslatorNeutron.clipboard_service import run_clipboard_watcher_in_thread
            from VezylTranslatorNeutron.hotkey_service import run_global_hotkeys_in_thread
            
            run_clipboard_watcher_in_thread()
            run_global_hotkeys_in_thread()
            
        except Exception as e:
            print(f"Error starting services: {e}")
        
        # Finish startup optimization
        if fast_startup_enabled:
            try:
                if self.main_window:
                    self.main_window.after(2000, lambda: finish_startup())
                else:
                    self.main_window.after(3000, lambda: finish_startup())
            except Exception as e:
                print(f"Error in finish startup: {e}")
        
        # Check startup mode
        startup_mode = any('--startup-dir' in arg for arg in sys.argv if isinstance(arg, str))
        
        if startup_mode:
            print("Starting in background mode (system startup)")
            if self.main_window:
                self.main_window.withdraw()
        else:
            print("Starting in normal mode")
            if self.main_window:
                self.main_window.show_tab("Trang chủ")
        
        # Start main loop
        try:
            if self.main_window:
                self.main_window.mainloop()
        except Exception as e:
            print(f"Error in main loop: {e}")
            return False
        
        return True
    
    def on_close(self, window):
        """Cleanup resources when closing window"""
        try:
            self._shutting_down = True
            self.cleanup_mousewheel_handlers()
            
            # Cancel all pending translations
            for future in list(self.pending_translations.values()):
                try:
                    future.cancel()
                except:
                    pass
            self.pending_translations.clear()
            
            # Shutdown ThreadPool
            if hasattr(self, 'translation_executor') and not self.translation_executor._shutdown:
                self.translation_executor.shutdown(wait=False)
            
            # Check if Ctrl is pressed when closing to exit completely
            if getattr(self.translator, 'enable_ctrl_tracking', True) and self.ctrl_pressed:
                window.destroy()
                os._exit(0)
            else:
                window.withdraw()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            window.withdraw()
    
    def cleanup(self):
        """Cleanup all application resources"""
        try:
            self._shutting_down = True
            
            # Cleanup controllers
            self.cleanup_mousewheel_handlers()
            
            # Cancel all pending translations
            for future in list(self.pending_translations.values()):
                try:
                    future.cancel()
                except:
                    pass
            self.pending_translations.clear()
            
            # Shutdown ThreadPool
            if hasattr(self, 'translation_executor') and not self.translation_executor._shutdown:
                self.translation_executor.shutdown(wait=False)
            
            # Cleanup translation controller
            if self.auto_save_state.get("timer_id"):
                try:
                    self.auto_save_state["timer_id"] = None
                except:
                    pass
            self.auto_save_state = {"saved": False, "timer_id": None, "last_content": ""}
            
            print("ApplicationCore cleanup completed")
            
        except Exception as e:
            print(f"Error during ApplicationCore cleanup: {e}")


# === MAIN FUNCTION ===

def main():
    """Main entry point"""
    app = ApplicationCore()
    return app.run()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
