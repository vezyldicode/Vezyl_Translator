"""
Marian MT Model Downloader - Developer Tool
Tải xuống các models Marian MT từ HuggingFace Hub

Developer Tool for VezylTranslator
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import requests
import os
import sys
from pathlib import Path
import json
from datetime import datetime
import tempfile

class MarianModelDownloader:
    def __init__(self):
        # Initialize Tkinter with error handling for PyInstaller
        try:
            self.root = tk.Tk()
            self.root.title("Marian MT Model Downloader - Developer Tool")
            self.root.geometry("800x600")
            self.root.resizable(True, True)
            
            # Set window icon if available
            try:
                if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                    # PyInstaller bundle
                    icon_path = Path(sys._MEIPASS) / "resources" / "logo.ico"
                else:
                    icon_path = Path(__file__).parent / "resources" / "logo.ico"
                
                if icon_path.exists():
                    self.root.iconbitmap(str(icon_path))
            except Exception:
                # Ignore icon errors
                pass
                
        except Exception as e:
            # If Tkinter initialization fails, show error and exit
            self.log_to_console(f"Failed to initialize GUI: {e}")
            sys.exit(1)
        
        # Handle PyInstaller bundled app path
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller bundle - use executable location for models
                script_dir = Path(sys.executable).parent.absolute()
                # For PyInstaller, prefer user directory to avoid permission issues
                base_dir = Path(tempfile.gettempdir()) / "VezylTranslator"
            else:
                # Other bundlers
                script_dir = Path(sys.executable).parent.absolute()
                base_dir = script_dir
        else:
            # Running as script
            script_dir = Path(__file__).parent.absolute()
            base_dir = script_dir
            
        # Try to use script directory first, fallback to temp if needed
        try:
            self.models_dir = base_dir / "resources" / "marian_models"
            self.models_dir.mkdir(parents=True, exist_ok=True)
            # Test write permission
            test_file = self.models_dir / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
            self.log_to_console(f"Models directory: {self.models_dir}")
        except Exception as e:
            self.log_to_console(f"Cannot use primary directory ({e}), using fallback...")
            # Fallback to user temp directory
            self.models_dir = Path(tempfile.gettempdir()) / "VezylTranslator" / "marian_models"
            self.models_dir.mkdir(parents=True, exist_ok=True)
            self.log_to_console(f"Using fallback directory: {self.models_dir}")
        
        # Available language codes from HuggingFace Helsinki-NLP
        self.available_languages = {
            "en": "English",
            "vi": "Vietnamese",
            "de": "German", 
            "fr": "French",
            "es": "Spanish",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "th": "Thai",
            "tr": "Turkish",
            "pl": "Polish",
            "nl": "Dutch",
            "sv": "Swedish",
            "da": "Danish",
            "no": "Norwegian",
            "fi": "Finnish",
            "he": "Hebrew",
            "cs": "Czech",
            "hu": "Hungarian",
            "ro": "Romanian",
            "bg": "Bulgarian",
            "hr": "Croatian",
            "sk": "Slovak",
            "sl": "Slovenian",
            "et": "Estonian",
            "lv": "Latvian",
            "lt": "Lithuanian",
            "mt": "Maltese",
            "ga": "Irish",
            "cy": "Welsh",
            "eu": "Basque",
            "ca": "Catalan",
            "gl": "Galician",
            "is": "Icelandic",
            "mk": "Macedonian",
            "sq": "Albanian",
            "sr": "Serbian",
            "bs": "Bosnian",
            "mul": "Multilingual"
        }
        
        self.download_queue = []
        self.is_downloading = False
        
        self.setup_ui()
        
    def log_to_console(self, message):
        """Safely log message to console - PyInstaller compatible"""
        try:
            if sys.stdout:
                print(message)
                if hasattr(sys.stdout, 'flush'):
                    sys.stdout.flush()
        except:
            # If console output fails, just continue silently
            pass
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Marian MT Model Downloader", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Language selection frame
        lang_frame = ttk.LabelFrame(main_frame, text="Select Languages", padding="10")
        lang_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        lang_frame.columnconfigure(1, weight=1)
        
        # Source language
        ttk.Label(lang_frame, text="Source Language:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.src_lang_var = tk.StringVar()
        self.src_combo = ttk.Combobox(lang_frame, textvariable=self.src_lang_var, 
                                     values=list(self.available_languages.values()), 
                                     state="readonly", width=20)
        self.src_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))
        
        # Target language
        ttk.Label(lang_frame, text="Target Language:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.dest_lang_var = tk.StringVar()
        self.dest_combo = ttk.Combobox(lang_frame, textvariable=self.dest_lang_var,
                                      values=list(self.available_languages.values()),
                                      state="readonly", width=20)
        self.dest_combo.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        # Options frame
        options_frame = ttk.Frame(lang_frame)
        options_frame.grid(row=1, column=0, columnspan=4, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # Bidirectional checkbox
        self.bidirectional_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Download bidirectional models (A→B and B→A)", 
                       variable=self.bidirectional_var).grid(row=0, column=0, sticky=tk.W)
        
        # Add to queue button
        ttk.Button(options_frame, text="Add to Download Queue", 
                  command=self.add_to_queue).grid(row=0, column=1, padx=(20, 0))
        
        # Queue and log frame
        queue_frame = ttk.LabelFrame(main_frame, text="Download Queue & Log", padding="10")
        queue_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        queue_frame.columnconfigure(0, weight=1)
        queue_frame.rowconfigure(1, weight=1)
        
        # Queue listbox
        queue_list_frame = ttk.Frame(queue_frame)
        queue_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        queue_list_frame.columnconfigure(0, weight=1)
        
        ttk.Label(queue_list_frame, text="Download Queue:").grid(row=0, column=0, sticky=tk.W)
        
        # Queue listbox with scrollbar
        queue_frame_inner = ttk.Frame(queue_list_frame)
        queue_frame_inner.grid(row=1, column=0, sticky=(tk.W, tk.E))
        queue_frame_inner.columnconfigure(0, weight=1)
        
        self.queue_listbox = tk.Listbox(queue_frame_inner, height=4)
        self.queue_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        queue_scrollbar = ttk.Scrollbar(queue_frame_inner, orient=tk.VERTICAL, command=self.queue_listbox.yview)
        queue_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.queue_listbox.configure(yscrollcommand=queue_scrollbar.set)
        
        # Queue control buttons
        queue_controls = ttk.Frame(queue_list_frame)
        queue_controls.grid(row=2, column=0, pady=(5, 0))
        
        ttk.Button(queue_controls, text="Clear Queue", 
                  command=self.clear_queue).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(queue_controls, text="Remove Selected", 
                  command=self.remove_selected).grid(row=0, column=1)
        
        # Log text area
        ttk.Label(queue_frame, text="Download Log:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(queue_frame, height=12, wrap=tk.WORD)
        self.log_text.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, length=300, mode='determinate', 
                                          variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, padx=(0, 10))
        
        # Progress label
        self.progress_label = ttk.Label(control_frame, text="Ready")
        self.progress_label.grid(row=0, column=1, padx=(0, 20))
        
        # Download button
        self.download_btn = ttk.Button(control_frame, text="Start Download", 
                                     command=self.start_download_thread)
        self.download_btn.grid(row=0, column=2, padx=(0, 10))
        
        # Cancel button
        self.cancel_btn = ttk.Button(control_frame, text="Cancel", 
                                   command=self.cancel_download, state=tk.DISABLED)
        self.cancel_btn.grid(row=0, column=3)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text=f"Models directory: {self.models_dir.absolute()}")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Load existing models info
        self.log_message("Ready. Select languages and add to queue.")
        self.show_existing_models()
        
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def add_to_queue(self):
        """Add selected language pair to download queue"""
        src_lang_name = self.src_lang_var.get()
        dest_lang_name = self.dest_lang_var.get()
        
        if not src_lang_name or not dest_lang_name:
            messagebox.showwarning("Warning", "Please select both source and target languages.")
            return
            
        if src_lang_name == dest_lang_name:
            messagebox.showwarning("Warning", "Source and target languages cannot be the same.")
            return
            
        # Get language codes
        src_code = next(code for code, name in self.available_languages.items() if name == src_lang_name)
        dest_code = next(code for code, name in self.available_languages.items() if name == dest_lang_name)
        
        # Add to queue
        models_to_add = []
        
        # Primary direction
        primary_model = f"{src_code}-{dest_code}"
        if primary_model not in self.download_queue:
            models_to_add.append(primary_model)
            self.download_queue.append(primary_model)
            
        # Bidirectional
        if self.bidirectional_var.get():
            reverse_model = f"{dest_code}-{src_code}"
            if reverse_model not in self.download_queue:
                models_to_add.append(reverse_model)
                self.download_queue.append(reverse_model)
        
        # Update UI
        for model in models_to_add:
            self.queue_listbox.insert(tk.END, model)
            
        if models_to_add:
            self.log_message(f"Added to queue: {', '.join(models_to_add)}")
        else:
            self.log_message("Models already in queue.")
            
    def clear_queue(self):
        """Clear download queue"""
        self.download_queue.clear()
        self.queue_listbox.delete(0, tk.END)
        self.log_message("Queue cleared.")
        
    def remove_selected(self):
        """Remove selected item from queue"""
        selection = self.queue_listbox.curselection()
        if selection:
            index = selection[0]
            model = self.queue_listbox.get(index)
            self.queue_listbox.delete(index)
            self.download_queue.remove(model)
            self.log_message(f"Removed from queue: {model}")
            
    def show_existing_models(self):
        """Show already downloaded models"""
        if self.models_dir.exists():
            existing_models = [item.name for item in self.models_dir.iterdir() 
                             if item.is_dir() and "-" in item.name]
            if existing_models:
                self.log_message(f"Existing models: {', '.join(existing_models)}")
            else:
                self.log_message("No existing models found.")
                
    def start_download_thread(self):
        """Start download in separate thread"""
        if not self.download_queue:
            messagebox.showwarning("Warning", "Download queue is empty.")
            return
            
        if self.is_downloading:
            messagebox.showwarning("Warning", "Download already in progress.")
            return
            
        self.is_downloading = True
        self.download_btn.configure(state=tk.DISABLED)
        self.cancel_btn.configure(state=tk.NORMAL)
        
        download_thread = threading.Thread(target=self.download_models, daemon=True)
        download_thread.start()
        
    def cancel_download(self):
        """Cancel ongoing download"""
        self.is_downloading = False
        self.download_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED)
        self.progress_label.configure(text="Cancelled")
        self.log_message("Download cancelled by user.")
        
    def download_models(self):
        """Download all models in queue"""
        total_models = len(self.download_queue)
        
        for i, model_key in enumerate(self.download_queue):
            if not self.is_downloading:
                break
                
            try:
                self.progress_label.configure(text=f"Downloading {model_key} ({i+1}/{total_models})")
                self.log_message(f"Starting download: {model_key}")
                
                # Download model
                success = self.download_single_model(model_key)
                
                if success:
                    self.log_message(f"[SUCCESS] Successfully downloaded: {model_key}")
                else:
                    self.log_message(f"[FAILED] Failed to download: {model_key}")
                    
                # Update progress
                progress = ((i + 1) / total_models) * 100
                self.progress_var.set(progress)
                
            except Exception as e:
                self.log_message(f"[ERROR] Error downloading {model_key}: {str(e)}")
                
        # Cleanup
        if self.is_downloading:
            self.progress_label.configure(text="Download completed")
            self.log_message("All downloads completed.")
        
        self.is_downloading = False
        self.download_btn.configure(state=tk.NORMAL)
        self.cancel_btn.configure(state=tk.DISABLED)
        self.progress_var.set(0)
        
    def download_single_model(self, model_key):
        """Download a single model from HuggingFace"""
        try:
            # Create model directory
            model_path = self.models_dir / model_key
            model_path.mkdir(exist_ok=True)
            self.log_message(f"  Created directory: {model_path}")
            
            # HuggingFace model identifier
            hf_model_id = f"Helsinki-NLP/opus-mt-{model_key}"
            base_url = f"https://huggingface.co/{hf_model_id}/resolve/main"
            self.log_message(f"  Downloading from: {hf_model_id}")
            
            # Files to download
            files_to_download = [
                "pytorch_model.bin",
                "config.json",
                "tokenizer.json",
                "vocab.json",
                "source.spm", 
                "target.spm"
            ]
            
            successful_downloads = 0
            
            for filename in files_to_download:
                if not self.is_downloading:
                    return False
                    
                file_url = f"{base_url}/{filename}"
                file_path = model_path / filename
                
                try:
                    self.log_message(f"  Downloading {filename}...")
                    
                    # Add headers to avoid being blocked
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    response = requests.get(file_url, stream=True, timeout=60, headers=headers)
                    
                    if response.status_code == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        
                        with open(file_path, 'wb') as f:
                            downloaded = 0
                            for chunk in response.iter_content(chunk_size=8192):
                                if not self.is_downloading:
                                    return False
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    
                        # Verify file was written
                        if file_path.exists() and file_path.stat().st_size > 0:
                            successful_downloads += 1
                            self.log_message(f"    [OK] {filename} downloaded successfully ({file_path.stat().st_size} bytes)")
                        else:
                            self.log_message(f"    [ERROR] {filename} download failed (file empty or not created)")
                    else:
                        self.log_message(f"    [WARNING] {filename} not found (status: {response.status_code})")
                        
                except requests.exceptions.RequestException as e:
                    self.log_message(f"    [ERROR] Network error downloading {filename}: {str(e)}")
                except OSError as e:
                    self.log_message(f"    [ERROR] File system error downloading {filename}: {str(e)}")
                except Exception as e:
                    self.log_message(f"    [ERROR] Unexpected error downloading {filename}: {str(e)}")
                    
            # Consider successful if we got at least the essential files
            required_files = ["pytorch_model.bin", "config.json"]
            has_required = all((model_path / f).exists() and (model_path / f).stat().st_size > 0 
                             for f in required_files)
            
            if has_required:
                self.log_message(f"  Model {model_key} downloaded successfully ({successful_downloads} files)")
                return True
            else:
                self.log_message(f"  Model {model_key} download incomplete (missing required files)")
                return False
                
        except Exception as e:
            self.log_message(f"Error downloading model {model_key}: {str(e)}")
            import traceback
            self.log_message(f"Traceback: {traceback.format_exc()}")
            return False
            
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Set UTF-8 encoding for stdout to handle Unicode characters
    try:
        if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        # Fallback for PyInstaller or other environments
        pass
    
    # Safe console output function for PyInstaller
    def safe_print(message):
        try:
            if sys.stdout:
                print(message)
                if hasattr(sys.stdout, 'flush'):
                    sys.stdout.flush()
        except:
            pass
    
    safe_print("Marian MT Model Downloader - Developer Tool")
    safe_print("=" * 50)
    
    try:
        # Determine if running as PyInstaller bundle
        if getattr(sys, 'frozen', False):
            safe_print("Running as compiled executable...")
            current_dir = Path(sys.executable).parent
        else:
            safe_print("Running as Python script...")
            current_dir = Path.cwd()
        
        safe_print(f"Current directory: {current_dir}")
        
        # Check for resources directory - but don't prompt in exe mode
        resources_dir = current_dir / "resources"
        if not resources_dir.exists():
            safe_print("Warning: 'resources' directory not found in current directory.")
            safe_print("This tool works best when run from the VezylTranslator project root.")
            
            # Only prompt if running as script AND in interactive mode
            if not getattr(sys, 'frozen', False) and sys.stdin and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty():
                safe_print("Continue anyway? (y/n): ")
                try:
                    choice = input().lower()
                    if choice != 'y':
                        safe_print("Exiting...")
                        sys.exit(1)
                except:
                    # If input fails, just continue
                    safe_print("Input failed, continuing anyway...")
            else:
                # Running as exe or non-interactive, just continue
                safe_print("Continuing with fallback directory...")
        
        # Check required packages
        safe_print("Checking dependencies...")
        
        try:
            import requests
            safe_print("[OK] requests module available")
        except ImportError:
            safe_print("[ERROR] requests module not found. Install with: pip install requests")
            # In exe mode, show messagebox instead of sys.exit
            if getattr(sys, 'frozen', False):
                try:
                    import tkinter
                    from tkinter import messagebox
                    root = tkinter.Tk()
                    root.withdraw()
                    messagebox.showerror("Missing Dependency", 
                                       "requests module not found.\n\nThis tool requires the requests library.")
                    root.destroy()
                except:
                    pass
            sys.exit(1)
            
        try:
            import tkinter
            safe_print("[OK] tkinter module available")
        except ImportError:
            safe_print("[ERROR] tkinter module not found. Please install tkinter.")
            sys.exit(1)
        
        safe_print("All dependencies OK. Starting GUI downloader...")
        
        downloader = MarianModelDownloader()
        downloader.run()
        
    except KeyboardInterrupt:
        safe_print("\nDownloader interrupted by user.")
    except Exception as e:
        safe_print(f"Error starting downloader: {e}")
        import traceback
        safe_print("Full traceback:")
        try:
            traceback.print_exc()
        except:
            safe_print("Could not print traceback")
        
        # In exe mode, also show error in messagebox
        if getattr(sys, 'frozen', False):
            try:
                import tkinter
                from tkinter import messagebox
                root = tkinter.Tk()
                root.withdraw()
                messagebox.showerror("Application Error", 
                                   f"Error starting downloader:\n\n{str(e)}")
                root.destroy()
            except:
                pass
