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
SOFTWARE_VERSION: Final[str] = "1.5.3"
SOFTWARE_VERSION_MAJOR: Final[int] = 1
SOFTWARE_VERSION_MINOR: Final[int] = 5
SOFTWARE_VERSION_PATCH: Final[int] = 3
SOFTWARE_URL: Final[str] = "https://vezyl.io/translator"
SOFTWARE_AUTHOR: Final[str] = "Tuan Viet Nguyen"
SOFTWARE_COPYRIGHT: Final[str] = "Copyright (c) 2025 Vezyl. All rights reserved."

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
LOGO_BLACK_FILE: Final[str] = os.path.join(RESOURCES_DIR, "logo_black.ico")
LOGO_RED_FILE: Final[str] = os.path.join(RESOURCES_DIR, "logo_red.ico")
LOGO_PNG_FILE: Final[str] = os.path.join(RESOURCES_DIR, "logo.png")
VERSION_FILE: Final[str] = os.path.join(RESOURCES_DIR, "version")

# Icon assets
FAVORITE_ICON: Final[str] = os.path.join(RESOURCES_DIR, "favorite.png")
HISTORY_ICON: Final[str] = os.path.join(RESOURCES_DIR, "history.png")
SETTINGS_ICON: Final[str] = os.path.join(RESOURCES_DIR, "settings.png")
REVERSE_ICON: Final[str] = os.path.join(RESOURCES_DIR, "reverse.png")
SAVE_ICON: Final[str] = os.path.join(RESOURCES_DIR, "save_btn.png")


# === Application Defaults ===
DEFAULT_LOCALE: Final[str] = "en"
DEFAULT_THEME: Final[str] = "dark"
DEFAULT_FONT: Final[str] = "Segoe UI"
DEFAULT_FONT_SIZE: Final[int] = 12

# Window defaults
DEFAULT_WINDOW_WIDTH: Final[int] = 1000
DEFAULT_WINDOW_HEIGHT: Final[int] = 700
MIN_WINDOW_WIDTH: Final[int] = 800
MIN_WINDOW_HEIGHT: Final[int] = 600


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

REVERSE_LANGUAGE_CODES: Final[Dict[str, str]] = {
    v: k for k, v in LANGUAGE_CODES.items()
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


# === Hotkey Constants ===
class HotkeyDefaults:
    """Default hotkey combinations"""
    GLOBAL_TRANSLATE: Final[str] = "ctrl+shift+t"
    GLOBAL_REVERSE: Final[str] = "ctrl+shift+r"
    SHOW_HIDE: Final[str] = "ctrl+shift+v"
    SCREENSHOT_TRANSLATE: Final[str] = "ctrl+shift+s"


# === Error Messages ===
class ErrorMessages:
    """Centralized error message constants"""
    FILE_NOT_FOUND: Final[str] = "File not found: {file_path}"
    INVALID_CONFIG: Final[str] = "Invalid configuration: {config_name}"
    NETWORK_FAILURE: Final[str] = "Network connection failed: {details}"
    TRANSLATION_FAILED: Final[str] = "Translation failed: {provider} - {error}"
    MODEL_LOAD_FAILED: Final[str] = "Model loading failed: {model_name}"
    PERMISSION_DENIED: Final[str] = "Permission denied: {action}"
    RESOURCE_NOT_FOUND: Final[str] = "Resource not found: {resource}"
    
    # Common patterns
    GENERIC_ERROR: Final[str] = "An error occurred: {details}"
    TIMEOUT_ERROR: Final[str] = "Operation timed out after {seconds} seconds"
    VALIDATION_ERROR: Final[str] = "Validation failed: {field} - {reason}"


# === Success Messages ===
class SuccessMessages:
    """Centralized success message constants"""
    CONFIG_SAVED: Final[str] = "Configuration saved successfully"
    TRANSLATION_COMPLETE: Final[str] = "Translation completed"
    MODEL_LOADED: Final[str] = "Model loaded: {model_name}"
    CACHE_CLEARED: Final[str] = "Cache cleared successfully"
    EXPORT_COMPLETE: Final[str] = "Export completed: {file_path}"
    IMPORT_COMPLETE: Final[str] = "Import completed: {count} items"


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
    REQUEST_TIMEOUT: Final[int] = 10  # seconds
    MAX_RETRIES: Final[int] = 3
    RETRY_DELAY: Final[float] = 1.0  # seconds
    
    # Google Translate
    GOOGLE_TRANSLATE_URL: Final[str] = "https://translate.googleapis.com/translate_a/single"
    
    # Rate limiting
    REQUESTS_PER_MINUTE: Final[int] = 60
    BURST_LIMIT: Final[int] = 10


# === File System Constants ===
class FileSystem:
    """File system related constants"""
    MAX_FILE_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
    BACKUP_EXTENSION: Final[str] = ".bak"
    TEMP_EXTENSION: Final[str] = ".tmp"
    
    # File patterns
    CONFIG_PATTERN: Final[str] = "*.json"
    LOCALE_PATTERN: Final[str] = "*.json"
    MODEL_PATTERN: Final[str] = "pytorch_model.bin"


# === Cache Variables ===
last_translated_text: str = ""  # Backward compatibility


# === Utility Functions ===

def get_version_tuple() -> tuple[int, int, int]:
    """Get version as tuple of integers"""
    return (SOFTWARE_VERSION_MAJOR, SOFTWARE_VERSION_MINOR, SOFTWARE_VERSION_PATCH)


def get_full_version_string() -> str:
    """Get full version string with software name"""
    return f"{SOFTWARE_NAME} v{SOFTWARE_VERSION}"


def get_user_agent() -> str:
    """Get user agent string for HTTP requests"""
    return APIConstants.USER_AGENT


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return os.getenv(EnvVars.VEZYL_DEBUG, "0").lower() in ("1", "true", "yes")


def is_fast_startup() -> bool:
    """Check if fast startup mode is enabled"""
    return os.getenv(EnvVars.VEZYL_FAST_STARTUP, "0") == "1"


def get_log_level() -> str:
    """Get configured log level"""
    return os.getenv(EnvVars.VEZYL_LOG_LEVEL, "INFO").upper()


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