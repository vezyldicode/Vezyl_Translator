"""
Settings Controller Module for VezylTranslator
Handles settings management and configuration logic
"""

import os
import winsound
from VezylTranslatorNeutron import constant
from VezylTranslatorProton.config import get_config_manager
from VezylTranslatorNeutron.hotkey_service import register_hotkey, unregister_hotkey


class SettingsController:
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
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        
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
                self.translator.set_startup(self.translator.start_at_startup)
            setup_ctrl_tracking_callback()
            update_hotkey_system_callback(old_homepage_hotkey, old_clipboard_hotkey)
        
        return save_success
    
    def update_hotkey_system(self, old_homepage_hotkey, old_clipboard_hotkey):
        """Update hotkey system based on config changes"""
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
