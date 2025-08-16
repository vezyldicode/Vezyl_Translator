import threading
import os
from PIL import Image
from pystray import Icon, MenuItem, Menu
from VezylTranslatorNeutron.constant import RESOURCES_DIR

tray_icon_instance = None

def get_tray_icon_instance():
    global tray_icon_instance
    return tray_icon_instance

def safe_show_homepage_from_tray():
    """
    Safely show homepage from tray icon with main window recreation if needed
    """
    try:
        # Try to get main window using global context first
        import VezylTranslator
        if hasattr(VezylTranslator, 'get_or_create_main_window'):
            main_window = VezylTranslator.get_or_create_main_window()
            if main_window is not None:
                # Reset shutdown flag if exists
                if hasattr(main_window, '_shutting_down'):
                    main_window._shutting_down = False
                main_window.show_and_fill_homepage()
                return True
        
        print("Could not get main window from global context for tray")
        return False
    except Exception as e:
        print(f"Failed to show homepage from tray: {e}")
        return False

def run_tray_icon_in_thread(
    SOFTWARE,
    get_windows_theme,
    toggle_clipboard_watcher,
    show_homepage,
    on_quit,
    menu_texts
):
    def on_tray_left_click(icon):
        toggle_clipboard_watcher()

    def on_homepage_cb(icon, item):
        # Try safe homepage function first
        if safe_show_homepage_from_tray():
            return
        
        # Fallback to original method if safe method fails
        try:
            show_homepage()
        except Exception as e:
            print(f"Fallback homepage method also failed: {e}")

    def on_quit_cb(icon, item):
        on_quit(icon, item)

    def start_tray_icon():
        try:
            # Lấy đường dẫn icon dựa trên vị trí file chính (main script)
            base_dir = os.path.dirname(os.path.abspath(os.sys.argv[0]))
            icon_path = os.path.join(base_dir, RESOURCES_DIR, "logo.ico")
            icon_path_dark = os.path.join(base_dir, RESOURCES_DIR, "logo_black.ico")
            if get_windows_theme() == "dark":
                icon_image = Image.open(icon_path)
            else:
                icon_image = Image.open(icon_path_dark)
            menu = Menu(
                MenuItem(menu_texts["toggle_clipboard_translate"], on_tray_left_click, default=True),
                Menu.SEPARATOR,
                MenuItem(menu_texts["open_homepage"], on_homepage_cb),
                MenuItem(menu_texts["quit"], on_quit_cb)
            )
            icon = Icon(
                SOFTWARE,
                icon_image,
                SOFTWARE,
                menu=menu
            )
            global tray_icon_instance
            tray_icon_instance = icon
            icon.run()
        except Exception as e:
            import sys
            sys.excepthook(*sys.exc_info())

    threading.Thread(target=start_tray_icon, daemon=True).start()
    
    # Return immediately, but provide a short delay for icon to initialize
    import time
    time.sleep(0.5)