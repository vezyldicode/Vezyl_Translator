"""
Configuration Management System for VezylTranslator
Centralized config handling for all configuration types
Author: Tuan Viet Nguyen  
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import os
import json
import toml
import base64
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field, asdict
from pathlib import Path

from VezylTranslatorNeutron import constant


@dataclass
class AppConfig:
    """Main application configuration"""
    # Interface settings
    interface_language: str = 'vi'
    font: str = "JetBrains Mono"
    default_fonts: List[str] = field(default_factory=lambda: [
        "JetBrains Mono", "Consolas", "Segoe UI", "Calibri", "Arial", "Verdana"
    ])
    
    # Startup settings
    start_at_startup: bool = True
    show_homepage_at_startup: bool = True
    
    # Translation settings
    always_show_transtale: bool = True
    dest_lang: str = 'vi'
    translation_model: str = 'google'
    translation_models: Dict[str, str] = field(default_factory=lambda: {
        "google": "🌐 Google Translator",
        "deepl": "🔬 DeepL Translator", 
        "marian": "🤖 Marian MT (Offline)"
    })
    lang_display: Dict[str, str] = field(default_factory=lambda: {
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
    })
    
    # Input/Control settings
    enable_ctrl_tracking: bool = False
    enable_hotkeys: bool = False
    hotkey: str = 'ctrl+shift+c'
    clipboard_hotkey: str = 'ctrl+shift+v'
    ctrl_to_exit: bool = False
    
    # History settings
    save_translate_history: bool = True
    max_history_items: int = 20
    auto_save_after: int = 3000
    
    # UI/Popup settings 
    icon_size: int = 60
    icon_dissapear_after: int = 5
    popup_dissapear_after: int = 5
    max_length_on_popup: int = 500


@dataclass
class ClientConfig:
    """Client-specific configuration (encrypted)"""
    language_interface: str = ""
    theme_interface: str = ""
    webhook_url: str = ""


@dataclass
class PerformanceConfig:
    """Performance-related configuration"""
    fast_startup_enabled: bool = True
    lazy_import_enabled: bool = True
    clipboard_optimization: bool = True
    translation_cache_size: int = 100
    max_concurrent_translations: int = 3
    startup_delay_ms: int = 100
    

class ConfigManager:
    """Unified configuration manager for all config types"""
    
    def __init__(self):
        self._app_config: Optional[AppConfig] = None
        self._client_config: Optional[ClientConfig] = None
        self._performance_config: Optional[PerformanceConfig] = None
        
        # Config file paths
        self.app_config_file = constant.DEFAULT_CONFIG_FILE
        self.client_config_file = constant.CLIENT_CONFIG_FILE
        self.performance_config_file = constant.PERFORMANCE_CONFIG_FILE
        
        # Ensure config directory exists
        self._ensure_config_directory()
    
    def _ensure_config_directory(self):
        """Ensure config directory exists"""
        config_dir = Path(constant.CONFIG_DIR)
        config_dir.mkdir(exist_ok=True)
    
    # === App Configuration ===
    
    def load_app_config(self) -> AppConfig:
        """Load main application configuration"""
        if self._app_config is None:
            self._app_config = self._load_app_config_from_file()
        return self._app_config
    
    def _load_app_config_from_file(self) -> AppConfig:
        """Load app config from JSON file"""
        default_config = AppConfig()
        
        try:
            if os.path.exists(self.app_config_file):
                with open(self.app_config_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                # Update default config with file data
                default_dict = asdict(default_config)
                default_dict.update(file_data)
                
                # Create new config from merged data
                return AppConfig(**{k: v for k, v in default_dict.items() 
                                  if k in AppConfig.__dataclass_fields__})
        except Exception as e:
            print(f"Error loading app config: {e}")
        
        return default_config
    
    def save_app_config(self, config: Optional[AppConfig] = None) -> bool:
        """Save app configuration to file"""
        if config is None:
            config = self._app_config
        
        if config is None:
            return False
        
        try:
            config_dict = asdict(config)
            with open(self.app_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            self._app_config = config
            return True
        except Exception as e:
            print(f"Error saving app config: {e}")
            return False
    
    def update_app_config(self, **kwargs) -> bool:
        """Update app config with new values"""
        config = self.load_app_config()
        
        # Update only valid fields
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return self.save_app_config(config)
    
    # === Client Configuration ===
    
    def load_client_config(self) -> ClientConfig:
        """Load client configuration from TOML"""
        if self._client_config is None:
            self._client_config = self._load_client_config_from_file()
        return self._client_config
    
    def _load_client_config_from_file(self) -> ClientConfig:
        """Load client config from TOML file"""
        default_config = ClientConfig()
        
        try:
            if os.path.exists(self.client_config_file):
                with open(self.client_config_file, 'r', encoding='utf-8') as f:
                    file_data = toml.load(f)
                
                return ClientConfig(
                    language_interface=file_data.get('language_interface', ''),
                    theme_interface=file_data.get('theme_interface', ''),
                    webhook_url=file_data.get('webhook_url', '')
                )
        except Exception as e:
            print(f"Error loading client config: {e}")
        
        return default_config
    
    def save_client_config(self, config: Optional[ClientConfig] = None) -> bool:
        """Save client configuration to TOML file"""
        if config is None:
            config = self._client_config
        
        if config is None:
            return False
        
        try:
            config_dict = asdict(config)
            with open(self.client_config_file, 'w', encoding='utf-8') as f:
                toml.dump(config_dict, f)
            
            self._client_config = config
            return True
        except Exception as e:
            print(f"Error saving client config: {e}")
            return False
    
    # === Performance Configuration ===
    
    def load_performance_config(self) -> PerformanceConfig:
        """Load performance configuration"""
        if self._performance_config is None:
            self._performance_config = self._load_performance_config_from_file()
        return self._performance_config
    
    def _load_performance_config_from_file(self) -> PerformanceConfig:
        """Load performance config from JSON file"""
        default_config = PerformanceConfig()
        
        try:
            if os.path.exists(self.performance_config_file):
                with open(self.performance_config_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                # Update default config with file data
                default_dict = asdict(default_config)
                default_dict.update(file_data)
                
                return PerformanceConfig(**{k: v for k, v in default_dict.items() 
                                          if k in PerformanceConfig.__dataclass_fields__})
        except Exception as e:
            print(f"Error loading performance config: {e}")
        
        return default_config
    
    def save_performance_config(self, config: Optional[PerformanceConfig] = None) -> bool:
        """Save performance configuration"""
        if config is None:
            config = self._performance_config
        
        if config is None:
            return False
        
        try:
            config_dict = asdict(config)
            with open(self.performance_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            
            self._performance_config = config
            return True
        except Exception as e:
            print(f"Error saving performance config: {e}")
            return False
    
    # === Unified Interface ===
    
    def load_all_configs(self) -> tuple[AppConfig, ClientConfig, PerformanceConfig]:
        """Load all configuration types"""
        return (
            self.load_app_config(),
            self.load_client_config(), 
            self.load_performance_config()
        )
    
    def reload_all_configs(self) -> tuple[AppConfig, ClientConfig, PerformanceConfig]:
        """Force reload all configurations from files"""
        self._app_config = None
        self._client_config = None
        self._performance_config = None
        return self.load_all_configs()
    
    def get_config_value(self, key: str, config_type: str = 'app') -> Any:
        """Get specific config value by key and type"""
        if config_type == 'app':
            config = self.load_app_config()
        elif config_type == 'client':
            config = self.load_client_config()
        elif config_type == 'performance':
            config = self.load_performance_config()
        else:
            raise ValueError(f"Unknown config type: {config_type}")
        
        return getattr(config, key, None)
    
    def set_config_value(self, key: str, value: Any, config_type: str = 'app') -> bool:
        """Set specific config value by key and type"""
        if config_type == 'app':
            return self.update_app_config(**{key: value})
        elif config_type == 'client':
            config = self.load_client_config()
            if hasattr(config, key):
                setattr(config, key, value)
                return self.save_client_config(config)
        elif config_type == 'performance':
            config = self.load_performance_config()
            if hasattr(config, key):
                setattr(config, key, value)
                return self.save_performance_config(config)
        
        return False
    
    # === Migration & Validation ===
    
    def migrate_from_legacy_config(self, legacy_config_dict: Dict[str, Any]) -> bool:
        """Migrate from legacy config dictionary to new config system"""
        try:
            # Create app config from legacy data
            app_config = AppConfig()
            app_dict = asdict(app_config)
            
            # Update with legacy values that exist
            for key, value in legacy_config_dict.items():
                if key in app_dict:
                    app_dict[key] = value
            
            new_app_config = AppConfig(**app_dict)
            return self.save_app_config(new_app_config)
        except Exception as e:
            print(f"Error migrating legacy config: {e}")
            return False
    
    def validate_configs(self) -> Dict[str, List[str]]:
        """Validate all configurations and return any errors"""
        errors = {
            'app': [],
            'client': [],
            'performance': []
        }
        
        try:
            # Validate app config
            app_config = self.load_app_config()
            if not app_config.interface_language:
                errors['app'].append("Interface language is required")
            if app_config.max_history_items < 1:
                errors['app'].append("Max history items must be positive")
            
            # Validate client config
            client_config = self.load_client_config()
            # Client config validation would go here
            
            # Validate performance config
            perf_config = self.load_performance_config()
            if perf_config.translation_cache_size < 0:
                errors['performance'].append("Translation cache size cannot be negative")
        
        except Exception as e:
            errors['app'].append(f"Config validation error: {e}")
        
        return errors


# === Legacy Support Functions ===

def load_config(config_file: str, default_config: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    manager = ConfigManager()
    
    # If it's the main config file, use new system
    if config_file == constant.DEFAULT_CONFIG_FILE:
        app_config = manager.load_app_config()
        return asdict(app_config)
    
    # Fall back to old method for other files
    config = default_config.copy()
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config)
    except Exception as e:
        print(f"Error loading config: {e}")
    return config


def save_config(config_file: str, config_data: Dict[str, Any]) -> bool:
    """Legacy function for backward compatibility"""
    manager = ConfigManager()
    
    # If it's the main config file, use new system
    if config_file == constant.DEFAULT_CONFIG_FILE:
        return manager.migrate_from_legacy_config(config_data)
    
    # Fall back to old method for other files
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_default_config() -> Dict[str, Any]:
    """Legacy function for backward compatibility"""
    return asdict(AppConfig())


# === Global Config Manager Instance ===
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance"""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager


def reset_config_manager():
    """Reset the global config manager (for testing)"""
    global _global_config_manager
    _global_config_manager = None


# === Convenience Functions ===

def get_app_config() -> AppConfig:
    """Get application configuration"""
    return get_config_manager().load_app_config()


def get_client_config() -> ClientConfig:
    """Get client configuration"""
    return get_config_manager().load_client_config()


def get_performance_config() -> PerformanceConfig:
    """Get performance configuration"""
    return get_config_manager().load_performance_config()


def update_app_setting(key: str, value: Any) -> bool:
    """Update a single app setting"""
    return get_config_manager().set_config_value(key, value, 'app')


def get_app_setting(key: str, default: Any = None) -> Any:
    """Get a single app setting"""
    try:
        return get_config_manager().get_config_value(key, 'app')
    except:
        return default
