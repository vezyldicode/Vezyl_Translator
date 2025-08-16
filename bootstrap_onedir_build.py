import sys
import os
import time
import tkinter as tk
from tkinter import ttk

print("🚀 VezylTranslator starting...")

class QuickLoader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Vezyl Translator")
        self.root.geometry("300x120")
        self.root.resizable(False, False)
        self.root.configure(bg='#1e1e1e')
        self.root.eval('tk::PlaceWindow . center')
        # Simple UI
        tk.Label(self.root, text="Vezyl Translator", font=("Arial", 14, "bold"), fg="white", bg="#1e1e1e").pack(pady=15)
        self.progress = ttk.Progressbar(self.root, mode='indeterminate', length=250)
        self.progress.pack(pady=10)
        self.progress.start(15)
        self.status = tk.Label(self.root, text="Starting...", font=("Arial", 9), fg="#cccccc", bg="#1e1e1e")
        self.status.pack(pady=5)
        self.root.update()

    def update(self, msg):
        try:
            if self.root and self.root.winfo_exists():
                self.status.config(text=msg)
                self.root.update()
                print(f"[LOADING] {msg}")
        except tk.TclError:
            # Window was destroyed, ignore updates
            pass

    def close(self):
        try:
            if self.root and self.root.winfo_exists():
                self.progress.stop()
                self.root.destroy()
        except tk.TclError:
            # Window already destroyed
            pass

# Show immediately
loader = QuickLoader()
start_time = time.time()

try:
    # Import main app
    loader.update("Loading core...")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Pre-load critical modules
    loader.update("Loading system modules...")
    try:
        import winsound
    except ImportError:
        print("Warning: winsound not available")
    
    # Import standard library modules that might be needed
    import json
    import toml
    import configparser
    import base64
    import pathlib
    
    loader.update("Loading VezylTranslator...")
    from VezylTranslator import main
    
    elapsed = time.time() - start_time
    loader.update(f"Ready! ({elapsed:.1f}s)")
    time.sleep(0.3)
    loader.close()
    
    print(f"✅ Startup completed in {elapsed:.1f}s")
    main()
    
except Exception as e:
    try:
        loader.update(f"Error: {e}")
        print(f"❌ Error: {e}")
        time.sleep(2)
    except:
        print(f"❌ Error: {e}")
    finally:
        loader.close()
    
    try:
        import subprocess
        subprocess.Popen(["VezylTranslatorCrashHandler.exe", str(e), "Vezyl Translator", "1.0.0"])
    except:
        pass
