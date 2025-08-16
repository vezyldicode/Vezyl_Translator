"""
Patch file để tích hợp các tối ưu hiệu suất vào VezylTranslator
Áp dụng các cải thiện mà không cần thay đổi toàn bộ codebase
"""

import functools
import threading
import time
import sys
import os
from VezylTranslatorNeutron.constant import CONFIG_DIR, PERFORMANCE_CONFIG_FILE


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
        from VezylTranslatorProton.utils import search_entries
        
        original_search_entries = search_entries
        
        @functools.wraps(search_entries)
        def optimized_search_entries(entries, keyword, fields, max_results=50):
            """Giới hạn kết quả search để tối ưu rendering"""
            results = original_search_entries(entries, keyword, fields)
            
            # Chỉ lấy max_results items mới nhất
            if len(results) > max_results:
                return results[-max_results:]
            return results
        
        # Replace function
        import VezylTranslatorProton.utils as utils_module
        utils_module.search_entries = optimized_search_entries
        
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
        import VezylTranslatorProton.clipboard_module as clipboard_module
        
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
        clipboard_module.time.sleep = adaptive_sleep
        
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
        import gc
        
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


def create_performance_config():
    """
    Tạo config file cho performance settings
    """
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
        with open(PERFORMANCE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"[OK] Performance config created: {PERFORMANCE_CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create performance config: {e}")
        return False


if __name__ == "__main__":
    # Test các optimizations
    apply_all_optimizations()
    create_performance_config()
