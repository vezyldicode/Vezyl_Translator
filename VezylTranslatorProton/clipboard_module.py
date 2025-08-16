"""
Thư viện này là một phần của VezylTranslator, một ứng dụng dịch thuật mã nguồn mở được phát triển bởi Vezyl.
Vui lòng không sao chép, chỉnh sửa hoặc phân phối mã nguồn này mà không có sự cho phép của tác giả.
Copyright (c) 2023-2024 Vezyl. All rights reserved.

Quản lý các chức năng thao tác đến clipboard 
"""



import pyperclip
import pyautogui
import time
import os
import sys
import re
from VezylTranslatorNeutron.constant import RESOURCES_DIR
import winsound
from PIL import Image
from functools import lru_cache
from threading import Lock
from VezylTranslatorProton.utils import get_windows_theme
from VezylTranslatorProton.tray_module import get_tray_icon_instance

# Thêm lock để đồng bộ hóa truy cập clipboard
_clipboard_lock = Lock()

def _safe_clipboard_paste(max_retries=3, retry_delay=0.1):
    """
    Truy cập clipboard an toàn với retry logic
    """
    for attempt in range(max_retries):
        try:
            with _clipboard_lock:
                return pyperclip.paste()
        except Exception as e:
            error_str = str(e).lower()
            # Kiểm tra lỗi clipboard cụ thể
            if any(keyword in error_str for keyword in [
                'openclipboard', 'pyperclipwindowsexception', 
                'clipboard', 'access denied', 'sharing violation'
            ]):
                if attempt < max_retries - 1:
                    print(f"Clipboard access attempt {attempt + 1} failed, retrying...")
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"Clipboard access failed after {max_retries} attempts: {e}")
                    return ""  # Trả về chuỗi rỗng thay vì crash
            else:
                # Lỗi không phải clipboard, re-raise
                raise e
    return ""

def _safe_clipboard_copy(text, max_retries=3, retry_delay=0.1):
    """
    Copy text to clipboard safely
    """
    for attempt in range(max_retries):
        try:
            with _clipboard_lock:
                pyperclip.copy(text)
                return True
        except Exception as e:
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in [
                'openclipboard', 'pyperclipwindowsexception',
                'clipboard', 'access denied'
            ]):
                if attempt < max_retries - 1:
                    print(f"Clipboard copy attempt {attempt + 1} failed, retrying...")
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    print(f"Clipboard copy failed after {max_retries} attempts: {e}")
                    return False
            else:
                raise e
    return False

# Cache cho format_text để tối ưu hiệu suất
@lru_cache(maxsize=100)
def _format_text_cached(text_hash, text):
    """Cache version của format_text"""
    return _format_text_internal(text)

def _format_text_internal(text):
    """
    Format văn bản về dạng chuẩn, loại bỏ các chi tiết thừa.
    Internal function không cache
    """
    if not text or not text.strip():
        return text
    
    # Loại bỏ các ký tự điều khiển không mong muốn (trừ \n, \t)
    formatted_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Chuẩn hóa xuống dòng: thay thế \r\n và \r thành \n
    formatted_text = re.sub(r'\r\n|\r', '\n', formatted_text)
    
    # Loại bỏ xuống dòng liên tục (2+ lần) thành 1 lần xuống dòng
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    
    # Loại bỏ khoảng trắng thừa ở đầu và cuối mỗi dòng
    lines = formatted_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Giữ nguyên dòng trống, chỉ clean dòng có nội dung
        if line.strip():
            # Loại bỏ khoảng trắng thừa ở đầu và cuối dòng
            cleaned_line = line.strip()
            # Chuẩn hóa khoảng trắng giữa các từ (loại bỏ nhiều space liên tục)
            cleaned_line = re.sub(r'\s+', ' ', cleaned_line)
            cleaned_lines.append(cleaned_line)
        else:
            cleaned_lines.append('')
    
    formatted_text = '\n'.join(cleaned_lines)
    
    # Loại bỏ xuống dòng thừa ở đầu và cuối văn bản
    formatted_text = formatted_text.strip()
    
    # Loại bỏ tab thừa và chuẩn hóa thụt lề
    # Chuyển tab thành 4 spaces và loại bỏ thụt lề không đều
    lines = formatted_text.split('\n')
    if len(lines) > 1:
        # Tìm mức thụt lề tối thiểu (không tính dòng trống)
        min_indent = float('inf')
        for line in lines:
            if line.strip():  # Bỏ qua dòng trống
                # Đếm số khoảng trắng/tab ở đầu dòng
                indent_match = re.match(r'^(\s*)', line)
                if indent_match:
                    indent = indent_match.group(1)
                    # Chuyển tab thành 4 spaces để tính toán
                    indent_spaces = indent.replace('\t', '    ')
                    if len(indent_spaces) < min_indent:
                        min_indent = len(indent_spaces)
        
        # Loại bỏ thụt lề chung nếu tất cả dòng đều có thụt lề
        if min_indent != float('inf') and min_indent > 0:
            normalized_lines = []
            for line in lines:
                if line.strip():  # Dòng có nội dung
                    # Chuyển tab thành spaces
                    line_with_spaces = line.replace('\t', '    ')
                    # Loại bỏ thụt lề chung
                    if len(line_with_spaces) >= min_indent:
                        normalized_lines.append(line_with_spaces[min_indent:])
                    else:
                        normalized_lines.append(line.strip())
                else:  # Dòng trống
                    normalized_lines.append('')
            formatted_text = '\n'.join(normalized_lines)
    
    return formatted_text

def format_text(text):
    """
    Format văn bản với cache để tối ưu hiệu suất
    """
    if not text or not text.strip():
        return text
    
    # Tạo hash đơn giản cho cache
    text_hash = hash(text) % 10000
    
    try:
        return _format_text_cached(text_hash, text)
    except:
        # Fallback nếu cache có vấn đề
        return _format_text_internal(text)

def clear_format_cache():
    """Xóa cache để tiết kiệm memory"""
    _format_text_cached.cache_clear()

def clipboard_watcher(
    translator_instance,
    main_window_instance,
    always_show_transtale,
    show_popup_func,
    show_icon_func,
    show_homepage_func   # <-- thêm tham số này
):
    """
    Theo dõi clipboard với adaptive interval để tối ưu CPU usage.
    Enhanced với safe clipboard access và error handling
    """
    # Sử dụng safe clipboard access
    recent_value = _safe_clipboard_paste()
    
    # Adaptive interval variables
    current_interval = 0.8  # Start với 0.8s thay vì 0.5s
    min_interval = 0.5
    max_interval = 2.0
    idle_count = 0
    last_activity_time = time.time()
    consecutive_errors = 0
    max_consecutive_errors = 10
    
    print("Clipboard watcher started with safe access")
    
    while True:
        try:
            # Kiểm tra trạng thái bật/tắt watcher
            if not getattr(translator_instance, "clipboard_watcher_enabled", True):
                time.sleep(max_interval)  # Sleep lâu hơn khi disabled
                continue
            if getattr(translator_instance, "Is_icon_showing", False):
                time.sleep(0.3)
                continue
            else:
                # Sử dụng safe clipboard paste thay vì pyperclip.paste() trực tiếp
                tmp_value = _safe_clipboard_paste()
                
                # Reset error counter khi truy cập clipboard thành công
                consecutive_errors = 0
                
                if tmp_value != recent_value and tmp_value.strip():
                    # Có hoạt động - reset interval
                    current_interval = min_interval
                    idle_count = 0
                    last_activity_time = time.time()
                    
                    # Format văn bản trước khi sử dụng
                    formatted_value = format_text(tmp_value)
                    recent_value = tmp_value  # Lưu giá trị gốc để so sánh lần sau
                    
                    try:
                        x, y = pyautogui.position()
                    except:
                        x, y = 0, 0  # Fallback position
                        
                    if always_show_transtale:
                        print("popup")
                        show_popup_func(formatted_value, x, y)
                    else:
                        print("icon")
                        show_icon_func(formatted_value, x, y)
                else:
                    # Không có hoạt động - tăng interval dần
                    idle_count += 1
                    time_since_activity = time.time() - last_activity_time
                    
                    if time_since_activity > 30:  # 30s không hoạt động
                        current_interval = min(max_interval, current_interval * 1.1)
                    elif time_since_activity > 10:  # 10s
                        current_interval = min(1.5, current_interval * 1.05)
                        
                # Adaptive sleep
                time.sleep(current_interval)
                
        except Exception as e:
            consecutive_errors += 1
            print(f"Clipboard watcher error {consecutive_errors}: {e}")
            
            # Kiểm tra nếu là lỗi clipboard cụ thể
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in [
                'openclipboard', 'pyperclipwindowsexception',
                'clipboard', 'access denied', 'sharing violation'
            ]):
                print("Clipboard access error detected, continuing with extended delay...")
                time.sleep(2.0)  # Sleep lâu hơn khi gặp lỗi clipboard
            else:
                # Lỗi khác, log và tiếp tục
                print(f"Non-clipboard error: {e}")
                sys.excepthook(*sys.exc_info())
                time.sleep(1.0)
            
            # Nếu quá nhiều lỗi liên tiếp, tạm dừng lâu hơn
            if consecutive_errors >= max_consecutive_errors:
                print(f"Too many consecutive errors ({consecutive_errors}), entering extended pause...")
                time.sleep(10.0)  # Pause 10 giây
                consecutive_errors = 0  # Reset counter

def get_clipboard_text():
    """
    Lấy văn bản từ clipboard và format về dạng chuẩn.
    Enhanced với safe clipboard access
    
    Returns:
        str: Văn bản đã được format từ clipboard
    """
    raw_text = _safe_clipboard_paste()
    return format_text(raw_text)

def set_clipboard_text(text):
    """
    Set clipboard text with safe access
    """
    return _safe_clipboard_copy(text)

def toggle_clipboard_watcher(translator_instance):
    """
    Toggle clipboard watcher và thay đổi icon tray theo trạng thái (tối ưu async)
    """
    if translator_instance is None:
        return
    
    # Toggle state
    translator_instance.clipboard_watcher_enabled = not getattr(
        translator_instance, "clipboard_watcher_enabled", True
    )
    
    state = "ON" if translator_instance.clipboard_watcher_enabled else "OFF"
    print(f"Clipboard watcher toggled: {state}")

    # Phát âm thanh thông báo (non-blocking)
    try:
        if translator_instance.clipboard_watcher_enabled:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            winsound.MessageBeep(winsound.MB_ICONHAND)
    except:
        pass  # Ignore sound errors

    # Cập nhật icon tray trong background thread để không block
    def update_tray_icon():
        tray_icon = get_tray_icon_instance()
        if tray_icon is None:
            return
            
        try:
            # Chọn icon phù hợp
            if not translator_instance.clipboard_watcher_enabled:
                icon_path = os.path.join(RESOURCES_DIR, "logo_red.ico")
            else:
                if get_windows_theme() == "dark":
                    icon_path = os.path.join(RESOURCES_DIR, "logo.ico")
                else:
                    icon_path = os.path.join(RESOURCES_DIR, "logo_black.ico")
            
            # Load và set icon nếu file tồn tại
            if os.path.exists(icon_path):
                new_icon = Image.open(icon_path)
                tray_icon.icon = new_icon
                
                # Refresh icon với delay ngắn hơn
                tray_icon.visible = False
                time.sleep(0.05)  # Giảm từ 0.1s xuống 0.05s
                tray_icon.visible = True
                
                print(f"Icon updated to {'red' if not translator_instance.clipboard_watcher_enabled else 'normal'}")
        except Exception as e:
            print(f"Error updating icon: {e}")
    
    # Chạy update icon trong background thread
    import threading
    threading.Thread(target=update_tray_icon, daemon=True).start()