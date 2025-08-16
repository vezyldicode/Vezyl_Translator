"""
UI Components Module for VezylTranslator
Contains reusable UI component builders
"""

import os
import tkinter as tk
import customtkinter as ctk
try:
    from PIL import Image
except ImportError:
    Image = None
from VezylTranslatorNeutron import constant


class UIComponents:
    def __init__(self, translator, theme):
        self.translator = translator
        self.theme = theme
    
    def load_image(self, filename, size=(24, 24), fallback_text=""):
        """Load image with fallback"""
        try:
            if Image is None:
                print(f"PIL not available, cannot load image {filename}")
                return None
            img_path = os.path.join(constant.RESOURCES_DIR, filename)
            image = Image.open(img_path)
            return ctk.CTkImage(image, size=size)
        except Exception as e:
            print(f"Không thể load ảnh {filename}: {e}")
            return None
    
    def create_navigation_bar(self, parent, nav_buttons_dict):
        """Create navigation bar with buttons"""
        nav_bar = ctk.CTkFrame(parent, width=70, fg_color="#23272f", border_width=0)
        nav_bar.pack(side="left", fill="y", padx=0, pady=0)
        nav_bar.pack_propagate(False)
        
        # Load button images
        button_configs = [
            ("Trang chủ", "logo.png", "top"),
            ("Lịch sử", "history.png", "top"),
            ("Yêu thích", "favorite.png", "top"),
            ("Cài đặt", "settings.png", "bottom")
        ]
        
        for text, img_file, position in button_configs:
            img = self.load_image(img_file, (32, 32))
            
            # Create container frame for each button to control positioning
            btn_container = ctk.CTkFrame(nav_bar, fg_color="transparent", height=60)
            
            btn = ctk.CTkButton(
                btn_container, 
                image=img, 
                text="", 
                width=78, 
                height=60,
                fg_color="transparent", 
                hover_color="#444",
                corner_radius=8,
                border_width=0
            )
            
            # Position button with 2px left margin
            btn.place(x=2, y=0)
            
            if position == "top":
                btn_container.pack(pady=5, fill="x", padx=0)
            else:
                btn_container.pack(side="bottom", pady=20, fill="x", padx=0)
            
            nav_buttons_dict[text] = btn
        
        return nav_bar
    
    def create_content_frame(self, parent):
        """Create main content frame"""
        content_frame = ctk.CTkFrame(parent, fg_color="#2d323e")
        content_frame.pack(side="left", fill="both", expand=True)
        return content_frame
    
    def create_tab_frame(self, parent):
        """Create frame for tab content"""
        frame = ctk.CTkFrame(parent, fg_color="#23272f")
        frame.pack(fill="both", expand=True, padx=60, pady=60)
        return frame
    
    def create_language_combo(self, parent, values, variable, width=180, command=None):
        """Create language selection combobox"""
        combo = ctk.CTkComboBox(
            parent,
            values=values,
            width=width,
            state="readonly",
            variable=variable,
            font=(self.translator.font, 13),
            command=command
        )
        return combo
    
    def create_text_area(self, parent, font_size=18, text_color="#f5f5f5", bg_color="#23272f", read_only=False):
        """Create text area widget"""
        text_widget = ctk.CTkTextbox(
            parent, 
            font=(self.translator.font, font_size, "bold"),
            wrap="word", 
            fg_color=bg_color, 
            text_color=text_color, 
            border_width=0
        )
        
        if read_only:
            text_widget.configure(state="disabled")
        
        return text_widget
    
    def create_text_frame_with_copy_button(self, parent, bg_color="#23272f", text_color="#f5f5f5", copy_callback=None):
        """Create frame with text area and copy button"""
        frame = ctk.CTkFrame(parent, fg_color=bg_color)
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Text area
        text_widget = self.create_text_area(frame, text_color=text_color, bg_color=bg_color)
        text_widget.grid(row=0, column=0, sticky="nsew")
        
        # Copy button
        copy_img = self.load_image("save_btn.png", (24, 24))
        copy_btn = ctk.CTkButton(
            frame,
            image=copy_img,
            text="",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#444",
            command=copy_callback if copy_callback else lambda: None
        )
        copy_btn.grid(row=1, column=0, sticky="w", padx=(4, 0), pady=(0, 6))
        
        return frame, text_widget, copy_btn
    
    def create_icon_button(self, parent, image_file, size=(24, 24), command=None):
        """Create icon-only button"""
        img = self.load_image(image_file, size)
        
        btn = ctk.CTkButton(
            parent,
            image=img,
            text="",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#444",
            command=command
        )
        
        return btn
    
    def create_scrollable_frame(self, parent, bg_color="#23272f"):
        """Create scrollable frame with canvas and scrollbar"""
        scrollable_frame = ctk.CTkFrame(parent, fg_color=bg_color)
        
        canvas = tk.Canvas(scrollable_frame, bg=bg_color, highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = ctk.CTkScrollbar(scrollable_frame, orientation="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Content frame on canvas
        content_frame = ctk.CTkFrame(canvas, fg_color=bg_color)
        window_id = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        return scrollable_frame, canvas, scrollbar, content_frame, window_id
    
    def create_title_with_search(self, parent, title_text, search_var, search_placeholder="🔍 Tìm kiếm..."):
        """Create title frame with search entry"""
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        # Title
        title = ctk.CTkLabel(
            title_frame, 
            text=title_text, 
            font=(self.translator.font, 20, "bold"), 
            text_color="#00ff99"
        )
        title.pack(side="left", anchor="w")
        
        # Search entry
        search_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text=search_placeholder,
            textvariable=search_var,
            width=260,
            font=(self.translator.font, 14)
        )
        search_entry.pack(side="right", padx=(0, 0), pady=0)
        
        return title_frame, title, search_entry
    
    def create_entry_card(self, parent, bg_color="#23272f", border_color="#444", corner_radius=8):
        """Create entry card frame"""
        entry_frame = ctk.CTkFrame(
            parent,
            fg_color=bg_color,
            border_width=1,
            border_color=border_color,
            corner_radius=corner_radius
        )
        entry_frame.grid_columnconfigure(0, weight=1)
        
        return entry_frame
    
    def create_date_label(self, parent, date_text, width=110):
        """Create date label for grouping"""
        date_label = ctk.CTkLabel(
            parent,
            text=date_text,
            font=(self.translator.font, 14, "bold"),
            text_color="#00ff99",
            width=width,
            anchor="w"
        )
        
        return date_label
    
    def create_info_label(self, parent, info_text, text_color="#888"):
        """Create info label (time, language info, etc.)"""
        info_label = ctk.CTkLabel(
            parent, 
            text=info_text, 
            font=(self.translator.font, 12, "italic"), 
            text_color=text_color
        )
        
        return info_label
    
    def create_content_label(self, parent, content_text, text_color="#f5f5f5", bold=False):
        """Create content label"""
        font_style = "bold" if bold else "normal"
        content_label = ctk.CTkLabel(
            parent,
            text=content_text,
            font=(self.translator.font, 15, font_style),
            text_color=text_color,
            anchor="w",
            justify="left"
        )
        
        return content_label
    
    def create_settings_group_label(self, parent, group_name):
        """Create settings group label"""
        group_label = ctk.CTkLabel(
            parent, 
            text=group_name, 
            font=(self.translator.font, 15, "bold"), 
            text_color="#00ff99"
        )
        
        return group_label
    
    def create_settings_field_label(self, parent, field_name):
        """Create settings field label"""
        field_label = ctk.CTkLabel(
            parent, 
            text=field_name, 
            anchor="w", 
            font=(self.translator.font, 13)
        )
        
        return field_label
    
    def create_checkbox_field(self, parent, value):
        """Create checkbox field for settings"""
        var = tk.BooleanVar(value=value)
        checkbox = ctk.CTkCheckBox(parent, variable=var, text="")
        checkbox.var = var
        
        return checkbox
    
    def create_entry_field(self, parent, value="", width=200):
        """Create entry field for settings"""
        entry = ctk.CTkEntry(parent, width=width)
        if value:
            entry.insert(0, str(value))
        
        return entry
    
    def create_readonly_entry_field(self, parent, value="", cursor="hand2", width=200):
        """Create readonly entry field (for hotkeys)"""
        var = tk.StringVar(value=value)
        entry = ctk.CTkEntry(parent, textvariable=var, state="readonly", width=width)
        entry.var = var
        entry.configure(cursor=cursor)
        
        return entry
    
    def create_combo_field(self, parent, values, current_value, width=220):
        """Create combobox field for settings"""
        var = tk.StringVar(value=current_value)
        combo = ctk.CTkComboBox(
            parent,
            values=values,
            variable=var,
            state="readonly",
            font=(self.translator.font, 13),
            width=width
        )
        combo.set(current_value)
        combo.var = var
        
        return combo
    
    def create_save_button(self, parent, text="Lưu", width=120, command=None):
        """Create save button"""
        save_btn = ctk.CTkButton(
            parent, 
            text=text, 
            width=width,
            command=command
        )
        
        return save_btn
    
    def create_copyright_label(self, parent, copyright_text):
        """Create copyright label"""
        copyright_label = ctk.CTkLabel(
            parent,
            text=copyright_text,
            font=(self.translator.font, 12, "italic"),
            text_color="#888"
        )
        
        return copyright_label
