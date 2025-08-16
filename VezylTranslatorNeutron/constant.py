"""
Zentrum Constants and Configuration
Enhanced with type hints and better organization
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import os
from typing import Final, Dict, List, Optional
from pathlib import Path


# === Software Information ===
SOFTWARE_NAME: Final[str] = "Vezyl Translator"
SOFTWARE_VERSION: Final[str] = "1.5.14"

# Backward compatibility
SOFTWARE = SOFTWARE_NAME
DEFAULT_CONFIG_FILE = None  # Will be set below


# === Base Directory Paths ===
BASE_DIR: Final[Path] = Path(__file__).parent.parent
RESOURCES_DIR: Final[str] = "resources"
CONFIG_DIR: Final[str] = "config"

# Local directory (Windows APPDATA)
LOCAL_DIR: Final[str] = os.path.join(os.getenv('APPDATA'), "Vezyl_Translator", "local")
LOG_DIR: Final[str] = os.path.join(LOCAL_DIR, "log")


# === Configuration Files ===
CLIENT_CONFIG_FILE: Final[str] = os.path.join(CONFIG_DIR, "client.toml")
GENERAL_CONFIG_FILE: Final[str] = os.path.join(CONFIG_DIR, "general.json")
PERFORMANCE_CONFIG_FILE: Final[str] = os.path.join(CONFIG_DIR, "performance.json")

# Backward compatibility
DEFAULT_CONFIG_FILE = GENERAL_CONFIG_FILE


# === Resource Directories ===
LOCALES_DIR: Final[str] = os.path.join(RESOURCES_DIR, "locales")
MARIAN_MODELS_DIR: Final[str] = os.path.join(RESOURCES_DIR, "marian_models")
MARIAN_MODELS_FALLBACK_DIR: Final[str] = os.path.join("VezylTranslator", "marian_models")
ICONS_DIR: Final[str] = RESOURCES_DIR
ASSETS_DIR: Final[str] = RESOURCES_DIR


# === Data Files ===
TRANSLATE_LOG_FILE: Final[str] = os.path.join(LOCAL_DIR, "translate_log.enc")
FAVORITE_LOG_FILE: Final[str] = os.path.join(LOCAL_DIR, "favorite_log.enc")


# === Resource Files ===
LOGO_FILE: Final[str] = os.path.join(RESOURCES_DIR, "logo.ico")


# === Application Defaults ===
DEFAULT_LOCALE: Final[str] = "en"
DEFAULT_THEME: Final[str] = "dark"

# === Supported Languages ===
SUPPORTED_LOCALES: Final[List[str]] = ["en", "vi"]
SUPPORTED_THEMES: Final[List[str]] = ["light", "dark", "auto"]


# === Translation Provider Constants ===
class TranslationProviders:
    """Translation provider constants"""
    GOOGLE: Final[str] = "google"
    MARIAN: Final[str] = "marian"
    
    ALL_PROVIDERS: Final[List[str]] = [GOOGLE, MARIAN]
    DEFAULT_PROVIDER: Final[str] = GOOGLE


# === Language Code Mappings ===
LANGUAGE_CODES: Final[Dict[str, str]] = {
    "Vietnamese": "vi",
    "English": "en",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
    "Russian": "ru",
    "Chinese": "zh-cn",
    "Japanese": "ja",
    "Korean": "ko",
}


# === Performance Constants ===
class PerformanceSettings:
    """Performance-related constants"""
    MAX_HISTORY_ITEMS: Final[int] = 100
    MAX_FAVORITES_ITEMS: Final[int] = 50
    CLIPBOARD_CHECK_INTERVAL: Final[float] = 0.8
    UI_UPDATE_DEBOUNCE: Final[int] = 300  # milliseconds
    TRANSLATION_TIMEOUT: Final[int] = 30  # seconds
    MAX_CONCURRENT_TRANSLATIONS: Final[int] = 3
    MEMORY_CLEANUP_INTERVAL: Final[int] = 60  # seconds





# === Environment Variables ===
class EnvVars:
    """Environment variable names"""
    VEZYL_FAST_STARTUP: Final[str] = "VEZYL_FAST_STARTUP"
    VEZYL_DEBUG: Final[str] = "VEZYL_DEBUG"
    VEZYL_LOG_LEVEL: Final[str] = "VEZYL_LOG_LEVEL"
    VEZYL_CONFIG_DIR: Final[str] = "VEZYL_CONFIG_DIR"
    VEZYL_THEME_OVERRIDE: Final[str] = "VEZYL_THEME_OVERRIDE"
    DISABLE_IMMEDIATE_MODEL_LOADING: Final[str] = "DISABLE_IMMEDIATE_MODEL_LOADING"


# === API Constants ===
class APIConstants:
    """API-related constants"""
    USER_AGENT: Final[str] = f"{SOFTWARE_NAME}/{SOFTWARE_VERSION}"





# === Cache Variables ===
last_translated_text: str = ""  # Backward compatibility


# === Utility Functions ===

def get_full_version_string() -> str:
    """Get full version string with software name"""
    return f"{SOFTWARE_NAME} v{SOFTWARE_VERSION}"


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return os.getenv(EnvVars.VEZYL_DEBUG, "0").lower() in ("1", "true", "yes")


def is_fast_startup() -> bool:
    """Check if fast startup mode is enabled"""
    return os.getenv(EnvVars.VEZYL_FAST_STARTUP, "0") == "1"


# === Validation Functions ===

def validate_language_code(code: str) -> bool:
    """Validate language code"""
    return code in LANGUAGE_CODES.values()


def validate_locale(locale: str) -> bool:
    """Validate locale code"""
    return locale in SUPPORTED_LOCALES


def validate_theme(theme: str) -> bool:
    """Validate theme name"""
    return theme in SUPPORTED_THEMES


def validate_provider(provider: str) -> bool:
    """Validate translation provider"""
    return provider in TranslationProviders.ALL_PROVIDERS


# === Path Helpers ===

def ensure_directories() -> None:
    """Ensure all required directories exist"""
    import os
    directories = [CONFIG_DIR, LOCAL_DIR, LOG_DIR]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


def get_config_path(filename: str) -> str:
    """Get full path for config file"""
    return os.path.join(CONFIG_DIR, filename)


def get_resource_path(filename: str) -> str:
    """Get full path for resource file"""
    return os.path.join(RESOURCES_DIR, filename)


def get_local_path(filename: str) -> str:
    """Get full path for local file"""
    return os.path.join(LOCAL_DIR, filename)