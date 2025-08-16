"""
Unified Utility Helpers for VezylTranslator
Consolidated utilities, performance helpers, and common functions
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.

Consolidated from:
- utils.py (Common utilities)
- performance_patches.py (Performance optimizations)
- startup_optimizer.py (Startup optimization)
- lazy_imports.py (Lazy loading system)
"""

import functools
import threading
import time
import sys
import os
import gc
import winreg
import customtkinter as ctk
import toml
from typing import Optional, List, Dict, Any, Callable, Tuple, Union
from VezylTranslatorNeutron.constant import CONFIG_DIR, CLIENT_CONFIG_FILE, PERFORMANCE_CONFIG_FILE


# === UI Utilities ===

def show_confirm_popup(
    parent: ctk.CTk, 
    title: str, 
    message: str, 
    on_confirm: Callable[[], None], 
    on_cancel: Optional[Callable[[], None]] = None, 
    width: int = 420, 
    height: int = 180, 
    _: Optional[Any] = None
) -> ctk.CTkToplevel:
    """
    Display confirmation popup with unified CustomTkinter interface
    
    Args:
        parent: Parent window
        title: Popup title
        message: Confirmation message
        on_confirm: Callback for confirm action
        on_cancel: Optional callback for cancel action
        width: Popup width
        height: Popup height
        _: Optional localization object
        
    Returns:
        CTkToplevel popup window
    """
    confirm = ctk.CTkToplevel(parent)
    confirm.title(title)
    confirm.resizable(False, False)
    confirm.overrideredirect(True)  # Remove window frame
    
    # Center popup on parent
    parent.update_idletasks()
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()
    x = parent_x + (parent_w - width) // 3
    y = parent_y + (parent_h - height) // 2
    confirm.geometry(f"{width}x{height}+{x}+{y}")
    confirm.transient(parent)
    confirm.grab_set()
    confirm.configure(bg="#23272f")

    # Main frame with border
    main_frame = ctk.CTkFrame(
        confirm,
        fg_color="#23272f",
        border_color="#333",
        border_width=1,
        corner_radius=10
    )
    main_frame.pack(fill="both", expand=True, padx=0, pady=0)

    # Title
    title_label = ctk.CTkLabel(
        main_frame,
        text=title,
        font=(parent.translator.font, 17, "bold"),
        text_color="#00ff99"
    )
    title_label.pack(pady=(18, 2))
    
    # Message
    msg_label = ctk.CTkLabel(
        main_frame,
        text=message,
        font=(parent.translator.font, 14),
        text_color="#f5f5f5",
        wraplength=width-60,
        justify="center"
    )
    msg_label.pack(pady=(8, 18), padx=18, fill="x")
    
    # Buttons
    btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    btn_frame.pack(pady=(0, 10))
    
    def confirm_and_close() -> None:
        confirm.destroy()
        if on_confirm:
            on_confirm()
    
    def cancel_and_close() -> None:
        confirm.destroy()
        if on_cancel:
            on_cancel()
    
    # Button text with localization
    confirm_text = _._("confirm_popup")["confirm"] if _ else "Confirm"
    cancel_text = _._("confirm_popup")["cancel"] if _ else "Cancel"
    
    confirm_btn = ctk.CTkButton(
        btn_frame, text=confirm_text, width=120, fg_color="#00ff99", text_color="#23272f",
        font=(parent.translator.font, 13, "bold"), command=confirm_and_close
    )
    confirm_btn.pack(side="left", padx=12)
    
    cancel_btn = ctk.CTkButton(
        btn_frame, text=cancel_text, width=120, fg_color="#444", text_color="#f5f5f5",
        font=(parent.translator.font, 13), command=cancel_and_close
    )
    cancel_btn.pack(side="left", padx=12)
    
    confirm.focus_set()
    confirm.wait_window()
    return confirm


# === System Utilities ===

def get_windows_theme() -> str:
    """
    Get Windows theme (light/dark)
    
    Returns:
        Theme string: 'light', 'dark', or 'unknown (error)'
    """
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value == 1 else "dark"
    except Exception as e:
        return f"unknown ({e})"


def get_client_preferences() -> Tuple[str, str]:
    """
    Get client language and theme preferences
    
    Returns:
        Tuple of (language_interface, theme_interface)
    """
    try:
        secret = toml.load(CLIENT_CONFIG_FILE)
        return secret.get("language_interface", ""), secret.get("theme_interface", "")
    except Exception as e:
        print(f"Error loading client preferences: {e}")
        return "", ""


def ensure_local_dir(local_dir: str) -> None:
    """
    Ensure local directory exists
    
    Args:
        local_dir: Directory path to ensure
    """
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)


def search_entries(entries: List[Dict[str, Any]], keyword: str, fields: List[str]) -> List[Dict[str, Any]]:
    """
    Search entries containing keyword in specified fields (case-insensitive)
    
    Args:
        entries: List of entry dictionaries
        keyword: Search keyword
        fields: List of field names to search in
        
    Returns:
        Filtered list of entries
    """
    if not keyword:
        return entries
    
    keyword = keyword.lower().strip()
    filtered = []
    
    for item in entries:
        for field in fields:
            if keyword in str(item.get(field, "")).lower():
                filtered.append(item)
                break
                
    return filtered


# === Performance Optimizations ===

class PerformanceOptimizer:
    """Unified performance optimization manager"""
    
    def __init__(self):
        self._optimizations_applied = set()
        self._monitoring_active = False
    
    def optimize_memory_management(self) -> bool:
        """Apply memory management optimizations"""
        try:
            # Adjust garbage collection thresholds
            gc.set_threshold(700, 10, 10)
            
            # Start periodic cleanup
            def periodic_cleanup():
                gc.collect()
                if self._monitoring_active:
                    threading.Timer(60.0, periodic_cleanup).start()
            
            periodic_cleanup()
            self._optimizations_applied.add("memory")
            print("[OK] Memory optimizations applied")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to apply memory optimizations: {e}")
            return False
    
    def optimize_search_performance(self, max_results: int = 50) -> bool:
        """Optimize search result performance by limiting results"""
        try:
            # Monkey patch search_entries to limit results
            original_search = search_entries
            
            @functools.wraps(search_entries)
            def optimized_search(entries: List[Dict], keyword: str, fields: List[str]) -> List[Dict]:
                results = original_search(entries, keyword, fields)
                # Return only the most recent results
                if len(results) > max_results:
                    return results[-max_results:]
                return results
            
            # Replace in global scope
            globals()['search_entries'] = optimized_search
            self._optimizations_applied.add("search")
            print("[OK] Search performance optimized")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to optimize search: {e}")
            return False
    
    def start_performance_monitoring(self) -> bool:
        """Start performance monitoring (requires psutil)"""
        try:
            import psutil
            self._monitoring_active = True
            
            def monitor_performance():
                if not self._monitoring_active:
                    return
                    
                try:
                    process = psutil.Process()
                    cpu_percent = process.cpu_percent()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    
                    if cpu_percent > 50 or memory_mb > 200:
                        print(f"[WARNING] High resource usage - CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f}MB")
                        
                except Exception as e:
                    print(f"Performance monitoring error: {e}")
                finally:
                    if self._monitoring_active:
                        threading.Timer(30.0, monitor_performance).start()
            
            monitor_performance()
            self._optimizations_applied.add("monitoring")
            print("[OK] Performance monitoring started")
            return True
        except ImportError:
            print("[INFO] psutil not available, performance monitoring disabled")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to start performance monitoring: {e}")
            return False
    
    def apply_all_optimizations(self) -> int:
        """Apply all performance optimizations"""
        print("=== Applying Performance Optimizations ===")
        
        optimizations = [
            ("Memory Management", self.optimize_memory_management),
            ("Search Performance", self.optimize_search_performance),
            ("Performance Monitoring", self.start_performance_monitoring),
        ]
        
        success_count = 0
        for name, optimization_func in optimizations:
            try:
                if optimization_func():
                    success_count += 1
            except Exception as e:
                print(f"[ERROR] {name} failed: {e}")
        
        print(f"=== {success_count}/{len(optimizations)} optimizations applied ===")
        return success_count
    
    def get_optimization_status(self) -> Dict[str, bool]:
        """Get status of applied optimizations"""
        return {
            "memory": "memory" in self._optimizations_applied,
            "search": "search" in self._optimizations_applied,
            "monitoring": "monitoring" in self._optimizations_applied,
        }
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self._monitoring_active = False


# === Startup Optimization ===

class StartupOptimizer:
    """Fast startup optimization manager"""
    
    def __init__(self):
        self.deferred_imports = []
        self.startup_time = time.time()
        self.fast_mode = os.getenv('VEZYL_FAST_STARTUP', '0') == '1'
    
    def defer_import(self, module_name: str, callback: Optional[Callable] = None) -> None:
        """Defer heavy imports until after startup"""
        if self.fast_mode:
            self.deferred_imports.append((module_name, callback))
    
    def load_deferred_imports(self) -> None:
        """Load all deferred imports in background thread"""
        if not self.deferred_imports:
            return
        
        print("🔄 Loading deferred imports in background...")
        
        def load_in_background():
            for module_name, callback in self.deferred_imports:
                try:
                    start = time.time()
                    
                    # Dynamic import based on module name
                    if module_name == 'transformers':
                        import transformers
                    elif module_name == 'torch':
                        import torch
                    elif module_name == 'pyperclip':
                        import pyperclip
                    elif module_name == 'pyautogui':
                        import pyautogui
                    
                    load_time = time.time() - start
                    print(f"[OK] Loaded {module_name} in {load_time:.3f}s")
                    
                    if callback:
                        callback()
                        
                except ImportError as e:
                    print(f"[WARNING] Could not load {module_name}: {e}")
                except Exception as e:
                    print(f"❌ Error loading {module_name}: {e}")
        
        # Load in background thread
        thread = threading.Thread(target=load_in_background, daemon=True)
        thread.start()
    
    def get_startup_time(self) -> float:
        """Get elapsed startup time"""
        return time.time() - self.startup_time
    
    def finish_startup(self) -> None:
        """Call after main window is shown"""
        if self.fast_mode:
            startup_time = self.get_startup_time()
            print(f"⚡ Main startup completed in {startup_time:.3f}s")
            self.load_deferred_imports()


# === Lazy Import System ===

class LazyImporter:
    """Lazy loader for heavy libraries"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
        self._available = None
    
    @property
    def available(self) -> bool:
        """Check if module is available without loading"""
        if self._available is None:
            try:
                __import__(self.module_name)
                self._available = True
                print(f"[OK] {self.module_name} available (lazy loaded)")
            except ImportError:
                self._available = False
                print(f"[WARNING] {self.module_name} not available")
        return self._available
    
    def get_module(self) -> Optional[Any]:
        """Get the actual module (loads on first access)"""
        if self._module is None and self.available:
            print(f"🔄 Loading {self.module_name} (first time)...")
            start_time = time.time()
            self._module = __import__(self.module_name)
            load_time = time.time() - start_time
            print(f"[OK] {self.module_name} loaded in {load_time:.3f}s")
        return self._module
    
    def get_attribute(self, attr_name: str) -> Optional[Any]:
        """Get attribute from lazy-loaded module"""
        module = self.get_module()
        if module:
            return getattr(module, attr_name, None)
        return None


# === Global Instances ===

# Performance optimizer instance
performance_optimizer = PerformanceOptimizer()

# Startup optimizer instance
startup_optimizer = StartupOptimizer()

# Lazy importers for heavy libraries
transformers_lazy = LazyImporter('transformers')


# === Convenience Functions ===

def apply_performance_optimizations() -> int:
    """Apply all performance optimizations"""
    return performance_optimizer.apply_all_optimizations()


def optimize_startup() -> None:
    """Configure startup optimizations"""
    if startup_optimizer.fast_mode:
        print("[FastStartup] Fast startup mode enabled")
        startup_optimizer.defer_import('transformers')
        startup_optimizer.defer_import('torch')
        startup_optimizer.defer_import('pyperclip')
        startup_optimizer.defer_import('pyautogui')
        os.environ['DISABLE_IMMEDIATE_MODEL_LOADING'] = '1'


def finish_startup() -> None:
    """Finish startup optimization after main window is shown"""
    startup_optimizer.finish_startup()


def get_transformers_available() -> bool:
    """Check if transformers is available without loading"""
    return transformers_lazy.available


def get_marian_model() -> Optional[Any]:
    """Get MarianMTModel (lazy loaded)"""
    return transformers_lazy.get_attribute('MarianMTModel')


def get_marian_tokenizer() -> Optional[Any]:
    """Get MarianTokenizer (lazy loaded)"""
    return transformers_lazy.get_attribute('MarianTokenizer')


def create_performance_config() -> bool:
    """Create performance configuration file"""
    config = {
        "clipboard_watcher": {
            "min_interval": 0.8,
            "max_interval": 3.0,
            "adaptive_timing": True
        },
        "ui_rendering": {
            "max_history_items": 50,
            "debounce_delay": 300,
            "virtual_scrolling": True
        },
        "translation": {
            "max_concurrent": 3,
            "timeout_seconds": 30,
            "use_thread_pool": True
        },
        "memory": {
            "gc_threshold": [700, 10, 10],
            "periodic_cleanup": True,
            "cleanup_interval": 60
        }
    }
    
    try:
        import json
        ensure_local_dir(os.path.dirname(PERFORMANCE_CONFIG_FILE))
        with open(PERFORMANCE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"[OK] Performance config created: {PERFORMANCE_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create performance config: {e}")
        return False


# === Cleanup Functions ===

def cleanup_helpers() -> None:
    """Cleanup helper resources"""
    performance_optimizer.stop_monitoring()
    print("[OK] Helper resources cleaned up")


# === Public API ===
__all__ = [
    # UI Utilities
    'show_confirm_popup',
    
    # System Utilities
    'get_windows_theme', 'get_client_preferences', 'ensure_local_dir', 'search_entries',
    
    # Performance
    'PerformanceOptimizer', 'performance_optimizer', 'apply_performance_optimizations',
    
    # Startup
    'StartupOptimizer', 'startup_optimizer', 'optimize_startup', 'finish_startup',
    
    # Lazy Imports
    'LazyImporter', 'get_transformers_available', 'get_marian_model', 'get_marian_tokenizer',
    
    # Config
    'create_performance_config',
    
    # Cleanup
    'cleanup_helpers',
    
    # Performance Patches
    'patch_clipboard_module', 'patch_gui_translations', 'optimize_text_change_debouncing',
    'optimize_history_rendering', 'optimize_clipboard_polling', 'apply_memory_optimizations',
    'monitor_performance', 'apply_all_optimizations'
]


# ============================================================================
# Performance Patches (từ performance_patches.py)
# ============================================================================

def patch_clipboard_module():
    """
    Clipboard module đã được tối ưu trực tiếp trong code gốc
    """
    print("[OK] Clipboard module already optimized (integrated)")
    return True


def patch_gui_translations():
    """
    GUI đã được tối ưu trực tiếp với ThreadPool
    """
    print("[OK] GUI translations already optimized (integrated)")
    return True


def optimize_text_change_debouncing():
    """
    Tối ưu debouncing cho text change events
    """
    original_after = None
    
    def optimized_after(self, ms, func=None, *args):
        """Optimized version of tkinter after method with proper signature"""
        # Xử lý tất cả các variants của after method
        if func is None:
            return original_after(self, ms)
            
        # Kiểm tra nếu là debounce function
        if (hasattr(func, '__name__') and 
            ('debounce' in func.__name__.lower() or 'text_change' in func.__name__.lower())):
            
            # Tăng delay để giảm tần suất gọi
            ms = max(ms, 300)  # Minimum 300ms delay
            
        # Gọi original method với tất cả arguments
        return original_after(self, ms, func, *args)
    
    try:
        import tkinter as tk
        if original_after is None:
            original_after = tk.Misc.after
            tk.Misc.after = optimized_after
            
        print("[OK] Text change debouncing optimized")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to optimize debouncing: {e}")
        return False


def optimize_history_rendering():
    """
    Tối ưu rendering của history list
    """
    try:
        # Patch search_entries để giới hạn kết quả
        original_search_entries = search_entries
        
        @functools.wraps(search_entries)
        def optimized_search_entries(entries, keyword, fields, max_results=50):
            """Giới hạn kết quả search để tối ưu rendering"""
            results = original_search_entries(entries, keyword, fields)
            
            # Chỉ lấy max_results items mới nhất
            if len(results) > max_results:
                return results[-max_results:]
            return results
        
        # Replace function in global scope
        globals()['search_entries'] = optimized_search_entries
        
        print("[OK] History rendering optimized")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to optimize history rendering: {e}")
        return False


def optimize_clipboard_polling():
    """
    Tối ưu polling interval của clipboard
    """
    try:
        # Patch time.sleep trong clipboard module
        import VezylTranslatorNeutron.clipboard_service as clipboard_service
        
        original_sleep = time.sleep
        
        def adaptive_sleep(seconds):
            """Sleep với adaptive timing"""
            # Trong clipboard watcher, tăng sleep time
            frame = sys._getframe(1)
            if frame and 'clipboard_watcher' in str(frame.f_code.co_name):
                # Tăng sleep time để giảm CPU usage
                seconds = max(seconds, 0.8)  # Minimum 0.8s
                
            return original_sleep(seconds)
        
        # Apply trong scope của clipboard module
        clipboard_service.time.sleep = adaptive_sleep
        
        print("[OK] Clipboard polling optimized")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to optimize clipboard polling: {e}")
        return False


def apply_memory_optimizations():
    """
    Áp dụng các tối ưu memory
    """
    try:
        # Tăng threshold cho garbage collection
        gc.set_threshold(700, 10, 10)  # Default: 700, 10, 10
        
        # Định kỳ dọn dẹp memory
        def periodic_cleanup():
            gc.collect()
            threading.Timer(60.0, periodic_cleanup).start()  # Mỗi 60s
            
        periodic_cleanup()
        
        print("[OK] Memory optimizations applied")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to apply memory optimizations: {e}")
        return False


def monitor_performance():
    """
    Monitor hiệu suất ứng dụng (optional - requires psutil)
    """
    try:
        import psutil
        import threading
        
        def log_performance():
            try:
                process = psutil.Process()
                cpu_percent = process.cpu_percent()
                memory_mb = process.memory_info().rss / 1024 / 1024
                
                if cpu_percent > 50 or memory_mb > 200:  # Thresholds
                    print(f"[WARNING] High resource usage - CPU: {cpu_percent:.1f}%, Memory: {memory_mb:.1f}MB")
                
            except Exception as e:
                print(f"Performance monitoring error: {e}")
            finally:
                # Schedule next check
                threading.Timer(30.0, log_performance).start()
                
        log_performance()
        
        print("[OK] Performance monitoring started")
        return True
    except ImportError:
        print("[INFO] psutil not available, performance monitoring disabled")
        return True  # Không phải lỗi, chỉ là không có psutil
    except Exception as e:
        print(f"[ERROR] Failed to start performance monitoring: {e}")
        return False


def apply_all_optimizations():
    """
    Áp dụng tất cả các tối ưu hiệu suất
    """
    print("=== Applying Performance Optimizations ===")
    
    optimizations = [
        ("Clipboard Module", patch_clipboard_module),
        ("GUI Translations", patch_gui_translations),
        # ("Text Debouncing", optimize_text_change_debouncing),  # Disabled - causes conflicts with customtkinter
        ("History Rendering", optimize_history_rendering),
        ("Clipboard Polling", optimize_clipboard_polling),
        ("Memory Management", apply_memory_optimizations),
        ("Performance Monitoring", monitor_performance),
    ]
    
    success_count = 0
    for name, optimization_func in optimizations:
        try:
            if optimization_func():
                success_count += 1
        except Exception as e:
            print(f"[ERROR] {name} failed: {e}")
    
    print(f"=== {success_count}/{len(optimizations)} optimizations applied ===")
    return success_count
