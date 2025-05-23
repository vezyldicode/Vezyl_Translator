import keyboard
import pyperclip
import time
from utils import get_clipboard_content

def on_f2_press():
    clipboard_content = pyperclip.paste()
    get_clipboard_content(clipboard_content)

def main():
    keyboard.add_hotkey('F2', on_f2_press)
    print("Clipboard watcher is running. Press F2 to save clipboard content.")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()