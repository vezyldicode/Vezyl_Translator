import pyperclip
import pyautogui
import time
import os
import sys

def clipboard_watcher(
    translator_instance,
    main_window_instance,
    always_show_transtale,
    show_popup_func,
    show_icon_func,
    show_homepage_func   # <-- thêm tham số này
):
    """
    Theo dõi clipboard, gọi show_popup_func hoặc show_icon_func khi clipboard thay đổi.
    """
    recent_value = pyperclip.paste()
    while True:
        try:
            # Kiểm tra trạng thái bật/tắt watcher
            if not getattr(translator_instance, "clipboard_watcher_enabled", True):
                time.sleep(0.5)
                continue
            if getattr(translator_instance, "Is_icon_showing", False):
                time.sleep(0.3)
                continue
            else:
                tmp_value = pyperclip.paste()
                if tmp_value != recent_value and tmp_value.strip():
                    recent_value = tmp_value
                    x, y = pyautogui.position()
                    if always_show_transtale:
                        print("popup")
                        show_popup_func(tmp_value, x, y)
                    else:
                        print("icon")
                        show_icon_func(tmp_value, x, y)
                time.sleep(0.5)
        except Exception as e:
            sys.excepthook(*sys.exc_info())

def get_clipboard_text():
    return pyperclip.paste()

def set_clipboard_text(text):
    pyperclip.copy(text)