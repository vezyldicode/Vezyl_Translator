"""
Thư viện này là một phần của VezylTranslator, một ứng dụng dịch thuật mã nguồn mở được phát triển bởi Vezyl.
Vui lòng không sao chép, chỉnh sửa hoặc phân phối mã nguồn này mà không có sự cho phép của tác giả.
Copyright (c) 2023-2024 Vezyl. All rights reserved.

Thư viện quản lý giao diện chính của ứng dụng dịch thuật
"""

import os
import threading
import tkinter as tk
from PIL import Image
import winsound

import customtkinter as ctk
from VezylTranslatorProton.clipboard_module import set_clipboard_text

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
from VezylTranslatorNeutron import constant
from VezylTranslatorProton.config_module import load_config, save_config, get_default_config
from VezylTranslatorProton.hotkey_manager_module import (
    register_hotkey, 
    unregister_hotkey)
class MainWindow(ctk.CTkToplevel):
    def __init__(
        self, translator,
        language_interface, theme_interface, _
    ):
        super().__init__()
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
        ctk.set_appearance_mode("dark")
        self.translator = translator
        self.title(constant.SOFTWARE + " " + constant.SOFTWARE_VERSION)

        # Lấy theme của máy user và chỉnh icon theo theme
        self.theme = get_windows_theme()
        if self.theme == "dark":
            try:
                self.after(200, lambda: self.wm_iconbitmap("resources/logo.ico"))
            except:
                print("Không thể load icon")
        else:
            try:
                self.after(200, lambda: self.wm_iconbitmap("resources/logo_black.ico"))
            except:
                print("Không thể load icon")

        # Kích thước mặc định cửa sổ
        self.width = 900
        self.height = 600
        self.geometry(f"{self.width}x{self.height}")
        self.resizable(True, True)
        self.is_fullscreen = False
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.exit_fullscreen)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Cấu hình các tab
        self.tabs = {
            "Trang chủ": self.show_tab_home,
            "Lịch sử": self.show_tab_history,
            "Yêu thích": self.show_tab_favorite,
            "Cài đặt": self.open_settings
        }
        self.build_ui()

        # Hiển thị mặc định tab home khi khởi tạo
        self.show_tab_home()

        # Theo dõi sự kiện bấm Ctrl
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
        language_interface = self.language_interface
        theme_interface = self.theme_interface
        _ = self._
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
            command=lambda: set_clipboard_text(src_text.get("1.0", "end").strip())
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
        if constant.last_translated_text:
            src_text.delete("1.0", "end")
            src_text.insert("1.0", constant.last_translated_text)

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
            command=lambda: set_clipboard_text(dest_text.get("1.0", "end").strip())
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
            text = src_text.get("1.0", "end").strip()
            if text:
                constant.last_translated_text = text
                auto_save_state["saved"] = True
                print("Auto-saved last_translated_text")
                # Ghi log khi lưu trên homepage
                src_lang_display = src_lang_var.get()
                if src_lang_display == _._("home")["auto_detect"]:
                    src_lang = "auto"
                else:
                    src_lang = next((k for k, v in lang_display.items() if v == src_lang_display), "auto")
                dest_lang_display = dest_lang_var.get()
                dest_lang = next((k for k, v in lang_display.items() if v == dest_lang_display), self.translator.dest_lang)
                write_log_entry(
                    constant.last_translated_text, 
                    src_lang, 
                    dest_lang, 
                    "homepage", 
                    constant.TRANSLATE_LOG_FILE, 
                    language_interface, 
                    theme_interface
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
        language_interface = self.language_interface
        theme_interface = self.theme_interface
        _ = self._
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
        log_file = constant.TRANSLATE_LOG_FILE
        history = read_history_entries(log_file, language_interface, theme_interface)

        def delete_all_history_entries_ui():
            show_confirm_popup(
                parent=self,
                title=_._("confirm_popup")["title"],
                message=_._("history")["menu"]["delete_confirm"],
                on_confirm=lambda: (
                    ensure_local_dir(constant.LOCAL_DIR),
                    delete_all_history_entries(constant.TRANSLATE_LOG_FILE),
                    self.show_tab_history()
                ),
                width=420,
                height=180,
                _=_
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
                                      command=lambda: delete_history_entry_ui(t, c))
                    menu.add_command(
                        label=_._("history")["menu"]["add_to_favorite"],
                        command=lambda: write_favorite_entry(
                            original_text=c,
                            translated_text=item.get("translated_text", ""),  # Nếu có trường này trong log
                            src_lang=s,
                            dest_lang=d,
                            note="",
                            log_file=constant.FAVORITE_LOG_FILE,           # log_file
                            language_interface=language_interface,          # language_interface
                            theme_interface=theme_interface  
                        )
                    )
                    menu.add_separator()
                    menu.add_command(label=_._("history")["menu"]["delete_all"], command=delete_all_history_entries_ui)
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

            def delete_history_entry_ui(time_str, last_translated_text):
                delete_history_entry(
                    constant.TRANSLATE_LOG_FILE,
                    language_interface,
                    theme_interface,
                    time_str,
                    last_translated_text
                )
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
        language_interface = self.language_interface
        theme_interface = self.theme_interface
        _ = self._
        _ = self._
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

        # Đọc và giải mã log yêu thích sử dụng hàm đã tách
        log_file = constant.FAVORITE_LOG_FILE
        favorites = read_favorite_entries(log_file, language_interface, theme_interface)

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
                src_disp = lang_display.get(src_lang, src_lang)
                dest_disp = lang_display.get(dest_lang, dest_lang)
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
                    update_favorite_note(constant.FAVORITE_LOG_FILE, language_interface, theme_interface, entry_time, new_note)
                    self.show_tab_favorite()  # Gọi lại hàm để cập nhật giao diện

                note_entry.bind("<Return>", lambda event, entry_time=time_str, note_var=note_var: save_note(event, entry_time, note_var))
                
                def delete_all_favorite_entries_ui():
                    show_confirm_popup(
                        parent=self,
                        title=_._("confirm_popup")["title"],
                        message=_._("favorite")["menu"]["delete_confirm"],
                        on_confirm=lambda: (
                            ensure_local_dir(constant.LOCAL_DIR),
                            delete_all_favorite_entries(constant.FAVORITE_LOG_FILE),
                            self.show_tab_favorite()
                        ),
                        width=420,
                        height=180,
                        _=_
                    )
                # --- Thêm menu chuột phải ---
                def show_context_menu(event, t=time_str, o=original_text):
                    menu = tk.Menu(self, tearoff=0)
                    menu.add_command(label=_._("favorite")["menu"]["delete"], 
                                     command=lambda: (
                                         delete_favorite_entry(constant.FAVORITE_LOG_FILE, language_interface, theme_interface, t, o),
                                         self.show_tab_favorite()
                                     ))
                    menu.add_separator()
                    menu.add_command(label=_._("favorite")["menu"]["delete_all"], command=delete_all_favorite_entries_ui)
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
        _ = self._
        _ = self._
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
                ("always_show_transtale", _._("settings")["general"]["hotkey"], bool),
                ("hotkey", _._("settings")["general"]["hotkey"], "hotkey"),
                ("clipboard_hotkey", _._("settings")["general"]["clipboard_hotkey"], "hotkey"),
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
                elif typ == "hotkey":
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
            text=f"{constant.SOFTWARE}. version {constant.SOFTWARE_VERSION} - Copyright © 2025 by Vezyl",
            font=(self.translator.font, 12, "italic"),
            text_color="#888"
        )
        copyright_label.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=10)

        # --- Hàm lưu config ---
        def on_save_config():
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            try:
                config_data = load_config(self.translator.config_file, get_default_config())
            except Exception:
                config_data = get_default_config()
            old_homepage_hotkey = self.translator.hotkey
            old_clipboard_hotkey = self.translator.clipboard_hotkey


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
            save_config(self.translator.config_file, config_data)
            self.translator.load_config()
            # --- Cập nhật trạng thái khởi động cùng Windows ---
            self.translator.set_startup(self.translator.start_at_startup)
            # --- Cập nhật các hotkey ---
            if self.translator.hotkey != old_homepage_hotkey:
                unregister_hotkey("homepage")
                register_hotkey(
                    "homepage",
                    self.translator.hotkey,
                    lambda: show_homepage()
                )
            if self.translator.clipboard_hotkey != old_clipboard_hotkey:
                unregister_hotkey("clipboard")
                def toggle_clipboard_watcher():
                    self.translator.clipboard_watcher_enabled = not getattr(self.translator, "clipboard_watcher_enabled", True)
                    state = "ON" if self.translator.clipboard_watcher_enabled else "OFF"
                    print(f"Clipboard watcher toggled: {state}")
                    import winsound
                    if self.translator.clipboard_watcher_enabled:
                        winsound.MessageBeep(winsound.MB_ICONASTERISK)
                    else:
                        winsound.MessageBeep(winsound.MB_ICONHAND)
                register_hotkey(
                    "clipboard",
                    self.translator.clipboard_hotkey,
                    toggle_clipboard_watcher
                )
            self.open_settings()
        save_btn.configure(command=on_save_config)

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

    def on_close(self):        # Kiểm tra nếu giữ Ctrl khi đóng thì thoát toàn bộ chương trình
        try:
            if self.ctrl_pressed:
                self.destroy()
                os._exit(0)
            else:
                self.withdraw()
        except Exception:
            self.withdraw()
    
    def fill_homepage_text(self, text):
        _ = self._
        for widget in self.content_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkTextbox):
                        print("Found CTkTextbox, filling text")
                        child.delete("1.0", "end")
                        child.insert("1.0", text)
                        return True
                    if isinstance(child, ctk.CTkFrame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, ctk.CTkTextbox):
                                print("Found nested CTkTextbox, filling text")
                                subchild.delete("1.0", "end")
                                subchild.insert("1.0", text)
                                return True
        print("No CTkTextbox found to fill")
        return False
    
    def show_and_fill_homepage(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.show_tab_home()
        # Fill nếu có last_translated_text
        def try_fill():
            if constant.last_translated_text:
                filled = self.fill_homepage_text(constant.last_translated_text)
                if not filled:
                    self.after(100, try_fill)
        self.after(100, try_fill)

    def open_entry_in_homepage(self, src_lang, dest_lang, content):
        _ = self._
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
