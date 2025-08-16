"""
Unified Main Window Module for VezylTranslator
Consolidated from gui.py, gui_optimized.py, gui_backup.py
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import os
import tkinter as tk
import customtkinter as ctk
from VezylTranslatorNeutron import constant

# Import backend controllers
# (Controllers have been merged into this file)

# Import consolidated UI modules
from VezylTranslatorElectron.events import UIEvents
from VezylTranslatorElectron.components import UIComponents
from VezylTranslatorNeutron.helpers import get_windows_theme

# Additional imports for GUIController
import threading
from concurrent.futures import ThreadPoolExecutor


# === GUI Controller (merged from VezylTranslatorProton/gui_controller.py) ===
class GUIController:
    """GUI Controller - Handles main GUI logic and coordinates between UI and backend modules"""
    
    def __init__(self, translator, language_interface, theme_interface, _):
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
        
        # Translation executor for async operations
        self.translation_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="gui_translate")
        self.pending_translations = {}
        
        # UI state management
        self._shutting_down = False
        self.ctrl_pressed = False
        self.active_mousewheel_handlers = []
        
        # Window state
        self.is_fullscreen = False
        self.width = 900
        self.height = 600
        
    def get_window_config(self):
        """Get window configuration"""
        return {
            'title': f"{constant.SOFTWARE} {constant.SOFTWARE_VERSION}",
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
    
    def destroy_cleanup(self):
        """Cleanup for window destruction"""
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
            
            # Shutdown ThreadPool if still running
            if hasattr(self, 'translation_executor') and not self.translation_executor._shutdown:
                self.translation_executor.shutdown(wait=False)
                
        except Exception as e:
            print(f"Error during destroy cleanup: {e}")


# === Settings Controller (merged from VezylTranslatorProton/settings_controller.py) ===
class SettingsController:
    """Settings Controller - Handles settings management and configuration logic"""
    
    def __init__(self, translator, language_interface, theme_interface, _):
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
    
    def get_config_groups(self):
        """Get configuration groups and fields"""
        lang_display = self.translator.lang_display
        lang_codes = list(lang_display.keys())
        
        return [
            (self._("settings")["general"]["title"], [
                ("start_at_startup", self._("settings")["general"]["start_at_startup"], bool),
                ("show_homepage_at_startup", self._("settings")["general"]["show_homepage_at_startup"], bool),
                ("always_show_transtale", self._("settings")["general"]["always_show_translate"], bool),
                ("enable_ctrl_tracking", self._("settings")["general"]["enable_ctrl_tracking"], bool),
                ("enable_hotkeys", self._("settings")["general"]["enable_hotkeys"], bool),
                ("hotkey", self._("settings")["general"]["hotkey"], "hotkey"),
                ("clipboard_hotkey", self._("settings")["general"]["clipboard_hotkey"], "hotkey"),
            ]),
            (self._("settings")["history"]["title"], [
                ("save_translate_history", self._("settings")["history"]["save_translate_history"], bool),
                ("max_history_items", self._("settings")["history"]["max_history_items"], int),
            ]),
            (self._("settings")["popup_and_icon"]["title"], [
                ("icon_size", self._("settings")["popup_and_icon"]["icon_size"], int),
                ("icon_dissapear_after", self._("settings")["popup_and_icon"]["icon_dissapear_after"], int),
                ("popup_dissapear_after", self._("settings")["popup_and_icon"]["popup_dissapear_after"], int),
                ("max_length_on_popup", self._("settings")["popup_and_icon"]["max_length_on_popup"], int),
            ]),
            (self._("settings")["language"]["title"], [
                ("dest_lang", self._("settings")["language"]["dest_lang"], "combo"),
                ("font", self._("settings")["language"]["font"], str),
            ]),
            (self._("settings")["translation"]["title"], [
                ("translation_model", self._("settings")["translation"]["translation_model"], "translation_model"),
            ])
        ]
    
    def get_translation_models(self):
        """Get available translation models"""
        try:
            from VezylTranslatorProton.translator import get_translation_engine
            engine = get_translation_engine()
            return engine.get_available_models()
        except Exception:
            # Fallback to static list
            return {
                "google": "🌐 Google Translator",
                "bing": "🔍 Bing Translator", 
                "deepl": "🔬 DeepL Translator",
                "marian": "🤖 Marian MT (Local)",
                "opus": "📚 OPUS-MT (Local)"
            }
    
    def get_marian_supported_languages(self):
        """Get Marian supported languages"""
        try:
            from VezylTranslatorProton.translator import get_translation_engine
            engine = get_translation_engine()
            supported = engine.get_supported_languages("marian")
            lang_pairs = list(supported.values())
            return f"🌐 Hỗ trợ: {', '.join(lang_pairs)}"
        except Exception:
            return "🌐 Hỗ trợ: Đang tải..."
    
    def create_hotkey_click_handler(self, entry_widget):
        """Create hotkey click handler for hotkey entry fields"""
        def on_hotkey_click(event):
            entry_widget.configure(state="normal")
            entry_widget.delete(0, "end")
            entry_widget.insert(0, "Press keys...")
            entry_widget.focus_set()
            
            pressed_keys = set()
            
            def on_key_press(e):
                k = e.keysym.lower()
                pressed_keys.add(k)
                
                # Build hotkey string
                keys = []
                for mod in ["control", "ctrl", "shift", "alt", "win", "meta"]:
                    if mod in pressed_keys:
                        keys.append(mod)
                
                # Add main key (non-modifier)
                for k2 in pressed_keys:
                    if k2 not in ["control", "ctrl", "shift", "alt", "win", "meta"]:
                        keys.append(k2)
                
                # Map to standard keyboard format
                mapping = {
                    "control_l": "ctrl", "control_r": "ctrl",
                    "ctrl_l": "ctrl", "ctrl_r": "ctrl",
                    "alt_l": "alt", "alt_r": "alt",
                    "shift_l": "shift", "shift_r": "shift",
                    "win_l": "windows", "win_r": "windows",
                    "meta_l": "windows", "meta_r": "windows"
                }
                
                keys_mapped = []
                for key in keys:
                    key_lower = key.lower()
                    keys_mapped.append(mapping.get(key_lower, key_lower))
                
                # Remove duplicates while preserving order
                seen = set()
                result = []
                for x in keys_mapped:
                    if x not in seen:
                        seen.add(x)
                        result.append(x)
                
                hotkey_str = "+".join([k.upper() if len(k) == 1 else k for k in result])
                entry_widget.delete(0, "end")
                entry_widget.insert(0, hotkey_str)
            
            def on_key_release(e):
                k = e.keysym.lower()
                if k in pressed_keys:
                    pressed_keys.remove(k)
                
                # When all keys released, save and stop listening
                if not pressed_keys:
                    entry_widget.configure(state="readonly")
                    entry_widget.unbind("<KeyPress>")
                    entry_widget.unbind("<KeyRelease>")
            
            entry_widget.bind("<KeyPress>", on_key_press)
            entry_widget.bind("<KeyRelease>", on_key_release)
        
        return on_hotkey_click
    
    def save_config_from_entries(self, entries, setup_ctrl_tracking_callback, update_hotkey_system_callback):
        """Save configuration from UI entries using new config manager"""
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except ImportError:
            pass  # winsound not available on non-Windows
        
        # Store old hotkey values for comparison
        old_homepage_hotkey = self.translator.hotkey
        old_clipboard_hotkey = self.translator.clipboard_hotkey
        
        lang_display = self.translator.lang_display
        translation_models = self.get_translation_models()
        
        # Process each entry and update translator instance
        for key, (entry, typ) in entries.items():
            if typ is bool:
                val = entry.var.get()
            elif typ is int:
                try:
                    val = int(entry.get())
                except Exception:
                    val = 0
            elif typ == "combo" and key == "dest_lang":
                display_val = entry.var.get()
                val = next((k for k, v in lang_display.items() if v == display_val), self.translator.dest_lang)
            elif typ == "translation_model":
                display_val = entry.var.get()
                val = next((k for k, v in translation_models.items() if v == display_val), "google")
            elif key == "font":
                val = entry.var.get()
            else:
                val = entry.get()
            
            # Update translator instance attribute
            setattr(self.translator, key, val)
        
        # Save configuration using new config manager
        save_success = self.translator.save_config()
        
        if save_success:
            # Update system settings
            if hasattr(self.translator, 'set_startup'):
                from VezylTranslatorProton.app import StartupManager
                StartupManager.set_startup(self.translator.start_at_startup)
            setup_ctrl_tracking_callback()
            update_hotkey_system_callback(old_homepage_hotkey, old_clipboard_hotkey)
        
        return save_success
    
    def update_hotkey_system(self, old_homepage_hotkey, old_clipboard_hotkey):
        """Update hotkey system based on config changes"""
        try:
            from VezylTranslatorNeutron.hotkey_service import register_hotkey, unregister_hotkey
            
            # Always unregister existing hotkeys first
            unregister_hotkey("homepage")
            unregister_hotkey("clipboard")
            
            # If hotkeys are enabled, register them
            if hasattr(self.translator, 'enable_hotkeys') and self.translator.enable_hotkeys:
                # Register homepage hotkey
                register_hotkey(
                    "homepage",
                    self.translator.hotkey,
                    lambda: self._show_and_fill_homepage()
                )
                
                # Register clipboard toggle hotkey
                register_hotkey(
                    "clipboard", 
                    self.translator.clipboard_hotkey,
                    lambda: self._toggle_clipboard_watcher()
                )
                
                print("Hotkeys enabled")
            else:
                print("Hotkeys disabled")
                
        except Exception as e:
            print(f"Error updating hotkey system: {e}")
    
    def _show_and_fill_homepage(self):
        """Callback for homepage hotkey - to be set by GUI"""
        if hasattr(self, 'show_homepage_callback'):
            self.show_homepage_callback()
    
    def _toggle_clipboard_watcher(self):
        """Callback for clipboard hotkey"""
        try:
            from VezylTranslatorNeutron.clipboard_service import toggle_clipboard_watcher
            toggle_clipboard_watcher(self.translator)
        except Exception as e:
            print(f"Error toggling clipboard watcher: {e}")
    
    def set_show_homepage_callback(self, callback):
        """Set callback for showing homepage"""
        self.show_homepage_callback = callback
    
    def get_copyright_text(self):
        """Get copyright text for footer"""
        return f"{constant.SOFTWARE}. version {constant.SOFTWARE_VERSION} - Copyright © 2025 by Vezyl"
    
    def cleanup(self):
        """Cleanup settings controller resources"""
        # Clear callback reference
        self.show_homepage_callback = None


# === Tab Controller (merged from VezylTranslatorProton/tab_controller.py) ===
class TabController:
    """Tab Controller - Handles logic for different tabs (History, Favorites, etc.)"""
    
    def __init__(self, translator, language_interface, theme_interface, _):
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
    
    def get_history_data(self, search_keyword="", max_items=30):
        """Get filtered and limited history data"""
        from VezylTranslatorNeutron.helpers import search_entries
        from VezylTranslatorProton.storage import read_history_entries
        
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
        from VezylTranslatorNeutron.helpers import search_entries
        from VezylTranslatorProton.storage import read_favorite_entries
        
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
            from VezylTranslatorProton.storage import delete_history_entry
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
        from VezylTranslatorNeutron.helpers import ensure_local_dir, show_confirm_popup
        from VezylTranslatorProton.storage import delete_all_history_entries
        
        show_confirm_popup(
            parent=parent,
            title=self._("confirm_popup")["title"],
            message=self._("history")["menu"]["delete_confirm"],
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
            from VezylTranslatorProton.storage import delete_favorite_entry
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
        from VezylTranslatorNeutron.helpers import ensure_local_dir, show_confirm_popup
        from VezylTranslatorProton.storage import delete_all_favorite_entries
        
        show_confirm_popup(
            parent=parent,
            title=self._("confirm_popup")["title"],
            message=self._("favorite")["menu"]["delete_confirm"],
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
            from VezylTranslatorProton.storage import update_favorite_note
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
            from VezylTranslatorNeutron.helpers import ensure_local_dir
            from VezylTranslatorProton.storage import write_favorite_entry
            
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
            from VezylTranslatorNeutron.clipboard_service import set_clipboard_text
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
                label=self._("history")["menu"]["add_to_favorite"], 
                command=lambda: (
                    self.add_to_favorites(content, item.get("translated_text", ""), src_lang, dest_lang),
                    print("Added to favorites")
                )
            )
            
            # Copy options
            menu.add_command(
                label="Copy original text", 
                command=lambda: self.copy_text_to_clipboard(content)
            )
            menu.add_command(
                label="Copy translated text", 
                command=lambda: self.copy_text_to_clipboard(item.get("translated_text", ""))
            )
            
            menu.add_separator()
            
            # Delete options
            menu.add_command(
                label=self._("history")["menu"]["delete"], 
                command=lambda: self.delete_history_entry_by_data(time_str, content, refresh_callback)
            )
            menu.add_command(
                label=self._("history")["menu"]["delete_all"], 
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
                label="Copy original text", 
                command=lambda: self.copy_text_to_clipboard(original_text)
            )
            
            menu.add_separator()
            
            # Delete options
            menu.add_command(
                label=self._("favorite")["menu"]["delete"], 
                command=lambda: self.delete_favorite_entry_by_data(time_str, original_text, refresh_callback)
            )
            menu.add_command(
                label=self._("favorite")["menu"]["delete_all"], 
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
    
    def cleanup(self):
        """Cleanup tab controller resources"""
        # Clear any cached data or references
        pass


# === Translation Controller (merged from VezylTranslatorProton/translation_controller.py) ===
class TranslationController:
    """Translation Controller - Handles translation logic and auto-save functionality"""
    
    def __init__(self, translator, language_interface, theme_interface, _):
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
        
        # Auto-save state management
        self.auto_save_state = {"saved": False, "timer_id": None, "last_content": ""}
    
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
                from VezylTranslatorProton.translator import get_translation_engine
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
                            from VezylTranslatorNeutron.helpers import ensure_local_dir
                            from VezylTranslatorProton.storage import write_log_entry
                            
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
                if src_lang_display == self._("home")["auto_detect"]:
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
    
    def cleanup(self):
        """Cleanup translation controller resources"""
        # Cancel any pending auto-save timer
        if self.auto_save_state.get("timer_id"):
            try:
                # Note: Cannot cancel after destruction, but we can clear the reference
                self.auto_save_state["timer_id"] = None
            except:
                pass
        
        # Clear auto-save state
        self.auto_save_state = {"saved": False, "timer_id": None, "last_content": ""}


class MainWindow(ctk.CTkToplevel):
    """Main window class for VezylTranslator desktop application"""
    
    def __init__(self, translator, language_interface, theme_interface, _):
        super().__init__()
        
        # Store references
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
        
        # Window state
        self.is_fullscreen = False
        self.ctrl_pressed = False
        
        # Initialize controllers
        self.gui_controller = GUIController(translator, language_interface, theme_interface, _)
        self.translation_controller = TranslationController(translator, language_interface, theme_interface, _)
        self.tab_controller = TabController(translator, language_interface, theme_interface, _)
        self.settings_controller = SettingsController(translator, language_interface, theme_interface, _)
        self.ui_events = UIEvents(translator, language_interface, theme_interface, _)
        
        # Initialize UI components helper
        self.ui_components = UIComponents(translator, "dark")
        
        # Set up window
        self._setup_window()
        
        # Build UI
        self._build_navigation()
        self._setup_content_area()
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Set initial active tab state
        self._update_active_tab("Trang chủ")
        
        # Initialize with home tab
        self.show_tab("Trang chủ")
    
    def _setup_window(self):
        """Setup window configuration"""
        ctk.set_appearance_mode("dark")
        
        config = self.gui_controller.get_window_config()
        self.title(config['title'])
        self.geometry(f"{config['width']}x{config['height']}")
        self.resizable(config['resizable'], config['resizable'])
        
        # Set icon with delay
        try:
            self.after(200, lambda: self.wm_iconbitmap(config['icon_path']))
        except:
            print("Cannot load icon")
        
        # Configure tabs
        self.tabs = {
            "Trang chủ": self.show_tab_home,
            "Lịch sử": self.show_tab_history,
            "Yêu thích": self.show_tab_favorite,
            "Cài đặt": self.show_tab_settings
        }
    
    def _build_navigation(self):
        """Build navigation bar"""
        self.nav_buttons = {}
        self.nav_bar = self.ui_components.create_navigation_bar(self, self.nav_buttons)
        
        # Bind navigation events
        for tab_name, button in self.nav_buttons.items():
            handler = self.ui_events.create_tab_button_handler(
                tab_name, self.show_tab
            )
            button.configure(command=handler)
    
    def _setup_content_area(self):
        """Setup content area"""
        self.content_frame = ctk.CTkFrame(self, fg_color="#2d323e")
        self.content_frame.pack(side="left", fill="both", expand=True)
    
    def _setup_event_handlers(self):
        """Setup window-level event handlers"""
        # Window protocol handlers
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Keyboard shortcuts
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
        self.bind("<KeyPress-Control_L>", self._ctrl_down)
        self.bind("<KeyRelease-Control_L>", self._ctrl_up)
        self.bind("<KeyPress-Control_R>", self._ctrl_down)
        self.bind("<KeyRelease-Control_R>", self._ctrl_up)
        
        # Focus management
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)
        
        # Set callback for settings controller
        self.settings_controller.set_show_homepage_callback(self.show_and_fill_homepage)
    
    def show_tab(self, tab_name):
        """Show specified tab"""
        if tab_name in self.tabs:
            self._update_active_tab(tab_name)
            self.tabs[tab_name]()
    
    def _update_active_tab(self, active_tab_name):
        """Update visual state of navigation buttons"""
        for tab_name, button in self.nav_buttons.items():
            if tab_name == active_tab_name:
                button.configure(fg_color="#404040")
            else:
                button.configure(fg_color="transparent")
    
    def _safe_clear_content_frame(self):
        """Safely clear content frame"""
        try:
            for widget in self.content_frame.winfo_children():
                widget.destroy()
        except tk.TclError:
            pass
    
    def show_tab_home(self):
        """Show home/translation tab"""
        # Safe widget cleanup
        self._safe_clear_content_frame()
        
        # Create main frame
        frame = self.ui_components.create_tab_frame(self.content_frame)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        lang_display = self.translator.lang_display
        lang_codes = list(lang_display.keys())
        
        # Source language combo
        src_lang_var = tk.StringVar(value="auto")
        src_lang_combo = self.ui_components.create_language_combo(
            frame, 
            [self._("home")["auto_detect"]] + [lang_display[code] for code in lang_codes],
            src_lang_var
        )
        src_lang_combo.grid(row=0, column=0, sticky="w", pady=(0, 5))
        src_lang_combo.set(self._("home")["auto_detect"])
        
        # Source text frame with copy button
        src_text_frame, src_text, copy_src_btn = self.ui_components.create_text_frame_with_copy_button(
            frame, "#23272f", "#f5f5f5"
        )
        src_text_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 10))
        
        # Set copy button command
        copy_src_btn.configure(
            command=lambda: self.tab_controller.copy_text_to_clipboard(
                src_text.get("1.0", "end").strip()
            )
        )
        
        # Reverse translation button
        reverse_button = self.ui_components.create_icon_button(
            frame, "reverse.png", (24, 24)
        )
        reverse_button.grid(row=1, column=0, sticky="se", padx=(0, 0), pady=(0, 10))
        
        # Destination frame
        dest_frame = ctk.CTkFrame(frame, fg_color="#181a20")
        dest_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, 0))
        dest_frame.grid_rowconfigure(0, weight=0)
        dest_frame.grid_rowconfigure(1, weight=1)
        dest_frame.grid_columnconfigure(0, weight=1)
        
        # Destination language combo
        dest_lang_var = tk.StringVar(value=lang_display.get(self.translator.dest_lang, "🇻🇳 Tiếng Việt"))
        dest_lang_combo = self.ui_components.create_language_combo(
            dest_frame,
            [lang_display[code] for code in lang_codes],
            dest_lang_var
        )
        dest_lang_combo.grid(row=0, column=0, sticky="w", padx=(0, 0), pady=(0, 0))
        
        # Destination text frame with copy button
        dest_text_frame, dest_text, copy_dest_btn = self.ui_components.create_text_frame_with_copy_button(
            dest_frame, "#181a20", "#00ff99", state="disabled"
        )
        dest_text_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))
        
        # Set copy destination button command
        copy_dest_btn.configure(
            command=lambda: self.tab_controller.copy_text_to_clipboard(
                dest_text.get("1.0", "end").strip()
            )
        )
        
        # Favorite button
        favorite_button = self.ui_components.create_icon_button(
            dest_frame, "favorite.png", (24, 24)
        )
        favorite_button.grid(row=1, column=0, sticky="se", padx=(0, 0), pady=(5, 0))
        
        # Configure favorite button command
        favorite_button.configure(
            command=lambda: self.tab_controller.add_to_favorites(
                src_text.get("1.0", "end").strip(),
                dest_text.get("1.0", "end").strip(),
                self.translator.src_lang,
                self.translator.dest_lang
            )
        )
        
        # Setup translation logic
        self._setup_translation_logic(
            src_text, dest_text, src_lang_var, dest_lang_var,
            src_lang_combo, dest_lang_combo, lang_display
        )
        
        # Setup reverse translation
        reverse_function = self.translation_controller.create_reverse_translation_function(
            src_text, dest_text, src_lang_combo, dest_lang_combo, lang_display
        )
        reverse_button.configure(command=reverse_function)
        
        # Fill last translated text if available
        self.translation_controller.fill_last_translated_text(src_text)
        
        # Setup auto-save
        self.translation_controller.setup_auto_save(src_text)
    
    def _setup_translation_logic(self, src_text, dest_text, src_lang_var, dest_lang_var, 
                                src_lang_combo, dest_lang_combo, lang_display):
        """Setup translation event handlers"""
        def on_text_change(event=None):
            if getattr(self.gui_controller, '_shutting_down', False):
                return
                
            text = src_text.get("1.0", "end").strip()
            
            # Get language codes
            src_lang = self.translation_controller.get_language_from_display(
                src_lang_var.get(), lang_display, self._("home")["auto_detect"]
            )
            dest_lang = self.translation_controller.get_language_from_display(
                dest_lang_var.get(), lang_display, ""
            )
            
            # Create and execute translation
            translate_function = self.translation_controller.create_translation_function(
                text, src_lang, dest_lang, dest_text, 
                src_lang_combo, lang_display
            )
            
            widget_id = f"home_translate_{id(src_text)}"
            future = self.gui_controller.translate_async(widget_id, translate_function)
            
            if future is None:
                print("Translation not executed - system unavailable")
        
        # Create debounced handler
        debounced_handler = self.translation_controller.create_debounced_text_change_handler(
            src_text, on_text_change, 300
        )
        
        # Bind events
        src_text.bind("<<Modified>>", lambda e: (src_text.edit_modified(0), debounced_handler()))
        src_text.bind("<KeyRelease>", lambda e: debounced_handler())
        
        # Bind combo changes
        src_lang_combo.configure(command=lambda _: on_text_change())
        dest_lang_combo.configure(command=lambda _: on_text_change())
    
    def show_tab_history(self):
        """Show history tab"""
        # Safe widget cleanup
        self._safe_clear_content_frame()
        
        # Create title and search
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(side="top", fill="x", padx=60, pady=(20, 0))

        title = ctk.CTkLabel(title_frame, 
                             text=self._("history")["title"], 
                             font=(self.translator.font, 20, "bold"), text_color="#00ff99")
        title.pack(side="left", anchor="w")

        # Search entry
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="🔍 Tìm kiếm...",
            textvariable=search_var,
            width=260,
            font=(self.translator.font, 14)
        )
        search_entry.pack(side="right", padx=(0, 0), pady=0)
        
        # Create scrollable content
        scrollable_frame, canvas, scrollbar, history_frame, window_id = self.ui_components.create_scrollable_frame(
            self.content_frame
        )
        scrollable_frame.pack(fill="both", expand=True, padx=60, pady=(10, 60))
        
        # Setup scrolling and resizing
        resize_handler = self.ui_events.create_canvas_resize_handler(canvas, window_id)
        canvas.bind("<Configure>", resize_handler)
        
        configure_handler = self.ui_events.create_scrollregion_update_handler(canvas)
        history_frame.bind("<Configure>", configure_handler)
        
        # Setup mousewheel
        mousewheel_handler = self.gui_controller.safe_mousewheel_handler(canvas)
        self.gui_controller.add_mousewheel_handler(canvas, mousewheel_handler)
        
        # Render function
        def render_history_list():
            self._render_history_entries(history_frame, search_var.get())
        
        # Setup search handler
        self.ui_events.create_search_handler(search_var, render_history_list)
        
        # Initial render
        render_history_list()
    
    def show_tab_favorite(self):
        """Show favorites tab"""
        # Safe widget cleanup
        self._safe_clear_content_frame()
        
        # Create title and search
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(side="top", fill="x", padx=60, pady=(20, 0))

        title = ctk.CTkLabel(title_frame, 
                             text=self._("favorite")["title"], 
                             font=(self.translator.font, 20, "bold"), 
                             text_color="#00ff99")
        title.pack(side="left", anchor="w")

        # Search entry
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="🔍 Tìm kiếm...",
            textvariable=search_var,
            width=260,
            font=(self.translator.font, 14)
        )
        search_entry.pack(side="right", padx=(0, 0), pady=0)
        
        # Create scrollable content
        scrollable_frame, canvas, scrollbar, favorite_frame, window_id = self.ui_components.create_scrollable_frame(
            self.content_frame
        )
        scrollable_frame.pack(fill="both", expand=True, padx=60, pady=(10, 60))
        
        # Setup scrolling and resizing
        resize_handler = self.ui_events.create_canvas_resize_handler(canvas, window_id)
        canvas.bind("<Configure>", resize_handler)
        
        configure_handler = self.ui_events.create_scrollregion_update_handler(canvas)
        favorite_frame.bind("<Configure>", configure_handler)
        
        # Setup mousewheel
        mousewheel_handler = self.gui_controller.safe_mousewheel_handler(canvas)
        self.gui_controller.add_mousewheel_handler(canvas, mousewheel_handler)
        
        # Render function
        def render_favorite_list():
            self._render_favorite_entries(favorite_frame, search_var.get())
        
        # Setup search handler
        self.ui_events.create_search_handler(search_var, render_favorite_list)
        
        # Initial render
        render_favorite_list()
    
    def _render_history_entries(self, parent, search_keyword=""):
        """Render history entries"""
        # Clear existing widgets
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get data
        entries = self.tab_controller.get_history_data(search_keyword)
        
        if not entries:
            empty_label = self.ui_components.create_content_label(
                parent, self._("history")["empty"]
            )
            empty_label.grid(row=1, column=0, columnspan=2, pady=20)
            return
        
        parent.grid_columnconfigure(1, weight=1)
        grouped_entries = self.tab_controller.group_entries_by_date(entries)
        
        row_idx = 1
        for entry_data in grouped_entries:
            item = entry_data['item']
            date_str = entry_data['date_str']
            show_date = entry_data['show_date']
            
            # Show date if needed
            if show_date:
                date_label = self.ui_components.create_date_label(parent, date_str)
                date_label.grid(row=row_idx, column=0, sticky="nw", padx=(0, 16), pady=(8, 0))
                row_idx += 1
            
            # Create entry card
            entry_frame = self.ui_components.create_entry_card(parent)
            entry_frame.grid(row=row_idx, column=1, sticky="ew", pady=6, padx=0)
            
            # Add content
            self._add_history_entry_content(entry_frame, item)
            
            row_idx += 1
    
    def _add_history_entry_content(self, entry_frame, item):
        """Add content to history entry frame"""
        time_str = item.get("time", "")
        content = item.get("last_translated_text", "")
        src_lang = item.get("src_lang", "")
        dest_lang = item.get("dest_lang", "")
        
        # Info label
        info_label = self.ui_components.create_info_label(
            entry_frame, f"{time_str[11:]} | {src_lang}"
        )
        info_label.grid(row=0, column=0, sticky="w", padx=10, pady=(4, 0))
        
        # Content label
        content_label = self.ui_components.create_content_label(entry_frame, content)
        content_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 8))
        
        # Setup events
        double_click_handler = self.tab_controller.create_double_click_handler(
            src_lang, dest_lang, content, self.open_entry_in_homepage
        )
        
        context_menu_handler = self.tab_controller.create_history_context_menu_handler(
            self, time_str, content, src_lang, dest_lang, item, 
            lambda: self.show_tab("Lịch sử"), self.open_entry_in_homepage
        )
        
        on_enter, on_leave = self.tab_controller.create_hover_effect_handlers(entry_frame)
        
        # Bind events to all widgets
        widgets = [entry_frame, info_label, content_label]
        for widget in widgets:
            widget.bind("<Double-Button-1>", double_click_handler)
            widget.bind("<Button-3>", context_menu_handler)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
    
    def _render_favorite_entries(self, parent, search_keyword=""):
        """Render favorite entries"""
        # Clear existing widgets
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get data
        entries = self.tab_controller.get_favorite_data(search_keyword)
        
        if not entries:
            empty_label = self.ui_components.create_content_label(
                parent, self._("favorite")["empty"]
            )
            empty_label.grid(row=0, column=0, columnspan=2, pady=20)
            return
        
        parent.grid_columnconfigure(1, weight=1)
        grouped_entries = self.tab_controller.group_entries_by_date(entries)
        
        row_idx = 0
        for entry_data in grouped_entries:
            item = entry_data['item']
            date_str = entry_data['date_str']
            show_date = entry_data['show_date']
            
            # Show date if needed
            if show_date:
                date_label = self.ui_components.create_date_label(parent, date_str)
                date_label.grid(row=row_idx, column=0, sticky="nw", padx=(0, 16), pady=(8, 0))
                row_idx += 1
            
            # Create entry card
            entry_frame = self.ui_components.create_entry_card(parent)
            entry_frame.grid(row=row_idx, column=1, sticky="ew", pady=6, padx=0)
            
            # Add content
            self._add_favorite_entry_content(entry_frame, item)
            
            row_idx += 1
    
    def _add_favorite_entry_content(self, entry_frame, item):
        """Add content to favorite entry frame"""
        time_str = item.get("time", "")
        original_text = item.get("original_text", "")
        translated_text = item.get("translated_text", "")
        src_lang = item.get("src_lang", "")
        dest_lang = item.get("dest_lang", "")
        note = item.get("note", "")
        
        lang_display = self.translator.lang_display
        src_disp = lang_display.get(src_lang, src_lang)
        dest_disp = lang_display.get(dest_lang, dest_lang)
        
        # Info label
        info_label = self.ui_components.create_info_label(
            entry_frame, f"{time_str[11:]} | {src_disp} → {dest_disp}"
        )
        info_label.grid(row=0, column=0, sticky="w", padx=10, pady=(4, 0))
        
        # Original text
        content_label = self.ui_components.create_content_label(entry_frame, original_text)
        content_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 4))
        
        # Translated text
        translated_label = self.ui_components.create_content_label(
            entry_frame, translated_text, "#00ff99", True
        )
        translated_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))
        
        # Note entry
        note_var = tk.StringVar(value=note)
        note_entry = ctk.CTkEntry(
            entry_frame,
            textvariable=note_var,
            font=(self.translator.font, 12, "italic"),
            width=400
        )
        note_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
        
        # Setup events
        double_click_handler = self.tab_controller.create_double_click_handler(
            src_lang, dest_lang, original_text, self.open_entry_in_homepage
        )
        
        context_menu_handler = self.tab_controller.create_favorite_context_menu_handler(
            self, time_str, original_text, lambda: self.show_tab("Yêu thích")
        )
        
        note_save_handler = self.ui_events.create_entry_note_save_handler(
            note_var, time_str, lambda t, n: self.tab_controller.update_favorite_note_by_data(
                t, n, lambda: self.show_tab("Yêu thích")
            )
        )
        
        on_enter, on_leave = self.tab_controller.create_hover_effect_handlers(entry_frame)
        
        # Bind events
        widgets = [entry_frame, info_label, content_label, translated_label]
        for widget in widgets:
            widget.bind("<Double-Button-1>", double_click_handler)
            widget.bind("<Button-3>", context_menu_handler)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        note_entry.bind("<Return>", note_save_handler)
    
    def show_tab_settings(self):
        """Show settings tab with fixed footer for save button"""
        # Safe widget cleanup with error handling
        self._safe_clear_content_frame()
        
        # Create main container with grid layout
        main_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True)
        
        # Configure grid: scrollable area (top) + fixed footer (bottom)
        main_container.grid_rowconfigure(0, weight=1)  # Scrollable area takes remaining space
        main_container.grid_rowconfigure(1, weight=0)  # Footer is fixed height
        main_container.grid_columnconfigure(0, weight=1)
        
        # Create scrollable area
        scrollable_frame = ctk.CTkFrame(main_container, fg_color="#2d323e")
        scrollable_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        canvas = tk.Canvas(scrollable_frame, bg="#2d323e", highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(scrollable_frame, orientation="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Mouse wheel handling
        mousewheel_handler = self.gui_controller.safe_mousewheel_handler(canvas)
        self.gui_controller.add_mousewheel_handler(canvas, mousewheel_handler)

        # Create form frame for settings content
        form_frame = ctk.CTkFrame(canvas, fg_color="#2d323e")
        window_id = canvas.create_window((0, 0), window=form_frame, anchor="nw")

        # Build settings form content (without save button)
        entries = self._build_settings_form_content(form_frame, canvas, window_id)
        
        # Create fixed footer for save button and copyright
        self._create_settings_footer_fixed(main_container, entries)
    
    def _build_settings_form_content(self, parent, canvas, window_id):
        """Build settings form content without save button"""
        lang_display = self.translator.lang_display
        lang_codes = list(lang_display.keys())
        
        # Config groups
        config_groups = [
            (self._("settings")["general"]["title"], [
                ("start_at_startup", self._("settings")["general"]["start_at_startup"], bool),
                ("show_homepage_at_startup", self._("settings")["general"]["show_homepage_at_startup"], bool),
                ("always_show_transtale", self._("settings")["general"]["always_show_translate"], bool),
                ("enable_ctrl_tracking", self._("settings")["general"]["enable_ctrl_tracking"], bool),
                ("enable_hotkeys", self._("settings")["general"]["enable_hotkeys"], bool),
                ("hotkey", self._("settings")["general"]["hotkey"], "hotkey"),
                ("clipboard_hotkey", self._("settings")["general"]["clipboard_hotkey"], "hotkey"),
            ]),
            (self._("settings")["history"]["title"], [
                ("save_translate_history", self._("settings")["history"]["save_translate_history"], bool),
                ("max_history_items", self._("settings")["history"]["max_history_items"], int),
            ]),
            (self._("settings")["popup_and_icon"]["title"], [
                ("icon_size", self._("settings")["popup_and_icon"]["icon_size"], int),
                ("icon_dissapear_after", self._("settings")["popup_and_icon"]["icon_dissapear_after"], int),
                ("popup_dissapear_after", self._("settings")["popup_and_icon"]["popup_dissapear_after"], int),
                ("max_length_on_popup", self._("settings")["popup_and_icon"]["max_length_on_popup"], int),
            ]),
            (self._("settings")["language"]["title"], [
                ("interface_language", self._("settings")["language"]["interface_language"], "combo"),
                ("dest_lang", self._("settings")["language"]["dest_lang"], "combo"),
                ("font", self._("settings")["language"]["font"], "combo"),
            ]),
            (self._("settings")["translation"]["title"], [
                ("translation_model", self._("settings")["translation"]["translation_model"], "translation_model"),
            ]),
        ]

        entries = {}
        row_idx = 0

        for section_title, fields in config_groups:
            # Section header
            header_label = ctk.CTkLabel(
                parent,
                text=section_title,
                font=(self.translator.font, 14, "bold"),
                text_color="#00ff99"
            )
            header_label.grid(row=row_idx, column=0, columnspan=2, padx=18, pady=(20 if row_idx > 0 else 10, 10), sticky="w")
            row_idx += 1

            # Fields in section
            for key, label_text, typ in fields:
                # Label
                label = ctk.CTkLabel(
                    parent,
                    text=label_text,
                    font=(self.translator.font, 12),
                    text_color="#cccccc"
                )
                label.grid(row=row_idx, column=0, padx=18, pady=6, sticky="w")

                # Entry field
                if typ == "translation_model":
                    entry = self._create_translation_model_field(parent, getattr(self.translator, key))
                else:
                    entry = self._create_settings_field(parent, key, typ)
                
                entry.grid(row=row_idx, column=1, padx=10, pady=6, sticky="ew")
                entries[key] = (entry, typ)
                parent.grid_columnconfigure(1, weight=1)
                
                # Handle special cases that need extra rows
                if typ == "translation_model" and hasattr(entry, 'supported_languages_label'):
                    row_idx += 2
                else:
                    row_idx += 1

        # Canvas event handlers
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        parent.bind("<Configure>", on_configure)

        def resize_canvas(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", resize_canvas)

        return entries
    
    def _create_settings_footer_fixed(self, main_container, entries):
        """Create fixed footer with save button and copyright outside scrollable area"""
        footer = ctk.CTkFrame(main_container, fg_color="#2d323e", height=80)
        footer.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        footer.grid_propagate(False)  # Maintain fixed height
        footer.grid_columnconfigure(0, weight=0)
        footer.grid_columnconfigure(1, weight=1)
        
        # Save button
        save_btn = ctk.CTkButton(
            footer,
            text=self._("settings")["general"]["save_settings"],
            command=lambda: self._save_settings(entries),
            font=(self.translator.font, 13, "bold"),
            height=40,
            width=120
        )
        save_btn.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=15)
        
        # Copyright label
        from VezylTranslatorNeutron import constant
        copyright_label = ctk.CTkLabel(
            footer,
            text=f"© 2025 {constant.SOFTWARE} v{constant.SOFTWARE_VERSION} by Vezyl",
            font=(self.translator.font, 10),
            text_color="#888888"
        )
        copyright_label.grid(row=0, column=1, sticky="w", padx=(10, 20), pady=15)
    
    def _create_settings_field(self, parent, key, typ):
        """Create settings field widget"""
        val = getattr(self.translator, key)
        lang_display = self.translator.lang_display
        
        if typ is bool:
            return self.ui_components.create_checkbox_field(parent, val)
        elif typ is int:
            return self.ui_components.create_entry_field(parent, str(val))
        elif typ == "combo" and key == "dest_lang":
            lang_codes = list(lang_display.keys())
            current_display = lang_display.get(val, next(iter(lang_display.values())))
            return self.ui_components.create_combo_field(
                parent, [lang_display[code] for code in lang_codes], current_display
            )
        elif key == "font":
            fonts = getattr(self.translator, "default_fonts", ["JetBrains Mono"])
            return self.ui_components.create_combo_field(parent, fonts, val)
        elif typ == "translation_model":
            return self._create_translation_model_field(parent, val)
        elif typ == "hotkey":
            entry = self.ui_components.create_readonly_entry_field(parent, val)
            click_handler = self.settings_controller.create_hotkey_click_handler(entry)
            entry.bind("<Button-1>", click_handler)
            return entry
        else:
            return self.ui_components.create_entry_field(parent, str(val))
    
    def _create_translation_model_field(self, parent, current_value):
        """Create translation model field with language support info"""
        translation_models = self.settings_controller.get_translation_models()
        current_display = translation_models.get(current_value, "🌐 Google Translator")
        
        entry = self.ui_components.create_combo_field(
            parent, list(translation_models.values()), current_display
        )
        
        # Create supported languages label
        supported_languages_label = self.ui_components.create_info_label(parent, "")
        
        def update_supported_languages(*args):
            selected_model = entry.var.get()
            if "Marian MT" in selected_model:
                languages_text = self.settings_controller.get_marian_supported_languages()
                supported_languages_label.configure(text=languages_text)
                supported_languages_label.grid(row=99, column=0, columnspan=2, sticky="w", padx=18, pady=(2, 6))
            else:
                supported_languages_label.configure(text="")
                supported_languages_label.grid_remove()
        
        entry.var.trace("w", update_supported_languages)
        update_supported_languages()
        entry.supported_languages_label = supported_languages_label
        
        return entry
    
    def _save_settings(self, entries):
        """Save settings configuration"""
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        
        old_homepage_hotkey = self.translator.hotkey
        old_clipboard_hotkey = self.translator.clipboard_hotkey
        
        lang_display = self.translator.lang_display
        
        for key, (entry, typ) in entries.items():
            if typ is bool:
                val = entry.var.get()
            elif typ is int:
                try:
                    val = int(entry.get())
                except Exception:
                    val = 0
            elif typ == "combo" and key == "dest_lang":
                display_val = entry.var.get()
                val = next((k for k, v in lang_display.items() if v == display_val), self.translator.dest_lang)
            elif typ == "translation_model":
                display_val = entry.var.get()
                translation_models = self.settings_controller.get_translation_models()
                val = next((k for k, v in translation_models.items() if v == display_val), "google")
            elif key == "font":
                val = entry.var.get()
            else:
                val = entry.get()
            
            # Update translator instance attribute directly
            setattr(self.translator, key, val)
        
        # Save configuration using new config system
        save_success = self.translator.save_config()
        
        if not save_success:
            print("Failed to save configuration")
        
        # Update system settings
        from VezylTranslatorProton.app import StartupManager
        StartupManager.set_startup(self.translator.start_at_startup)
        self.gui_controller.setup_ctrl_tracking(self)
        
        # Update hotkey system
        self._update_hotkey_system(old_homepage_hotkey, old_clipboard_hotkey)
        
        # Refresh settings tab
        self.show_tab_settings()
    
    def _update_hotkey_system(self, old_homepage_hotkey, old_clipboard_hotkey):
        """Update hotkey system"""
        from VezylTranslatorNeutron.hotkey_service import register_hotkey, unregister_hotkey
        from VezylTranslatorNeutron.clipboard_service import toggle_clipboard_watcher as unified_toggle_clipboard_watcher
        
        try:
            # Always unregister existing hotkeys first
            unregister_hotkey("homepage")
            unregister_hotkey("clipboard")
            
            # If hotkeys are enabled, register them
            if hasattr(self.translator, 'enable_hotkeys') and self.translator.enable_hotkeys:
                # Register homepage hotkey
                register_hotkey(
                    "homepage",
                    self.translator.hotkey,
                    lambda: self.show_and_fill_homepage()
                )
                
                # Register clipboard toggle hotkey using the unified function
                register_hotkey(
                    "clipboard", 
                    self.translator.clipboard_hotkey,
                    lambda: unified_toggle_clipboard_watcher(self.translator)
                )
                
                print("Hotkeys enabled")
            else:
                print("Hotkeys disabled")
                
        except Exception as e:
            print(f"Error updating hotkey system: {e}")
    
    # === Event Handlers ===
    
    def _on_window_close(self):
        """Handle window close event"""
        try:
            # Stop any running threads
            if hasattr(self, 'translation_controller'):
                self.translation_controller.cleanup()
            
            # Hide window instead of destroying
            self.withdraw()
        except Exception as e:
            print(f"Error during window close: {e}")
            self.destroy()
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode"""
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)
    
    def _ctrl_down(self, event=None):
        """Handle Ctrl key press"""
        self.ctrl_pressed = True
    
    def _ctrl_up(self, event=None):
        """Handle Ctrl key release"""
        self.ctrl_pressed = False
    
    def _on_focus_in(self, event=None):
        """Handle window focus in"""
        # Update clipboard monitoring state
        if hasattr(self.translator, 'clipboard_monitor'):
            self.translator.clipboard_monitor.window_focused = True
    
    def _on_focus_out(self, event=None):
        """Handle window focus out"""
        # Update clipboard monitoring state
        if hasattr(self.translator, 'clipboard_monitor'):
            self.translator.clipboard_monitor.window_focused = False
    
    # === Public Methods ===
    
    def refresh_current_tab(self):
        """Refresh the currently active tab"""
        # Find active tab and refresh it
        for tab_name, button in self.nav_buttons.items():
            if button.cget("fg_color") != "transparent":
                self.show_tab(tab_name)
                break
    
    def update_language_interface(self, language_interface, theme_interface):
        """Update language interface"""
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        
        # Update all controllers
        self.gui_controller.update_interface(language_interface, theme_interface)
        self.translation_controller.language_interface = language_interface
        self.translation_controller.theme_interface = theme_interface
        self.tab_controller.language_interface = language_interface
        self.tab_controller.theme_interface = theme_interface
        self.settings_controller.language_interface = language_interface
        self.settings_controller.theme_interface = theme_interface
        
        # Refresh current tab to apply changes
        self.refresh_current_tab()
    
    def get_window_state(self):
        """Get current window state for persistence"""
        try:
            return {
                'geometry': self.geometry(),
                'state': self.state(),
                'is_fullscreen': self.is_fullscreen
            }
        except:
            return {}
    
    def restore_window_state(self, state_dict):
        """Restore window state from persistence"""
        try:
            if 'geometry' in state_dict:
                self.geometry(state_dict['geometry'])
            if 'is_fullscreen' in state_dict and state_dict['is_fullscreen']:
                self.toggle_fullscreen()
        except Exception as e:
            print(f"Error restoring window state: {e}")
    
    def show_and_fill_homepage(self):
        """Show homepage and fill with last translated text"""
        if getattr(self.gui_controller, '_shutting_down', False):
            print("Resetting shutdown flag for window reactivation")
            self.gui_controller._shutting_down = False
        
        try:
            # Check if window still exists
            if not self.winfo_exists():
                print("Window no longer exists, cannot show homepage")
                return
                
            self.deiconify()
            self.lift()
            self.focus_force()
            self.show_tab("Trang chủ")
            
            def try_fill():
                try:
                    if getattr(self.gui_controller, '_shutting_down', False):
                        return
                    
                    if not self.winfo_exists():
                        return
                    
                    if constant.last_translated_text:
                        filled = self._fill_homepage_text(constant.last_translated_text)
                        if not filled and not getattr(self.gui_controller, '_shutting_down', False):
                            if self.winfo_exists():
                                self.after(100, try_fill)
                except Exception as e:
                    print(f"Error in try_fill: {e}")
            
            if self.winfo_exists():
                self.after(100, try_fill)
        except Exception as e:
            print(f"Error showing and filling homepage: {e}")
    
    def _fill_homepage_text(self, text):
        """Fill homepage text input"""
        if getattr(self.gui_controller, '_shutting_down', False):
            return False
        
        try:
            # Check if window still exists
            if not self.winfo_exists() or not hasattr(self, 'content_frame') or not self.content_frame.winfo_exists():
                return False
                
            for widget in self.content_frame.winfo_children():
                if not widget.winfo_exists():
                    continue
                    
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if not child.winfo_exists():
                            continue
                            
                        if isinstance(child, ctk.CTkTextbox):
                            child.delete("1.0", "end")
                            child.insert("1.0", text)
                            return True
                        if isinstance(child, ctk.CTkFrame):
                            for subchild in child.winfo_children():
                                if not subchild.winfo_exists():
                                    continue
                                    
                                if isinstance(subchild, ctk.CTkTextbox):
                                    subchild.delete("1.0", "end")
                                    subchild.insert("1.0", text)
                                    return True
            return False
        except Exception as e:
            print(f"Error filling homepage text: {e}")
            return False
    
    def open_entry_in_homepage(self, src_lang, dest_lang, content):
        """Open entry in homepage with specified languages and content"""
        self.show_tab("Trang chủ")
        
        def find_and_set_elements():
            # Find elements and set values
            main_frame = None
            for widget in self.content_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    main_frame = widget
                    break
            
            if not main_frame:
                self.after(100, find_and_set_elements)
                return
            
            # Find and set comboboxes and text
            src_lang_combo = None
            dest_lang_combo = None
            src_text = None
            
            # Find source language combo (first combo)
            for child in main_frame.winfo_children():
                if isinstance(child, ctk.CTkComboBox):
                    src_lang_combo = child
                    break
            
            # Find source text (first textbox in a frame)
            for child in main_frame.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ctk.CTkTextbox):
                            src_text = subchild
                            break
                    if src_text:
                        break
            
            # Find destination combo (in destination frame)
            for child in main_frame.winfo_children():
                if isinstance(child, ctk.CTkFrame) and child.cget("fg_color") == "#181a20":
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ctk.CTkComboBox):
                            dest_lang_combo = subchild
                            break
                    break
            
            # Set values
            lang_display = self.translator.lang_display
            
            if src_lang_combo:
                if src_lang == "auto":
                    src_lang_combo.set(self._("home")["auto_detect"])
                elif src_lang in lang_display:
                    src_lang_combo.set(lang_display[src_lang])
            
            if dest_lang_combo and dest_lang in lang_display:
                dest_lang_combo.set(lang_display[dest_lang])
            
            if src_text:
                src_text.delete("1.0", "end")
                src_text.insert("1.0", content)
                src_text.edit_modified(True)
                src_text.event_generate("<<Modified>>")
        
        self.after(100, find_and_set_elements)
    
    # === Cleanup Methods ===
    
    def cleanup(self):
        """Cleanup resources before closing"""
        try:
            # Cleanup controllers
            if hasattr(self, 'translation_controller'):
                self.translation_controller.cleanup()
            
            if hasattr(self, 'tab_controller'):
                self.tab_controller.cleanup()
            
            if hasattr(self, 'settings_controller'):
                self.settings_controller.cleanup()
            
            # Clear UI components
            if hasattr(self, 'ui_components'):
                self.ui_components.cleanup()
                
        except Exception as e:
            print(f"Error during cleanup: {e}")


# === Legacy Support ===
# For backward compatibility with existing imports

# Export MainWindow class for import compatibility
__all__ = ['MainWindow']
