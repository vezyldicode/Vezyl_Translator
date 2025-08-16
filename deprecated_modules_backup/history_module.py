import os
import json
from datetime import datetime
from VezylTranslatorProton.file_flow import encrypt_aes, decrypt_aes, get_aes_key
from VezylTranslatorProton.utils import ensure_local_dir


def write_log_entry(
    last_translated_text, src_lang, dest_lang, source,
    log_file, language_interface, theme_interface,
    save_translate_history=True, max_items=20
):
    """
    Ghi một bản ghi vào file lịch sử dịch (mã hóa AES).
    """
    ensure_local_dir(os.path.dirname(log_file))
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

def read_history_entries(log_file, language_interface, theme_interface):
    """
    Đọc và giải mã toàn bộ lịch sử dịch.
    """
    key = get_aes_key(language_interface, theme_interface)
    history = []
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
                    print(f"Lỗi giải mã log: {e}")
    return history

def delete_history_entry(log_file, language_interface, theme_interface, time_str, last_translated_text):
    """
    Xóa một entry khỏi lịch sử dịch dựa trên time và last_translated_text.
    """
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

def delete_all_history_entries(log_file):
    """
    Xóa toàn bộ lịch sử dịch.
    """
    if os.path.exists(log_file):
        open(log_file, "w", encoding="utf-8").close()
