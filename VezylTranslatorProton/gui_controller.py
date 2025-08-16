"""
GUI Controller Module for VezylTranslator
Handles main GUI logic and coordinates between UI and backend modules
"""

import os
import threading
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from VezylTranslatorNeutron import constant
from VezylTranslatorProton.utils import get_windows_theme


class GUIController:
    def __init__(self, translator, language_interface, theme_interface, _):
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
        
        # Translation executor for async operations
        self.translation_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="gui_translate")
        self.pending_translations = {}
        
        # UI state management
        self._shutting_down = False
        self.ctrl_pressed = False
        self.active_mousewheel_handlers = []
        
        # Window state
        self.is_fullscreen = False
        self.width = 900
        self.height = 600
        
    def get_window_config(self):
        """Get window configuration"""
        return {
            'title': f"{constant.SOFTWARE} {constant.SOFTWARE_VERSION}",
            'width': self.width,
            'height': self.height,
            'icon_path': self._get_icon_path(),
            'resizable': True
        }
    
    def _get_icon_path(self):
        """Get appropriate icon based on system theme"""
        theme = get_windows_theme()
        if theme == "dark":
            return os.path.join(constant.RESOURCES_DIR, "logo.ico")
        else:
            return os.path.join(constant.RESOURCES_DIR, "logo_black.ico")
    
    def translate_async(self, widget_id, translate_function):
        """Execute translation asynchronously using ThreadPool"""
        if self._shutting_down:
            print("Translation skipped: Application shutting down")
            return None
            
        if not hasattr(self, 'translation_executor') or self.translation_executor._shutdown:
            print("Translation executor unavailable or shutdown")
            return None
            
        # Cancel pending translation for this widget
        if widget_id in self.pending_translations:
            try:
                self.pending_translations[widget_id].cancel()
            except:
                pass
            
        try:
            future = self.translation_executor.submit(translate_function)
            self.pending_translations[widget_id] = future
            
            def on_complete(fut):
                self.pending_translations.pop(widget_id, None)
                try:
                    fut.result()
                except Exception as e:
                    print(f"Translation error: {e}")
                    
            future.add_done_callback(on_complete)
            return future
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                print("Translation executor has been shutdown")
                return None
            else:
                raise
    
    def cancel_translation(self, widget_id):
        """Cancel translation for specific widget"""
        if widget_id in self.pending_translations:
            try:
                self.pending_translations[widget_id].cancel()
            except:
                pass
            self.pending_translations.pop(widget_id, None)
    
    def setup_ctrl_tracking(self, window):
        """Setup or disable Ctrl key tracking"""
        # Unbind all Ctrl events first
        window.unbind_all('<Control_L>')
        window.unbind_all('<Control_R>')
        window.unbind_all('<KeyRelease-Control_L>')
        window.unbind_all('<KeyRelease-Control_R>')
        
        # Only bind if explicitly enabled
        if getattr(self.translator, 'enable_ctrl_tracking', False):
            window.bind_all('<Control_L>', self._ctrl_down)
            window.bind_all('<Control_R>', self._ctrl_down)
            window.bind_all('<KeyRelease-Control_L>', self._ctrl_up)
            window.bind_all('<KeyRelease-Control_R>', self._ctrl_up)
            print("Ctrl tracking enabled (may cause system delays)")
        else:
            print("Ctrl tracking disabled (recommended for performance)")
    
    def _ctrl_down(self, event=None):
        self.ctrl_pressed = True

    def _ctrl_up(self, event=None):
        self.ctrl_pressed = False
    
    def add_mousewheel_handler(self, canvas, handler_func):
        """Add mousewheel handler and track it for cleanup"""
        self.active_mousewheel_handlers.append((canvas, handler_func))
        canvas.bind_all("<MouseWheel>", handler_func)
        
    def cleanup_mousewheel_handlers(self):
        """Clean up all tracked mousewheel handlers"""
        for canvas, handler_func in self.active_mousewheel_handlers:
            try:
                if canvas.winfo_exists():
                    canvas.unbind_all("<MouseWheel>")
            except:
                pass
        self.active_mousewheel_handlers.clear()

    def safe_mousewheel_handler(self, canvas):
        """Create a safe mousewheel handler for a canvas"""
        def _on_mousewheel(event):
            try:
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            except:
                pass
        return _on_mousewheel
    
    def toggle_fullscreen(self, window):
        self.is_fullscreen = not self.is_fullscreen
        window.attributes("-fullscreen", self.is_fullscreen)

    def exit_fullscreen(self, window):
        self.is_fullscreen = False
        window.attributes("-fullscreen", False)
    
    def on_close(self, window):
        """Cleanup resources when closing window"""
        try:
            self._shutting_down = True
            self.cleanup_mousewheel_handlers()
            
            # Cancel all pending translations
            for future in list(self.pending_translations.values()):
                try:
                    future.cancel()
                except:
                    pass
            self.pending_translations.clear()
            
            # Shutdown ThreadPool
            if hasattr(self, 'translation_executor') and not self.translation_executor._shutdown:
                self.translation_executor.shutdown(wait=False)
            
            # Check if Ctrl is pressed when closing to exit completely
            if getattr(self.translator, 'enable_ctrl_tracking', True) and self.ctrl_pressed:
                window.destroy()
                os._exit(0)
            else:
                window.withdraw()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            window.withdraw()
    
    def destroy_cleanup(self):
        """Cleanup for window destruction"""
        try:
            self._shutting_down = True
            self.cleanup_mousewheel_handlers()
            
            # Cancel all pending translations
            for future in list(self.pending_translations.values()):
                try:
                    future.cancel()
                except:
                    pass
            self.pending_translations.clear()
            
            # Shutdown ThreadPool if still running
            if hasattr(self, 'translation_executor') and not self.translation_executor._shutdown:
                self.translation_executor.shutdown(wait=False)
                
        except Exception as e:
            print(f"Error during destroy cleanup: {e}")
