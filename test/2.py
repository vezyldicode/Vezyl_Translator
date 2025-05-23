import customtkinter as ctk
import keyboard
import pyperclip
import json
import os
from datetime import datetime
import threading
import tkinter.messagebox as messagebox
import time

class ClipboardLogger:
    def __init__(self):
        # Thiết lập chế độ màu và theme
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        # Tạo cửa sổ chính
        self.root = ctk.CTk()
        self.root.title("Clipboard Logger - Cấu hình")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # File cấu hình và file lưu clipboard
        self.config_file = "config.json"
        self.clipboard_file = "clipboard_log.txt"
        
        # Biến lưu trữ
        self.current_hotkey = "ctrl+shift+c"
        self.is_logging = False
        self.hotkey_thread = None
        self.stop_hotkey = False
        
        # Tải cấu hình
        self.load_config()
        
        # Tạo giao diện
        self.create_interface()
    
    def create_interface(self):
        # Tiêu đề
        title_label = ctk.CTkLabel(
            self.root, 
            text="Clipboard Logger", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=15)
        
        # Frame cấu hình hotkey
        hotkey_frame = ctk.CTkFrame(self.root)
        hotkey_frame.pack(pady=10, padx=20, fill="x")
        
        hotkey_label = ctk.CTkLabel(
            hotkey_frame, 
            text="Hotkey hiện tại:", 
            font=ctk.CTkFont(size=14)
        )
        hotkey_label.pack(pady=(10, 5))
        
        self.hotkey_entry = ctk.CTkEntry(
            hotkey_frame, 
            placeholder_text="Ví dụ: ctrl+shift+c",
            width=300
        )
        self.hotkey_entry.pack(pady=5)
        self.hotkey_entry.insert(0, self.current_hotkey)
        
        # Hướng dẫn
        help_label = ctk.CTkLabel(
            hotkey_frame,
            text="Hướng dẫn: ctrl+alt+c, shift+f1, ctrl+shift+v, etc.",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        help_label.pack(pady=(0, 10))
        
        # Nút cập nhật hotkey
        update_btn = ctk.CTkButton(
            self.root,
            text="Cập nhật Hotkey",
            command=self.update_hotkey,
            width=200
        )
        update_btn.pack(pady=10)
        
        # Frame trạng thái
        status_frame = ctk.CTkFrame(self.root)
        status_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Trạng thái: Chưa bắt đầu",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)
        
        # Label hiển thị số lần đã lưu
        self.count_label = ctk.CTkLabel(
            status_frame,
            text="Đã lưu: 0 lần",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.count_label.pack(pady=(0, 10))
        
        # Nút bật/tắt logging
        self.toggle_btn = ctk.CTkButton(
            self.root,
            text="Bắt đầu Logging",
            command=self.toggle_logging,
            width=200
        )
        self.toggle_btn.pack(pady=10)
        
        # Nút test hotkey
        test_btn = ctk.CTkButton(
            self.root,
            text="Test Hotkey",
            command=self.test_hotkey,
            width=200,
            fg_color="orange",
            hover_color="darkorange"
        )
        test_btn.pack(pady=5)
        
        # Nút xem file log
        view_btn = ctk.CTkButton(
            self.root,
            text="Xem File Log",
            command=self.view_log_file,
            width=200
        )
        view_btn.pack(pady=5)
        
        # Nút xóa log
        clear_btn = ctk.CTkButton(
            self.root,
            text="Xóa Log",
            command=self.clear_log,
            width=200,
            fg_color="red",
            hover_color="darkred"
        )
        clear_btn.pack(pady=5)
        
        # Biến đếm
        self.save_count = 0
    
    def load_config(self):
        """Tải cấu hình từ file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_hotkey = config.get('hotkey', 'ctrl+shift+c')
        except Exception as e:
            print(f"Lỗi khi tải cấu hình: {e}")
    
    def save_config(self):
        """Lưu cấu hình vào file"""
        try:
            config = {
                'hotkey': self.current_hotkey
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Lỗi khi lưu cấu hình: {e}")
    
    def hotkey_listener(self):
        """Thread lắng nghe hotkey"""
        try:
            while not self.stop_hotkey:
                if keyboard.is_pressed(self.current_hotkey.replace('+', '+')):
                    if self.is_logging:
                        self.save_clipboard()
                        time.sleep(0.5)  # Tránh bấm liên tục
                time.sleep(0.1)
        except Exception as e:
            print(f"Lỗi trong hotkey listener: {e}")
    
    def setup_hotkey_listener(self):
        """Thiết lập listener cho hotkey"""
        try:
            # Dừng thread cũ nếu có
            self.stop_hotkey_listener()
            
            # Bắt đầu thread mới
            self.stop_hotkey = False
            self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
            self.hotkey_thread.start()
            
            self.status_label.configure(text=f"Đang lắng nghe hotkey: {self.current_hotkey}")
            return True
        except Exception as e:
            self.status_label.configure(text=f"Lỗi thiết lập listener: {str(e)}")
            return False
    
    def stop_hotkey_listener(self):
        """Dừng listener hotkey"""
        self.stop_hotkey = True
        if self.hotkey_thread and self.hotkey_thread.is_alive():
            self.hotkey_thread.join(timeout=1)
    
    def update_hotkey(self):
        """Cập nhật hotkey mới"""
        new_hotkey = self.hotkey_entry.get().strip()
        if not new_hotkey:
            messagebox.showerror("Lỗi", "Vui lòng nhập hotkey!")
            return
        
        try:
            # Cập nhật hotkey
            self.current_hotkey = new_hotkey
            self.save_config()
            
            # Nếu đang logging thì cập nhật listener
            if self.is_logging:
                if self.setup_hotkey_listener():
                    messagebox.showinfo("Thành công", f"Đã cập nhật hotkey thành: {new_hotkey}")
                else:
                    messagebox.showerror("Lỗi", "Không thể thiết lập hotkey mới")
            else:
                messagebox.showinfo("Thành công", f"Đã lưu hotkey: {new_hotkey}")
                self.status_label.configure(text=f"Hotkey đã lưu: {new_hotkey}")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi cập nhật hotkey: {str(e)}")
    
    def test_hotkey(self):
        """Test hotkey hiện tại"""
        test_content = f"Test hotkey lúc {datetime.now().strftime('%H:%M:%S')}"
        
        # Tạm thời copy nội dung test vào clipboard  
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except:
            pass
            
        pyperclip.copy(test_content)
        
        # Lưu clipboard
        if self.save_clipboard():
            messagebox.showinfo("Test thành công", f"Đã test và lưu: {test_content}")
        
        # Khôi phục clipboard cũ
        try:
            if old_clipboard:
                pyperclip.copy(old_clipboard)
        except:
            pass
    
    def save_clipboard(self):
        """Lưu nội dung clipboard vào file"""
        try:
            clipboard_content = pyperclip.paste()
            if clipboard_content:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with open(self.clipboard_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*50}\n")
                    f.write(f"Thời gian: {timestamp}\n")
                    f.write(f"Hotkey: {self.current_hotkey}\n")
                    f.write(f"{'='*50}\n")
                    f.write(f"{clipboard_content}\n")
                
                # Cập nhật đếm và trạng thái
                self.save_count += 1
                self.status_label.configure(text=f"Vừa lưu lúc {timestamp}")
                self.count_label.configure(text=f"Đã lưu: {self.save_count} lần")
                
                print(f"Đã lưu clipboard: {clipboard_content[:50]}...")  # Debug
                return True
            else:
                self.status_label.configure(text="Clipboard trống!")
                return False
                
        except Exception as e:
            self.status_label.configure(text=f"Lỗi khi lưu: {str(e)}")
            print(f"Lỗi lưu clipboard: {e}")  # Debug
            return False
    
    def toggle_logging(self):
        """Bật/tắt chế độ logging"""
        if not self.is_logging:
            # Bắt đầu logging
            if self.setup_hotkey_listener():
                self.is_logging = True
                self.toggle_btn.configure(text="Dừng Logging", fg_color="red", hover_color="darkred")
                self.status_label.configure(text=f"Đang chờ hotkey: {self.current_hotkey}")
            else:
                messagebox.showerror("Lỗi", "Không thể bắt đầu logging!")
        else:
            # Dừng logging
            self.is_logging = False
            self.stop_hotkey_listener()
            self.toggle_btn.configure(text="Bắt đầu Logging", fg_color="#1f538d", hover_color="#14375e")
            self.status_label.configure(text="Đã dừng logging")
    
    def view_log_file(self):
        """Mở file log"""
        try:
            if os.path.exists(self.clipboard_file):
                if os.name == 'nt':  # Windows
                    os.startfile(self.clipboard_file)
                else:  # Linux/Mac
                    os.system(f'xdg-open "{self.clipboard_file}"')
            else:
                messagebox.showinfo("Thông báo", "File log chưa tồn tại!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở file log: {str(e)}")
    
    def clear_log(self):
        """Xóa file log"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa toàn bộ log?"):
            try:
                if os.path.exists(self.clipboard_file):
                    os.remove(self.clipboard_file)
                    self.save_count = 0
                    self.count_label.configure(text="Đã lưu: 0 lần")
                    messagebox.showinfo("Thành công", "Đã xóa file log!")
                    self.status_label.configure(text="Đã xóa file log")
                else:
                    messagebox.showinfo("Thông báo", "File log không tồn tại!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa file log: {str(e)}")
    
    def run(self):
        """Chạy ứng dụng"""
        print("Chương trình đã khởi động!")
        print(f"Hotkey mặc định: {self.current_hotkey}")
        print("Nhấn 'Bắt đầu Logging' để bắt đầu lắng nghe hotkey")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        print("Đang đóng chương trình...")
        self.stop_hotkey_listener()
        self.root.destroy()

def main():
    try:
        # Kiểm tra quyền admin trên Windows
        if os.name == 'nt':
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("CẢNH BÁO: Chương trình có thể cần quyền Administrator để hoạt động tốt!")
                print("Hãy thử chạy lại với quyền Administrator nếu hotkey không hoạt động.")
        
        app = ClipboardLogger()
        app.run()
        
    except ImportError as e:
        print("Lỗi: Thiếu thư viện cần thiết!")
        print("Vui lòng cài đặt các thư viện sau:")
        print("pip install customtkinter keyboard pyperclip")
        print(f"Chi tiết lỗi: {e}")
    except Exception as e:
        print(f"Lỗi không mong muốn: {e}")

if __name__ == "__main__":
    main()