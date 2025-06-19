import os
import json
from datetime import datetime
from googletrans import Translator as GoogleTranslator

from .file_flow import encrypt_aes, decrypt_aes, get_aes_key
from .utils import ensure_local_dir

def write_favorite_entry(original_text, translated_text, src_lang, dest_lang, note,
                         log_file, language_interface, theme_interface):
    """
    Lưu bản dịch yêu thích vào file log_file (mã hóa AES).
    Nếu translated_text rỗng thì sẽ tự động dịch original_text từ src_lang sang dest_lang.
    """
    print("trying to write favorite entry")
    ensure_local_dir(os.path.dirname(log_file))
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

def read_favorite_entries(log_file, language_interface, theme_interface):
    """
    Đọc và giải mã toàn bộ bản ghi yêu thích từ file log_file.
    Trả về list các dict bản ghi.
    """
    entries = []
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
                    entries.append(log_data)
                except Exception:
                    continue
    return entries

def delete_favorite_entry(log_file, language_interface, theme_interface, time_str, original_text):
    """
    Xóa một bản ghi yêu thích theo time_str và original_text.
    """
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

def delete_all_favorite_entries(log_file):
    """
    Xóa toàn bộ bản ghi yêu thích.
    """
    if os.path.exists(log_file):
        open(log_file, "w", encoding="utf-8").close()

def update_favorite_note(log_file, language_interface, theme_interface, entry_time, new_note):
    """
    Cập nhật ghi chú cho một bản ghi yêu thích theo entry_time.
    """
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