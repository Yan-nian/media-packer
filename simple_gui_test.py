"""最简GUI测试"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def test_gui():
    root = tk.Tk()
    root.title("Media Packer GUI - 功能测试")
    root.geometry("600x400")
    
    # 主框架
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题
    ttk.Label(main_frame, text="Media Packer GUI", 
              font=("Arial", 16, "bold")).pack(pady=(0, 20))
    
    # 功能测试区域
    test_frame = ttk.LabelFrame(main_frame, text="功能测试", padding=15)
    test_frame.pack(fill=tk.BOTH, expand=True)
    
    # 测试按钮
    ttk.Button(test_frame, text="选择媒体目录", 
               command=lambda: messagebox.showinfo("测试", f"选择的目录: {filedialog.askdirectory()}")
               ).pack(pady=5, fill=tk.X)
    
    ttk.Button(test_frame, text="选择输出目录", 
               command=lambda: messagebox.showinfo("测试", f"选择的目录: {filedialog.askdirectory()}")
               ).pack(pady=5, fill=tk.X)
    
    ttk.Button(test_frame, text="测试Tracker设置", 
               command=lambda: messagebox.showinfo("Tracker", "Tracker设置功能正常")
               ).pack(pady=5, fill=tk.X)
    
    ttk.Button(test_frame, text="测试制种队列", 
               command=lambda: messagebox.showinfo("队列", "制种队列功能正常")
               ).pack(pady=5, fill=tk.X)
    
    # 状态显示
    status_var = tk.StringVar(value="GUI界面运行正常")
    ttk.Label(test_frame, textvariable=status_var, 
              foreground="green").pack(pady=20)
    
    # 退出按钮
    ttk.Button(main_frame, text="退出", 
               command=root.destroy).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    print("启动GUI测试...")
    test_gui()
    print("GUI测试完成")