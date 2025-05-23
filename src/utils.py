def get_clipboard_content():
    import pyperclip
    return pyperclip.paste()

def save_to_file(content, file_path):
    with open(file_path, 'a') as file:
        file.write(content + '\n')