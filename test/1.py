import pyperclip
import pyautogui 
import tkinter as tk
import customtkinter as ctk
import threading
import time
import json
import os
import keyboard

class Translator:
    def __init__(self):
        self.config_file = "config.json"  # Add this line
        self.current_hotkey = 'ctrl+shift+c'
        self.load_config()
        threading.Thread(target=self.clipboard_watcher, daemon=True).start()
        while True:
            time.sleep(1)

    def show_popup(self, text, x, y):  # Add self
        popup = ctk.CTkToplevel()
        popup.wm_overrideredirect(True)
        popup.wm_attributes('-topmost', True)
        popup.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(popup, text=text, 
                             bg_color="lightyellow", 
                             text_color="black", 
                             padx=10, pady=5, wraplength=400, justify="left")
        # popup = tk.Tk()
        # popup.overrideredirect(True)
        # popup.attributes('-topmost', True)
        # popup.geometry(f"+{x}+{y}")

        # label = tk.Label(popup, text=text, bg="lightyellow", fg="black", padx=10, pady=5, wraplength=400, justify="left")
        label.pack()

        popup.after(3000, popup.destroy)
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
