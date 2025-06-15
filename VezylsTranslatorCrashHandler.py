import sys
import os
import logging
import datetime
import platform
import re
import requests
import tkinter.messagebox as mb
import toml

# Constants
LOG_DIR = os.path.join("local", "log")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DEFAULT_SOFTWARE = "Unknown"
DEFAULT_VERSION = "Unknown"
WEBHOOK_ENV_VAR = "VEZYLS_TRANSLATOR_DISCORD_WEBHOOK"

def setup_logging():
    """
    Thiết lập logging cho crash handler.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "crash_handler.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format=LOG_FORMAT,
        encoding="utf-8"
    )

def parse_traceback(traceback_str):
    """
    Phân tích traceback để lấy loại lỗi, file, dòng và message.
    """
    error_type = ""
    error_file = ""
    error_line = ""
    error_message = ""
    lines = traceback_str.strip().splitlines()
    # Tìm dòng chứa thông tin file và dòng lỗi cuối cùng
    for i in range(len(lines) - 1, -1, -1):
        m = re.match(r'  File "(.+)", line (\d+), in (.+)', lines[i])
        if m:
            error_file = m.group(1)
            error_line = m.group(2)
            break
    # Loại lỗi và message ở dòng cuối cùng
    if lines:
        last_line = lines[-1]
        if ": " in last_line:
            error_type, error_message = last_line.split(": ", 1)
        else:
            error_type = last_line
    return error_type, error_file, error_line, error_message

def write_crash_log(traceback_str, software, version):
    """
    Ghi thông tin lỗi vào file log riêng biệt cho từng crash.
    """
    now = datetime.datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M%S")
    log_filename = f"crash_{time_str}.log"
    log_path = os.path.join(LOG_DIR, log_filename)
    os_info = platform.platform()
    error_type, error_file, error_line, error_message = parse_traceback(traceback_str)
    log_content = (
        f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Software: {software}\n"
        f"Version: {version}\n"
        f"OS: {os_info}\n"
        f"Error Type: {error_type}\n"
        f"File: {error_file}\n"
        f"Line: {error_line}\n"
        f"Message: {error_message}\n"
        f"Full Traceback:\n{traceback_str}\n"
    )
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_content)
    logging.info(f"Crash log written to {log_path}")
    return log_path

def send_log_to_discord(log_path, webhook_url):
    """
    Gửi file log tới Discord webhook.
    """
    try:
        with open(log_path, "rb") as f:
            files = {"file": (os.path.basename(log_path), f, "text/plain")}
            data = {"content": "Vezyl Translator - Crash Report"}
            response = requests.post(webhook_url, data=data, files=files, timeout=10)
            response.raise_for_status()
        logging.info("Crash log sent to Discord webhook successfully.")
        return True
    except Exception as exc:
        logging.error(f"Failed to send log to Discord: {exc}")
        return False

def show_error_dialog(error_file, error_type, log_path, sent_to_discord):
    """
    Hiển thị thông báo lỗi cho người dùng.
    """
    message = (
        f"{error_file or '[Unknown file]'}\n"
        f"An unexpected error occurred!\n\n"
        f"Error type: {error_type or '[Unknown error]'}\n"
        f"Details have been saved to:\n{log_path}"
    )
    if sent_to_discord:
        message += "\n\nWe have received your crash report and will fix it soon."
    mb.showerror("Vezyl Translator - Crash Handler", message)

def get_webhook_url():
    """
    Đọc webhook_url từ file config/client.toml.
    Trả về chuỗi URL nếu có, hoặc None nếu không tìm thấy.
    """
    config_path = os.path.join("config", "client.toml")
    try:
        config = toml.load(config_path)
        return config.get("webhook_url", None)
    except Exception as e:
        print(f"cannot read webhook_url: {e}")
        return None

def main():
    setup_logging()
    # Nhận lỗi từ dòng lệnh hoặc stdin
    if len(sys.argv) > 3:
        traceback_str = sys.argv[1]
        software = sys.argv[2]
        version = sys.argv[3]
    else:
        traceback_str = sys.stdin.read()
        software = DEFAULT_SOFTWARE
        version = DEFAULT_VERSION

    error_type, error_file, _, _ = parse_traceback(traceback_str)
    log_path = write_crash_log(traceback_str, software, version)

    webhook_url = get_webhook_url()
    sent_to_discord = False
    if webhook_url:
        sent_to_discord = send_log_to_discord(log_path, webhook_url)

    show_error_dialog(error_file, error_type, log_path, sent_to_discord)

if __name__ == "__main__":
    main()