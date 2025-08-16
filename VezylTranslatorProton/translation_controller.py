"""
Translation Controller Module for VezylTranslator
Handles translation logic and auto-save functionality
"""

import threading
from VezylTranslatorNeutron import constant
from VezylTranslatorProton.translator import get_translation_engine
from VezylTranslatorProton.storage import write_log_entry
from VezylTranslatorElectron.helpers import ensure_local_dir


class TranslationController:
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
