"""
Thư viện chứa các hằng số chung cho toàn bộ ứng dụng Vezyl Translator.
"""

import os

# General constants
SOFTWARE = "Vezyl Translator"
SOFTWARE_VERSION = "1.5.2"

# Paths
LOCAL_DIR = os.path.join(os.getenv('APPDATA'), "Vezyl_Translator", "local")
TRANSLATE_LOG_FILE = os.path.join(LOCAL_DIR, "translate_log.enc")
FAVORITE_LOG_FILE = os.path.join(LOCAL_DIR, "favorite_log.enc")

RESOURCES_DIR = "resources"
LOCALES_DIR = os.path.join(RESOURCES_DIR, "locales")
MARIAN_MODELS_DIR = os.path.join(RESOURCES_DIR, "marian_models")
MARIAN_MODELS_FALLBACK_DIR = os.path.join("VezylTranslator", "marian_models")


CONFIG_DIR = "config"
DEFAULT_CONFIG_FILE = os.path.join(CONFIG_DIR, "general.json")
PERFORMANCE_CONFIG_FILE = os.path.join(CONFIG_DIR, "performance.json")
CLIENT_CONFIG_FILE = os.path.join(CONFIG_DIR, "client.toml")

# cache
last_translated_text = ""