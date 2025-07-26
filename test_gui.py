"""简化的GUI测试版本"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from pathlib import Path

class SimpleGUITest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Media Packer GUI - 测试版")
        self.root.geometry("800x600")
        
        self.media_directories = []
        self.output_directory = ""
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 媒体目录设置
        media_frame = ttk.LabelFrame(main_frame, text="媒体目录设置", padding=10)
        media_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(media_frame, text="监控目录:").pack(anchor=tk.W)
        
        self.dirs_listbox = tk.Listbox(media_frame, height=4)
        self.dirs_listbox.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(media_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="添加目录", command=self.add_directory).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="删除目录", command=self.remove_directory).pack(side=tk.LEFT)
        
        # 输出设置
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="种子输出目录:").pack(anchor=tk.W)
        
        output_dir_frame = ttk.Frame(output_frame)
        output_dir_frame.pack(fill=tk.X, pady=5)
        
        self.output_var = tk.StringVar()
        ttk.Entry(output_dir_frame, textvariable=self.output_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_dir_frame, text="选择", command=self.select_output).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Tracker设置
        tracker_frame = ttk.LabelFrame(main_frame, text="Tracker设置", padding=10)
        tracker_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(tracker_frame, text="Tracker列表 (每行一个):").pack(anchor=tk.W)
        
        self.tracker_text = tk.Text(tracker_frame, height=4)
        self.tracker_text.pack(fill=tk.X, pady=5)
        self.tracker_text.insert(tk.END, "https://tracker1.example.com/announce\\nhttps://tracker2.example.com/announce")
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="开始制种", command=self.start_torrenting).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="保存设置", command=self.save_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="加载设置", command=self.load_settings).pack(side=tk.LEFT, padx=10)
        
        # 状态显示
        status_frame = ttk.LabelFrame(main_frame, text="状态", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_text = tk.Text(status_frame, height=10)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        self.log("GUI界面初始化完成")
    
    def add_directory(self):
        directory = filedialog.askdirectory(title="选择媒体目录")
        if directory and directory not in self.media_directories:
            self.media_directories.append(directory)
            self.dirs_listbox.insert(tk.END, directory)
            self.log(f"添加目录: {directory}")
    
    def remove_directory(self):
        selection = self.dirs_listbox.curselection()
        if selection:
            index = selection[0]
            directory = self.media_directories[index]
            self.media_directories.pop(index)
            self.dirs_listbox.delete(index)
            self.log(f"删除目录: {directory}")
    
    def select_output(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_directory = directory
            self.output_var.set(directory)
            self.log(f"设置输出目录: {directory}")
    
    def start_torrenting(self):
        if not self.media_directories:
            messagebox.showwarning("警告", "请先添加媒体目录")
            return
        
        if not self.output_directory:
            messagebox.showwarning("警告", "请先设置输出目录")
            return
        
        trackers = self.tracker_text.get(1.0, tk.END).strip().split("\\n")
        trackers = [t.strip() for t in trackers if t.strip()]
        
        if not trackers:
            messagebox.showwarning("警告", "请设置至少一个Tracker")
            return
        
        self.log("开始制种...")
        self.log(f"媒体目录: {', '.join(self.media_directories)}")
        self.log(f"输出目录: {self.output_directory}")
        self.log(f"Tracker数量: {len(trackers)}")
        
        messagebox.showinfo("提示", "制种功能需要安装完整依赖包才能使用")
    
    def save_settings(self):
        settings = {
            "media_directories": self.media_directories,
            "output_directory": self.output_directory,
            "trackers": self.tracker_text.get(1.0, tk.END).strip().split("\\n")
        }
        
        filename = filedialog.asksaveasfilename(
            title="保存设置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")]
        )
        
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.log(f"设置已保存到: {filename}")
    
    def load_settings(self):
        filename = filedialog.askopenfilename(
            title="加载设置",
            filetypes=[("JSON文件", "*.json")]
        )
        
        if filename and Path(filename).exists():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.media_directories = settings.get("media_directories", [])
                self.output_directory = settings.get("output_directory", "")
                trackers = settings.get("trackers", [])
                
                # 更新界面
                self.dirs_listbox.delete(0, tk.END)
                for directory in self.media_directories:
                    self.dirs_listbox.insert(tk.END, directory)
                
                self.output_var.set(self.output_directory)
                
                self.tracker_text.delete(1.0, tk.END)
                self.tracker_text.insert(tk.END, "\\n".join(trackers))
                
                self.log(f"设置已从 {filename} 加载")
            except Exception as e:
                messagebox.showerror("错误", f"加载设置失败: {e}")
    
    def log(self, message):
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\\n")
        self.status_text.see(tk.END)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SimpleGUITest()
    app.run()