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
        self.ui_components = UIComponents(translator, "dark")  # Use a simple theme string
        
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
        
        # Update active tab highlighting
        self._update_active_tab(tab_name)
        
        # Show requested tab
        if tab_name in self.tabs:
            self.tabs[tab_name]()
        else:
            self.show_tab_home()
    
    def _update_active_tab(self, active_tab_name):
        """Update active tab highlighting"""
        # Tab background colors mapping
        tab_colors = {
            "Trang chủ": "#2d323e",      # Same as content frame
            "Lịch sử": "#2d323e", 
            "Yêu thích": "#2d323e",
            "Cài đặt": "#2d323e"
        }
        
        # Reset all tab buttons to transparent
        for tab_name, button in self.nav_buttons.items():
            button.configure(fg_color="transparent")
        
        # Set active tab button to match its content background color
        if active_tab_name in self.nav_buttons and active_tab_name in tab_colors:
            active_button = self.nav_buttons[active_tab_name]
            active_color = tab_colors[active_tab_name]
            active_button.configure(fg_color=active_color)
    
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
                             text=self._._("history")["title"], 
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
        # Safe widget cleanup
        self._safe_clear_content_frame()
        
        # Create title and search
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(side="top", fill="x", padx=60, pady=(20, 0))

        title = ctk.CTkLabel(title_frame, 
                             text=self._._("favorite")["title"], 
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
    
    def _safe_clear_content_frame(self):
        """Safely clear content frame with proper error handling"""
        if not hasattr(self, 'content_frame') or not self.content_frame.winfo_exists():
            return
            
        try:
            # Get all children first
            children = list(self.content_frame.winfo_children())
            
            # Destroy widgets in reverse order to avoid dependency issues
            for widget in reversed(children):
                try:
                    if widget.winfo_exists():
                        # Unbind any events first
                        try:
                            widget.unbind_all()
                        except:
                            pass
                        
                        # Destroy the widget
                        widget.destroy()
                except Exception as e:
                    print(f"Warning: Failed to destroy widget {widget}: {e}")
                    continue
                    
            # Force update to ensure cleanup is complete
            self.content_frame.update_idletasks()
            
        except Exception as e:
            print(f"Error clearing content frame: {e}")
            # As fallback, just try to recreate the content frame
            try:
                self.content_frame.destroy()
                self._setup_content_area()
            except:
                pass
    
    def _build_settings_form_content(self, parent, canvas, window_id):
        """Build settings form content without save button and copyright"""
        lang_display = self.translator.lang_display
        lang_codes = list(lang_display.keys())
        
        # Config groups (same as old file)
        config_groups = [
            (self._._("settings")["general"]["title"], [
                ("start_at_startup", self._._("settings")["general"]["start_at_startup"], bool),
                ("show_homepage_at_startup", self._._("settings")["general"]["show_homepage_at_startup"], bool),
                ("always_show_transtale", self._._("settings")["general"]["always_show_translate"], bool),
                ("enable_ctrl_tracking", self._._("settings")["general"]["enable_ctrl_tracking"], bool),
                ("enable_hotkeys", self._._("settings")["general"]["enable_hotkeys"], bool),
                ("hotkey", self._._("settings")["general"]["hotkey"], "hotkey"),
                ("clipboard_hotkey", self._._("settings")["general"]["clipboard_hotkey"], "hotkey"),
            ]),
            (self._._("settings")["history"]["title"], [
                ("save_translate_history", self._._("settings")["history"]["save_translate_history"], bool),
                ("max_history_items", self._._("settings")["history"]["max_history_items"], int),
            ]),
            (self._._("settings")["popup_and_icon"]["title"], [
                ("icon_size", self._._("settings")["popup_and_icon"]["icon_size"], int),
                ("icon_dissapear_after", self._._("settings")["popup_and_icon"]["icon_dissapear_after"], int),
                ("popup_dissapear_after", self._._("settings")["popup_and_icon"]["popup_dissapear_after"], int),
                ("max_length_on_popup", self._._("settings")["popup_and_icon"]["max_length_on_popup"], int),
            ]),
            (self._._("settings")["language"]["title"], [
                ("interface_language", self._._("settings")["language"]["interface_language"], "combo"),
                ("dest_lang", self._._("settings")["language"]["dest_lang"], "combo"),
                ("font", self._._("settings")["language"]["font"], "combo"),
            ]),
            (self._._("settings")["translation"]["title"], [
                ("translation_model", self._._("settings")["translation"]["translation_model"], "translation_model"),
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
                text_color="#00ff99"  # Changed from white to blue header color
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

        # Canvas event handlers (same as old file)
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
            text=self._._("settings")["general"]["save_settings"],
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

    def _build_settings_form_old_style(self, parent, canvas, window_id):
        """Build settings form using old style"""
        lang_display = self.translator.lang_display
        lang_codes = list(lang_display.keys())
        
        # Config groups (same as old file)
        config_groups = [
            (self._._("settings")["general"]["title"], [
                ("start_at_startup", self._._("settings")["general"]["start_at_startup"], bool),
                ("show_homepage_at_startup", self._._("settings")["general"]["show_homepage_at_startup"], bool),
                ("always_show_transtale", self._._("settings")["general"]["always_show_translate"], bool),
                ("enable_ctrl_tracking", self._._("settings")["general"]["enable_ctrl_tracking"], bool),
                ("enable_hotkeys", self._._("settings")["general"]["enable_hotkeys"], bool),
                ("hotkey", self._._("settings")["general"]["hotkey"], "hotkey"),
                ("clipboard_hotkey", self._._("settings")["general"]["clipboard_hotkey"], "hotkey"),
            ]),
            (self._._("settings")["history"]["title"], [
                ("save_translate_history", self._._("settings")["history"]["save_translate_history"], bool),
                ("max_history_items", self._._("settings")["history"]["max_history_items"], int),
            ]),
            (self._._("settings")["popup_and_icon"]["title"], [
                ("icon_size", self._._("settings")["popup_and_icon"]["icon_size"], int),
                ("icon_dissapear_after", self._._("settings")["popup_and_icon"]["icon_dissapear_after"], int),
                ("popup_dissapear_after", self._._("settings")["popup_and_icon"]["popup_dissapear_after"], int),
                ("max_length_on_popup", self._._("settings")["popup_and_icon"]["max_length_on_popup"], int),
            ]),
            (self._._("settings")["language"]["title"], [
                ("dest_lang", self._._("settings")["language"]["dest_lang"], "combo"),
                ("font", self._._("settings")["language"]["font"], str),
            ]),
            (self._._("settings")["translation"]["title"], [
                ("translation_model", self._._("settings")["translation"]["translation_model"], "translation_model"),
            ])
        ]

        entries = {}
        row_idx = 0
        for group_name, fields in config_groups:
            # Group title
            group_label = ctk.CTkLabel(parent, text=group_name, font=(self.translator.font, 15, "bold"), text_color="#00ff99")
            group_label.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=(18, 6))
            row_idx += 1
            
            for key, label_text, typ in fields:
                # Field label
                ctk.CTkLabel(parent, text=label_text, anchor="w", font=(self.translator.font, 13)).grid(row=row_idx, column=0, sticky="w", padx=18, pady=6)
                val = getattr(self.translator, key)
                
                # Create field based on type (exact same logic as old file)
                if typ is bool:
                    var = tk.BooleanVar(value=val)
                    entry = ctk.CTkCheckBox(parent, variable=var, text="")
                    entry.var = var
                elif typ is int:
                    entry = ctk.CTkEntry(parent)
                    entry.insert(0, str(val))
                elif typ == "combo" and key == "dest_lang":
                    current_display = lang_display.get(val, next(iter(lang_display.values())))
                    var = tk.StringVar(value=current_display)
                    entry = ctk.CTkComboBox(
                        parent,
                        values=[lang_display[code] for code in lang_codes],
                        variable=var,
                        state="readonly",
                        font=(self.translator.font, 13),
                        width=220
                    )
                    entry.set(current_display)
                    entry.var = var
                elif key == "font":
                    fonts = self.translator.default_fonts if hasattr(self.translator, "default_fonts") else ["JetBrains Mono"]
                    var = tk.StringVar(value=val)
                    entry = ctk.CTkComboBox(
                        parent,
                        values=fonts,
                        variable=var,
                        state="readonly",
                        font=(self.translator.font, 13),
                        width=220
                    )
                    entry.set(val)
                    entry.var = var
                elif typ == "translation_model":
                    translation_models = getattr(self.translator, 'translation_models', {
                        "google": "🌐 Google Translator",
                        "bing": "🔍 Bing Translator", 
                        "deepl": "🔬 DeepL Translator",
                        "marian": "🤖 Marian MT (Local)",
                        "opus": "📚 OPUS-MT (Local)"
                    })
                    current_display = translation_models.get(val, "🌐 Google Translator")
                    var = tk.StringVar(value=current_display)
                    entry = ctk.CTkComboBox(
                        parent,
                        values=list(translation_models.values()),
                        variable=var,
                        state="readonly",
                        font=(self.translator.font, 13),
                        width=220
                    )
                    entry.set(current_display)
                    entry.var = var
                    
                    # Language support label for Marian
                    supported_languages_label = ctk.CTkLabel(
                        parent, 
                        text="", 
                        font=(self.translator.font, 11),
                        text_color="#888888",
                        anchor="w"
                    )
                    
                    def update_supported_languages(*args):
                        selected_model = var.get()
                        if "Marian MT" in selected_model:
                            try:
                                from VezylTranslatorProton.translator import get_translation_engine
                                engine = get_translation_engine()
                                supported = engine.get_supported_languages("marian")
                                lang_pairs = list(supported.values())
                                languages_text = f"🌐 Hỗ trợ: {', '.join(lang_pairs)}"
                                supported_languages_label.configure(text=languages_text)
                                supported_languages_label.grid(row=row_idx+1, column=0, columnspan=2, 
                                                              sticky="w", padx=18, pady=(2, 6))
                            except:
                                supported_languages_label.configure(text="")
                                supported_languages_label.grid_remove()
                        else:
                            supported_languages_label.configure(text="")
                            supported_languages_label.grid_remove()
                    
                    var.trace("w", update_supported_languages)
                    update_supported_languages()
                    entry.supported_languages_label = supported_languages_label
                    
                elif typ == "hotkey":
                    var = tk.StringVar(value=val)
                    entry = ctk.CTkEntry(parent, textvariable=var, state="readonly")
                    entry.var = var
                    entry.configure(cursor="hand2")
                    
                    def on_hotkey_click(event, entry=entry):
                        # Same hotkey logic as old file
                        entry.configure(state="normal")
                        entry.delete(0, "end")
                        entry.insert(0, "Press keys...")
                        entry.focus_set()
                        pressed_keys = set()
                        
                        def on_key_press(e):
                            k = e.keysym.lower()
                            pressed_keys.add(k)
                            keys = []
                            for mod in ["control", "ctrl", "shift", "alt", "win", "meta"]:
                                if mod in pressed_keys:
                                    keys.append(mod)
                            for k2 in pressed_keys:
                                if k2 not in ["control", "ctrl", "shift", "alt", "win", "meta"]:
                                    keys.append(k2)
                            
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
                            
                            seen = set()
                            result = []
                            for x in keys_mapped:
                                if x not in seen:
                                    seen.add(x)
                                    result.append(x)
                            hotkey_str = "+".join([k.upper() if len(k) == 1 else k for k in result])
                            entry.delete(0, "end")
                            entry.insert(0, hotkey_str)
                        
                        def on_key_release(e):
                            k = e.keysym.lower()
                            if k in pressed_keys:
                                pressed_keys.remove(k)
                            if not pressed_keys:
                                entry.configure(state="readonly")
                                entry.unbind("<KeyPress>")
                                entry.unbind("<KeyRelease>")
                        
                        entry.bind("<KeyPress>", on_key_press)
                        entry.bind("<KeyRelease>", on_key_release)
                    
                    entry.bind("<Button-1>", on_hotkey_click)
                else:
                    entry = ctk.CTkEntry(parent)
                    entry.insert(0, str(val))
                
                entry.grid(row=row_idx, column=1, padx=10, pady=6, sticky="ew")
                entries[key] = (entry, typ)
                parent.grid_columnconfigure(1, weight=1)
                
                # Handle special cases that need extra rows
                if typ == "translation_model" and hasattr(entry, 'supported_languages_label'):
                    row_idx += 2
                else:
                    row_idx += 1

        # Save button (same as old file)
        import winsound
        # NOTE: Save button moved to fixed footer, not in scrollable area
        
        # NOTE: Copyright moved to fixed footer, not in scrollable area
        
        # Canvas event handlers (same as old file)
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        parent.bind("<Configure>", on_configure)

        def resize_canvas(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", resize_canvas)

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
    
    def _save_settings(self, entries):
        """Save settings configuration using old logic"""
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        
        # Use new config system - update translator instance directly
        # Configuration will be saved through the translator's save_config method
        
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
                translation_models = getattr(self.translator, 'translation_models', {
                    "google": "🌐 Google Translator",
                    "bing": "🔍 Bing Translator", 
                    "deepl": "🔬 DeepL Translator",
                    "marian": "🤖 Marian MT (Local)",
                    "opus": "📚 OPUS-MT (Local)"
                })
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
        self.translator.set_startup(self.translator.start_at_startup)
        self.gui_controller.setup_ctrl_tracking(self)
        
        # Update hotkey system (use old logic)
        self._update_hotkey_system_old_style(old_homepage_hotkey, old_clipboard_hotkey)
        
        # Refresh settings tab
        self.show_tab_settings()
    
    def _update_hotkey_system_old_style(self, old_homepage_hotkey, old_clipboard_hotkey):
        """Update hotkey system using old logic"""
        from VezylTranslatorProton.hotkey_manager_module import register_hotkey, unregister_hotkey
        from VezylTranslatorProton.clipboard_module import toggle_clipboard_watcher as unified_toggle_clipboard_watcher
        
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
