"""
Thư viện này là một phần của VezylTranslator, một ứng dụng dịch thuật mã nguồn mở được phát triển bởi Vezyl.
Vui lòng không sao chép, chỉnh sửa hoặc phân phối mã nguồn này mà không có sự cho phép của tác giả.
Copyright (c) 2023-2024 Vezyl. All rights reserved.

Thư viện cung cấp chức năng hiển thị icon và popup cho ứng dụ            translated = result["text"]
            src_lang = result.get("src", "auto")  # Get detected language
            
            # Update constant for consistency
            constant.last_translated_text = translated
            
            popup.after(0, lambda: (
                label_src_lang.configure(text=src_lang_display),
                label_trans.configure(text=translated),
                combo_src_lang.set(lang_display.get(src_lang, src_lang))
            ))
            # Ghi log
            write_log_entry(
                translated,  # Use actual translated text
                src_lang, 
                dest_lang, 
                "popup", 
                constant.TRANSLATE_LOG_FILE, 
                language_interface, 
                theme_interface
            )or
"""



import os
import threading
import sys
import winsound
import json
from PIL import Image
import customtkinter as ctk
from VezylTranslatorNeutron import constant
from VezylTranslatorProton.file_flow import (
    pad, 
    unpad, 
    encrypt_aes, 
    decrypt_aes, 
    get_aes_key)
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
from VezylTranslatorProton.utils import (
    get_windows_theme, 
    show_confirm_popup, 
    get_client_preferences, 
    ensure_local_dir, 
    search_entries
)
from VezylTranslatorProton.clipboard_module import clipboard_watcher, get_clipboard_text, set_clipboard_text
from VezylTranslatorProton.translate_module import translate_with_model

import threading

def ensure_main_window_available(translator, main_window_instance, language_interface, theme_interface, _):
    """
    Ensure main window is available and not shutting down.
    If needed, recreate the main window.
    """
    # First try to get from global context
    try:
        import VezylTranslator
        if hasattr(VezylTranslator, 'get_or_create_main_window'):
            global_window = VezylTranslator.get_or_create_main_window()
            if global_window is not None:
                return global_window
    except Exception as e:
        print(f"Could not get main window from global context: {e}")
    
    # Check if current main window is usable
    if (main_window_instance is not None and 
        hasattr(main_window_instance, 'winfo_exists') and
        main_window_instance.winfo_exists() and
        not getattr(main_window_instance, '_shutting_down', False)):
        return main_window_instance
    
    # If main window is not usable, try to recreate it
    try:
        print("Recreating main window from popup manager...")
        from VezylTranslatorElectron.gui import MainWindow
        
        # Create new main window
        new_window = MainWindow(translator, language_interface, theme_interface, _)
        translator.main_window = new_window
        
        # Ensure the new window has translation executor initialized
        if hasattr(new_window, 'gui_controller') and hasattr(new_window.gui_controller, 'translation_executor'):
            if new_window.gui_controller.translation_executor is None:
                # Force initialization of translation executor
                new_window.gui_controller._ensure_translation_executor()
        
        # Try to update global reference
        try:
            import VezylTranslator
            if hasattr(VezylTranslator, 'update_main_window_instance'):
                VezylTranslator.update_main_window_instance(new_window)
        except:
            pass
        
        return new_window
    except Exception as e:
        print(f"Failed to recreate main window: {e}")
        return None

def safe_configure_widget(widget, **kwargs):
    """Safely configure widget with existence check"""
    try:
        if widget and hasattr(widget, 'winfo_exists') and widget.winfo_exists():
            widget.configure(**kwargs)
            return True
    except Exception as e:
        print(f"Widget configure error: {e}")
    return False

def show_popup_safe(translator, text, x, y, main_window_instance, language_interface, theme_interface, _):
    """Wrapper đảm bảo show_popup luôn chạy trên main thread."""
    def call():
        # Ensure we have a working main window before showing popup
        working_main_window = ensure_main_window_available(
            translator, main_window_instance, language_interface, theme_interface, _
        )
        
        if working_main_window is None:
            print("Warning: No main window available for popup")
            return
            
        show_popup(
            translator, text, x, y,
            working_main_window, language_interface, theme_interface, _
        )
    if threading.current_thread() is threading.main_thread():
        call()
    else:
        translator.root.after(0, call)

def show_icon_safe(translator, text, x, y, main_window_instance, language_interface, theme_interface, _):
    """Wrapper đảm bảo show_icon luôn chạy trên main thread."""
    def call():
        # Ensure we have a working main window before showing icon
        working_main_window = ensure_main_window_available(
            translator, main_window_instance, language_interface, theme_interface, _
        )
        
        if working_main_window is None:
            print("Warning: No main window available for icon")
            return
            
        show_icon(
            translator, text, x, y,
            working_main_window, language_interface, theme_interface, _
        )
    if threading.current_thread() is threading.main_thread():
        call()
    else:
        translator.root.after(0, call)

def show_popup(translator, text, x, y, main_window_instance, language_interface, theme_interface, _):
    constant.last_translated_text = text

    lang_display = translator.lang_display
    lang_codes = list(lang_display.keys())
    display_to_code = {v: k for k, v in lang_display.items()}
    dest_lang = translator.dest_lang

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
        fav_img = ctk.CTkImage(light_image=Image.open(os.path.join(constant.RESOURCES_DIR, "fav.png")), size=(18, 18))
    except Exception:
        fav_img = None
    try:
        fav_clicked_img = ctk.CTkImage(light_image=Image.open(os.path.join(constant.RESOURCES_DIR, "fav_clicked.png")), size=(18, 18))
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
            src_lang_val = getattr(translator, "last_src_lang", "auto")
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
        font=(translator.font, 13, "underline"),
        text_color="#00ff99",
        cursor="hand2"
    )
    open_label.pack(side="left", padx=(0, 0))
    def on_open_click(event=None):
        popup.destroy()
        try:
            # Ensure main window is available
            available_window = ensure_main_window_available(
                translator, main_window_instance, language_interface, theme_interface, _
            )
            
            if available_window is not None:
                available_window.show_and_fill_homepage()
            else:
                print("Cannot open homepage: Main window unavailable")
        except Exception as e:
            print(f"Error opening homepage from popup: {e}")
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
        font=(translator.font, 14, "italic"),
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
        font=(translator.font, 18, "bold")
    )
    label_src.pack(anchor="w", padx=10, pady=(0, 10))

    label_dest_lang = ctk.CTkLabel(
        frame,
        text=lang_display.get(dest_lang, dest_lang),
        text_color="#aaaaaa",
        font=(translator.font, 14, "italic"),
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
        font=(translator.font, 18, "bold")
    )
    label_trans.pack(anchor="w", padx=10, pady=(0, 10))

    try:
        copy_img = ctk.CTkImage(light_image=Image.open(os.path.join(constant.RESOURCES_DIR, "save_btn.png")), size=(24, 24))
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
            # Lấy model dịch từ translator instance
            model_name = getattr(translator, 'translation_model', 'google')
            result = translate_with_model(
                text,
                src_lang="auto",
                dest_lang=dest_lang,
                model_name=model_name
            )
            translated = result["text"]
            src_lang = result["src"]
            src_lang_display = lang_display.get(src_lang, src_lang)
            # Cập nhật giao diện trên main thread với safe checking
            def safe_update_ui():
                try:
                    if label_src_lang.winfo_exists():
                        label_src_lang.configure(text=src_lang_display)
                    if label_trans.winfo_exists():
                        label_trans.configure(text=translated)
                    if combo_src_lang.winfo_exists():
                        combo_src_lang.set(lang_display.get(src_lang, src_lang))
                except Exception as e:
                    print(f"UI update error (widget destroyed): {e}")
                    
            popup.after(0, safe_update_ui)
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
            def safe_show_error():
                try:
                    if label_trans.winfo_exists():
                        label_trans.configure(text=f"Lỗi dịch: {e}")
                except Exception:
                    print(f"Error showing translation error: {e}")
                    
            popup.after(0, safe_show_error)

    # Chạy dịch ở thread phụ
    threading.Thread(target=do_translate, daemon=True).start()

    def update_translation(new_src_lang):
        try:
            # Lấy model dịch từ translator instance
            model_name = getattr(translator, 'translation_model', 'google')
            result = translate_with_model(text, src_lang=new_src_lang, dest_lang=dest_lang, model_name=model_name)
            translated = result["text"]  # Sửa lại từ result.text thành result["text"]
            
            # Update constant for consistency
            constant.last_translated_text = translated
            
            src_lang_display = lang_display.get(new_src_lang, new_src_lang)
            dest_lang_display = lang_display.get(dest_lang, dest_lang)
            # Cập nhật các label with safe checking
            safe_configure_widget(label_src_lang, text=f"{src_lang_display}")
            safe_configure_widget(label_dest_lang, text=f"{dest_lang_display}")
            safe_configure_widget(label_trans, text=translated)
            
            # Write to history log
            try:
                write_log_entry(
                    translated,  # Use actual translated text
                    new_src_lang, 
                    dest_lang, 
                    "popup", 
                    constant.TRANSLATE_LOG_FILE, 
                    language_interface, 
                    theme_interface
                )
            except Exception as e:
                print(f"Error writing popup history: {e}")
            safe_configure_widget(label_trans, text=translated) # Hiển thị lại bản dịch
        except Exception as e:
            safe_configure_widget(label_trans, text=f"Cannot translate: {e}")

    def on_combo_change(selected_value):
        selected_lang_code = display_to_code.get(selected_value)
        if selected_lang_code:
            update_translation(selected_lang_code)

    combo_src_lang.configure(command=on_combo_change)
    try:
        combo_src_lang.set(lang_display.get('auto', list(lang_display.values())[0]))
    except Exception:
        combo_src_lang.set(lang_display.get('en', '🇺🇸 English'))

    close_job = [None]
    def schedule_close():
        popup_dissapear_after = translator.popup_dissapear_after * 1000  # chuyển sang mili giây  
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

def show_icon(translator, text, x, y, main_window_instance, language_interface, theme_interface, _):
    try:
        translator.Is_icon_showing = True

        # Lấy kích thước màn hình
        screen_width = translator.root.winfo_screenwidth()
        screen_height = translator.root.winfo_screenheight()
        icon_size = translator.icon_size
        icon_dissapear_after = translator.icon_dissapear_after *1000 # chuyển sang mili giây
        max_length_on_popup = translator.max_length_on_popup
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

        icon_win = ctk.CTkToplevel(translator.root)
        icon_win.wm_overrideredirect(True)
        icon_win.wm_attributes('-topmost', True)
        icon_win.wm_geometry(f"{icon_size}x{icon_size}+{icon_x}+{icon_y}")

        # Load icon từ file và resize thành hình vuông
        # icon dựa trên theme
        if get_windows_theme() == "dark":
            img = Image.open(os.path.join(constant.RESOURCES_DIR, "logo.png"))
        else:
            img = Image.open(os.path.join(constant.RESOURCES_DIR, "logo_black_bg.png"))
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
            translator.Is_icon_showing = False
            icon_win.withdraw()
            # Popup cũng đối xứng quanh chuột như icon
            popup_x = icon_x
            popup_y = icon_y + icon_size + 10 if y < screen_height // 2 else icon_y - icon_size - 10
            if len(text) > max_length_on_popup:
                    constant.last_translated_text = text
                    def open_homepage():
                        try:
                            # Ensure main window is available
                            available_window = ensure_main_window_available(
                                translator, main_window_instance, language_interface, theme_interface, _
                            )
                            
                            if available_window is not None:
                                available_window.show_and_fill_homepage()
                            else:
                                print("Cannot open homepage: Main window unavailable")
                        except Exception as e:
                            print(f"Error opening homepage: {e}")
                    translator.root.after(0, open_homepage)
            else:
                translator.show_popup(text, popup_x, popup_y)

        img_label.bind("<Button-1>", on_click)
        img_label.configure(cursor="hand2")

        def destroy_icon():
            translator.Is_icon_showing = False
            icon_win.destroy()

        icon_win.after(icon_dissapear_after, destroy_icon)
        icon_win.lift()
        icon_win.after(100, lambda: icon_win.attributes('-alpha', 0.9))

    except Exception as e:
        translator.Is_icon_showing = False
        print(f"Lỗi show_icon: {e}", file=sys.stderr)