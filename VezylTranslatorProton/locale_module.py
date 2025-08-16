import json
import os
from VezylTranslatorNeutron.constant import LOCALES_DIR

_locale_dict = {}

def load_locale(locale_code, locales_dir=None):
    global _locale_dict
    if locales_dir is None:
        locales_dir = LOCALES_DIR
    
    # Handle None or empty locale_code
    if not locale_code:
        locale_code = "en"  # Default to English
    
    path = os.path.join(locales_dir, f"{locale_code}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _locale_dict = json.load(f)
    except Exception as e:
        print(f"Cannot load locale {locale_code}: {e}")
        # Try to fallback to English if the requested locale fails
        if locale_code != "en":
            try:
                fallback_path = os.path.join(locales_dir, "en.json")
                with open(fallback_path, "r", encoding="utf-8") as f:
                    _locale_dict = json.load(f)
                print(f"Loaded fallback English locale")
            except Exception as fallback_e:
                print(f"Cannot load fallback locale: {fallback_e}")
                _locale_dict = {}
        else:
            _locale_dict = {}

def _(key):
    return _locale_dict.get(key, key)