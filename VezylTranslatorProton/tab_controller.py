"""
Tab Controller Module for VezylTranslator
Handles logic for different tabs (History, Favorites, etc.)
"""

import tkinter as tk
from VezylTranslatorNeutron import constant
from VezylTranslatorElectron.helpers import search_entries, ensure_local_dir, show_confirm_popup
from VezylTranslatorProton.storage import (
    read_history_entries, delete_history_entry, delete_all_history_entries,
    read_favorite_entries, delete_favorite_entry, delete_all_favorite_entries,
    update_favorite_note, write_favorite_entry
)
from VezylTranslatorNeutron.clipboard_service import set_clipboard_text


class TabController:
    def __init__(self, translator, language_interface, theme_interface, _):
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
    
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
    
    def cleanup(self):
        """Cleanup tab controller resources"""
        # Clear any cached data or references
        pass
