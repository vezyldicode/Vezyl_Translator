import sys
import tkinter.messagebox as mb
import datetime

def main():
    # Nhận lỗi từ dòng lệnh hoặc file
    if len(sys.argv) > 1:
        error_msg = sys.argv[1]
    else:
        error_msg = sys.stdin.read()
    # Ghi log
    with open("crash.log", "a", encoding="utf-8") as f:
        f.write(f"\n[{datetime.datetime.now()}]\n{error_msg}\n")
    # Hiển thị thông báo
    mb.showerror("Vezyl Translator - Crash", f"Đã xảy ra lỗi nghiêm trọng!\n\n{error_msg}\nChi tiết đã được lưu vào crash.log.")

if __name__ == "__main__":
    main()