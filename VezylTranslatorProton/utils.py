import winreg
import customtkinter as ctk
import os
import toml
from VezylTranslatorNeutron.constant import CONFIG_DIR, CLIENT_CONFIG_FILE

def show_confirm_popup(parent, title, message, on_confirm, on_cancel=None, width=420, height=180, _=None):
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
    # Lưu ý: cần import _ từ locale_module ở file sử dụng
    confirm_text = _._("confirm_popup")["confirm"] if _ else "Confirm"
    cancel_text = _._("confirm_popup")["cancel"] if _ else "Cancel"
    confirm_btn = ctk.CTkButton(
        btn_frame, text=confirm_text, width=120, fg_color="#00ff99", text_color="#23272f",
        font=(parent.translator.font, 13, "bold"), command=confirm_and_close
    )
    confirm_btn.pack(side="left", padx=12)
    cancel_btn = ctk.CTkButton(
        btn_frame, text=cancel_text, width=120, fg_color="#444", text_color="#f5f5f5",
        font=(parent.translator.font, 13), command=cancel_and_close
    )
    cancel_btn.pack(side="left", padx=12)
    confirm.focus_set()
    confirm.wait_window()
    return confirm

def get_windows_theme():
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value == 1 else "dark"
    except Exception as e:
        return f"unknown ({e})"
    
def get_client_preferences():
    secret_path = CLIENT_CONFIG_FILE
    try:
        secret = toml.load(secret_path)
        return secret.get("language_interface", ""), secret.get("theme_interface", "")
    except Exception as e:
        print(f"The software has been edited unwanted {e}")

def ensure_local_dir(local_dir):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

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