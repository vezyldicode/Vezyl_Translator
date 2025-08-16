"""
Optimized GUI Module for VezylTranslator
Frontend-only implementation with backend logic moved to separate controllers
Copyright (c) 2023-2024 Vezyl. All rights reserved.
"""

import os
import tkinter as tk
import customtkinter as ctk
from VezylTranslatorNeutron import constant

# Import backend controllers
from VezylTranslatorProton.gui_controller import GUIController
from VezylTranslatorProton.translation_controller import TranslationController
from VezylTranslatorProton.tab_controller import TabController
from VezylTranslatorProton.settings_controller import SettingsController
from VezylTranslatorProton.ui_events import UIEvents
from VezylTranslatorProton.ui_components import UIComponents


class MainWindow(ctk.CTkToplevel):
    def __init__(self, translator, language_interface, theme_interface, _):
        super().__init__()
        
        # Store references
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
        
        # Initialize controllers
        self.gui_controller = GUIController(translator, language_interface, theme_interface, _)
        self.translation_controller = TranslationController(translator, language_interface, theme_interface, _)
        self.tab_controller = TabController(translator, language_interface, theme_interface, _)
        self.settings_controller = SettingsController(translator, language_interface, theme_interface, _)
        self.ui_events = UIEvents(translator, language_interface, theme_interface, _)
        
        # Initialize UI components helper
        self.ui_components = UIComponents(translator, self.gui_controller._get_icon_path())
        
        # Set up window
        self._setup_window()
        
        # Build UI
        self._build_navigation()
        self._setup_content_area()
        
        # Setup event handlers
        self._setup_event_handlers()
        
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
        self.content_frame = self.ui_components.create_content_frame(self)
    
    def _setup_event_handlers(self):
        """Setup window-level event handlers"""
        self.ui_events.setup_window_events(self, self.gui_controller)
        self.gui_controller.setup_ctrl_tracking(self)
        
        # Set callback for settings controller
        self.settings_controller.set_show_homepage_callback(self.show_and_fill_homepage)
    
    def show_tab(self, tab_name):
        """Show specified tab"""
        # Cleanup previous tab
        self.gui_controller.cleanup_mousewheel_handlers()
        
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Show requested tab
        if tab_name in self.tabs:
            self.tabs[tab_name]()
        else:
            self.show_tab_home()
    
    def show_tab_home(self):
        """Show home/translation tab"""
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
            [self._._("home")["auto_detect"]] + [lang_display[code] for code in lang_codes],
            src_lang_var
        )
        src_lang_combo.grid(row=0, column=0, sticky="w", pady=(0, 5))
        src_lang_combo.set(self._._("home")["auto_detect"])
        
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
            frame, "reverse.png", (36, 36)
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
        dest_lang_combo.set(lang_display.get(self.translator.dest_lang, "🇻🇳 Tiếng Việt"))
        
        # Destination text frame with copy button
        dest_text_frame, dest_text, copy_dest_btn = self.ui_components.create_text_frame_with_copy_button(
            dest_frame, "#181a20", "#00ff99"
        )
        dest_text_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))
        dest_text.configure(state="disabled")
        
        # Set copy button command
        copy_dest_btn.configure(
            command=lambda: self.tab_controller.copy_text_to_clipboard(
                dest_text.get("1.0", "end").strip()
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
                src_lang_var.get(), lang_display, self._._("home")["auto_detect"]
            )
            dest_lang = self.translation_controller.get_language_from_display(
                dest_lang_var.get(), lang_display, ""
            )
            
            # Create and execute translation
            translate_function = self.translation_controller.create_translation_function(
                text, src_lang, dest_lang, dest_text
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
        # Create title and search
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(side="top", fill="x", padx=60, pady=(20, 0))
        
        search_var = tk.StringVar()
        title_frame, title, search_entry = self.ui_components.create_title_with_search(
            self.content_frame, self._._("history")["title"], search_var
        )
        title_frame.pack(side="top", fill="x", padx=60, pady=(20, 0))
        
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
    
    def _render_history_entries(self, parent, search_keyword=""):
        """Render history entries"""
        # Clear existing widgets
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get data
        entries = self.tab_controller.get_history_data(search_keyword)
        
        if not entries:
            empty_label = self.ui_components.create_content_label(
                parent, self._._("history")["empty"]
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
    
    def show_tab_favorite(self):
        """Show favorites tab"""
        # Create title and search
        search_var = tk.StringVar()
        title_frame, title, search_entry = self.ui_components.create_title_with_search(
            self.content_frame, self._._("favorite")["title"], search_var
        )
        title_frame.pack(side="top", fill="x", padx=60, pady=(20, 0))
        
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
    
    def _render_favorite_entries(self, parent, search_keyword=""):
        """Render favorite entries"""
        # Clear existing widgets
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Get data
        entries = self.tab_controller.get_favorite_data(search_keyword)
        
        if not entries:
            empty_label = self.ui_components.create_content_label(
                parent, self._._("favorite")["empty"]
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
        """Show settings tab"""
        # Create scrollable content
        scrollable_frame, canvas, scrollbar, form_frame, window_id = self.ui_components.create_scrollable_frame(
            self.content_frame
        )
        scrollable_frame.pack(side="top", fill="both", expand=True)
        
        # Setup scrolling
        mousewheel_handler = self.gui_controller.safe_mousewheel_handler(canvas)
        self.gui_controller.add_mousewheel_handler(canvas, mousewheel_handler)
        
        resize_handler = self.ui_events.create_canvas_resize_handler(canvas, window_id)
        canvas.bind("<Configure>", resize_handler)
        
        configure_handler = self.ui_events.create_scrollregion_update_handler(canvas)
        form_frame.bind("<Configure>", configure_handler)
        
        # Build settings form
        entries = self._build_settings_form(form_frame)
        
        # Create footer
        self._create_settings_footer(entries)
    
    def _build_settings_form(self, parent):
        """Build settings form"""
        config_groups = self.settings_controller.get_config_groups()
        entries = {}
        row_idx = 0
        
        for group_name, fields in config_groups:
            # Group label
            group_label = self.ui_components.create_settings_group_label(parent, group_name)
            group_label.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=(18, 6))
            row_idx += 1
            
            # Fields
            for key, label_text, typ in fields:
                # Field label
                field_label = self.ui_components.create_settings_field_label(parent, label_text)
                field_label.grid(row=row_idx, column=0, sticky="w", padx=18, pady=6)
                
                # Create field widget
                entry = self._create_settings_field(parent, key, typ)
                entry.grid(row=row_idx, column=1, padx=10, pady=6, sticky="ew")
                
                entries[key] = (entry, typ)
                parent.grid_columnconfigure(1, weight=1)
                
                # Handle special cases that need extra rows
                if typ == "translation_model" and hasattr(entry, 'supported_languages_label'):
                    row_idx += 2
                else:
                    row_idx += 1
        
        return entries
    
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
    
    def _create_settings_footer(self, entries):
        """Create settings footer with save button"""
        footer = ctk.CTkFrame(self.content_frame, fg_color="#23272f")
        footer.pack(side="bottom", fill="x", pady=(0, 0))
        footer.grid_columnconfigure(0, weight=0)
        footer.grid_columnconfigure(1, weight=1)
        
        # Save button
        save_btn = self.ui_components.create_save_button(
            footer, self._._("settings")["save"]
        )
        save_btn.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)
        
        # Copyright label
        copyright_text = self.settings_controller.get_copyright_text()
        copyright_label = self.ui_components.create_copyright_label(footer, copyright_text)
        copyright_label.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=10)
        
        # Configure save button
        save_btn.configure(command=lambda: self._save_settings(entries))
    
    def _save_settings(self, entries):
        """Save settings configuration"""
        success = self.settings_controller.save_config_from_entries(
            entries,
            lambda: self.gui_controller.setup_ctrl_tracking(self),
            self.settings_controller.update_hotkey_system
        )
        
        if success:
            self.show_tab_settings()  # Refresh settings tab
    
    def open_entry_in_homepage(self, src_lang, dest_lang, content):
        """Open entry in homepage with specified languages and content"""
        self.show_tab("Trang chủ")
        
        def find_and_set_elements():
            # Find elements and set values (similar to original implementation)
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
                    src_lang_combo.set(self._._("home")["auto_detect"])
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
    
    def show_and_fill_homepage(self):
        """Show homepage and fill with last translated text"""
        if getattr(self.gui_controller, '_shutting_down', False):
            print("Resetting shutdown flag for window reactivation")
            self.gui_controller._shutting_down = False
        
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
            self.show_tab("Trang chủ")
            
            def try_fill():
                if getattr(self.gui_controller, '_shutting_down', False):
                    return
                
                if constant.last_translated_text:
                    filled = self._fill_homepage_text(constant.last_translated_text)
                    if not filled and not getattr(self.gui_controller, '_shutting_down', False):
                        self.after(100, try_fill)
            
            self.after(100, try_fill)
        except Exception as e:
            print(f"Error showing and filling homepage: {e}")
    
    def _fill_homepage_text(self, text):
        """Fill homepage text input"""
        if getattr(self.gui_controller, '_shutting_down', False):
            return False
        
        try:
            for widget in self.content_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkTextbox):
                            child.delete("1.0", "end")
                            child.insert("1.0", text)
                            return True
                        if isinstance(child, ctk.CTkFrame):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, ctk.CTkTextbox):
                                    subchild.delete("1.0", "end")
                                    subchild.insert("1.0", text)
                                    return True
            return False
        except Exception as e:
            print(f"Error filling homepage text: {e}")
            return False
    
    def destroy(self):
        """Override destroy to ensure proper cleanup"""
        self.gui_controller.destroy_cleanup()
        super().destroy()
