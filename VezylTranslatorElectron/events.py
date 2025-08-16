"""
Unified UI Events Module for VezylTranslator
Consolidated event handling and coordination system
Author: Tuan Viet Nguyen
Copyright (c) 2025 Vezyl. All rights reserved.
"""

import tkinter as tk


class UIEvents:
    """Unified UI event management and coordination"""
    
    def __init__(self, translator, language_interface, theme_interface, _):
        self.translator = translator
        self.language_interface = language_interface
        self.theme_interface = theme_interface
        self._ = _
        
        # Event callbacks registry
        self.callbacks = {}
        
        # Debounce timers
        self.debounce_timers = {}
    
    # === Event System ===
    
    def register_callback(self, event_name, callback):
        """Register callback for specific event"""
        if event_name not in self.callbacks:
            self.callbacks[event_name] = []
        self.callbacks[event_name].append(callback)
    
    def trigger_event(self, event_name, *args, **kwargs):
        """Trigger all callbacks for an event"""
        if event_name in self.callbacks:
            for callback in self.callbacks[event_name]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"Error in callback for {event_name}: {e}")
    
    # === Navigation Events ===
    
    def create_tab_button_handler(self, tab_name, show_tab_callback):
        """Create tab button click handler"""
        def on_tab_click():
            show_tab_callback(tab_name)
            self.trigger_event('tab_changed', tab_name)
        
        return on_tab_click
    
    # === Search Events ===
    
    def create_search_handler(self, search_var, render_callback, delay=300):
        """Create search input handler with debouncing"""
        def on_search_change(*args):
            timer_key = id(search_var)
            
            # Cancel previous timer
            if timer_key in self.debounce_timers:
                try:
                    search_var.tk.after_cancel(self.debounce_timers[timer_key])
                except:
                    pass
            
            # Set new timer
            self.debounce_timers[timer_key] = search_var.tk.after(delay, render_callback)
        
        search_var.trace_add("write", on_search_change)
        return on_search_change
    
    # === Canvas and Scrolling Events ===
    
    def create_canvas_resize_handler(self, canvas, window_id):
        """Create canvas resize handler"""
        def resize_canvas(event):
            try:
                canvas.itemconfig(window_id, width=event.width)
            except:
                pass
        
        return resize_canvas
    
    def create_scrollregion_update_handler(self, canvas):
        """Create scroll region update handler"""
        def on_configure(event):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
            except:
                pass
        
        return on_configure
    
    # === Widget Event Binding ===
    
    def bind_widget_events(self, widget, event_handlers):
        """Bind multiple events to a widget"""
        for event, handler in event_handlers.items():
            try:
                widget.bind(event, handler)
            except Exception as e:
                print(f"Error binding {event} to widget: {e}")
    
    def bind_multiple_widgets(self, widgets, event, handler):
        """Bind same event to multiple widgets"""
        for widget in widgets:
            try:
                widget.bind(event, handler)
            except Exception as e:
                print(f"Error binding event to widget: {e}")
    
    # === Form Events ===
    
    def create_entry_note_save_handler(self, note_var, entry_time, update_callback):
        """Create handler for saving note entries"""
        def save_note(event):
            new_note = note_var.get()
            update_callback(entry_time, new_note)
        
        return save_note
    
    # === Window Events ===
    
    def create_window_close_handler(self, cleanup_callback):
        """Create window close handler"""
        def on_close():
            cleanup_callback()
            self.trigger_event('window_closing')
        
        return on_close
    
    def create_fullscreen_toggle_handler(self, window, controller):
        """Create fullscreen toggle handler"""
        def toggle_fullscreen(event=None):
            controller.toggle_fullscreen(window)
            self.trigger_event('fullscreen_toggled', controller.is_fullscreen)
        
        return toggle_fullscreen
    
    def create_fullscreen_exit_handler(self, window, controller):
        """Create fullscreen exit handler"""
        def exit_fullscreen(event=None):
            controller.exit_fullscreen(window)
            self.trigger_event('fullscreen_exited')
        
        return exit_fullscreen
    
    # === Input Events ===
    
    def create_combo_change_handler(self, callback):
        """Create combobox change handler"""
        def on_combo_change(selected_value):
            callback(selected_value)
            self.trigger_event('combo_changed', selected_value)
        
        return on_combo_change
    
    def create_text_modification_handler(self, text_widget, callback):
        """Create text modification handler"""
        def on_text_modified(event):
            text_widget.edit_modified(False)  # Reset modified flag
            callback(event)
            self.trigger_event('text_modified', text_widget.get("1.0", "end").strip())
        
        return on_text_modified
    
    def create_button_click_handler(self, callback, *args, **kwargs):
        """Create button click handler"""
        def on_button_click():
            callback(*args, **kwargs)
            self.trigger_event('button_clicked', callback.__name__ if hasattr(callback, '__name__') else 'unknown')
        
        return on_button_click
    
    # === Window Setup ===
    
    def setup_window_events(self, window, controller):
        """Setup common window events"""
        # Fullscreen events
        window.bind("<F11>", self.create_fullscreen_toggle_handler(window, controller))
        window.bind("<Escape>", self.create_fullscreen_exit_handler(window, controller))
        
        # Close event
        window.protocol("WM_DELETE_WINDOW", self.create_window_close_handler(
            lambda: controller.on_close(window)
        ))
        
        return {
            'fullscreen_toggle': self.create_fullscreen_toggle_handler(window, controller),
            'fullscreen_exit': self.create_fullscreen_exit_handler(window, controller),
            'close': self.create_window_close_handler(lambda: controller.on_close(window))
        }
    
    # === Cleanup ===
    
    def cleanup(self):
        """Cleanup event handlers and timers"""
        # Cancel all debounce timers
        for timer_id in self.debounce_timers.values():
            try:
                # Note: We can't access tk after destruction, so this may fail
                pass
            except:
                pass
        
        self.debounce_timers.clear()
        self.callbacks.clear()


# === Legacy Support ===
# For backward compatibility with existing imports

__all__ = ['UIEvents']
