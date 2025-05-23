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

class Translator:
    def __init__(self):
        self.config_file = "config.json"
        self.current_hotkey = 'ctrl+shift+c'
        self.load_config()
        self.translator = GoogleTranslator()  # Thêm dòng này
        threading.Thread(target=self.clipboard_watcher, daemon=True).start()
        while True:
            time.sleep(1)

    def translate_text(self, text):
        try:
            result = self.translator.translate(text, dest='vi')
            return result.text
        except Exception as e:
            return f"Lỗi dịch: {e}"

    def show_popup(self, text, x, y):
        result = self.translator.translate(text, dest='vi')
        translated = result.text
        src_lang = result.src
        dest_lang = 'vi'

        # Bảng tên ngôn ngữ và cờ
        lang_display = {
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
            "th": "🇹🇭 ไทย",
            # Thêm các ngôn ngữ khác nếu muốn
        }

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
            corner_radius=2
        )
        frame.pack(padx=8, pady=8, fill="both", expand=True)

        label_src_lang = ctk.CTkLabel(
            frame,
            text=f"{src_lang_display}",
            text_color="#aaaaaa",
            font=("JetBrains Mono", 14, "italic"),
            anchor="w"
        )
        label_src_lang.pack(anchor="w", padx=10, pady=(10, 0))

        label_src = ctk.CTkLabel(
            frame,
            text=text,
            fg_color="#23272f",
            text_color="#f5f5f5",
            padx=10, pady=5,
            wraplength=400,
            justify="left",
            font=("JetBrains Mono", 18, "bold")
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
            font=("JetBrains Mono", 18)
        )
        label_trans.pack(anchor="w", padx=10, pady=(0, 10))

        # --- Quản lý thời gian tự động đóng ---
        close_job = [None]  # Dùng list để mutable trong closure

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
            popup.wm_attributes('-alpha', 0.5)
            schedule_close()

        popup.bind("<Enter>", on_enter)
        popup.bind("<Leave>", on_leave)

        schedule_close()
        popup.mainloop()

    def load_config(self):
        """Tải cấu hình từ file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_hotkey = config.get('hotkey', 'ctrl+shift+c')
        except Exception as e:
            print(f"Lỗi khi tải cấu hình: {e}")

    def clipboard_watcher(self):  # Add self
        recent_value = ""
        while True:
            tmp_value = pyperclip.paste()
            if tmp_value != recent_value and tmp_value.strip():
                recent_value = tmp_value
                x, y = pyautogui.position()
                threading.Thread(target=self.show_popup, args=(tmp_value, x + 10, y + 10), daemon=True).start()
            time.sleep(0.3)

def main():
    app = Translator()

if __name__ == "__main__":
    main()
