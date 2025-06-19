import os
import json

def load_config(config_file, default_config):
    """
    Đọc file config JSON, trả về dict config (nếu lỗi trả về default_config).
    """
    config = default_config.copy()
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config)
    except Exception as e:
        print(f"Lỗi khi tải cấu hình: {e}")
    return config

def save_config(config_file, config_data):
    """
    Ghi dict config_data ra file JSON.
    """
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi khi lưu cấu hình: {e}")

def get_default_config():
    """
    Trả về dict config mặc định.
    """
    return {
        "interface_language": 'vi',
        "start_at_startup": True,
        "show_homepage_at_startup": True,
        "always_show_transtale": True,
        "save_translate_history": True,
        "auto_save_after": 3000,
        "icon_size": 60,
        "icon_dissapear_after": 5,
        "popup_dissapear_after": 5,
        "max_length_on_popup": 500,
        "max_history_items": 20,
        "hotkey": 'ctrl+shift+c',
        "clipboard_hotkey": 'ctrl+shift+v',
        "dest_lang": 'vi',
        "font": "JetBrains Mono",
        "default_fonts": [
            "JetBrains Mono", "Consolas", "Segoe UI", "Calibri", "Arial", "Verdana"
        ],
        "lang_display": {
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
    }