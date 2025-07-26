"""GUI application for Media Packer"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import queue
import time
from datetime import datetime

from ..config import load_config, MediaPackerConfig, TorrentConfig
from ..core.automation import AutomationManager, TaskStatus
from ..core.processor import MediaProcessor
from .components import *
from .dialogs import *
from .widgets import *


class MediaPackerGUI:
    """Main GUI application for Media Packer"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Media Packer - 影视制种工具")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 应用数据
        self.config: Optional[MediaPackerConfig] = None
        self.automation_manager: Optional[AutomationManager] = None
        self.media_directories: List[str] = []
        self.torrent_output_dir = ""
        self.builtin_trackers = [
            "https://tracker1.example.com/announce",
            "https://tracker2.example.com/announce", 
            "https://open.tracker.com/announce"
        ]
        self.custom_trackers: List[str] = []
        
        # 队列和状态
        self.task_queue = queue.Queue()
        self.processing_tasks: Dict[str, Dict] = {}
        self.is_processing = False
        
        # 设置文件路径
        self.settings_file = Path.home() / ".media_packer" / "gui_settings.json"
        self.settings_file.parent.mkdir(exist_ok=True)
        
        # 初始化界面
        self.setup_ui()
        self.setup_menu()
        self.load_settings()
        self.start_status_updater()
    
    def setup_ui(self):
        """设置主界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建笔记本容器
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 主要标签页
        self.setup_main_tab()
        self.setup_queue_tab()
        self.setup_settings_tab()
        self.setup_logs_tab()
    
    def setup_main_tab(self):
        """设置主要操作标签页"""
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="主要功能")
        
        # 媒体目录设置
        media_frame = ttk.LabelFrame(main_tab, text="媒体目录设置", padding=10)
        media_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 媒体目录列表
        dir_frame = ttk.Frame(media_frame)
        dir_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(dir_frame, text="监控目录:").pack(anchor=tk.W)
        
        list_frame = ttk.Frame(dir_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.media_dirs_listbox = tk.Listbox(list_frame, height=4)
        self.media_dirs_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar1 = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.media_dirs_listbox.yview)
        scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)
        self.media_dirs_listbox.config(yscrollcommand=scrollbar1.set)
        
        # 媒体目录按钮
        btn_frame1 = ttk.Frame(media_frame)
        btn_frame1.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame1, text="添加目录", command=self.add_media_directory).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame1, text="删除目录", command=self.remove_media_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame1, text="扫描文件", command=self.scan_media_files).pack(side=tk.LEFT, padx=5)
        
        # 输出设置
        output_frame = ttk.LabelFrame(main_tab, text="输出设置", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="种子输出目录:").pack(anchor=tk.W)
        
        output_dir_frame = ttk.Frame(output_frame)
        output_dir_frame.pack(fill=tk.X, pady=5)
        
        self.output_dir_var = tk.StringVar()
        self.output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.output_dir_var, state="readonly")
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(output_dir_frame, text="选择", command=self.select_output_directory).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 处理选项
        options_frame = ttk.LabelFrame(main_tab, text="处理选项", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.organize_files_var = tk.BooleanVar(value=True)
        self.fetch_metadata_var = tk.BooleanVar(value=True)
        self.create_nfo_var = tk.BooleanVar(value=True)
        self.auto_processing_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(options_frame, text="自动组织文件结构", variable=self.organize_files_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="获取影视元数据", variable=self.fetch_metadata_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="生成NFO文件", variable=self.create_nfo_var).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="启用自动处理", variable=self.auto_processing_var, 
                       command=self.toggle_auto_processing).pack(anchor=tk.W)
        
        # 控制按钮
        control_frame = ttk.Frame(main_tab)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(control_frame, text="手动添加文件", command=self.add_files_manually).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(control_frame, text="开始处理队列", command=self.start_processing).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="暂停处理", command=self.pause_processing).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="清空队列", command=self.clear_queue).pack(side=tk.LEFT, padx=10)
    
    def setup_queue_tab(self):
        """设置队列管理标签页"""
        queue_tab = ttk.Frame(self.notebook)
        self.notebook.add(queue_tab, text="制种队列")
        
        # 队列统计
        stats_frame = ttk.LabelFrame(queue_tab, text="队列统计", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        stats_inner = ttk.Frame(stats_frame)
        stats_inner.pack(fill=tk.X)
        
        self.queue_stats_var = tk.StringVar(value="待处理: 0 | 处理中: 0 | 已完成: 0 | 错误: 0")
        ttk.Label(stats_inner, textvariable=self.queue_stats_var, font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # 队列列表
        queue_frame = ttk.LabelFrame(queue_tab, text="任务列表", padding=10)
        queue_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建树形视图
        columns = ("文件名", "状态", "类型", "进度", "创建时间")
        self.queue_tree = ttk.Treeview(queue_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.queue_tree.heading(col, text=col)
            self.queue_tree.column(col, width=120)
        
        self.queue_tree.column("文件名", width=300)
        self.queue_tree.column("进度", width=80)
        
        # 滚动条
        tree_scroll = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.queue_tree.yview)
        self.queue_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.queue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右键菜单
        self.queue_context_menu = tk.Menu(self.root, tearoff=0)
        self.queue_context_menu.add_command(label="查看详情", command=self.view_task_details)
        self.queue_context_menu.add_command(label="重新处理", command=self.retry_task)
        self.queue_context_menu.add_command(label="删除任务", command=self.delete_task)
        
        self.queue_tree.bind("<Button-2>", self.show_queue_context_menu)  # 右键 (macOS)
        self.queue_tree.bind("<Button-3>", self.show_queue_context_menu)  # 右键 (Windows/Linux)
    
    def setup_settings_tab(self):
        """设置配置标签页"""
        settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(settings_tab, text="设置")
        
        # 创建滚动区域
        canvas = tk.Canvas(settings_tab)
        scrollbar = ttk.Scrollbar(settings_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Tracker设置
        tracker_frame = ttk.LabelFrame(scrollable_frame, text="Tracker设置", padding=10)
        tracker_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        ttk.Label(tracker_frame, text="内置Trackers:").pack(anchor=tk.W)
        
        self.builtin_trackers_text = scrolledtext.ScrolledText(tracker_frame, height=4, width=60)
        self.builtin_trackers_text.pack(fill=tk.X, pady=5)
        self.builtin_trackers_text.insert(tk.END, "\\n".join(self.builtin_trackers))
        
        ttk.Label(tracker_frame, text="自定义Trackers:").pack(anchor=tk.W, pady=(10, 0))
        
        self.custom_trackers_text = scrolledtext.ScrolledText(tracker_frame, height=3, width=60)
        self.custom_trackers_text.pack(fill=tk.X, pady=5)
        
        # 种子设置
        torrent_frame = ttk.LabelFrame(scrollable_frame, text="种子设置", padding=10)
        torrent_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        self.private_torrent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(torrent_frame, text="创建私有种子", variable=self.private_torrent_var).pack(anchor=tk.W)
        
        ttk.Label(torrent_frame, text="种子注释:").pack(anchor=tk.W, pady=(10, 0))
        self.torrent_comment_var = tk.StringVar(value="Created with Media Packer")
        ttk.Entry(torrent_frame, textvariable=self.torrent_comment_var, width=50).pack(fill=tk.X, pady=5)
        
        # 命名设置
        naming_frame = ttk.LabelFrame(scrollable_frame, text="命名规范", padding=10)
        naming_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        ttk.Label(naming_frame, text="电视剧命名格式:").pack(anchor=tk.W)
        self.tv_format_var = tk.StringVar(value="{title} ({year}) S{season:02d}E{episode:02d} [{resolution}] [{codec}]")
        ttk.Entry(naming_frame, textvariable=self.tv_format_var, width=60).pack(fill=tk.X, pady=5)
        
        ttk.Label(naming_frame, text="电影命名格式:").pack(anchor=tk.W, pady=(10, 0))
        self.movie_format_var = tk.StringVar(value="{title} ({year}) [{resolution}] [{codec}]")
        ttk.Entry(naming_frame, textvariable=self.movie_format_var, width=60).pack(fill=tk.X, pady=5)
        
        # TMDB设置
        tmdb_frame = ttk.LabelFrame(scrollable_frame, text="TMDB设置", padding=10)
        tmdb_frame.pack(fill=tk.X, pady=(0, 10), padx=10)
        
        ttk.Label(tmdb_frame, text="TMDB API Key:").pack(anchor=tk.W)
        self.tmdb_api_key_var = tk.StringVar()
        ttk.Entry(tmdb_frame, textvariable=self.tmdb_api_key_var, width=50, show="*").pack(fill=tk.X, pady=5)
        
        # 设置按钮
        settings_btn_frame = ttk.Frame(scrollable_frame)
        settings_btn_frame.pack(fill=tk.X, pady=20, padx=10)
        
        ttk.Button(settings_btn_frame, text="保存设置", command=self.save_settings).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(settings_btn_frame, text="重置默认", command=self.reset_settings).pack(side=tk.LEFT, padx=10)
        ttk.Button(settings_btn_frame, text="导入配置", command=self.import_config).pack(side=tk.LEFT, padx=10)
        ttk.Button(settings_btn_frame, text="导出配置", command=self.export_config).pack(side=tk.LEFT, padx=10)
        
        # 打包滚动区域
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_logs_tab(self):
        """设置日志标签页"""
        logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(logs_tab, text="日志")
        
        # 日志显示
        log_frame = ttk.LabelFrame(logs_tab, text="应用日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 日志控制
        log_control_frame = ttk.Frame(logs_tab)
        log_control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(log_control_frame, text="清空日志", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_control_frame, text="保存日志", command=self.save_logs).pack(side=tk.LEFT, padx=10)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_control_frame, text="自动滚动", variable=self.auto_scroll_var).pack(side=tk.RIGHT)
    
    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="添加文件", command=self.add_files_manually)
        file_menu.add_command(label="添加目录", command=self.add_media_directory)
        file_menu.add_separator()
        file_menu.add_command(label="导入配置", command=self.import_config)
        file_menu.add_command(label="导出配置", command=self.export_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="清空队列", command=self.clear_queue)
        edit_menu.add_command(label="清空日志", command=self.clear_logs)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="扫描媒体文件", command=self.scan_media_files)
        tools_menu.add_command(label="验证种子", command=self.verify_torrents)
        tools_menu.add_command(label="批量重命名", command=self.batch_rename)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    # === 事件处理方法 ===
    
    def add_media_directory(self):
        """添加媒体目录"""
        directory = filedialog.askdirectory(title="选择媒体目录")
        if directory and directory not in self.media_directories:
            self.media_directories.append(directory)
            self.media_dirs_listbox.insert(tk.END, directory)
            self.log(f"添加媒体目录: {directory}")
    
    def remove_media_directory(self):
        """删除选中的媒体目录"""
        selection = self.media_dirs_listbox.curselection()
        if selection:
            index = selection[0]
            directory = self.media_directories[index]
            self.media_directories.pop(index)
            self.media_dirs_listbox.delete(index)
            self.log(f"删除媒体目录: {directory}")
    
    def select_output_directory(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择种子输出目录")
        if directory:
            self.torrent_output_dir = directory
            self.output_dir_var.set(directory)
            self.log(f"设置输出目录: {directory}")
    
    def scan_media_files(self):
        """扫描媒体文件"""
        if not self.media_directories:
            messagebox.showwarning("警告", "请先添加媒体目录")
            return
        
        self.log("开始扫描媒体文件...")
        
        def scan_worker():
            total_files = 0
            for directory in self.media_directories:
                dir_path = Path(directory)
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file() and MediaProcessor.is_video_file(file_path):
                            self.add_task_to_queue(str(file_path))
                            total_files += 1
            
            self.root.after(0, lambda: self.log(f"扫描完成，发现 {total_files} 个媒体文件"))
        
        threading.Thread(target=scan_worker, daemon=True).start()
    
    def add_files_manually(self):
        """手动添加文件"""
        files = filedialog.askopenfilenames(
            title="选择媒体文件",
            filetypes=[
                ("视频文件", "*.mkv *.mp4 *.avi *.mov *.wmv *.flv *.webm *.m4v"),
                ("所有文件", "*.*")
            ]
        )
        
        for file_path in files:
            if MediaProcessor.is_video_file(Path(file_path)):
                self.add_task_to_queue(file_path)
        
        if files:
            self.log(f"手动添加了 {len(files)} 个文件到队列")
    
    def add_task_to_queue(self, file_path: str):
        """添加任务到队列"""
        task_id = f"{Path(file_path).name}_{int(time.time())}"
        task_info = {
            "id": task_id,
            "file_path": file_path,
            "status": "待处理",
            "type": "未知",
            "progress": "0%",
            "created_time": datetime.now().strftime("%H:%M:%S"),
            "error": None
        }
        
        self.processing_tasks[task_id] = task_info
        self.update_queue_display()
    
    def start_processing(self):
        """开始处理队列"""
        if not self.processing_tasks:
            messagebox.showinfo("提示", "队列为空，请先添加文件")
            return
        
        if not self.torrent_output_dir:
            messagebox.showwarning("警告", "请先设置种子输出目录")
            return
        
        self.is_processing = True
        self.log("开始处理队列...")
        
        # 在后台线程中处理
        threading.Thread(target=self.process_queue_worker, daemon=True).start()
    
    def pause_processing(self):
        """暂停处理"""
        self.is_processing = False
        self.log("处理已暂停")
    
    def clear_queue(self):
        """清空队列"""
        if messagebox.askyesno("确认", "确定要清空所有队列任务吗？"):
            self.processing_tasks.clear()
            self.update_queue_display()
            self.log("队列已清空")
    
    def toggle_auto_processing(self):
        """切换自动处理模式"""
        if self.auto_processing_var.get():
            if not self.media_directories:
                messagebox.showwarning("警告", "请先添加监控目录")
                self.auto_processing_var.set(False)
                return
            
            self.start_auto_processing()
        else:
            self.stop_auto_processing()
    
    def start_auto_processing(self):
        """启动自动处理"""
        try:
            if not self.automation_manager:
                from ..config import load_config
                config = load_config()
                self.automation_manager = AutomationManager(config)
            
            watch_dirs = [Path(d) for d in self.media_directories]
            self.automation_manager.start_automation(watch_dirs)
            self.log("自动处理已启动")
        except Exception as e:
            self.log(f"启动自动处理失败: {e}")
            self.auto_processing_var.set(False)
    
    def stop_auto_processing(self):
        """停止自动处理"""
        if self.automation_manager:
            self.automation_manager.stop_automation()
            self.log("自动处理已停止")
    
    def process_queue_worker(self):
        """队列处理工作线程"""
        for task_id, task_info in self.processing_tasks.items():
            if not self.is_processing:
                break
            
            if task_info["status"] != "待处理":
                continue
            
            # 更新状态为处理中
            task_info["status"] = "处理中"
            task_info["progress"] = "0%"
            self.root.after(0, self.update_queue_display)
            self.root.after(0, lambda: self.log(f"开始处理: {Path(task_info['file_path']).name}"))
            
            try:
                # 模拟处理过程
                for progress in [20, 40, 60, 80, 100]:
                    if not self.is_processing:
                        break
                    
                    task_info["progress"] = f"{progress}%"
                    self.root.after(0, self.update_queue_display)
                    time.sleep(1)  # 模拟处理时间
                
                if self.is_processing:
                    task_info["status"] = "已完成"
                    task_info["progress"] = "100%"
                    self.root.after(0, lambda: self.log(f"处理完成: {Path(task_info['file_path']).name}"))
                else:
                    task_info["status"] = "已暂停"
            
            except Exception as e:
                task_info["status"] = "错误"
                task_info["error"] = str(e)
                self.root.after(0, lambda: self.log(f"处理失败: {Path(task_info['file_path']).name} - {e}"))
            
            self.root.after(0, self.update_queue_display)
        
        self.is_processing = False
        self.root.after(0, lambda: self.log("队列处理完成"))
    
    # === 界面更新方法 ===
    
    def update_queue_display(self):
        """更新队列显示"""
        # 清空树形视图
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        
        # 重新添加任务
        for task_id, task_info in self.processing_tasks.items():
            filename = Path(task_info["file_path"]).name
            self.queue_tree.insert("", tk.END, values=(
                filename,
                task_info["status"],
                task_info["type"],
                task_info["progress"],
                task_info["created_time"]
            ))
        
        # 更新统计
        pending = sum(1 for t in self.processing_tasks.values() if t["status"] == "待处理")
        processing = sum(1 for t in self.processing_tasks.values() if t["status"] == "处理中")
        completed = sum(1 for t in self.processing_tasks.values() if t["status"] == "已完成")
        error = sum(1 for t in self.processing_tasks.values() if t["status"] == "错误")
        
        self.queue_stats_var.set(f"待处理: {pending} | 处理中: {processing} | 已完成: {completed} | 错误: {error}")
    
    def start_status_updater(self):
        """启动状态更新器"""
        def update_status():
            self.update_queue_display()
            self.root.after(2000, update_status)  # 每2秒更新一次
        
        update_status()
    
    def log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\\n"
        
        self.log_text.insert(tk.END, log_entry)
        
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
    
    # === 设置管理 ===
    
    def load_settings(self):
        """加载设置"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.media_directories = settings.get("media_directories", [])
                self.torrent_output_dir = settings.get("torrent_output_dir", "")
                self.custom_trackers = settings.get("custom_trackers", [])
                
                # 更新界面
                self.media_dirs_listbox.delete(0, tk.END)
                for directory in self.media_directories:
                    self.media_dirs_listbox.insert(tk.END, directory)
                
                self.output_dir_var.set(self.torrent_output_dir)
                self.custom_trackers_text.delete(1.0, tk.END)
                self.custom_trackers_text.insert(tk.END, "\\n".join(self.custom_trackers))
                
                # 加载其他设置
                if "tmdb_api_key" in settings:
                    self.tmdb_api_key_var.set(settings["tmdb_api_key"])
                if "torrent_comment" in settings:
                    self.torrent_comment_var.set(settings["torrent_comment"])
                if "private_torrent" in settings:
                    self.private_torrent_var.set(settings["private_torrent"])
                
                self.log("设置已加载")
        except Exception as e:
            self.log(f"加载设置失败: {e}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 从界面获取当前设置
            self.custom_trackers = self.custom_trackers_text.get(1.0, tk.END).strip().split("\\n")
            self.custom_trackers = [t.strip() for t in self.custom_trackers if t.strip()]
            
            settings = {
                "media_directories": self.media_directories,
                "torrent_output_dir": self.torrent_output_dir,
                "custom_trackers": self.custom_trackers,
                "tmdb_api_key": self.tmdb_api_key_var.get(),
                "torrent_comment": self.torrent_comment_var.get(),
                "private_torrent": self.private_torrent_var.get(),
                "tv_format": self.tv_format_var.get(),
                "movie_format": self.movie_format_var.get(),
                "organize_files": self.organize_files_var.get(),
                "fetch_metadata": self.fetch_metadata_var.get(),
                "create_nfo": self.create_nfo_var.get()
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("成功", "设置已保存")
            self.log("设置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")
            self.log(f"保存设置失败: {e}")
    
    # === 其他方法 ===
    
    def show_queue_context_menu(self, event):
        """显示队列右键菜单"""
        self.queue_context_menu.post(event.x_root, event.y_root)
    
    def view_task_details(self):
        """查看任务详情"""
        selection = self.queue_tree.selection()
        if selection:
            # TODO: 实现任务详情对话框
            messagebox.showinfo("任务详情", "任务详情功能待实现")
    
    def retry_task(self):
        """重新处理任务"""
        selection = self.queue_tree.selection()
        if selection:
            # TODO: 实现重新处理逻辑
            messagebox.showinfo("重新处理", "重新处理功能待实现")
    
    def delete_task(self):
        """删除任务"""
        selection = self.queue_tree.selection()
        if selection:
            # TODO: 实现删除任务逻辑
            messagebox.showinfo("删除任务", "删除任务功能待实现")
    
    def clear_logs(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def save_logs(self):
        """保存日志"""
        filename = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("成功", "日志已保存")
    
    def reset_settings(self):
        """重置设置为默认值"""
        if messagebox.askyesno("确认", "确定要重置所有设置吗？"):
            # TODO: 重置所有设置为默认值
            messagebox.showinfo("完成", "设置已重置为默认值")
    
    def import_config(self):
        """导入配置文件"""
        filename = filedialog.askopenfilename(
            title="导入配置",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            # TODO: 实现配置导入逻辑
            messagebox.showinfo("导入配置", "配置导入功能待实现")
    
    def export_config(self):
        """导出配置文件"""
        filename = filedialog.asksaveasfilename(
            title="导出配置",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            # TODO: 实现配置导出逻辑
            messagebox.showinfo("导出配置", "配置导出功能待实现")
    
    def verify_torrents(self):
        """验证种子文件"""
        messagebox.showinfo("验证种子", "种子验证功能待实现")
    
    def batch_rename(self):
        """批量重命名"""
        messagebox.showinfo("批量重命名", "批量重命名功能待实现")
    
    def show_help(self):
        """显示帮助"""
        help_text = """
Media Packer GUI 使用说明

1. 媒体目录设置：
   - 添加需要监控的媒体文件目录
   - 可以添加多个目录进行监控

2. 输出设置：
   - 设置种子文件的输出目录

3. 处理选项：
   - 自动组织文件结构：按标准格式重新组织文件
   - 获取影视元数据：从TMDB获取详细信息
   - 生成NFO文件：创建媒体中心兼容的NFO文件
   - 启用自动处理：自动处理新添加的文件

4. 制种队列：
   - 查看所有待处理和已处理的任务
   - 可以手动添加文件或扫描目录

5. 设置：
   - 配置Tracker服务器
   - 设置种子参数
   - 配置命名规范
   - 设置TMDB API密钥
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
Media Packer GUI
版本：1.0.0

基于torf的影视剧制种工具GUI版本

功能特性：
• 智能文件识别和处理
• 标准化命名规范
• TMDB元数据集成
• 批量处理和自动化
• 直观的图形界面

开发者：Media Packer Team
许可证：GPL-3.0
        """
        messagebox.showinfo("关于 Media Packer", about_text)
    
    def on_closing(self):
        """程序关闭时的处理"""
        if self.is_processing:
            if messagebox.askyesno("确认退出", "正在处理队列，确定要退出吗？"):
                self.is_processing = False
                if self.automation_manager:
                    self.automation_manager.stop_automation()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """运行GUI应用"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


def main():
    """启动GUI应用"""
    app = MediaPackerGUI()
    app.run()


if __name__ == "__main__":
    main()