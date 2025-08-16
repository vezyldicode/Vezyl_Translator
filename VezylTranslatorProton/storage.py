"""
Unified Storage System for VezylTranslator
Consolidates history, favorites, encryption, and file operations
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading

# Crypto imports
try:
    from Crypto.Cipher import AES
    from Crypto.Random import get_random_bytes
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[WARNING] Crypto library not available - encryption disabled")

from VezylTranslatorElectron.helpers import ensure_local_dir


class StorageType(Enum):
    """Types of storage entries"""
    HISTORY = "history"
    FAVORITE = "favorite"


@dataclass
class StorageEntry:
    """Base storage entry container"""
    entry_id: str
    entry_type: str
    timestamp: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StorageEntry':
        """Create from dictionary"""
        return cls(
            entry_id=data.get("entry_id", ""),
            entry_type=data.get("entry_type", ""),
            timestamp=data.get("timestamp", ""),
            data=data.get("data", {})
        )


@dataclass
class HistoryEntry:
    """History entry container"""
    time: str
    last_translated_text: str
    src_lang: str
    dest_lang: str
    source: str  # "homepage" or "popup"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoryEntry':
        """Create from dictionary"""
        return cls(
            time=data.get("time", ""),
            last_translated_text=data.get("last_translated_text", ""),
            src_lang=data.get("src_lang", ""),
            dest_lang=data.get("dest_lang", ""),
            source=data.get("source", "homepage")
        )


@dataclass
class FavoriteEntry:
    """Favorite entry container"""
    time: str
    original_text: str
    translated_text: str
    src_lang: str
    dest_lang: str
    note: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for backward compatibility"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FavoriteEntry':
        """Create from dictionary"""
        return cls(
            time=data.get("time", ""),
            original_text=data.get("original_text", ""),
            translated_text=data.get("translated_text", ""),
            src_lang=data.get("src_lang", ""),
            dest_lang=data.get("dest_lang", ""),
            note=data.get("note", "")
        )


class CryptoManager:
    """Handles encryption and decryption operations"""
    
    def __init__(self):
        self.crypto_available = CRYPTO_AVAILABLE
    
    def get_aes_key(self, language_interface: str, theme_interface: str) -> bytes:
        """Generate AES key from interface settings"""
        if not self.crypto_available:
            # Fallback key for when crypto is not available
            return b'VezylTranslator01'  # 16 bytes
        
        theme_ui = language_interface + theme_interface
        try:
            return base64.b64decode(theme_ui)
        except:
            # Fallback if base64 decode fails
            # Pad or truncate to 16 bytes
            key_bytes = theme_ui.encode('utf-8')
            if len(key_bytes) < 16:
                key_bytes = key_bytes + b'0' * (16 - len(key_bytes))
            elif len(key_bytes) > 16:
                key_bytes = key_bytes[:16]
            return key_bytes
    
    def pad(self, data: bytes) -> bytes:
        """Pad data to AES block size"""
        pad_len = 16 - len(data) % 16
        return data + bytes([pad_len] * pad_len)
    
    def unpad(self, data: bytes) -> bytes:
        """Remove padding from data"""
        if not data:
            return data
        pad_len = data[-1]
        return data[:-pad_len]
    
    def encrypt_aes(self, text: str, key: bytes) -> str:
        """Encrypt text using AES"""
        if not self.crypto_available:
            # Simple base64 encoding as fallback
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
        try:
            iv = get_random_bytes(16)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            data = text.encode('utf-8')
            ct_bytes = cipher.encrypt(self.pad(data))
            return base64.b64encode(iv + ct_bytes).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {e}")
            # Fallback to base64
            return base64.b64encode(text.encode('utf-8')).decode('utf-8')
    
    def decrypt_aes(self, enc_text: str, key: bytes) -> str:
        """Decrypt text using AES"""
        if not self.crypto_available:
            # Simple base64 decoding as fallback
            try:
                return base64.b64decode(enc_text).decode('utf-8')
            except:
                return enc_text  # Return as-is if not base64
        
        try:
            raw = base64.b64decode(enc_text)
            iv = raw[:16]
            ct = raw[16:]
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt = cipher.decrypt(ct)
            return self.unpad(pt).decode('utf-8')
        except Exception as e:
            print(f"Decryption error: {e}")
            # Try fallback base64 decode
            try:
                return base64.b64decode(enc_text).decode('utf-8')
            except:
                return enc_text  # Return as-is if can't decrypt


class StorageManager:
    """Unified storage manager for history, favorites, and file operations"""
    
    def __init__(self):
        self.crypto = CryptoManager()
        self._cache = {}
        self._cache_lock = threading.Lock()
    
    def _get_cache_key(self, log_file: str, entry_type: str) -> str:
        """Generate cache key"""
        return f"{entry_type}:{log_file}"
    
    def _invalidate_cache(self, log_file: str, entry_type: str):
        """Invalidate cache for file"""
        cache_key = self._get_cache_key(log_file, entry_type)
        with self._cache_lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
    
    def _read_encrypted_file(self, log_file: str, language_interface: str, theme_interface: str) -> List[str]:
        """Read and return raw encrypted lines from file"""
        lines = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = [line.rstrip("\n") for line in f if line.strip()]
            except Exception as e:
                print(f"Error reading file {log_file}: {e}")
        return lines
    
    def _write_encrypted_file(self, log_file: str, lines: List[str]):
        """Write encrypted lines to file"""
        try:
            ensure_local_dir(os.path.dirname(log_file))
            with open(log_file, "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")
        except Exception as e:
            print(f"Error writing file {log_file}: {e}")
    
    def _decrypt_entry(self, encrypted_line: str, language_interface: str, theme_interface: str) -> Optional[Dict[str, Any]]:
        """Decrypt and parse single entry"""
        try:
            key = self.crypto.get_aes_key(language_interface, theme_interface)
            log_json = self.crypto.decrypt_aes(encrypted_line, key)
            return json.loads(log_json)
        except Exception as e:
            print(f"Error decrypting entry: {e}")
            return None
    
    def _encrypt_entry(self, entry_data: Dict[str, Any], language_interface: str, theme_interface: str) -> str:
        """Encrypt single entry"""
        try:
            key = self.crypto.get_aes_key(language_interface, theme_interface)
            log_line = json.dumps(entry_data, ensure_ascii=False)
            return self.crypto.encrypt_aes(log_line, key)
        except Exception as e:
            print(f"Error encrypting entry: {e}")
            return ""
    
    # === HISTORY OPERATIONS ===
    
    def write_history_entry(
        self, 
        last_translated_text: str, 
        src_lang: str, 
        dest_lang: str, 
        source: str,
        log_file: str, 
        language_interface: str, 
        theme_interface: str,
        save_translate_history: bool = True, 
        max_items: int = 20
    ) -> bool:
        """Write history entry to encrypted file"""
        if not save_translate_history:
            return False
        
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry_data = {
                "time": now,
                "last_translated_text": last_translated_text,
                "src_lang": src_lang,
                "dest_lang": dest_lang,
                "source": source
            }
            
            # Read existing lines
            lines = self._read_encrypted_file(log_file, language_interface, theme_interface)
            
            # Limit to max_items
            if len(lines) >= max_items:
                lines = lines[-(max_items-1):]
            
            # Add new entry
            encrypted_line = self._encrypt_entry(entry_data, language_interface, theme_interface)
            if encrypted_line:
                lines.append(encrypted_line)
                self._write_encrypted_file(log_file, lines)
                self._invalidate_cache(log_file, "history")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error writing history entry: {e}")
            return False
    
    def read_history_entries(self, log_file: str, language_interface: str, theme_interface: str) -> List[HistoryEntry]:
        """Read all history entries"""
        # Check cache first
        cache_key = self._get_cache_key(log_file, "history")
        with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        entries = []
        lines = self._read_encrypted_file(log_file, language_interface, theme_interface)
        
        for line in lines:
            entry_data = self._decrypt_entry(line, language_interface, theme_interface)
            if entry_data:
                try:
                    history_entry = HistoryEntry.from_dict(entry_data)
                    entries.append(history_entry)
                except Exception as e:
                    print(f"Error parsing history entry: {e}")
        
        # Cache results
        with self._cache_lock:
            self._cache[cache_key] = entries
        
        return entries
    
    def delete_history_entry(self, log_file: str, language_interface: str, theme_interface: str, time_str: str, last_translated_text: str) -> bool:
        """Delete specific history entry"""
        try:
            lines = self._read_encrypted_file(log_file, language_interface, theme_interface)
            new_lines = []
            
            for line in lines:
                entry_data = self._decrypt_entry(line, language_interface, theme_interface)
                if entry_data:
                    if not (entry_data.get("time") == time_str and entry_data.get("last_translated_text") == last_translated_text):
                        new_lines.append(line)
                else:
                    # Keep unreadable lines
                    new_lines.append(line)
            
            self._write_encrypted_file(log_file, new_lines)
            self._invalidate_cache(log_file, "history")
            return True
            
        except Exception as e:
            print(f"Error deleting history entry: {e}")
            return False
    
    def delete_all_history_entries(self, log_file: str) -> bool:
        """Delete all history entries"""
        try:
            if os.path.exists(log_file):
                open(log_file, "w", encoding="utf-8").close()
                self._invalidate_cache(log_file, "history")
                return True
            return False
        except Exception as e:
            print(f"Error deleting all history entries: {e}")
            return False
    
    # === FAVORITE OPERATIONS ===
    
    def write_favorite_entry(
        self, 
        original_text: str, 
        translated_text: str, 
        src_lang: str, 
        dest_lang: str, 
        note: str,
        log_file: str, 
        language_interface: str, 
        theme_interface: str
    ) -> bool:
        """Write favorite entry to encrypted file"""
        try:
            print("Writing favorite entry to storage...")
            
            # Auto-translate if translated_text is empty
            if not translated_text:
                from VezylTranslatorProton.translator import get_translation_engine
                try:
                    engine = get_translation_engine()
                    result = engine.translate(original_text, src_lang, dest_lang)
                    translated_text = result.text
                except Exception as e:
                    translated_text = f"Lỗi dịch: {e}"
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry_data = {
                "time": now,
                "original_text": original_text,
                "translated_text": translated_text,
                "src_lang": src_lang,
                "dest_lang": dest_lang,
                "note": note
            }
            
            # Read existing lines and append
            lines = self._read_encrypted_file(log_file, language_interface, theme_interface)
            encrypted_line = self._encrypt_entry(entry_data, language_interface, theme_interface)
            
            if encrypted_line:
                lines.append(encrypted_line)
                self._write_encrypted_file(log_file, lines)
                self._invalidate_cache(log_file, "favorite")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error writing favorite entry: {e}")
            return False
    
    def read_favorite_entries(self, log_file: str, language_interface: str, theme_interface: str) -> List[FavoriteEntry]:
        """Read all favorite entries"""
        # Check cache first
        cache_key = self._get_cache_key(log_file, "favorite")
        with self._cache_lock:
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        entries = []
        lines = self._read_encrypted_file(log_file, language_interface, theme_interface)
        
        for line in lines:
            entry_data = self._decrypt_entry(line, language_interface, theme_interface)
            if entry_data:
                try:
                    favorite_entry = FavoriteEntry.from_dict(entry_data)
                    entries.append(favorite_entry)
                except Exception as e:
                    print(f"Error parsing favorite entry: {e}")
        
        # Cache results
        with self._cache_lock:
            self._cache[cache_key] = entries
        
        return entries
    
    def delete_favorite_entry(self, log_file: str, language_interface: str, theme_interface: str, time_str: str, original_text: str) -> bool:
        """Delete specific favorite entry"""
        try:
            lines = self._read_encrypted_file(log_file, language_interface, theme_interface)
            new_lines = []
            
            for line in lines:
                entry_data = self._decrypt_entry(line, language_interface, theme_interface)
                if entry_data:
                    if not (entry_data.get("time") == time_str and entry_data.get("original_text") == original_text):
                        new_lines.append(line)
                else:
                    # Keep unreadable lines
                    new_lines.append(line)
            
            self._write_encrypted_file(log_file, new_lines)
            self._invalidate_cache(log_file, "favorite")
            return True
            
        except Exception as e:
            print(f"Error deleting favorite entry: {e}")
            return False
    
    def delete_all_favorite_entries(self, log_file: str) -> bool:
        """Delete all favorite entries"""
        try:
            if os.path.exists(log_file):
                open(log_file, "w", encoding="utf-8").close()
                self._invalidate_cache(log_file, "favorite")
                return True
            return False
        except Exception as e:
            print(f"Error deleting all favorite entries: {e}")
            return False
    
    def update_favorite_note(self, log_file: str, language_interface: str, theme_interface: str, entry_time: str, new_note: str) -> bool:
        """Update note for specific favorite entry"""
        try:
            lines = self._read_encrypted_file(log_file, language_interface, theme_interface)
            new_lines = []
            updated = False
            
            for line in lines:
                entry_data = self._decrypt_entry(line, language_interface, theme_interface)
                if entry_data and entry_data.get("time") == entry_time:
                    # Update note
                    entry_data["note"] = new_note
                    encrypted_line = self._encrypt_entry(entry_data, language_interface, theme_interface)
                    if encrypted_line:
                        new_lines.append(encrypted_line)
                        updated = True
                    else:
                        new_lines.append(line)  # Keep original if encryption fails
                else:
                    new_lines.append(line)
            
            if updated:
                self._write_encrypted_file(log_file, new_lines)
                self._invalidate_cache(log_file, "favorite")
            
            return updated
            
        except Exception as e:
            print(f"Error updating favorite note: {e}")
            return False
    
    # === UTILITY OPERATIONS ===
    
    def clear_cache(self):
        """Clear all cached entries"""
        with self._cache_lock:
            self._cache.clear()
    
    def get_file_size(self, log_file: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(log_file) if os.path.exists(log_file) else 0
        except:
            return 0
    
    def backup_file(self, log_file: str, backup_suffix: str = ".backup") -> bool:
        """Create backup of log file"""
        try:
            if os.path.exists(log_file):
                backup_path = log_file + backup_suffix
                import shutil
                shutil.copy2(log_file, backup_path)
                return True
            return False
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def export_to_json(self, log_file: str, language_interface: str, theme_interface: str, output_file: str, entry_type: str = "history") -> bool:
        """Export entries to unencrypted JSON file"""
        try:
            if entry_type == "history":
                entries = self.read_history_entries(log_file, language_interface, theme_interface)
            else:
                entries = self.read_favorite_entries(log_file, language_interface, theme_interface)
            
            # Convert to dict format
            export_data = [entry.to_dict() for entry in entries]
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False


# === Global Storage Manager Instance ===
_global_storage_manager: Optional[StorageManager] = None


def get_storage_manager() -> StorageManager:
    """Get the global storage manager instance"""
    global _global_storage_manager
    if _global_storage_manager is None:
        _global_storage_manager = StorageManager()
    return _global_storage_manager


def reset_storage_manager():
    """Reset the global storage manager (for testing)"""
    global _global_storage_manager
    _global_storage_manager = None


# === Legacy Support Functions ===

def write_log_entry(last_translated_text, src_lang, dest_lang, source, log_file, language_interface, theme_interface, save_translate_history=True, max_items=20):
    """Legacy function for writing history entries"""
    manager = get_storage_manager()
    return manager.write_history_entry(
        last_translated_text, src_lang, dest_lang, source, 
        log_file, language_interface, theme_interface,
        save_translate_history, max_items
    )


def read_history_entries(log_file, language_interface, theme_interface):
    """Legacy function for reading history entries"""
    manager = get_storage_manager()
    entries = manager.read_history_entries(log_file, language_interface, theme_interface)
    # Convert to dict format for backward compatibility
    return [entry.to_dict() for entry in entries]


def delete_history_entry(log_file, language_interface, theme_interface, time_str, last_translated_text):
    """Legacy function for deleting history entry"""
    manager = get_storage_manager()
    return manager.delete_history_entry(log_file, language_interface, theme_interface, time_str, last_translated_text)


def delete_all_history_entries(log_file):
    """Legacy function for deleting all history entries"""
    manager = get_storage_manager()
    return manager.delete_all_history_entries(log_file)


def write_favorite_entry(original_text, translated_text, src_lang, dest_lang, note, log_file, language_interface, theme_interface):
    """Legacy function for writing favorite entries"""
    manager = get_storage_manager()
    return manager.write_favorite_entry(
        original_text, translated_text, src_lang, dest_lang, note,
        log_file, language_interface, theme_interface
    )


def read_favorite_entries(log_file, language_interface, theme_interface):
    """Legacy function for reading favorite entries"""
    manager = get_storage_manager()
    entries = manager.read_favorite_entries(log_file, language_interface, theme_interface)
    # Convert to dict format for backward compatibility
    return [entry.to_dict() for entry in entries]


def delete_favorite_entry(log_file, language_interface, theme_interface, time_str, original_text):
    """Legacy function for deleting favorite entry"""
    manager = get_storage_manager()
    return manager.delete_favorite_entry(log_file, language_interface, theme_interface, time_str, original_text)


def delete_all_favorite_entries(log_file):
    """Legacy function for deleting all favorite entries"""
    manager = get_storage_manager()
    return manager.delete_all_favorite_entries(log_file)


def update_favorite_note(log_file, language_interface, theme_interface, entry_time, new_note):
    """Legacy function for updating favorite note"""
    manager = get_storage_manager()
    return manager.update_favorite_note(log_file, language_interface, theme_interface, entry_time, new_note)


# === Crypto Legacy Functions ===

def get_aes_key(language_interface, theme_interface):
    """Legacy function for getting AES key"""
    manager = get_storage_manager()
    return manager.crypto.get_aes_key(language_interface, theme_interface)


def encrypt_aes(text, key):
    """Legacy function for AES encryption"""
    manager = get_storage_manager()
    return manager.crypto.encrypt_aes(text, key)


def decrypt_aes(enc_text, key):
    """Legacy function for AES decryption"""
    manager = get_storage_manager()
    return manager.crypto.decrypt_aes(enc_text, key)


def pad(data):
    """Legacy function for padding"""
    manager = get_storage_manager()
    return manager.crypto.pad(data)


def unpad(data):
    """Legacy function for unpadding"""
    manager = get_storage_manager()
    return manager.crypto.unpad(data)


def encode_base64(data, filename=None):
    """Legacy function for base64 encoding (from crypto.py)"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    encoded = base64.b64encode(data).decode('utf-8')
    if filename:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(encoded)
        return None
    return encoded


def decode_base64(encoded_data):
    """Legacy function for base64 decoding (from crypto.py)"""
    if isinstance(encoded_data, str):
        encoded_data = encoded_data.encode('utf-8')
    return base64.b64decode(encoded_data)
