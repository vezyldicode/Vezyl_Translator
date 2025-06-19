"""
 * Program: Vezyl Translator
 * Version: beta 0.2
 * Author: Tuan Viet Nguyen
 * Website: https://github.com/vezyldicode
 * Date:  Mai 24, 2025
 * Description: 
 * 
 * This code is copyrighted by Tuan Viet Nguyen.
 * You may not use, distribute, or modify this code without the author's permission.
"""
from VezylTranslatorNeutron import constant
import sys
import traceback
import os
import subprocess


def external_crash_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    # Truyền software và software_version vào crash handler
    subprocess.Popen([
        "VezylTranslatorCrashHandler.exe",
        error_msg,
        constant.SOFTWARE,
        constant.SOFTWARE_VERSION
    ])
    os._exit(1)

sys.excepthook = external_crash_handler

import winsound
import pyautogui 
import tkinter as tk
import customtkinter as ctk
import threading
import time
import json
import base64
import winreg  # Thêm import này ở đầu file
from datetime import datetime
from googletrans import Translator as GoogleTranslator  # pip install googletrans==4.0.0-rc1
from PIL import Image  # pip install pillow
from pystray import Icon, MenuItem, Menu
import keyboard
import toml
import VezylTranslatorProton.locale_module  as _
from VezylTranslatorProton.file_flow import pad, unpad, encrypt_aes, decrypt_aes, get_aes_key
from VezylTranslatorProton.hotkey_manager_module import register_hotkey, unregister_hotkey
from VezylTranslatorProton.tray_module import run_tray_icon_in_thread
from VezylTranslatorProton.clipboard_module import clipboard_watcher, get_clipboard_text, set_clipboard_text
from VezylTranslatorProton.config_module import load_config, save_config, get_default_config
from VezylTranslatorProton.utils import (
    get_windows_theme, 
    show_confirm_popup, 
    get_client_preferences, 
    ensure_local_dir, 
    search_entries
)
from VezylTranslatorProton.translate_module import translate_with_model
from VezylTranslatorProton.history_module import (
    write_log_entry,
    read_history_entries,
    delete_history_entry,
    delete_all_history_entries
)
from VezylTranslatorProton.favorite_module import (
    write_favorite_entry,
    read_favorite_entries,
    delete_favorite_entry,
    delete_all_favorite_entries,
    update_favorite_note
)
from VezylTranslatorElectron.gui import MainWindow


class Translator:
    def __init__(self):
        print(f"{constant.SOFTWARE}. version {constant.SOFTWARE_VERSION} - Copyright © 2025 by Vezyl")
        # Load config
        self.config_file = "config/general.json"
        self.load_config()
        self.Is_icon_showing = False
        self.clipboard_watcher_enabled = True
        # Load locale
        locales_dir = os.path.join("resources", "locales")
        _.load_locale(self.interface_language, locales_dir)

        self.translator = GoogleTranslator()
        self.root = ctk.CTk()
        self.root.withdraw()
        # --- Thêm xử lý khởi động cùng Windows ---
        self.set_startup(self.start_at_startup)
        self.clipboard_thread = threading.Thread(
            print("Starting clipboard watcher..."),
            target=clipboard_watcher,
            args=(
                self,  # translator_instance
                getattr(self, "main_window", None),  # main_window_instance
                self.always_show_transtale,
                self.show_popup,
                self.show_icon,
                show_homepage
            ),
            daemon=True
        )
        self.clipboard_thread.start()

    def set_startup(self, enable):
        """
        Bật/tắt khởi động cùng Windows cho phần mềm.
        """
        app_name = "VezylTranslator"
        exe_path = os.path.abspath(sys.argv[0])
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            ) as key:
                if enable:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except FileNotFoundError:
                        pass
        except Exception as e:
            print(f"Cannot start with windows: {e}")

    def load_config(self):
        """load file config"""
        default_config = get_default_config()
        config = load_config(self.config_file, default_config)
        self.interface_language = config.get('interface_language')
        self.start_at_startup = config.get('start_at_startup')
        self.show_homepage_at_startup = config.get('show_homepage_at_startup')
        self.always_show_transtale = config.get('always_show_transtale')
        self.save_translate_history = config.get('save_translate_history')
        self.auto_save_after = config.get('auto_save_after')
        self.icon_size = config.get('icon_size')
        self.icon_dissapear_after = config.get('icon_dissapear_after')
        self.popup_dissapear_after = config.get('popup_dissapear_after')
        self.max_length_on_popup = config.get('max_length_on_popup')
        self.max_history_items = config.get('max_history_items')
        self.hotkey = config.get('hotkey')
        self.clipboard_hotkey = config.get('clipboard_hotkey')
        self.dest_lang = config.get('dest_lang')
        self.font = config.get('font')
        self.default_fonts = config.get('default_fonts')
        self.lang_display = config.get('lang_display')
        # --- Đảm bảo trạng thái khởi động cùng Windows đúng với config ---
        self.set_startup(self.start_at_startup)

    def show_popup(self, text, x, y):
        constant.last_translated_text = text

        lang_display = self.lang_display
        lang_codes = list(lang_display.keys())
        display_to_code = {v: k for k, v in lang_display.items()}
        dest_lang = self.dest_lang

        # --- Tạo popup trước, hiển thị "Đang dịch..." ---
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
        frame.pack(padx=0, pady=0, fill="both", expand=True)

        # --- HEADER: icon yêu thích + "mở trong cửa sổ" ---
        header_frame = ctk.CTkFrame(frame, fg_color="#23272f", height=30)  # Giảm chiều cao header
        header_frame.pack(fill="x", padx=10, pady=(4, 0))  # Giảm padding trên

        # Load icon yêu thích (favorite) với kích thước nhỏ hơn
        try:
            fav_img = ctk.CTkImage(light_image=Image.open("resources/fav.png"), size=(18, 18))
        except Exception:
            fav_img = None
        try:
            fav_clicked_img = ctk.CTkImage(light_image=Image.open("resources/fav_clicked.png"), size=(18, 18))
        except Exception:
            fav_clicked_img = None

        favorite_icon_state = {"clicked": False}

        favorite_btn = ctk.CTkButton(
            header_frame,
            image=fav_img,
            text="",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color="#444",
            corner_radius=12  # nhỏ hơn
        )
        favorite_btn.pack(side="left", padx=(0, 6), pady=0)  # Giảm padding

        def on_favorite_click():
            log_file = "favorite_log.enc"
            key = get_aes_key(language_interface, theme_interface)
            now_text = text
            now_translated = label_trans.cget("text")
            # Nếu chưa lưu thì lưu, đổi icon sang history
            if not favorite_icon_state["clicked"]:
                src_lang_val = getattr(self, "last_src_lang", "auto")
                write_favorite_entry(
                    original_text=now_text,
                    translated_text=now_translated,
                    src_lang=src_lang_val,
                    dest_lang=dest_lang,
                    note="popup",
                    log_file=constant.FAVORITE_LOG_FILE,           # log_file
                    language_interface=language_interface,          # language_interface
                    theme_interface=theme_interface              # theme_interface
                )
                favorite_icon_state["clicked"] = True
                if fav_clicked_img:
                    favorite_btn.configure(image=fav_clicked_img)
            # Nếu đã lưu thì xóa, đổi icon về fav_img
            else:
                # Đọc lại toàn bộ log
                lines = []
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = [line.rstrip("\n") for line in f if line.strip()]
                # Giải mã và lọc bỏ bản ghi cần xóa (so sánh original_text và translated_text)
                new_lines = []
                for line in lines:
                    try:
                        log_json = decrypt_aes(line, key)
                        log_data = json.loads(log_json)
                        if not (
                            log_data.get("original_text") == now_text and
                            log_data.get("translated_text") == now_translated and
                            log_data.get("note") == "popup"
                        ):
                            new_lines.append(line)
                    except Exception:
                        new_lines.append(line)
                # Ghi lại log đã xóa
                with open(log_file, "w", encoding="utf-8") as f:
                    for l in new_lines:
                        f.write(l + "\n")
                favorite_icon_state["clicked"] = False
                if fav_img:
                    favorite_btn.configure(image=fav_img)
        favorite_btn.configure(command=on_favorite_click)

        # Nút "mở trong cửa sổ"
        open_label = ctk.CTkLabel(
            header_frame,
            text=_._("popup")["open_translate_page"],
            font=(self.font, 13, "underline"),
            text_color="#00ff99",
            cursor="hand2"
        )
        open_label.pack(side="left", padx=(0, 0))
        def on_open_click(event=None):
            popup.destroy()
            show_homepage()
        open_label.bind("<Button-1>", on_open_click)

        combo_src_lang = ctk.CTkComboBox(
            frame,
            values=[lang_display[code] for code in lang_codes],
            width=200,
            state="readonly"
        )
        combo_src_lang.pack(anchor="w", padx=10, pady=(10, 0))

        label_src_lang = ctk.CTkLabel(
            frame,
            text="Đang phát hiện...",
            text_color="#aaaaaa",
            font=(self.font, 14, "italic"),
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
            font=(self.font, 18, "bold")
        )
        label_src.pack(anchor="w", padx=10, pady=(0, 10))

        label_dest_lang = ctk.CTkLabel(
            frame,
            text=lang_display.get(dest_lang, dest_lang),
            text_color="#aaaaaa",
            font=(self.font, 14, "italic"),
            anchor="w"
        )
        label_dest_lang.pack(anchor="w", padx=10, pady=(0, 0))

        label_trans = ctk.CTkLabel(
            frame,
            text="Đang dịch...",
            fg_color="#23272f",
            text_color="#00ff99",
            padx=10, pady=5,
            wraplength=400,
            justify="left",
            font=(self.font, 18, "bold")
        )
        label_trans.pack(anchor="w", padx=10, pady=(0, 10))

        try:
            copy_img = ctk.CTkImage(light_image=Image.open("resources/save_btn.png"), size=(24, 24))
        except Exception:
            copy_img = None

        def on_copy_click():
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            set_clipboard_text(label_trans.cget("text"))

        copy_btn = ctk.CTkButton(
            frame,
            image=copy_img,
            text="",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#444",
            command=on_copy_click
        )
        # Đặt ở góc dưới phải popup
        copy_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)


        # --- Hàm cập nhật kết quả dịch ---
        def do_translate():
            try:
                # Sử dụng hàm dịch với model mặc định (không truyền model từ ngoài vào)
                result = translate_with_model(
                    text,
                    src_lang="auto",
                    dest_lang=dest_lang
                )
                translated = result["text"]
                src_lang = result["src"]
                src_lang_display = lang_display.get(src_lang, src_lang)
                # Cập nhật giao diện trên main thread
                popup.after(0, lambda: (
                    label_src_lang.configure(text=src_lang_display),
                    label_trans.configure(text=translated),
                    combo_src_lang.set(lang_display.get(src_lang, src_lang))
                ))
                # Ghi log
                write_log_entry(
                    constant.last_translated_text, 
                    src_lang, 
                    dest_lang, 
                    "popup", 
                    constant.TRANSLATE_LOG_FILE, 
                    language_interface, 
                    theme_interface
                )
            except Exception as e:
                popup.after(0, lambda: label_trans.configure(text=f"Lỗi dịch: {e}"))

        # Chạy dịch ở thread phụ
        threading.Thread(target=do_translate, daemon=True).start()

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
            popup_dissapear_after = self.popup_dissapear_after * 1000  # chuyển sang mili giây  
            if close_job[0]:
                popup.after_cancel(close_job[0])
            close_job[0] = popup.after(popup_dissapear_after, popup.destroy)

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
            self.Is_icon_showing = True

            # Lấy kích thước màn hình
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            icon_size = self.icon_size
            icon_dissapear_after = self.icon_dissapear_after *1000 # chuyển sang mili giây
            max_length_on_popup = self.max_length_on_popup
            """
            --- Định vị vị trí icon 
            """
            # Xác định vị trí icon đối xứng quanh chuột
            # Nếu chuột ở nửa trái -> icon bên phải chuột, ngược lại bên trái
            # Nếu chuột ở nửa trên -> icon dưới chuột, ngược lại trên chuột
            if x < screen_width // 2:
                icon_x = x + 30
            else:
                icon_x = x - icon_size - 30
            if y < screen_height // 2:
                icon_y = y + 30
            else:
                icon_y = y - icon_size - 30

            # Đảm bảo icon không ra ngoài màn hình
            icon_x = max(0, min(icon_x, screen_width - icon_size))
            icon_y = max(0, min(icon_y, screen_height - icon_size))

            icon_win = ctk.CTkToplevel(self.root)
            icon_win.wm_overrideredirect(True)
            icon_win.wm_attributes('-topmost', True)
            icon_win.wm_geometry(f"{icon_size}x{icon_size}+{icon_x}+{icon_y}")

            # Load icon từ file và resize thành hình vuông
            # icon dựa trên theme
            if get_windows_theme() == "dark":
                img = Image.open(os.path.join("resources", "logo.png"))
            else:
                img = Image.open(os.path.join("resources", "logo_black_bg.png"))
            width, height = img.size
            if width != height:
                size = min(width, height)
                left = (width - size) // 2
                top = (height - size) // 2
                img = img.crop((left, top, left + size, top + size))
            img = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(icon_size - 30, icon_size - 30))

            # Tạo label chứa icon
            img_label = ctk.CTkLabel(
                icon_win,
                text="",
                image=ctk_img,
                width=icon_size,
                height=icon_size,
                corner_radius=0,
                fg_color="transparent"
            )
            img_label.pack(fill="both", expand=True, padx=0, pady=0)

            def on_click(event):
                print(f"Clicked on icon at ({icon_x}, {icon_y})")
                self.Is_icon_showing = False
                icon_win.withdraw()
                # Popup cũng đối xứng quanh chuột như icon
                popup_x = icon_x
                popup_y = icon_y + icon_size + 10 if y < screen_height // 2 else icon_y - icon_size - 10
                if len(text) > max_length_on_popup:
                        constant.last_translated_text = text
                        def open_homepage():
                            show_homepage()
                        self.root.after(0, open_homepage)
                else:
                    self.show_popup(text, popup_x, popup_y)

            img_label.bind("<Button-1>", on_click)
            img_label.configure(cursor="hand2")

            def destroy_icon():
                self.Is_icon_showing = False
                icon_win.destroy()

            icon_win.after(icon_dissapear_after, destroy_icon)
            icon_win.lift()
            icon_win.after(100, lambda: icon_win.attributes('-alpha', 0.9))

        except Exception as e:
            self.Is_icon_showing = False
            print(f"Lỗi show_icon: {e}", file=sys.stderr)


language_interface, theme_interface = get_client_preferences()






main_window_instance = None  # Biến toàn cục lưu MainWindow
translator_instance = None   # Biến toàn cục lưu Translator
tmp_clipboard = ""
tray_icon_instance = None   # Biến toàn cục lưu instance của Translator

def show_homepage():
    global main_window_instance, translator_instance
    if main_window_instance is not None:
        try:
            root = main_window_instance if hasattr(main_window_instance, 'after') else translator_instance.root
            def bring_window_to_front():
                main_window_instance.state('normal')
                main_window_instance.deiconify()
                main_window_instance.lift()
                main_window_instance.focus_force()
                main_window_instance.show_tab_home()
                # Kiểm tra liên tục cho đến khi fill thành công
                def try_fill():
                    if constant.last_translated_text != "":
                        print(f"Trying to fill homepage with:")
                        filled = main_window_instance.fill_homepage_text(constant.last_translated_text)
                        if not filled:
                            main_window_instance.after(100, try_fill)
                main_window_instance.after(100, try_fill)
            root.after(0, bring_window_to_front)
        except Exception as e:
            sys.excepthook(*sys.exc_info())
    else:
        print("Cua so chinh chua duoc khoi tao")

def toggle_clipboard_watcher(icon=None, item=None):
    global translator_instance, tray_icon_instance
    
    if translator_instance is not None:
        translator_instance.clipboard_watcher_enabled = not getattr(translator_instance, "clipboard_watcher_enabled", True)
        state = "ON" if translator_instance.clipboard_watcher_enabled else "OFF"
        print(f"Clipboard watcher toggled: {state}")
        
        # Sử dụng icon từ tham số hoặc biến toàn cục
        update_icon = icon if icon is not None else tray_icon_instance
        
        # Phát âm thanh thông báo
        if translator_instance.clipboard_watcher_enabled:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            winsound.MessageBeep(winsound.MB_ICONHAND)
        
        # Đổi icon tray theo trạng thái
        if update_icon is not None:
            try:
                # Tạo đối tượng Image mới cho icon
                if not translator_instance.clipboard_watcher_enabled:
                    new_icon = Image.open("resources/logo_red.ico")
                else:
                    if get_windows_theme() == "dark":
                        new_icon = Image.open("resources/logo.ico")
                    else:
                        new_icon = Image.open("resources/logo_black.ico")
                update_icon.icon = new_icon
                # Force icon to refresh
                update_icon.visible = False
                time.sleep(0.1)  # Đợi một chút
                update_icon.visible = True
                print(f"Icon updated to {'red' if not translator_instance.clipboard_watcher_enabled else 'normal'}")
            except Exception as e:
                print(f"Error updating icon: {e}")

def start_hotkey_listener():
    """Initialize all hotkey listeners using the configured hotkeys."""
    global translator_instance

    # Hotkey mở homepage
    register_hotkey(
        "homepage",
        translator_instance.hotkey,
        lambda: show_homepage()
    )

    # Hotkey bật/tắt clipboard watcher
    register_hotkey(
        "clipboard",
        translator_instance.clipboard_hotkey,
        toggle_clipboard_watcher
    )
    

def main():
    global translator_instance, main_window_instance
    translator_instance = Translator()
    main_window_instance = MainWindow(
    translator_instance,
    language_interface,
    theme_interface,
    _
)
    translator_instance.main_window = main_window_instance
    start_hotkey_listener()

    if translator_instance.show_homepage_at_startup:
        # Ensure window is visible with multiple approaches
        main_window_instance.deiconify()
        main_window_instance.lift()
        main_window_instance.focus_force()
        
        # Add a delayed show as backup to ensure window appears
        main_window_instance.after(1000, lambda: ensure_window_visible())
    else:
        main_window_instance.withdraw()

    def ensure_window_visible():
        if translator_instance.show_homepage_at_startup:
            main_window_instance.deiconify()
            main_window_instance.lift()
            main_window_instance.focus_force()
            main_window_instance.update()
            
    # Khởi động tray icon
    menu_texts = _._("menu_tray")
    run_tray_icon_in_thread(
        constant.SOFTWARE,
        get_windows_theme,
        toggle_clipboard_watcher,
        show_homepage,
        on_quit,
        menu_texts
    )

    # Chạy mainloop của MainWindow (main thread)
    main_window_instance.mainloop()

def on_homepage(icon, item):
    global main_window_instance
    if main_window_instance is not None:
        try:
            main_window_instance.after(0, show_homepage)
        except Exception as e:
            print(f"Loi hien thi cua so chinh: {e}")
            sys.excepthook(*sys.exc_info())
    else:
        print("Cua so chinh chua duoc khoi tao")

def on_quit(icon, item):
    icon.stop()
    os._exit(0)

if __name__ == "__main__":
    main()