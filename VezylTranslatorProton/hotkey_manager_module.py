import keyboard

hotkey_ids = {}  # Dictionary lưu các hotkey id

def unregister_hotkey(name):
    """Unregister a hotkey by name."""
    try:
        if name in hotkey_ids and hotkey_ids[name]:
            keyboard.remove_hotkey(hotkey_ids[name])
            hotkey_ids[name] = None
            return True
    except Exception as e:
        print(f"Error unregistering hotkey '{name}': {e}")
    return False

def register_hotkey(name, hotkey_str, callback):
    """Register a hotkey with a name, hotkey string, and callback."""
    unregister_hotkey(name)
    try:
        # Remove suppress=True to avoid system-wide key blocking
        hotkey_ids[name] = keyboard.add_hotkey(hotkey_str, callback, suppress=False)
        print(f"Registered hotkey '{name}': {hotkey_str}")
        return True
    except Exception as e:
        print(f"Failed to register hotkey '{name}' ({hotkey_str}): {e}")
        hotkey_ids[name] = None
    return False

def start_hotkey_system(translator_instance, main_window_instance, toggle_clipboard_callback):
    """Initialize all hotkey listeners using the configured hotkeys."""
    
    # Check if hotkeys are enabled in config
    if not getattr(translator_instance, 'enable_hotkeys', False):
        print("Hotkeys disabled in configuration")
        return False
    
    try:
        # Hotkey mở homepage
        success1 = register_hotkey(
            "homepage",
            translator_instance.hotkey,
            lambda: main_window_instance.show_and_fill_homepage()
        )

        # Hotkey bật/tắt clipboard watcher
        success2 = register_hotkey(
            "clipboard",
            translator_instance.clipboard_hotkey,
            toggle_clipboard_callback
        )
        
        if success1 and success2:
            print("All hotkeys registered successfully")
            return True
        else:
            print("Some hotkeys failed to register")
            return False
            
    except Exception as e:
        print(f"Error registering hotkeys: {e}")
        return False

def stop_hotkey_system():
    """Stop and unregister all hotkey listeners."""
    try:
        unregister_hotkey("homepage")
        unregister_hotkey("clipboard")
        print("All hotkeys unregistered successfully")
        return True
    except Exception as e:
        print(f"Error unregistering hotkeys: {e}")
        return False

def toggle_hotkey_system(translator_instance, main_window_instance, toggle_clipboard_callback, enable=None):
    """Toggle hotkey system on/off or set to specific state."""
    from .config_module import load_config, save_config, get_default_config
    
    if translator_instance is None:
        print("Translator instance not initialized")
        return False
    
    # If enable is None, toggle current state
    if enable is None:
        enable = not getattr(translator_instance, 'enable_hotkeys', False)
    
    # Update config
    translator_instance.enable_hotkeys = enable
    
    # Save to config file
    try:
        config = load_config(translator_instance.config_file, get_default_config())
        config['enable_hotkeys'] = enable
        save_config(translator_instance.config_file, config)
    except Exception as e:
        print(f"Error saving hotkey config: {e}")
    
    # Apply changes
    if enable:
        result = start_hotkey_system(translator_instance, main_window_instance, toggle_clipboard_callback)
        print(f"Hotkeys {'enabled' if result else 'failed to enable'}")
        return result
    else:
        result = stop_hotkey_system()
        print(f"Hotkeys {'disabled' if result else 'failed to disable'}")
        return result