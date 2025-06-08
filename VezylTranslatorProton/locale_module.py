import json
import os

_locale_dict = {}

def load_locale(locale_code, locales_dir=None):
    global _locale_dict
    path = os.path.join(locales_dir, f"{locale_code}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _locale_dict = json.load(f)
    except Exception as e:
        print(f"Cannot load locale {locale_code}: {e}")
        _locale_dict = {}

def _(key):
    return _locale_dict.get(key, key)