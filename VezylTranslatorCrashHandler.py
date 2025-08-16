import datetime
import logging
import os
import platform
import re
import sys
from typing import Tuple, Optional

import requests
import tkinter.messagebox as mb
import toml

from VezylTranslatorNeutron import constant
from VezylTranslatorProton.storage import decode_base64

# Constants
LOG_DIR = os.path.join(constant.LOCAL_DIR, "log")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DEFAULT_SOFTWARE = "Unknown"
DEFAULT_VERSION = "Unknown"

# Compile regex pattern once for better performance
TRACEBACK_PATTERN = re.compile(r'  File "(.+)", line (\d+), in (.+)')

def setup_logging() -> None:
    """Set up logging for crash handler."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "crash_handler.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format=LOG_FORMAT,
        encoding="utf-8"
    )
    

def parse_traceback(traceback_str: str) -> Tuple[str, str, str, str]:
    """
    Parse traceback to extract error type, file, line and message.
    
    Returns:
        Tuple of (error_type, error_file, error_line, error_message)
    """
    error_type = error_file = error_line = error_message = ""
    
    lines = traceback_str.strip().splitlines()
    if not lines:
        return error_type, error_file, error_line, error_message
        
    # Extract file and line from last traceback entry
    for line in reversed(lines):
        match = TRACEBACK_PATTERN.match(line)
        if match:
            error_file, error_line, _ = match.groups()
            break
    
    # Extract error type and message from last line
    last_line = lines[-1]
    if ": " in last_line:
        error_type, error_message = last_line.split(": ", 1)
    else:
        error_type = last_line
        
    return error_type, error_file, error_line, error_message

def write_crash_log(traceback_str: str, software: str, version: str) -> str:
    """
    Write error details to a timestamped log file.
    
    Returns:
        Path to the created log file
    """
    now = datetime.datetime.now()
    log_filename = f"crash_{now.strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(LOG_DIR, log_filename)
    
    error_type, error_file, error_line, error_message = parse_traceback(traceback_str)
    
    log_content = (
        f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Software: {software}\n"
        f"Version: {version}\n"
        f"OS: {platform.platform()}\n"
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

def send_log_to_discord(log_path: str, webhook_url: str) -> bool:
    """
    Send log file to Discord webhook.
    
    Returns:
        True if successful, False otherwise
    """
    if not webhook_url:
        logging.warning("No webhook URL provided")
        return False
        
    try:
        with open(log_path, "rb") as f:
            files = {"file": (os.path.basename(log_path), f, "text/plain")}
            data = {"content": "Vezyl Translator - Crash Report"}
            response = requests.post(
                webhook_url, 
                data=data, 
                files=files, 
                timeout=10
            )
            response.raise_for_status()
            
        logging.info("Crash log sent to Discord webhook successfully")
        return True
        
    except requests.RequestException as exc:
        logging.error(f"Network error sending log to Discord: {exc}")
        return False
    except IOError as exc:
        logging.error(f"File error sending log to Discord: {exc}")
        return False
    except Exception as exc:
        logging.error(f"Unexpected error sending log to Discord: {exc}")
        return False

def show_error_dialog(error_file: str, error_type: str, log_path: str, sent_to_discord: bool) -> None:
    """Display error dialog to the user."""
    message = (
        f"{error_file or '[Unknown file]'}\n"
        f"An unexpected error occurred!\n\n"
        f"Error type: {error_type or '[Unknown error]'}\n"
        f"Details have been saved to:\n{log_path}"
    )
    
    if sent_to_discord:
        message += "\n\nWe have received your crash report and will fix it soon."
        
    mb.showerror("Vezyl Translator - Crash Handler", message)

def get_webhook_url() -> Optional[str]:
    """
    Read webhook_url from config/client.toml.
    
    Returns:
        URL string if found, None otherwise
    """
    config_path = constant.CLIENT_CONFIG_FILE
    
    try:
        config = toml.load(config_path)
        encoded_url = config.get("webhook_url")
        
        if not encoded_url:
            logging.warning("No webhook_url found in config file")
            return None
            
        return decode_base64(encoded_url)
        
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_path}")
        return None
    except Exception as e:
        logging.error(f"Error reading webhook_url: {e}")
        return None

def main() -> None:
    """Main entry point for crash handler."""
    setup_logging()
    
    # Get traceback and app info
    if len(sys.argv) > 3:
        traceback_str = sys.argv[1]
        software = sys.argv[2]
        version = sys.argv[3]
    else:
        traceback_str = sys.stdin.read()
        software = DEFAULT_SOFTWARE
        version = DEFAULT_VERSION
    
    # Parse, log and report the error
    error_type, error_file, _, _ = parse_traceback(traceback_str)
    log_path = write_crash_log(traceback_str, software, version)
    
    webhook_url = get_webhook_url()
    sent_to_discord = webhook_url and send_log_to_discord(log_path, webhook_url)
    
    show_error_dialog(error_file, error_type, log_path, sent_to_discord)

if __name__ == "__main__":
    main()