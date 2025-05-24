"""
 * Program: Vezyl Translator
 * Version: alpha 0.1
 * Author: Tuan Viet Nguyen
 * Website: https://github.com/vezyldicode
 * Date: Feb 11, 2025
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

class Translator:
    def __init__(self):
        self.config_file = "config.json"
        self.current_hotkey = 'ctrl+shift+c'
        self.load_config()
        self.translator = GoogleTranslator()
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
        lang_codes = list(lang_display.keys())
        
        # Tạo mapping ngược từ display text về code
        display_to_code = {v: k for k, v in lang_display.items()}

        # Lấy ngôn ngữ gốc ban đầu
        result = self.translator.translate(text, dest='vi')
        translated = result.text
        src_lang = result.src
        dest_lang = 'vi'
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

        # Combobox chọn ngôn ngữ gốc
        combo_src_lang = ctk.CTkComboBox(
            frame,
            values=[lang_display[code] for code in lang_codes],
            width=200,
            state="readonly"
        )
        combo_src_lang.pack(anchor="w", padx=10, pady=(10, 0))

        # Hiển thị ngôn ngữ gốc
        label_src_lang = ctk.CTkLabel(
            frame,
            text=f"{src_lang_display}",
            text_color="#aaaaaa",
            font=("JetBrains Mono", 14, "italic"),
            anchor="w"
        )
        label_src_lang.pack(anchor="w", padx=10, pady=(0, 0))

        # Hiển thị nội dung gốc
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

        # Hiển thị ngôn ngữ đích
        label_dest_lang = ctk.CTkLabel(
            frame,
            text=f"{dest_lang_display}",
            text_color="#aaaaaa",
            font=("JetBrains Mono", 14, "italic"),
            anchor="w"
        )
        label_dest_lang.pack(anchor="w", padx=10, pady=(0, 0))

        # Hiển thị nội dung đích
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

        # Hàm dịch lại với ngôn ngữ gốc mới
        def update_translation(new_src_lang):
            try:
                result = self.translator.translate(text, src=new_src_lang, dest='vi')
                translated = result.text
                src_lang_display = lang_display.get(new_src_lang, new_src_lang)
                dest_lang_display = lang_display.get('vi', 'vi')
                # Cập nhật lại các label
                label_src_lang.configure(text=f"Ngôn ngữ gốc: {src_lang_display}")
                label_dest_lang.configure(text=f"Ngôn ngữ đích: {dest_lang_display}")
                label_trans.configure(text=translated)
            except Exception as e:
                label_trans.configure(text=f"Lỗi dịch: {e}")

        # Event thay đổi ngôn ngữ gốc
        def on_combo_change(selected_value):
            # Lấy code ngôn ngữ từ display text
            selected_lang_code = display_to_code.get(selected_value)
            if selected_lang_code:
                update_translation(selected_lang_code)

        # Gán command cho combobox
        combo_src_lang.configure(command=on_combo_change)
        
        # Đặt giá trị mặc định cho combobox
        try:
            combo_src_lang.set(lang_display[src_lang])
        except Exception:
            combo_src_lang.set(lang_display.get('en', '🇺🇸 English'))

        # --- Quản lý thời gian tự động đóng ---
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

    def load_config(self):
        """load file config"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_hotkey = config.get('hotkey', 'ctrl+shift+c')
        except Exception as e:
            print(f"Lỗi khi tải cấu hình: {e}")

    def clipboard_watcher(self):  # Add self
        recent_value = pyperclip.paste()
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
