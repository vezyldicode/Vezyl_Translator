"""
 * Program: Vezyl Translator
 * Version: alpha 0.1
 * Author: Tuan Viet Nguyen
 * Website: https://github.com/vezyldicode
 * Date:  Mai 24, 2025
 * Description: 
 * 
 * This code is copyrighted by Tuan Viet Nguyen.
 * You may not use, distribute, or modify this code without the author's permission.
"""


import pyperclip
import pyautogui 
import tkinter as tk
import customtkinter as ctk
import threading
import time
import json
import os
import keyboard
from googletrans import Translator as GoogleTranslator  # pip install googletrans==4.0.0-rc1
from PIL import Image  # pip install pillow
import sys
from pystray import Icon, MenuItem, Menu

class MainWindow(ctk.CTkToplevel):
    def __init__(self, translator: 'Translator'):
        super().__init__()
        self.translator = translator
        self.title("Vezyl Translator")
        self.geometry("900x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.resizable(True, True)  # Cho phép resize
        self.is_fullscreen = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
        self.tabs = {
            "Trang chủ": self.show_tab_home,
            "Lịch sử": self.show_tab_history,
            "Yêu thích": self.show_tab_favorite,
            "Cài đặt": self.open_settings
        }
        self.build_ui()
        self.show_tab_home()

    def build_ui(self):
        # Nav bar
        self.nav_bar = ctk.CTkFrame(self, width=70, fg_color="#23272f")
        self.nav_bar.pack(side="left", fill="y")
        self.nav_buttons = {}

        icons = [
            ("assets/logo.png", "Trang chủ"),
            ("assets/history.png", "Lịch sử"),
            ("assets/favorite.png", "Yêu thích"),
        ]
        for icon_path, tab_name in icons:
            try:
                img = ctk.CTkImage(light_image=Image.open(icon_path), size=(32, 32))
            except Exception:
                img = None
            btn = ctk.CTkButton(
                self.nav_bar, image=img, text="", width=60, height=60,
                fg_color="transparent", hover_color="#444",
                command=lambda t=tab_name: self.show_tab(t)
            )
            btn.pack(pady=10)
            self.nav_buttons[tab_name] = btn

        self.nav_bar.pack_propagate(False)

        # Settings icon ở dưới cùng
        try:
            settings_img = ctk.CTkImage(light_image=Image.open("assets/settings.png"), size=(32, 32))
        except Exception:
            settings_img = None
        settings_btn = ctk.CTkButton(
            self.nav_bar, image=settings_img, text="", width=60, height=60,
            fg_color="transparent", hover_color="#444",
            command=lambda: self.show_tab("Cài đặt")
        )
        settings_btn.pack(side="bottom", pady=20)
        self.nav_buttons["Cài đặt"] = settings_btn

        # Content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="#2d323e")
        self.content_frame.pack(side="left", fill="both", expand=True)

    def show_tab(self, tab_name):
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        # Gọi hàm tab tương ứng
        if tab_name in self.tabs:
            self.tabs[tab_name]()
        else:
            self.show_tab_home()

    def show_tab_home(self):
        label = ctk.CTkLabel(self.content_frame, text="Đây là Trang chủ", font=("JetBrains Mono", 20, "bold"))
        label.pack(pady=40)

    def show_tab_history(self):
        label = ctk.CTkLabel(self.content_frame, text="Lịch sử dịch", font=("JetBrains Mono", 20, "bold"))
        label.pack(pady=40)

    def show_tab_favorite(self):
        label = ctk.CTkLabel(self.content_frame, text="Các bản dịch yêu thích", font=("JetBrains Mono", 20, "bold"))
        label.pack(pady=40)

    def open_settings(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        # Hiển thị các trường config
        config = {
            "always_show_transtale": ("Hiện icon popup", bool),
            "icon_size": ("Kích thước icon", int),
            "hotkey": ("Hotkey", str),
            "dest_lang": ("Ngôn ngữ đích", str),
        }
        entries = {}
        row = 0
        for key, (label_text, typ) in config.items():
            ctk.CTkLabel(self.content_frame, text=label_text, anchor="w").grid(row=row, column=0, sticky="w", padx=10, pady=5)
            val = getattr(self.translator, key)
            entry = ctk.CTkEntry(self.content_frame)
            entry.insert(0, str(val))
            entry.grid(row=row, column=1, padx=10, pady=5)
            entries[key] = (entry, typ)
            row += 1

        def save_config():
            try:
                with open(self.translator.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                config_data = {}
            for key, (entry, typ) in entries.items():
                val = entry.get()
                if typ is bool:
                    val = val.lower() in ("1", "true", "yes", "on")
                elif typ is int:
                    val = int(val)
                config_data[key] = val
            with open(self.translator.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            self.translator.load_config()

        save_btn = ctk.CTkButton(self.content_frame, text="Lưu cài đặt", command=save_config)
        save_btn.grid(row=row, column=0, columnspan=2, pady=20)

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)

    def on_close(self):
        self.withdraw()  # Ẩn cửa sổ, không thoát app

class Translator:
    def __init__(self):
        print("Vezyl Translator - Alpha 0.1")
        self.config_file = "config.json"
        self.Is_icon_showing = False
        self.load_config()
        self.translator = GoogleTranslator()
        self.root = ctk.CTk()
        self.root.withdraw()
        self.main_window = MainWindow(self)
        self.main_window.deiconify()
        threading.Thread(target=self.clipboard_watcher, daemon=True).start()
        self.root.mainloop()

    def load_config(self):
        """load file config"""
        # Giá trị mặc định
        self.always_show_transtale = True
        self.icon_size = 60
        self.hotkey = 'ctrl+shift+c'
        self.dest_lang = 'vi'
        self.font = ("JetBrains Mono", 18, "bold")
        self.lang_display = {
            "en": "🇺🇸 English",
            "vi": "🇻🇳 Tiếng Việt",
            "ja": "🇯🇵 日本語",
            "ko": "🇰🇷 한국어",
            "zh-cn": "🇨🇳 中文(简体)",
            "zh-tw": "🇹🇼 中文(繁體)",
            "fr": "🇫🇷 Français",
            "de": "🇩🇪 Deutsch",
            "ru": "🇷🇺 Русский",
            "es": "🇪🇸 Español",
            "th": "🇹🇭 ไทย"
        }
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.always_show_transtale = config.get('always_show_transtale', self.always_show_transtale)
                    self.icon_size = config.get('icon_size', self.icon_size)
                    self.hotkey = config.get('hotkey', self.hotkey)
                    self.dest_lang = config.get('dest_lang', self.dest_lang)
                    self.font = tuple(config.get('font', list(self.font)))
                    self.lang_display = config.get('lang_display', self.lang_display)
        except Exception as e:
            print(f"Lỗi khi tải cấu hình: {e}")

    def translate_text(self, text):
        try:
            result = self.translator.translate(text, dest='vi')
            return result.text
        except Exception as e:
            return f"Lỗi dịch: {e}"

    def show_popup(self, text, x, y):
        lang_display = self.lang_display
        lang_codes = list(lang_display.keys())
        display_to_code = {v: k for k, v in lang_display.items()}

        # Lấy ngôn ngữ đích từ config
        dest_lang = self.dest_lang

        # Lấy ngôn ngữ gốc ban đầu
        result = self.translator.translate(text, dest=dest_lang)
        translated = result.text
        src_lang = result.src
        src_lang_display = lang_display.get(src_lang, src_lang)
        dest_lang_display = lang_display.get(dest_lang, dest_lang)

        popup = ctk.CTkToplevel()
        popup.wm_overrideredirect(True)
        popup.wm_attributes('-topmost', True)
        popup.wm_attributes('-alpha', 0.5)
        popup.wm_geometry(f"+{x}+{y}")

        frame = ctk.CTkFrame(
            popup,
            fg_color="#23272f",
            border_color="#4e5057",
            border_width=3,
            corner_radius=12
        )
        frame.pack(padx=8, pady=8, fill="both", expand=True)

        combo_src_lang = ctk.CTkComboBox(
            frame,
            values=[lang_display[code] for code in lang_codes],
            width=200,
            state="readonly"
        )
        combo_src_lang.pack(anchor="w", padx=10, pady=(10, 0))

        label_src_lang = ctk.CTkLabel(
            frame,
            text=f"{src_lang_display}",
            text_color="#aaaaaa",
            font=("JetBrains Mono", 14, "italic"),
            anchor="w"
        )
        label_src_lang.pack(anchor="w", padx=10, pady=(0, 0))

        label_src = ctk.CTkLabel(
            frame,
            text=text,
            fg_color="#23272f",
            text_color="#f5f5f5",
            padx=10, pady=5,
            wraplength=400,
            justify="left",
            font=self.font
        )
        label_src.pack(anchor="w", padx=10, pady=(0, 10))

        label_dest_lang = ctk.CTkLabel(
            frame,
            text=f"{dest_lang_display}",
            text_color="#aaaaaa",
            font=("JetBrains Mono", 14, "italic"),
            anchor="w"
        )
        label_dest_lang.pack(anchor="w", padx=10, pady=(0, 0))

        label_trans = ctk.CTkLabel(
            frame,
            text=translated,
            fg_color="#23272f",
            text_color="#00ff99",
            padx=10, pady=5,
            wraplength=400,
            justify="left",
            font=self.font
        )
        label_trans.pack(anchor="w", padx=10, pady=(0, 10))

        def update_translation(new_src_lang):
            try:
                # Dịch lại
                result = self.translator.translate(text, src=new_src_lang, dest=dest_lang)
                translated = result.text
                src_lang_display = lang_display.get(new_src_lang, new_src_lang)
                dest_lang_display = lang_display.get(dest_lang, dest_lang)
                # Cập nhật các label
                label_src_lang.configure(text=f"{src_lang_display}") # ngôn ngữ gốc mới
                label_dest_lang.configure(text=f"{dest_lang_display}") # ngôn ngữ đích mới
                label_trans.configure(text=translated) # Hiển thị lại bản dịch
            except Exception as e:
                label_trans.configure(text=f"Cannot translate: {e}")

        def on_combo_change(selected_value):
            selected_lang_code = display_to_code.get(selected_value)
            if selected_lang_code:
                update_translation(selected_lang_code)

        combo_src_lang.configure(command=on_combo_change)
        try:
            combo_src_lang.set(lang_display[src_lang])
        except Exception:
            combo_src_lang.set(lang_display.get('en', '🇺🇸 English'))

        close_job = [None]
        def schedule_close():
            if close_job[0]:
                popup.after_cancel(close_job[0])
            close_job[0] = popup.after(2000, popup.destroy)

        def on_enter(event):
            popup.wm_attributes('-alpha', 1.0)
            if close_job[0]:
                popup.after_cancel(close_job[0])
                close_job[0] = None

        def on_leave(event):
            popup.wm_attributes('-alpha', 0.7)
            schedule_close()

        popup.bind("<Enter>", on_enter)
        popup.bind("<Leave>", on_leave)

        schedule_close()
        popup.mainloop()

    def show_icon(self, text, x, y):
        # Hàm này phải luôn được gọi từ main thread!
        try:
            # Đặt trạng thái đang hiển thị icon
            self.Is_icon_showing = True
            icon_win = ctk.CTkToplevel(self.root)
            icon_win.wm_overrideredirect(True)
            icon_win.wm_attributes('-topmost', True)

            icon_size = self.icon_size
            icon_win.wm_geometry(f"{icon_size}x{icon_size}+{x}+{y}")

            # Load icon từ file và resize thành hình vuông
            img = Image.open(os.path.join("assets", "logo.png"))
            # Crop thành hình vuông nếu cần
            width, height = img.size
            if width != height:
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                img = img.crop((left, top, left + size, top + size))
            
            img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(icon_size -15, icon_size-15))

            # Tạo label để hiển thị hình ảnh
            img_label = ctk.CTkLabel(
                icon_win,
                text="",
                image=ctk_img,
                width=icon_size,
                height=icon_size,
                corner_radius=0,  # Không bo góc để hình vuông vức
                fg_color="transparent"  # Nền trong suốt
            )
            img_label.pack(fill="both", expand=True, padx=0, pady=0)

            # Bind sự kiện click cho label
            def on_click(event):
                self.Is_icon_showing = False
                icon_win.destroy()
                self.show_popup(text, x, y+30)

            img_label.bind("<Button-1>", on_click)
            # Thêm cursor pointer khi hover
            img_label.configure(cursor="hand2")

            # Hàm destroy icon và cập nhật trạng thái
            def destroy_icon():
                self.Is_icon_showing = False
                icon_win.destroy()

            icon_win.after(5000, destroy_icon)
            icon_win.lift()
            icon_win.after(100, lambda: icon_win.attributes('-alpha', 0.9))
            
        except Exception as e:
            self.Is_icon_showing = False  # Đặt về False nếu có lỗi
            print(f"Lỗi show_icon: {e}", file=sys.stderr)

    def clipboard_watcher(self):
        recent_value = pyperclip.paste()
        while True:
            if self.Is_icon_showing:
                time.sleep(0.3)
                continue
            else:
                tmp_value = pyperclip.paste()
                if tmp_value != recent_value and tmp_value.strip():
                    recent_value = tmp_value
                    x, y = pyautogui.position()
                    # Gọi show_icon trên main thread
                    self.root.after(0, self.show_icon, tmp_value, x + 10, y + 10)
                time.sleep(0.3)

def main():
    threading.Thread(target=Translator, daemon=True).start()
    icon_image = Image.open("assets/logo.ico")
    menu = Menu(MenuItem("Thoát", on_quit))
    icon = Icon("MyApp", icon_image, "Vezyl translator", menu)
    icon.run()
    # app = Translator()
    

def on_quit(icon, item):
    icon.stop()
    # sys.exit()



if __name__ == "__main__":
    main()
