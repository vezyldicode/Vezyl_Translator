"""
Fast Startup Optimizer for VezylTranslator
Tối ưu thời gian khởi động bằng cách delay load các module nặng
"""
import os
import sys
import time

# Enable fast startup mode
FAST_STARTUP = os.getenv('VEZYL_FAST_STARTUP', '0') == '1'

class FastStartupManager:
    def __init__(self):
        self.deferred_imports = []
        self.startup_time = time.time()
        
    def defer_import(self, module_name, callback=None):
        """Defer heavy imports until after startup"""
        self.deferred_imports.append((module_name, callback))
        
    def load_deferred_imports(self):
        """Load all deferred imports after main window is shown"""
        if not self.deferred_imports:
            return
            
        print("🔄 Loading deferred imports in background...")
        import threading
        
        def load_in_background():
            for module_name, callback in self.deferred_imports:
                try:
                    start = time.time()
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
        
    def get_startup_time(self):
        return time.time() - self.startup_time

# Global instance
fast_startup = FastStartupManager()

def optimize_imports():
    """Configure fast startup optimizations"""
    if FAST_STARTUP:
        print("[FastStartup] Fast startup mode enabled")
        
        # Defer heavy imports
        fast_startup.defer_import('transformers')
        fast_startup.defer_import('torch') 
        fast_startup.defer_import('pyperclip')
        fast_startup.defer_import('pyautogui')
        
        # Disable immediate model loading
        os.environ['DISABLE_IMMEDIATE_MODEL_LOADING'] = '1'
        
        return True
    return False

def finish_startup_optimization():
    """Call this after main window is shown"""
    if FAST_STARTUP:
        startup_time = fast_startup.get_startup_time()
        print(f"⚡ Main startup completed in {startup_time:.3f}s")
        
        # Load deferred imports in background
        fast_startup.load_deferred_imports()

def is_fast_startup():
    """Check if fast startup mode is enabled"""
    return FAST_STARTUP
