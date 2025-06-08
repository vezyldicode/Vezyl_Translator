import tkinter as tk
import webbrowser

def mo_trang_web():
    tu = entry.get().strip()
    if not tu:
        return
    url = f"https://www.verbformen.de/konjugation/?w={tu}"
    webbrowser.open(url)

# Giao diện tkinter
root = tk.Tk()
root.title("Tra từ tiếng Đức")

tk.Label(root, text="Nhập từ:").pack(pady=5)
entry = tk.Entry(root, width=30)
entry.pack()

tk.Button(root, text="Mở trong trình duyệt", command=mo_trang_web).pack(pady=10)

root.mainloop()
