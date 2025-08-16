"""
Unified Clipboard Service for VezylTranslator
Consolidated clipboard operations and monitoring service
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import pyperclip
import pyautogui
import time
import os
import sys
import re
import winsound
from PIL import Image
from functools import lru_cache
from threading import Lock
from VezylTranslatorNeutron.constant import RESOURCES_DIR

# Thread synchronization for clipboard access
_clipboard_lock = Lock()


class ClipboardService:
    """Unified clipboard operations and monitoring service"""
    
    def __init__(self):
        self.watcher_enabled = True
        self.is_icon_showing = False
        self.recent_value = ""
        
        # Adaptive monitoring settings
        self.current_interval = 0.8
        self.min_interval = 0.5
        self.max_interval = 2.0
        self.idle_count = 0
        self.last_activity_time = time.time()
        self.consecutive_errors = 0
        self.max_consecutive_errors = 10
    
    # === Core Clipboard Operations ===
    
    def _safe_clipboard_paste(self, max_retries=3, retry_delay=0.1):
        """Safe clipboard paste with retry logic"""
        for attempt in range(max_retries):
            try:
                with _clipboard_lock:
                    return pyperclip.paste()
            except Exception as e:
                error_str = str(e).lower()
                # Check for specific clipboard errors
                if any(keyword in error_str for keyword in [
                    'openclipboard', 'pyperclipwindowsexception', 
                    'clipboard', 'access denied', 'sharing violation'
                ]):
                    if attempt < max_retries - 1:
                        print(f"Clipboard access attempt {attempt + 1} failed, retrying...")
                        time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        continue
                    else:
                        print(f"Clipboard access failed after {max_retries} attempts: {e}")
                        return ""  # Return empty string instead of crash
                else:
                    # Non-clipboard error, re-raise
                    raise e
        return ""
    
    def _safe_clipboard_copy(self, text, max_retries=3, retry_delay=0.1):
        """Safe clipboard copy with retry logic"""
        for attempt in range(max_retries):
            try:
                with _clipboard_lock:
                    pyperclip.copy(text)
                    return True
            except Exception as e:
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in [
                    'openclipboard', 'pyperclipwindowsexception',
                    'clipboard', 'access denied'
                ]):
                    if attempt < max_retries - 1:
                        print(f"Clipboard copy attempt {attempt + 1} failed, retrying...")
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        print(f"Clipboard copy failed after {max_retries} attempts: {e}")
                        return False
                else:
                    raise e
        return False
    
    # === Text Formatting ===
    
    @lru_cache(maxsize=100)
    def _format_text_cached(self, text_hash, text):
        """Cached version of text formatting"""
        return self._format_text_internal(text)
    
    def _format_text_internal(self, text):
        """Internal text formatting without cache"""
        if not text or not text.strip():
            return text
        
        # Remove unwanted control characters (except \n, \t)
        formatted_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Normalize line breaks: replace \r\n and \r with \n
        formatted_text = re.sub(r'\r\n|\r', '\n', formatted_text)
        
        # Remove excessive line breaks (3+ consecutive) to 2
        formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
        
        # Clean whitespace at line start/end
        lines = formatted_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if line.strip():
                # Clean whitespace at line start/end
                cleaned_line = line.strip()
                # Normalize spaces between words
                cleaned_line = re.sub(r'\s+', ' ', cleaned_line)
                cleaned_lines.append(cleaned_line)
            else:
                cleaned_lines.append('')
        
        formatted_text = '\n'.join(cleaned_lines)
        
        # Remove leading/trailing line breaks
        formatted_text = formatted_text.strip()
        
        # Normalize indentation
        lines = formatted_text.split('\n')
        if len(lines) > 1:
            # Find minimum indentation level (excluding empty lines)
            min_indent = float('inf')
            for line in lines:
                if line.strip():
                    indent_match = re.match(r'^(\s*)', line)
                    if indent_match:
                        indent = indent_match.group(1)
                        # Convert tabs to 4 spaces for calculation
                        indent_spaces = indent.replace('\t', '    ')
                        if len(indent_spaces) < min_indent:
                            min_indent = len(indent_spaces)
            
            # Remove common indentation if present
            if min_indent != float('inf') and min_indent > 0:
                normalized_lines = []
                for line in lines:
                    if line.strip():  # Line with content
                        # Convert tabs to spaces
                        line_with_spaces = line.replace('\t', '    ')
                        # Remove common indentation
                        if len(line_with_spaces) >= min_indent:
                            normalized_lines.append(line_with_spaces[min_indent:])
                        else:
                            normalized_lines.append(line.strip())
                    else:  # Empty line
                        normalized_lines.append('')
                formatted_text = '\n'.join(normalized_lines)
        
        return formatted_text
    
    def format_text(self, text):
        """Format text with caching for performance"""
        if not text or not text.strip():
            return text
        
        # Create simple hash for cache
        text_hash = hash(text) % 10000
        
        try:
            return self._format_text_cached(text_hash, text)
        except:
            # Fallback if cache has issues
            return self._format_text_internal(text)
    
    def clear_format_cache(self):
        """Clear format cache to save memory"""
        self._format_text_cached.cache_clear()
    
    # === Public API ===
    
    def get_clipboard_text(self):
        """Get formatted text from clipboard"""
        raw_text = self._safe_clipboard_paste()
        return self.format_text(raw_text)
    
    def set_clipboard_text(self, text):
        """Set clipboard text safely"""
        return self._safe_clipboard_copy(text)
    
    # === Clipboard Monitoring ===
    
    def start_watcher(self, translator_instance, show_popup_func, show_icon_func, show_homepage_func):
        """Start clipboard monitoring with adaptive interval"""
        self.recent_value = self._safe_clipboard_paste()
        print("Clipboard watcher started with safe access")
        
        while True:
            try:
                # Check if watcher is enabled
                if not getattr(translator_instance, "clipboard_watcher_enabled", True):
                    time.sleep(self.max_interval)
                    continue
                
                if getattr(translator_instance, "Is_icon_showing", False):
                    time.sleep(0.3)
                    continue
                
                # Check clipboard content
                tmp_value = self._safe_clipboard_paste()
                
                # Reset error counter on successful access
                self.consecutive_errors = 0
                
                if tmp_value != self.recent_value and tmp_value.strip():
                    # Activity detected - reset interval
                    self.current_interval = self.min_interval
                    self.idle_count = 0
                    self.last_activity_time = time.time()
                    
                    # Format text before use
                    formatted_value = self.format_text(tmp_value)
                    self.recent_value = tmp_value  # Store original for comparison
                    
                    try:
                        x, y = pyautogui.position()
                    except:
                        x, y = 0, 0  # Fallback position
                    
                    always_show_translate = getattr(translator_instance, "always_show_transtale", False)
                    if always_show_translate:
                        print("popup")
                        show_popup_func(formatted_value, x, y)
                    else:
                        print("icon")
                        show_icon_func(formatted_value, x, y)
                else:
                    # No activity - gradually increase interval
                    self.idle_count += 1
                    time_since_activity = time.time() - self.last_activity_time
                    
                    if time_since_activity > 30:  # 30s idle
                        self.current_interval = min(self.max_interval, self.current_interval * 1.1)
                    elif time_since_activity > 10:  # 10s idle
                        self.current_interval = min(1.5, self.current_interval * 1.05)
                
                # Adaptive sleep
                time.sleep(self.current_interval)
                
            except Exception as e:
                self.consecutive_errors += 1
                print(f"Clipboard watcher error {self.consecutive_errors}: {e}")
                
                # Check if it's a clipboard-specific error
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in [
                    'openclipboard', 'pyperclipwindowsexception',
                    'clipboard', 'access denied', 'sharing violation'
                ]):
                    print("Clipboard access error detected, continuing with extended delay...")
                    time.sleep(2.0)
                else:
                    # Other error, log and continue
                    print(f"Non-clipboard error: {e}")
                    sys.excepthook(*sys.exc_info())
                    time.sleep(1.0)
                
                # Extended pause if too many consecutive errors
                if self.consecutive_errors >= self.max_consecutive_errors:
                    print(f"Too many consecutive errors ({self.consecutive_errors}), entering extended pause...")
                    time.sleep(10.0)
                    self.consecutive_errors = 0
    
    def toggle_watcher(self, translator_instance):
        """Toggle clipboard watcher and update tray icon"""
        if translator_instance is None:
            print("Error: translator_instance is None")
            return
        
        # Get current state
        old_state = getattr(translator_instance, "clipboard_watcher_enabled", True)
        
        # Toggle state
        translator_instance.clipboard_watcher_enabled = not old_state
        
        new_state = translator_instance.clipboard_watcher_enabled
        print(f"Clipboard watcher toggled: {old_state} -> {new_state}")
        
        # Play notification sound (non-blocking)
        try:
            if translator_instance.clipboard_watcher_enabled:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            else:
                winsound.MessageBeep(winsound.MB_ICONHAND)
        except:
            pass  # Ignore sound errors
        
        # Update tray icon in background thread
        print("Updating tray icon for clipboard state change...")
        self._update_tray_icon_async(translator_instance)
    
    def _update_tray_icon_async(self, translator_instance):
        """Update tray icon in background thread"""
        def update_tray_icon():
            try:
                # Import tray service module to get the global instance
                from VezylTranslatorNeutron.tray_service import _tray_service
                from VezylTranslatorNeutron.helpers import get_windows_theme
                
                # Use the dedicated method for updating clipboard state icon
                success = _tray_service.update_icon_for_clipboard_state(
                    translator_instance.clipboard_watcher_enabled,
                    get_windows_theme
                )
                
                if success:
                    print(f"Tray icon successfully updated: {'enabled' if translator_instance.clipboard_watcher_enabled else 'disabled'}")
                else:
                    print("Failed to update tray icon")
                    
            except Exception as e:
                print(f"Error updating tray icon: {e}")
                import traceback
                traceback.print_exc()
        
        # Run in background thread
        import threading
        threading.Thread(target=update_tray_icon, daemon=True).start()


# === Legacy Function Support ===
# For backward compatibility with existing code

_clipboard_service = ClipboardService()

def clipboard_watcher(translator_instance, main_window_instance, always_show_transtale, 
                     show_popup_func, show_icon_func, show_homepage_func):
    """Legacy wrapper for clipboard watcher"""
    return _clipboard_service.start_watcher(translator_instance, show_popup_func, show_icon_func, show_homepage_func)

def get_clipboard_text():
    """Legacy wrapper for getting clipboard text"""
    return _clipboard_service.get_clipboard_text()

def set_clipboard_text(text):
    """Legacy wrapper for setting clipboard text"""
    return _clipboard_service.set_clipboard_text(text)

def toggle_clipboard_watcher(translator_instance):
    """Legacy wrapper for toggling clipboard watcher"""
    return _clipboard_service.toggle_watcher(translator_instance)

def format_text(text):
    """Legacy wrapper for text formatting"""
    return _clipboard_service.format_text(text)

def clear_format_cache():
    """Legacy wrapper for clearing format cache"""
    return _clipboard_service.clear_format_cache()


# === Public API ===
__all__ = ['ClipboardService', 'clipboard_watcher', 'get_clipboard_text', 'set_clipboard_text', 
           'toggle_clipboard_watcher', 'format_text', 'clear_format_cache']
