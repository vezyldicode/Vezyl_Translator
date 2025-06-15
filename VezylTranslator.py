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
        "VezylsTranslatorCrashHandler.exe",
        error_msg,
        SOFTWARE,
        SOFTWARE_VERSION
    ])
    os._exit(1)

sys.excepthook = external_crash_handler

import pyperclip
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
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from pystray import Icon, MenuItem, Menu
import keyboard
import toml
import importlib.util
from VezylTranslatorProton.file_flow import *
import VezylTranslatorProton.locale_module  as _

SOFTWARE = "Vezyl Translator"
SOFTWARE_VERSION = "1.0.0 alpha"



def get_windows_theme():
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value == 1 else "dark"
    except Exception as e:
        return f"unknown ({e})"

def translate_with_model(text, src_lang="auto", dest_lang="vi", model=None):
    """
    Hàm dịch trung gian, dễ thay đổi model dịch sau này.
    """
    if not model:
        model = GoogleTranslator()
        print("Google Translator")
    else:
        print("Using custom model:", model)
    try:
        print("trying to translate")
        if src_lang == "auto":
            result = model.translate(text, dest=dest_lang)
        else:
            result = model.translate(text, src=src_lang, dest=dest_lang)
        return {
            "text": result.text,
            "src": result.src,
            "dest": dest_lang
        }
    except Exception as e:
        return {
            "text": f"Lỗi dịch: {e}",
            "src": src_lang,
            "dest": dest_lang
        }

def show_confirm_popup(parent, title, message, on_confirm, on_cancel=None, width=420, height=180):
    """
    Hiển thị popup xác nhận với giao diện đồng nhất CustomTkinter, không có thanh window, viền mỏng đẹp.
    """
    confirm = ctk.CTkToplevel(parent)
    confirm.title(title)
    confirm.resizable(False, False)
    confirm.overrideredirect(True)  # Bỏ thanh window
    # Đặt vị trí giữa parent
    parent.update_idletasks()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()
    x = parent_x + (parent_w - width) // 3
    y = parent_y + (parent_h - height) // 2
    confirm.geometry(f"{width}x{height}+{x}+{y}")
    confirm.transient(parent)
    confirm.grab_set()
    confirm.configure(bg="#23272f")  # Nền đồng nhất

    # Frame chính với border mỏng và bo góc nhẹ
    main_frame = ctk.CTkFrame(
        confirm,
        fg_color="#23272f",
        border_color="#333",
        border_width=1,
        corner_radius=10
    )
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)  # Không padding ngoài

    # Tiêu đề
    title_label = ctk.CTkLabel(
        main_frame,
        text=title,
        font=(parent.translator.font, 17, "bold"),
        text_color="#00ff99"
    )
    title_label.pack(pady=(18, 2))
    # Nội dung
    msg_label = ctk.CTkLabel(
        main_frame,
        text=message,
        font=(parent.translator.font, 14),
        text_color="#f5f5f5",
        wraplength=width-60,
        justify="center"
    )
    msg_label.pack(pady=(8, 18), padx=18, fill="x")
    # Nút xác nhận/hủy
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.pack(pady=(0, 10))
    def confirm_and_close():
        confirm.destroy()
        if on_confirm:
            on_confirm()
    def cancel_and_close():
        confirm.destroy()
        if on_cancel:
            on_cancel()
    confirm_btn = ctk.CTkButton(
        btn_frame, text=_._("confirm_popup")["confirm"], width=120, fg_color="#00ff99", text_color="#23272f",
        font=(parent.translator.font, 13, "bold"), command=confirm_and_close
    )
    confirm_btn.pack(side="left", padx=12)
    cancel_btn = ctk.CTkButton(
        btn_frame, text=_._("confirm_popup")["cancel"], width=120, fg_color="#444", text_color="#f5f5f5",
        font=(parent.translator.font, 13), command=cancel_and_close
    )
    cancel_btn.pack(side="left", padx=12)
    confirm.focus_set()
    confirm.wait_window()
    return confirm


class MainWindow(ctk.CTkToplevel):
    def __init__(self, translator: 'Translator'):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.translator = translator
        self.title(SOFTWARE + " " + SOFTWARE_VERSION)
        # self.wm_iconbitmap("resources/logo.ico")
        # Lấy theme của máy user
        self.theme = get_windows_theme()
        # Nếu theme là "dark" thì dùng dark mode, ngược lại dùng light mode
        if self.theme == "dark":
            try:
                self.after(200, lambda: self.wm_iconbitmap("resources/logo.ico"))
            except:
                print("Không thể load icon")
        else:
            try:
                self.after(200, lambda: self.wm_iconbitmap("resources/logo_black_bg.ico"))
            except:
                print("Không thể load icon")

        # Sửa kích thước cửa sổ theo 2 biến self.wide và self.height
        self.width = 900
        self.height = 600
        self.geometry(f"{self.width}x{self.height}")
        # self.bind("<Unmap>", lambda event: self.on_close() if self.state() == "iconic" else None)
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
        self.ctrl_pressed = False
        self.bind_all('<Control_L>', self._ctrl_down)
        self.bind_all('<Control_R>', self._ctrl_down)
        self.bind_all('<KeyRelease-Control_L>', self._ctrl_up)
        self.bind_all('<KeyRelease-Control_R>', self._ctrl_up)

    def build_ui(self):
        # Nav bar
        self.nav_bar = ctk.CTkFrame(self, width=70, fg_color="#23272f")
        self.nav_bar.pack(side="left", fill="y")
        self.nav_buttons = {}

        icons = [
            ("resources/logo.png", "Trang chủ"),
            ("resources/history.png", "Lịch sử"),
            ("resources/favorite.png", "Yêu thích"),
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
            settings_img = ctk.CTkImage(light_image=Image.open("resources/settings.png"), size=(32, 32))
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
        global tmp_clipboard, last_translated_text
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        lang_display = self.translator.lang_display
        lang_codes = list(lang_display.keys())

        # --- Layout tối giản: nhập trên, dịch dưới ---
        frame = ctk.CTkFrame(self.content_frame, 
                             fg_color="#23272f")
        frame.pack(fill="both", expand=True, padx=60, pady=60)

        frame.grid_rowconfigure(1, weight=1)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        # Combobox chọn ngôn ngữ nguồn
        src_lang_var = tk.StringVar(value="auto")
        src_lang_combo = ctk.CTkComboBox(
            frame,
            values=[_._("home")["auto_detect"]] + [lang_display[code] for code in lang_codes],
            width=180,
            state="readonly",
            variable=src_lang_var,
            font=(self.translator.font, 13),
            command=lambda _: on_text_change()  # Gọi lại dịch khi chọn ngôn ngữ nguồn
        )
        src_lang_combo.grid(row=0, column=0, sticky="w", pady=(0, 5))
        src_lang_combo.set(_._("home")["auto_detect"])

        # --- Frame chứa textbox nhập và nút copy ---
        src_text_frame = ctk.CTkFrame(frame, fg_color="#23272f")
        src_text_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 10))
        src_text_frame.grid_rowconfigure(0, weight=1)
        src_text_frame.grid_columnconfigure(0, weight=1)

        src_text = ctk.CTkTextbox(
            src_text_frame, font=(self.translator.font, 18, "bold"),
            wrap="word", fg_color="#23272f", text_color="#f5f5f5", border_width=0
        )
        src_text.grid(row=0, column=0, sticky="nsew")

        try:
            copy_img = ctk.CTkImage(light_image=Image.open("resources/save_btn.png"), size=(24, 24))
        except Exception:
            copy_img = None
        copy_src_btn = ctk.CTkButton(
            src_text_frame,
            image=copy_img,
            text="",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#444",
            command=lambda: pyperclip.copy(src_text.get("1.0", "end").strip())
        )
        copy_src_btn.grid(row=1, column=0, sticky="w", padx=(4, 0), pady=(0, 6))

        # nút dịch ngược nằm ở góc dưới phải textbox nhập nội dung
        try:
            reverse_img = ctk.CTkImage(light_image=Image.open("resources/reverse.png"), size=(24, 24))
        except Exception:
            reverse_img = None
        reverse_button = ctk.CTkButton(
            frame,
            image=reverse_img,
            text="",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#444",
            command=lambda: reverse_translate()
        )
        reverse_button.grid(row=1, column=0, sticky="se", padx=(0, 0), pady=(0, 10))

        # --- TỰ ĐỘNG FILL last_translated_text khi mở homepage ---
        if last_translated_text:
            src_text.delete("1.0", "end")
            src_text.insert("1.0", last_translated_text)

        # Frame chứa combobox ngôn ngữ đích và textbox dịch
        dest_frame = ctk.CTkFrame(frame, fg_color="#181a20")
        dest_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=(0, 0))
        dest_frame.grid_rowconfigure(0, weight=0)
        dest_frame.grid_rowconfigure(1, weight=1)
        dest_frame.grid_columnconfigure(0, weight=1)

        # Combobox ngôn ngữ đích ở góc trên trái của textbox dịch
        dest_lang_var = tk.StringVar(value=lang_display.get(self.translator.dest_lang, "🇻🇳 Tiếng Việt"))
        dest_lang_combo = ctk.CTkComboBox(
            dest_frame,
            values=[lang_display[code] for code in lang_codes],
            width=180,
            state="readonly",
            variable=dest_lang_var,
            font=(self.translator.font, 13),
            command=lambda _: on_text_change()  # Gọi lại dịch khi chọn ngôn ngữ đích
        )
        dest_lang_combo.grid(row=0, column=0, sticky="w", padx=(0, 0), pady=(0, 0))
        dest_lang_combo.set(lang_display.get(self.translator.dest_lang, "🇻🇳 Tiếng Việt"))

        # --- Frame chứa textbox dịch và nút copy ---
        dest_text_frame = ctk.CTkFrame(dest_frame, fg_color="#181a20")
        dest_text_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(5, 0))
        dest_text_frame.grid_rowconfigure(0, weight=1)
        dest_text_frame.grid_columnconfigure(0, weight=1)

        dest_text = ctk.CTkTextbox(
            dest_text_frame, font=(self.translator.font, 18, "bold"),
            wrap="word", fg_color="#181a20", text_color="#00ff99", border_width=0, state="disabled"
        )
        dest_text.grid(row=0, column=0, sticky="nsew")

        copy_dest_btn = ctk.CTkButton(
            dest_text_frame,
            image=copy_img,
            text="",
            width=36,
            height=36,
            fg_color="transparent",
            hover_color="#444",
            command=lambda: pyperclip.copy(dest_text.get("1.0", "end").strip())
        )
        copy_dest_btn.grid(row=1, column=0, sticky="w", padx=(4, 0), pady=(0, 6))

        # Hàm dịch ngược lại (từ đích về nguồn)
        def reverse_translate():
            # Lấy nội dung kết quả dịch
            dest_content = dest_text.get("1.0", "end").strip()
            if not dest_content:
                return
            # Lấy giá trị hiện tại của combobox
            src_lang_display = src_lang_var.get()
            dest_lang_display = dest_lang_var.get()
            # Đổi chỗ src và dest lang cho combobox
            src_lang_var.set(dest_lang_display)
            dest_lang_var.set(src_lang_display)
            src_lang_combo.set(dest_lang_display)
            dest_lang_combo.set(src_lang_display)
            # Đưa nội dung kết quả dịch lên textbox nhập
            src_text.delete("1.0", "end")
            src_text.insert("1.0", dest_content)
            # Gọi dịch lại
            on_text_change()

        # --- Logic dịch tự động khi thay đổi nội dung hoặc ngôn ngữ ---
        def on_text_change(event=None):
            print("Text changed, updating translation...")
            text = src_text.get("1.0", "end").strip()
            src_lang_display = src_lang_var.get()
            if src_lang_display == _._("home")["auto_detect"]:
                src_lang = "auto"
            else:
                src_lang = next((k for k, v in lang_display.items() if v == src_lang_display), "auto")
            dest_lang_display = dest_lang_var.get()
            dest_lang = next((k for k, v in lang_display.items() if v == dest_lang_display), self.translator.dest_lang)

            def do_translate():
                if text:
                    try:
                        result = translate_with_model(text, src_lang, dest_lang, self.translator.translator)
                        translated = result["text"]
                        src = result["src"]
                        def update_ui():
                            # Kiểm tra widget còn tồn tại không
                            if not dest_text.winfo_exists():
                                return
                            if src_lang == "auto":
                                src_lang_combo.set(lang_display.get(src, src))
                            dest_text.configure(state="normal")
                            dest_text.delete("1.0", "end")
                            dest_text.insert("1.0", translated)
                            dest_text.configure(state="disabled")
                        dest_text.after(0, update_ui)
                    except Exception as e:
                        def update_ui():
                            if not dest_text.winfo_exists():
                                return
                            dest_text.configure(state="normal")
                            dest_text.delete("1.0", "end")
                            dest_text.insert("1.0", f"Lỗi dịch: {e}")
                            dest_text.configure(state="disabled")
                        dest_text.after(0, update_ui)
                else:
                    def update_ui():
                        if not dest_text.winfo_exists():
                            return
                        src_lang_combo.set(_._("home")["auto_detect"])
                        dest_text.configure(state="normal")
                        dest_text.delete("1.0", "end")
                        dest_text.configure(state="disabled")
                    dest_text.after(0, update_ui)
                reset_auto_save()
            threading.Thread(target=do_translate, daemon=True).start()

        # Debounce khi nhập liệu
        def debounce_text_change(*args):
            if hasattr(debounce_text_change, "after_id") and debounce_text_change.after_id:
                src_text.after_cancel(debounce_text_change.after_id)
            debounce_text_change.after_id = src_text.after(250, on_text_change)
        debounce_text_change.after_id = None

        src_text.bind("<<Modified>>", lambda e: (src_text.edit_modified(0), debounce_text_change()))
        src_text.bind("<KeyRelease>", lambda e: debounce_text_change())

        # --- TỰ ĐỘNG LƯU last_translated_text ---
        auto_save_state = {"saved": False, "timer_id": None, "last_content": ""}

        def save_last_translated_text():
            global last_translated_text
            text = src_text.get("1.0", "end").strip()
            if text:
                last_translated_text = text
                auto_save_state["saved"] = True
                print("Auto-saved last_translated_text:")
                # Ghi log khi lưu trên homepage
                src_lang_display = src_lang_var.get()
                if src_lang_display == _._("home")["auto_detect"]:
                    src_lang = "auto"
                else:
                    src_lang = next((k for k, v in lang_display.items() if v == src_lang_display), "auto")
                dest_lang_display = dest_lang_var.get()
                dest_lang = next((k for k, v in lang_display.items() if v == dest_lang_display), self.translator.dest_lang)
                write_log_entry(
                    last_translated_text,
                    src_lang,
                    dest_lang,
                    "homepage"
                )

        def start_auto_save_timer():
            if auto_save_state["timer_id"]:
                src_text.after_cancel(auto_save_state["timer_id"])
            auto_save_state["timer_id"] = src_text.after(self.translator.auto_save_after, save_last_translated_text)

        def reset_auto_save():
            auto_save_state["saved"] = False
            auto_save_state["last_content"] = src_text.get("1.0", "end").strip()
            start_auto_save_timer()

        def on_src_text_key(event):
            # Nếu đã auto-save rồi, chỉ reset khi nội dung thay đổi
            current = src_text.get("1.0", "end").strip()
            if not auto_save_state["saved"]:
                start_auto_save_timer()
            elif current != auto_save_state["last_content"]:
                reset_auto_save()
            # Nếu bấm Enter thì lưu luôn
            if event.keysym == "Return" and not auto_save_state["saved"]:
                save_last_translated_text()

        src_text.bind("<KeyRelease>", on_src_text_key)

        # Khi mở homepage, reset auto-save state
        reset_auto_save()

    def show_tab_history(self):
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # --- Thanh tiêu đề và search ---
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(side="top", fill="x", padx=60, pady=(20, 0))

        title = ctk.CTkLabel(title_frame, 
                             text=_._("history")["title"], 
                             font=(self.translator.font, 20, "bold"), text_color="#00ff99")
        title.pack(side="left", anchor="w")

        # --- Thanh search ---
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="🔍 Tìm kiếm...",
            textvariable=search_var,
            width=260,
            font=(self.translator.font, 14)
        )
        search_entry.pack(side="right", padx=(0, 0), pady=0)

        # --- Frame chứa phần cuộn (canvas + scrollbar) ---
        scrollable_frame = ctk.CTkFrame(self.content_frame, fg_color="#23272f")
        scrollable_frame.pack(fill="both", expand=True, padx=60, pady=(10, 60))

        canvas = tk.Canvas(scrollable_frame, bg="#23272f", highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(scrollable_frame, orientation="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # --- Frame chứa các bản ghi lịch sử ---
        history_frame = ctk.CTkFrame(canvas, fg_color="#23272f")
        window_id = canvas.create_window((0, 0), window=history_frame, anchor="nw")

        # Đọc và giải mã log
        log_file = TRANSLATE_LOG_FILE
        history = []
        key = get_aes_key(language_interface, theme_interface)
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        log_json = decrypt_aes(line, key)
                        log_data = json.loads(log_json)
                        history.append(log_data)
                    except Exception as e:
                        print(f"Loi giai ma log: {e}")
        def delete_all_history_entries():
            show_confirm_popup(
                self,
                _._("confirm_popup")["title"],
                _._("history")["menu"]["delete_confirm"],
                on_confirm=lambda: (
                    ensure_local_dir(),
                    open(TRANSLATE_LOG_FILE, "w", encoding="utf-8").close() if os.path.exists(TRANSLATE_LOG_FILE) else None,
                    self.show_tab_history()
                )
            )

        # --- Hàm render danh sách history theo search ---
        def render_history_list():
            for widget in history_frame.winfo_children():
                widget.destroy()
            keyword = search_var.get()
            filtered = search_entries(history, keyword, ["last_translated_text", "translated_text"])
            if not filtered:
                ctk.CTkLabel(history_frame, text=_._("history")["empty"],
                              font=(self.translator.font, 15)).grid(row=1, column=0, columnspan=2, pady=20)
                return
            history_frame.grid_columnconfigure(1, weight=1)
            last_date = None
            row_idx = 1
            for item in reversed(filtered[-50:]):
                time_str = item.get("time", "")
                content = item.get("last_translated_text", "")
                src_lang = item.get("src_lang", "")
                dest_lang = item.get("dest_lang", "")
                date_str = time_str.split(" ")[0] if time_str else ""
                show_date = False
                if date_str != last_date:
                    show_date = True
                    last_date = date_str

                # Cột ngày (chỉ hiện nếu là bản ghi đầu tiên của ngày)
                if show_date:
                    date_label = ctk.CTkLabel(
                        history_frame,
                        text=date_str,
                        font=(self.translator.font, 14, "bold"),
                        text_color="#00ff99",
                        width=110,
                        anchor="w"
                    )
                    date_label.grid(row=row_idx, column=0, sticky="nw", padx=(0, 16), pady=(8, 0))
                else:
                    date_label = ctk.CTkLabel(
                        history_frame,
                        text="",
                        font=(self.translator.font, 14),
                        width=110
                    )
                    date_label.grid(row=row_idx, column=0, sticky="nw", padx=(0, 16))

                # Cột nội dung: frame mở rộng hết chiều ngang
                entry_frame = ctk.CTkFrame(
                    history_frame,
                    fg_color="#23272f",
                    border_width=1,
                    border_color="#444",
                    corner_radius=8
                )
                entry_frame.grid(row=row_idx, column=1, sticky="ew", pady=6, padx=0)
                entry_frame.grid_columnconfigure(0, weight=1)
                # Thời gian và src_lang
                info_label = ctk.CTkLabel(entry_frame, text=f"{time_str[11:]} | {src_lang}", font=(self.translator.font, 12, "italic"), text_color="#888")
                info_label.grid(row=0, column=0, sticky="w", padx=10, pady=(4,0))
                # Nội dung: không wraplength, sticky "w", mở rộng hết frame
                content_label = ctk.CTkLabel(
                    entry_frame,
                    text=content,
                    font=(self.translator.font, 15),
                    text_color="#f5f5f5",
                    anchor="w",
                    justify="left"
                )
                content_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,8))

                # --- Thêm sự kiện nhấn đúp ---
                def on_double_click(event, s=src_lang, d=dest_lang, c=content):
                    self.open_entry_in_homepage(s, d, c)
                entry_frame.bind("<Double-Button-1>", on_double_click)
                content_label.bind("<Double-Button-1>", on_double_click)
                info_label.bind("<Double-Button-1>", on_double_click)

                # --- Thêm menu chuột phải ---
                def show_context_menu(event, t=time_str, c=content, s=src_lang, d=dest_lang, item=item):
                    menu = tk.Menu(self, tearoff=0)
                    menu.add_command(label=_._("history")["menu"]["delete"],
                                      command=lambda: delete_history_entry(t, c))
                    menu.add_command(
                        label=_._("history")["menu"]["add_to_favorite"],
                        command=lambda: write_favorite_entry(
                            original_text=c,
                            translated_text=item.get("translated_text", ""),  # Nếu có trường này trong log
                            src_lang=s,
                            dest_lang=d,
                            note=""
                        )
                    )
                    menu.add_separator()
                    menu.add_command(label=_._("history")["menu"]["delete_all"], command=delete_all_history_entries)
                    menu.tk_popup(event.x_root, event.y_root)
                entry_frame.bind("<Button-3>", lambda e, t=time_str, c=content, s=src_lang, d=dest_lang, item=item: show_context_menu(e, t, c, s, d, item))
                content_label.bind("<Button-3>", lambda e, t=time_str, c=content, s=src_lang, d=dest_lang, item=item: show_context_menu(e, t, c, s, d, item))
                info_label.bind("<Button-3>", lambda e, t=time_str, c=content, s=src_lang, d=dest_lang, item=item: show_context_menu(e, t, c, s, d, item))

                # --- Thêm hiệu ứng hover ---
                def on_enter(event, frame=entry_frame):
                    frame.configure(fg_color="#181a20")
                def on_leave(event, frame=entry_frame):
                    frame.configure(fg_color="#23272f")
                entry_frame.bind("<Enter>", on_enter)
                entry_frame.bind("<Leave>", on_leave)
                content_label.bind("<Enter>", on_enter)
                content_label.bind("<Leave>", on_leave)
                info_label.bind("<Enter>", on_enter)
                info_label.bind("<Leave>", on_leave)
                row_idx += 1
            def delete_history_entry(time_str, last_translated_text):
                """
                Xóa một entry khỏi lịch sử dịch dựa trên time và last_translated_text.
                """
                log_file = TRANSLATE_LOG_FILE
                key = get_aes_key(language_interface, theme_interface)
                lines = []
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = [line.rstrip("\n") for line in f if line.strip()]
                new_lines = []
                for line in lines:
                    try:
                        log_json = decrypt_aes(line, key)
                        log_data = json.loads(log_json)
                        if not (log_data.get("time") == time_str and log_data.get("last_translated_text") == last_translated_text):
                            new_lines.append(line)
                    except Exception:
                        new_lines.append(line)
                with open(log_file, "w", encoding="utf-8") as f:
                    for l in new_lines:
                        f.write(l + "\n")
                self.show_tab_history()  # Cập nhật lại danh sách

        # --- Cập nhật scrollregion khi thay đổi kích thước ---
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        history_frame.bind("<Configure>", on_configure)

        # --- Đảm bảo canvas luôn fill chiều ngang ---
        def resize_canvas(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", resize_canvas)

        # --- Bắt sự kiện cuộn chuột ---
        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Gọi lại render khi search thay đổi ---
        search_var.trace_add("write", lambda *args: render_history_list())

        # --- Render lần đầu ---
        render_history_list()

    def show_tab_favorite(self):
        # Xóa nội dung cũ
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # --- Thanh tiêu đề và search ---
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(side="top", fill="x", padx=60, pady=(20, 0))

        title = ctk.CTkLabel(title_frame, 
                             text=_._("favorite")["title"], 
                             font=(self.translator.font, 20, "bold"), 
                             text_color="#00ff99")
        title.pack(side="left", anchor="w")

        # --- Thanh search ---
        search_var = tk.StringVar()
        search_entry = ctk.CTkEntry(
            title_frame,
            placeholder_text="🔍 Tìm kiếm...",
            textvariable=search_var,
            width=260,
            font=(self.translator.font, 14)
        )
        search_entry.pack(side="right", padx=(0, 0), pady=0)

        # --- Frame chứa phần cuộn (canvas + scrollbar) ---
        scrollable_frame = ctk.CTkFrame(self.content_frame, 
                                        fg_color="#23272f")
        scrollable_frame.pack(fill="both", expand=True, padx=60, pady=(10, 60))

        canvas = tk.Canvas(scrollable_frame, 
                           bg="#23272f", 
                           highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(scrollable_frame, 
                                     orientation="vertical", 
                                     command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # --- Frame chứa các bản ghi yêu thích ---
        favorite_frame = ctk.CTkFrame(canvas, fg_color="#23272f")
        window_id = canvas.create_window((0, 0), window=favorite_frame, anchor="nw")

        # Đọc và giải mã log yêu thích
        log_file = FAVORITE_LOG_FILE
        favorites = []
        key = get_aes_key(language_interface, theme_interface)
        if os.path.exists(log_file):
            with open(log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        log_json = decrypt_aes(line, key)
                        log_data = json.loads(log_json)
                        favorites.append(log_data)
                    except Exception as e:
                        print(f"cannot favorite: {e}")

        # --- Hàm render danh sách favorite theo search ---
        def render_favorite_list():
            # Xóa cũ
            for widget in favorite_frame.winfo_children():
                widget.destroy()
            # Lọc theo search
            keyword = search_var.get()
            filtered = search_entries(favorites, keyword, ["original_text", "translated_text", "note"])
            # Hiển thị danh sách
            if not filtered:
                ctk.CTkLabel(favorite_frame,
                              text=_._("favorite")["empty"], 
                              font=(self.translator.font, 15)).grid(row=0, column=0, columnspan=2, pady=20)
                return
            favorite_frame.grid_columnconfigure(1, weight=1)
            last_date = None
            row_idx = 0
            def delete_favorite_entry(time_str, original_text):
                log_file = FAVORITE_LOG_FILE
                key = get_aes_key(language_interface, theme_interface)
                # Đọc lại toàn bộ log
                lines = []
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = [line.rstrip("\n") for line in f if line.strip()]
                # Giải mã và lọc bỏ bản ghi cần xóa
                new_lines = []
                for line in lines:
                    try:
                        log_json = decrypt_aes(line, key)
                        log_data = json.loads(log_json)
                        if not (log_data.get("time") == time_str and log_data.get("original_text") == original_text):
                            new_lines.append(line)
                    except Exception:
                        new_lines.append(line)
                # Ghi lại log đã xóa
                with open(log_file, "w", encoding="utf-8") as f:
                    for l in new_lines:
                        f.write(l + "\n")
                # Refresh lại tab yêu thích
                self.show_tab_favorite()
            
            # Hàm xóa tất cả yêu thích với xác nhận
            def delete_all_favorite_entries():
                show_confirm_popup(
                    self,
                    _._("confirm_popup")["title"],
                    _._("favorite")["menu"]["delete_confirm"],
                    on_confirm=lambda: (
                        ensure_local_dir(),
                        open(FAVORITE_LOG_FILE, "w", encoding="utf-8").close() if os.path.exists(FAVORITE_LOG_FILE) else None,
                        self.show_tab_favorite()
                    )
                )

            for item in reversed(filtered[-100:]):
                time_str = item.get("time", "")
                original_text = item.get("original_text", "")
                translated_text = item.get("translated_text", "")
                src_lang = item.get("src_lang", "")
                dest_lang = item.get("dest_lang", "")
                note = item.get("note", "")
                date_str = time_str.split(" ")[0] if time_str else ""
                show_date = False
                if date_str != last_date:
                    show_date = True
                    last_date = date_str

                # Cột ngày (chỉ hiện nếu là bản ghi đầu tiên của ngày)
                if show_date:
                    date_label = ctk.CTkLabel(
                        favorite_frame,
                        text=date_str,
                        font=(self.translator.font, 14, "bold"),
                        text_color="#00ff99",
                        width=110,
                        anchor="w"
                    )
                    date_label.grid(row=row_idx, column=0, sticky="nw", padx=(0, 16), pady=(8, 0))
                    row_idx += 1

                # Cột nội dung: frame mở rộng hết chiều ngang
                entry_frame = ctk.CTkFrame(
                    favorite_frame,
                    fg_color="#23272f",
                    border_width=1,
                    border_color="#444",
                    corner_radius=8
                )
                entry_frame.grid(row=row_idx, column=1, sticky="ew", pady=6, padx=0)
                entry_frame.grid_columnconfigure(0, weight=1)
                # Header: thời gian và (src_lang -> dest_lang)
                lang_display = self.translator.lang_display
                src_disp = lang_display.get("src_Lang", 'src_lang')
                dest_disp = lang_display.get(dest_lang, 'dest_Lang')
                info_label = ctk.CTkLabel(
                    entry_frame,
                    text=f"{time_str[11:]} | {src_disp} → {dest_disp}",
                    font=(self.translator.font, 12, "italic"),
                    text_color="#888"
                )
                info_label.grid(row=0, column=0, sticky="w", padx=10, pady=(4,0))
                # Nội dung gốc
                content_label = ctk.CTkLabel(
                    entry_frame,
                    text=original_text,
                    font=(self.translator.font, 15),
                    text_color="#f5f5f5",
                    anchor="w",
                    justify="left"
                )
                content_label.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,4))
                # Nội dung dịch (màu xanh lá)
                translated_label = ctk.CTkLabel(
                    entry_frame,
                    text=translated_text,
                    font=(self.translator.font, 15, "bold"),
                    text_color="#00ff99",
                    anchor="w",
                    justify="left"
                )
                translated_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(0,8))
                # Nếu có ghi chú thì hiển thị nhỏ bên dưới
                note_var = tk.StringVar(value=note)
                note_entry = ctk.CTkEntry(
                    entry_frame,
                    textvariable=note_var,
                    font=(self.translator.font, 12, "italic"),
                    width=400
                )
                note_entry.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
                def on_double_click(event, s=src_lang, d=dest_lang, c=original_text):
                    self.open_entry_in_homepage(s, d, c)
                entry_frame.bind("<Double-Button-1>", on_double_click)
                content_label.bind("<Double-Button-1>", on_double_click)
                translated_label.bind("<Double-Button-1>", on_double_click)
                info_label.bind("<Double-Button-1>", on_double_click)
                def save_note(event, entry_time, note_var):
                    new_note = note_var.get()
                    log_file = FAVORITE_LOG_FILE
                    key = get_aes_key(language_interface, theme_interface)
                    # Đọc và giải mã toàn bộ log
                    lines = []
                    entries = []
                    if os.path.exists(log_file):
                        with open(log_file, "r", encoding="utf-8") as f:
                            for line in f:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    log_json = decrypt_aes(line, key)
                                    log_data = json.loads(log_json)
                                    entries.append((log_data, line))
                                except Exception:
                                    entries.append((None, line))
                    # Sửa note cho entry đúng time
                    new_lines = []
                    for log_data, old_line in entries:
                        if log_data and log_data.get("time") == entry_time:
                            log_data["note"] = new_note
                            log_line = json.dumps(log_data, ensure_ascii=False)
                            enc_line = encrypt_aes(log_line, key)
                            new_lines.append(enc_line)
                        else:
                            new_lines.append(old_line)
                    # Ghi lại file
                    with open(log_file, "w", encoding="utf-8") as f:
                        for l in new_lines:
                            f.write(l + "\n")
                    self.show_tab_favorite()  # Gọi lại hàm để cập nhật giao diện

                note_entry.bind("<Return>", lambda event, entry_time=time_str, note_var=note_var: save_note(event, entry_time, note_var))
                # --- Thêm menu chuột phải ---
                def show_context_menu(event, t=time_str, o=original_text):
                    menu = tk.Menu(self, tearoff=0)
                    menu.add_command(label=_._("favorite")["menu"]["delete"], 
                                     command=lambda: delete_favorite_entry(t, o))
                    menu.add_separator()
                    menu.add_command(label=_._("favorite")["menu"]["delete_all"], command=delete_all_favorite_entries)
                    menu.tk_popup(event.x_root, event.y_root)

                entry_frame.bind("<Button-3>", lambda e, t=time_str, o=original_text: show_context_menu(e, t, o))
                content_label.bind("<Button-3>", lambda e, t=time_str, o=original_text: show_context_menu(e, t, o))
                translated_label.bind("<Button-3>", lambda e, t=time_str, o=original_text: show_context_menu(e, t, o))
                info_label.bind("<Button-3>", lambda e, t=time_str, o=original_text: show_context_menu(e, t, o))
                # --- Thêm hiệu ứng hover ---
                def on_enter(event, frame=entry_frame):
                    frame.configure(fg_color="#181a20")
                def on_leave(event, frame=entry_frame):
                    frame.configure(fg_color="#23272f")
                entry_frame.bind("<Enter>", on_enter)
                entry_frame.bind("<Leave>", on_leave)
                content_label.bind("<Enter>", on_enter)
                content_label.bind("<Leave>", on_leave)
                translated_label.bind("<Enter>", on_enter)
                translated_label.bind("<Leave>", on_leave)
                info_label.bind("<Enter>", on_enter)
                info_label.bind("<Leave>", on_leave)
                row_idx += 1

        # --- Cập nhật scrollregion khi thay đổi kích thước ---
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        favorite_frame.bind("<Configure>", on_configure)

        # --- Đảm bảo canvas luôn fill chiều ngang ---
        def resize_canvas(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", resize_canvas)

        # --- Bắt sự kiện cuộn chuột ---
        def _on_mousewheel(event):
            try:
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except Exception:
                pass
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Gọi lại render khi search thay đổi ---
        search_var.trace_add("write", lambda *args: render_favorite_list())

        # --- Render lần đầu ---
        render_favorite_list()

    def open_settings(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        lang_display = self.translator.lang_display
        lang_codes = list(lang_display.keys())

        # --- Frame chứa phần cuộn (canvas + scrollbar) ---
        scrollable_frame = ctk.CTkFrame(self.content_frame, fg_color="#23272f")
        scrollable_frame.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(scrollable_frame, bg="#23272f", highlightthickness=0, bd=0)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(scrollable_frame, orientation="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # --- Bắt sự kiện cuộn chuột ---
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Frame chứa form đặt trên canvas ---
        form_frame = ctk.CTkFrame(canvas, fg_color="#23272f")
        window_id = canvas.create_window((0, 0), window=form_frame, anchor="nw")

        # --- Nhóm các trường cấu hình ---
        config_groups = [
            (_._("settings")["general"]["title"], [
                ("start_at_startup", _._("settings")["general"]["start_at_startup"], bool),
                ("show_homepage_at_startup", _._("settings")["general"]["show_homepage_at_startup"], bool),
                ("always_show_transtale", _._("settings")["general"]["always_show_translate"], bool),
                ("hotkey", _._("settings")["general"]["hotkey"], str),
            ]),
            (_._("settings")["history"]["title"], [
                ("save_translate_history", _._("settings")["history"]["save_translate_history"], bool),
                ("max_history_items", _._("settings")["history"]["max_history_items"], int),
                
            ]),
            (_._("settings")["popup_and_icon"]["title"], [
                ("icon_size", _._("settings")["popup_and_icon"]["icon_size"], int),
                ("icon_dissapear_after", _._("settings")["popup_and_icon"]["icon_dissapear_after"], int),
                ("popup_dissapear_after", _._("settings")["popup_and_icon"]["popup_dissapear_after"], int),
                ("max_length_on_popup", _._("settings")["popup_and_icon"]["max_length_on_popup"], int),
            ]),
            (_._("settings")["language"]["title"], [
                ("dest_lang", _._("settings")["language"]["dest_lang"], "combo"),
                ("font", _._("settings")["language"]["font"], str),
            ])
        ]

        entries = {}
        row_idx = 0
        for group_name, fields in config_groups:
            # Tiêu đề nhóm
            group_label = ctk.CTkLabel(form_frame, text=group_name, font=(self.translator.font, 15, "bold"), text_color="#00ff99")
            group_label.grid(row=row_idx, column=0, columnspan=2, sticky="w", padx=5, pady=(18, 6))
            row_idx += 1
            for key, label_text, typ in fields:
                ctk.CTkLabel(form_frame, text=label_text, anchor="w", font=(self.translator.font, 13)).grid(row=row_idx, column=0, sticky="w", padx=18, pady=6)
                val = getattr(self.translator, key)
                if typ is bool:
                    var = tk.BooleanVar(value=val)
                    entry = ctk.CTkCheckBox(form_frame, variable=var, text="")
                    entry.var = var
                elif typ is int:
                    entry = ctk.CTkEntry(form_frame)
                    entry.insert(0, str(val))
                elif typ == "combo" and key == "dest_lang":
                    current_display = lang_display.get(val, next(iter(lang_display.values())))
                    var = tk.StringVar(value=current_display)
                    entry = ctk.CTkComboBox(
                        form_frame,
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
                        form_frame,
                        values=fonts,
                        variable=var,
                        state="readonly",
                        font=(self.translator.font, 13),
                        width=220
                    )
                    entry.set(val)
                    entry.var = var
                # ... bên trong MainWindow.open_settings(), phần elif key == "hotkey": ...
                elif key == "hotkey":
                    var = tk.StringVar(value=val)
                    entry = ctk.CTkEntry(form_frame, textvariable=var, state="readonly")
                    entry.var = var
                    entry.configure(cursor="hand2")
                    def on_hotkey_click(event, entry=entry):
                        entry.configure(state="normal")
                        entry.delete(0, "end")
                        entry.insert(0, "Press keys...")
                        entry.focus_set()
                        pressed_keys = set()
                        def on_key_press(e):
                            k = e.keysym.lower()
                            pressed_keys.add(k)
                            # Build hotkey string
                            keys = []
                            for mod in ["control", "ctrl", "shift", "alt", "win", "meta"]:
                                if mod in pressed_keys:
                                    keys.append(mod)
                            # Add main key (non-modifier)
                            for k2 in pressed_keys:
                                if k2 not in ["control", "ctrl", "shift", "alt", "win", "meta"]:
                                    keys.append(k2)
                            # Map về chuẩn keyboard
                            mapping = {
                                "control_l": "ctrl",
                                "control_r": "ctrl",
                                "ctrl_l": "ctrl",
                                "ctrl_r": "ctrl",
                                "alt_l": "alt",
                                "alt_r": "alt",
                                "shift_l": "shift",
                                "shift_r": "shift",
                                "win_l": "windows",
                                "win_r": "windows",
                                "meta_l": "windows",
                                "meta_r": "windows"
                            }
                            keys_mapped = []
                            for key in keys:
                                key_lower = key.lower()
                                keys_mapped.append(mapping.get(key_lower, key_lower))
                            # Loại bỏ trùng lặp và giữ thứ tự
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
                            # Khi nhả phím cuối cùng thì lưu lại và dừng lắng nghe
                            if not pressed_keys:
                                entry.configure(state="readonly")
                                entry.unbind("<KeyPress>")
                                entry.unbind("<KeyRelease>")
                        entry.bind("<KeyPress>", on_key_press)
                        entry.bind("<KeyRelease>", on_key_release)
                    entry.bind("<Button-1>", on_hotkey_click)
                else:
                    entry = ctk.CTkEntry(form_frame)
                    entry.insert(0, str(val))
                entry.grid(row=row_idx, column=1, padx=10, pady=6, sticky="ew")
                entries[key] = (entry, typ)
                form_frame.grid_columnconfigure(1, weight=1)
                row_idx += 1

        # --- Footer frame (luôn ở dưới cùng, ngoài canvas) ---
        footer = ctk.CTkFrame(self.content_frame, fg_color="#23272f")
        footer.pack(side="bottom", fill="x", pady=(0, 0))
        footer.grid_columnconfigure(0, weight=0)
        footer.grid_columnconfigure(1, weight=1)

        save_btn = ctk.CTkButton(footer, 
                                 text=_._("settings")["save"], 
                                 width=120)
        save_btn.grid(row=0, column=0, sticky="w", padx=(20, 10), pady=10)

        copyright_label = ctk.CTkLabel(
            footer,
            text=f"{SOFTWARE}. version {SOFTWARE_VERSION} - Copyright © 2025 by Vezyl",
            font=(self.translator.font, 12, "italic"),
            text_color="#888"
        )
        copyright_label.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=10)

        # --- Hàm lưu config ---
        def save_config():
            try:
                with open(self.translator.config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                config_data = {}

            old_hotkey = self.translator.hotkey

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
                elif key == "font":
                    val = entry.var.get()
                else:
                    val = entry.get()
                config_data[key] = val
            with open(self.translator.config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.translator.load_config()
            # --- Cập nhật trạng thái khởi động cùng Windows ---
            self.translator.set_startup(self.translator.start_at_startup)
            if old_hotkey != self.translator.hotkey:
                register_new_hotkey(self.translator.hotkey)
        save_btn.configure(command=save_config)

        # --- Cập nhật scrollregion khi thay đổi kích thước ---
        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        form_frame.bind("<Configure>", on_configure)

        # --- Đảm bảo canvas luôn fill chiều ngang ---
        def resize_canvas(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind("<Configure>", resize_canvas)

    def toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, event=None):
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)

    def _ctrl_down(self, event=None):
        self.ctrl_pressed = True

    def _ctrl_up(self, event=None):
        self.ctrl_pressed = False

    def on_close(self):
        # Kiểm tra nếu giữ Ctrl khi đóng thì thoát toàn bộ chương trình
        try:
            if self.ctrl_pressed:
                self.destroy()
                os._exit(0)
            else:
                self.withdraw()
        except Exception:
            self.withdraw()
    
    def show(self):
        self.deiconify()
        main_window_instance.lift()
        main_window_instance.focus_force()

    def fill_homepage_text(self, text):
        # Tìm tab home, điền text vào textbox nguồn nếu đang ở tab home
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

    def open_entry_in_homepage(self, src_lang, dest_lang, content):
        """
        Open the homepage tab, set the source and destination languages, and fill the input textbox.
        
        Parameters:
            src_lang: Source language code (e.g., 'en', 'auto')
            dest_lang: Destination language code (e.g., 'vi')
            content: Text to translate
        """
        # Switch to home tab first
        self.show_tab_home()
        
        # Need to let the home tab fully render before finding elements
        def find_and_set_elements():
            # Find the main content frame
            main_frame = None
            for widget in self.content_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    main_frame = widget
                    break
                    
            if not main_frame:
                # If main frame not found yet, try again after a short delay
                self.after(100, find_and_set_elements)
                return
                
            # 1. Find and set source language combobox
            src_lang_combo = None
            for child in main_frame.winfo_children():
                if isinstance(child, ctk.CTkComboBox):
                    src_lang_combo = child
                    break
                    
            # 2. Find source text box (typically first CTkTextbox inside a frame)
            src_text = None
            src_text_frame = None
            for child in main_frame.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for subchild in child.winfo_children():
                        if isinstance(subchild, ctk.CTkTextbox):
                            src_text = subchild
                            src_text_frame = child
                            break
                    if src_text:
                        break
                        
            # 3. Find destination frame and language combobox
            dest_frame = None
            dest_lang_combo = None
            for child in main_frame.winfo_children():
                if isinstance(child, ctk.CTkFrame) and child != src_text_frame:
                    dest_frame = child
                    # Find combobox in destination frame
                    for subchild in dest_frame.winfo_children():
                        if isinstance(subchild, ctk.CTkComboBox):
                            dest_lang_combo = subchild
                            break
                    break
                    
            # Set values if all elements were found
            lang_display = self.translator.lang_display
            
            if src_lang_combo:
                if src_lang == "auto":
                    src_lang_combo.set(_._("home")["auto_detect"])
                elif src_lang in lang_display:
                    src_lang_combo.set(lang_display[src_lang])
                    
            if dest_lang_combo and dest_lang in lang_display:
                dest_lang_combo.set(lang_display[dest_lang])
                
            if src_text:
                # Clear and set the source text
                src_text.delete("1.0", "end")
                src_text.insert("1.0", content)
                
                # Trigger translation by simulating a text change event
                src_text.edit_modified(True)
                src_text.event_generate("<<Modified>>")
        
        # Start the process of finding and setting elements
        self.after(100, find_and_set_elements)

def search_entries(entries, keyword, fields):
    """
    Trả về danh sách các entry có chứa keyword (không phân biệt hoa thường)
    ở bất kỳ trường nào trong fields (list tên trường).
    """
    if not keyword:
        return entries
    keyword = keyword.lower().strip()
    filtered = []
    for item in entries:
        for field in fields:
            if keyword in str(item.get(field, "")).lower():
                filtered.append(item)
                break
    return filtered

class Translator:
    def __init__(self):
        print(f"{SOFTWARE}. version {SOFTWARE_VERSION} - Copyright © 2025 by Vezyl")
        self.config_file = "config/general.json"
        self.Is_icon_showing = False
        self.load_config()
        locales_dir = os.path.join("resources", "locales")
        _.load_locale(self.interface_language, locales_dir)
        self.translator = GoogleTranslator()
        self.root = ctk.CTk()
        self.root.withdraw()
        # --- Thêm xử lý khởi động cùng Windows ---
        self.set_startup(self.start_at_startup)
        threading.Thread(target=self.clipboard_watcher, daemon=True).start()

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
        # Giá trị mặc định
        self.interface_language = 'vi'
        self.start_at_startup = True
        self.show_homepage_at_startup = True
        self.always_show_transtale = True
        self.save_translate_history = True
        self.auto_save_after = 3000
        self.icon_size = 60
        self.icon_dissapear_after = 5
        self.popup_dissapear_after = 5
        self.max_length_on_popup = 500
        self.max_history_items = 20
        self.hotkey = 'ctrl+shift+c'
        self.dest_lang = 'vi'
        self.font = "JetBrains Mono"
        self.default_fonts = [
            "JetBrains Mono", "Consolas", "Segoe UI", "Calibri", "Arial", "Verdana"
        ]
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
                    self.interface_language = config.get('interface_language', self.interface_language)
                    self.start_at_startup = config.get('start_at_startup', self.start_at_startup)
                    self.show_homepage_at_startup = config.get('show_homepage_at_startup', self.show_homepage_at_startup)
                    self.always_show_transtale = config.get('always_show_transtale', self.always_show_transtale)
                    self.save_translate_history = config.get('save_translate_history', self.save_translate_history)
                    self.auto_save_after = config.get('auto_save_after', self.auto_save_after)
                    self.icon_size = config.get('icon_size', self.icon_size)
                    self.icon_dissapear_after = config.get('icon_dissapear_after', self.icon_dissapear_after)
                    self.popup_dissapear_after = config.get('popup_dissapear_after', self.popup_dissapear_after)
                    self.max_length_on_popup = config.get('max_length_on_popup', self.max_length_on_popup)
                    self.max_history_items = config.get('max_history_items', self.max_history_items)
                    self.hotkey = config.get('hotkey', self.hotkey)
                    self.dest_lang = config.get('dest_lang', self.dest_lang)
                    self.font = config.get('font', self.font)
                    self.default_fonts = config.get('default_fonts', self.default_fonts)
                    self.lang_display = config.get('lang_display', self.lang_display)
        except Exception as e:
            print(f"Loi khi tai cau hinh: {e}")
        # --- Đảm bảo trạng thái khởi động cùng Windows đúng với config ---
        self.set_startup(self.start_at_startup)

    def show_popup(self, text, x, y):
        global last_translated_text
        last_translated_text = text

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
        frame.pack(padx=8, pady=8, fill="both", expand=True)

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
                    note="popup"
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
                    last_translated_text,
                    src_lang,
                    dest_lang,
                    "popup"
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
        global last_translated_text
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
            img = Image.open(os.path.join("resources", "logo.png"))
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
                global last_translated_text
                print(f"Clicked on icon at ({icon_x}, {icon_y})")
                self.Is_icon_showing = False
                icon_win.withdraw()
                # Popup cũng đối xứng quanh chuột như icon
                popup_x = icon_x
                popup_y = icon_y + icon_size + 10 if y < screen_height // 2 else icon_y - icon_size - 10
                if len(text) > max_length_on_popup:
                        last_translated_text = text
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

    def clipboard_watcher(self):
        global tmp_clipboard, last_translated_text, main_window_instance
        recent_value = pyperclip.paste()
        while True:
            try:
                always_show_transtale = self.always_show_transtale
                if self.Is_icon_showing:
                    time.sleep(0.3)
                    continue
                else:
                    tmp_value = pyperclip.paste()
                    if tmp_value != recent_value and tmp_value.strip():
                        recent_value = tmp_value
                        tmp_clipboard = recent_value
                        x, y = pyautogui.position()
                        if always_show_transtale:
                            print("popup")
                            self.root.after(0, self.show_popup, tmp_value, x, y)
                        else:
                            print("icon")
                            self.root.after(0, self.show_icon, tmp_value, x, y)   
                    time.sleep(0.5)
            except Exception as e:
                sys.excepthook(*sys.exc_info())

def get_client_preferences():
    secret_path = os.path.join("config", "client.toml")
    try:
        secret = toml.load(secret_path)
        return secret.get("language_interface", ""), secret.get("theme_interface", "")
    except Exception as e:
        print(f"The software has been edited unwanted {e}")

language_interface, theme_interface = get_client_preferences()

LOCAL_DIR = "local"
TRANSLATE_LOG_FILE = os.path.join(LOCAL_DIR, "translate_log.enc")
FAVORITE_LOG_FILE = os.path.join(LOCAL_DIR, "favorite_log.enc")

# Đảm bảo thư mục local luôn tồn tại trước khi thao tác file
def ensure_local_dir():
    if not os.path.exists(LOCAL_DIR):
        os.makedirs(LOCAL_DIR)

def write_log_entry(last_translated_text, src_lang, dest_lang, source):
    global translator_instance
    save_translate_history = getattr(translator_instance, "save_translate_history", True)
    max_items = getattr(translator_instance, "max_history_items", 20)
    ensure_local_dir()
    log_file = TRANSLATE_LOG_FILE
    if not save_translate_history:
        return
    key = get_aes_key(language_interface, theme_interface)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_data = {
        "time": now,
        "last_translated_text": last_translated_text,
        "src_lang": src_lang,
        "dest_lang": dest_lang,
        "source": source  # "homepage" hoặc "popup"
    }
    log_line = json.dumps(log_data, ensure_ascii=False)
    enc_line = encrypt_aes(log_line, key)
    lines = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]
    if len(lines) >= max_items:
        lines = lines[-(max_items-1):]
    lines.append(enc_line)
    with open(log_file, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

def write_favorite_entry(original_text, translated_text, src_lang, dest_lang, note):
    """
    Lưu bản dịch yêu thích vào file favorite_log.enc (mã hóa AES).
    Nếu translated_text rỗng thì sẽ tự động dịch original_text từ src_lang sang dest_lang.
    """
    ensure_local_dir()
    log_file = FAVORITE_LOG_FILE
    key = get_aes_key(language_interface, theme_interface)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not translated_text:
        try:
            translator = GoogleTranslator()
            if src_lang == "auto":
                result = translator.translate(original_text, dest=dest_lang)
            else:
                result = translator.translate(original_text, src=src_lang, dest=dest_lang)
            translated_text = result.text
        except Exception as e:
            translated_text = f"Lỗi dịch: {e}"

    log_data = {
        "time": now,
        "original_text": original_text,
        "translated_text": translated_text,
        "src_lang": src_lang,
        "dest_lang": dest_lang,
        "note": note
    }
    log_line = json.dumps(log_data, ensure_ascii=False)
    enc_line = encrypt_aes(log_line, key)

    lines = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f if line.strip()]
    lines.append(enc_line)
    with open(log_file, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")


main_window_instance = None  # Biến toàn cục lưu MainWindow
translator_instance = None   # Biến toàn cục lưu Translator
tmp_clipboard = ""
last_translated_text = ""  # Biến toàn cục lưu bản dịch cuối
global hotkey_id
hotkey_id = None

def show_homepage():
    global main_window_instance, translator_instance, last_translated_text
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
                    if last_translated_text != "":
                        filled = main_window_instance.fill_homepage_text(last_translated_text)
                        if not filled:
                            main_window_instance.after(100, try_fill)
                main_window_instance.after(100, try_fill)
            root.after(0, bring_window_to_front)
        except Exception as e:
            sys.excepthook(*sys.exc_info())
    else:
        print("Cua so chinh chua duoc khoi tao")

def unregister_current_hotkey():
    """Unregister the current global hotkey if any."""
    global hotkey_id
    try:
        if hotkey_id:
            keyboard.remove_hotkey(hotkey_id)
            print(f"Unregistered hotkey: {translator_instance.hotkey}")
            hotkey_id = None
            return True
    except Exception as e:
        print(f"Error unregistering hotkey: {e}")
    return False

def register_new_hotkey(hotkey_str=None):
    """Register a new global hotkey."""
    global hotkey_id
    if not hotkey_str:
        hotkey_str = translator_instance.hotkey
    
    def open_homepage_from_hotkey():
        print(f"Opening homepage from hotkey: {hotkey_str}")
        try:
            translator_instance.root.after(0, show_homepage)
        except Exception as e:
            print(f"Error opening homepage from hotkey: {e}")
            sys.excepthook(*sys.exc_info())
    
    try:
        # Unregister any existing hotkey first
        unregister_current_hotkey()
        # Register new hotkey
        hotkey_id = keyboard.add_hotkey(hotkey_str, open_homepage_from_hotkey, suppress=True)
        print(f"Hotkey listener registered: {hotkey_str}")
        return True
    except Exception as e:
        print(f"Failed to register hotkey {hotkey_str}: {e}")
        sys.excepthook(*sys.exc_info())
    return False

def start_hotkey_listener():
    """Initialize the hotkey listener using the configured hotkey."""
    register_new_hotkey()

def main():
    global translator_instance, main_window_instance

    translator_instance = Translator()
    main_window_instance = MainWindow(translator_instance)
    translator_instance.main_window = main_window_instance
    start_hotkey_listener()

    if not translator_instance.show_homepage_at_startup:
        main_window_instance.withdraw()

    # Khởi động tray icon ở thread phụ
    def tray_icon_thread():
        try:
            if get_windows_theme() == "dark":
                icon_image = Image.open("resources/logo.ico")
            else:
                icon_image = Image.open("resources/logo_black_bg.ico")
            menu = Menu(
                MenuItem(_._("menu_tray")["open_homepage"], on_homepage),
                MenuItem(_._("menu_tray")["quit"], on_quit)
            )
            def on_homepage_click(icon):
                show_homepage()
            icon = Icon(
                "MyApp",
                icon_image,
                SOFTWARE,
                menu,
                on_clicked=on_homepage_click
            )
            icon.run()
        except Exception:
            sys.excepthook(*sys.exc_info())
    threading.Thread(target=tray_icon_thread, daemon=True).start()

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


