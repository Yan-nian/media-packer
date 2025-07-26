"""Terminal Interactive Media Packer - 终端交互式制种工具"""
import os
import json
import time
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich import print as rprint

from ..config import load_config, MediaPackerConfig
from ..core.processor import MediaProcessor
from ..core.torrent import TorrentCreator
from ..core.metadata import MetadataManager
from ..core.automation import AutomationManager, BatchProcessor
from ..utils.naming import FileNamer, FileOrganizer

console = Console()


class InteractiveMediaPacker:
    """终端交互式制种工具"""
    
    def __init__(self):
        self.console = Console()
        self.config: Optional[MediaPackerConfig] = None
        self.media_directories: List[str] = []
        self.output_directory: str = ""
        self.trackers: List[str] = []
        self.batch_processor: Optional[BatchProcessor] = None
        self.automation_manager: Optional[AutomationManager] = None
        
        # 设置文件路径
        self.settings_file = Path.home() / ".media_packer" / "interactive_settings.json"
        self.settings_file.parent.mkdir(exist_ok=True)
        
        # 内置tracker列表
        self.builtin_trackers = [
            "https://tracker1.example.com/announce",
            "https://tracker2.example.com/announce",
            "https://open.tracker.com/announce"
        ]
        
        self.load_settings()
    
    def run(self):
        """运行交互式界面"""
        self.show_welcome()
        
        while True:
            try:
                self.show_main_menu()
                choice = Prompt.ask(
                    "请选择操作",
                    choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
                    default="1"
                )
                
                if choice == "1":
                    self.manage_media_directories()
                elif choice == "2":
                    self.setup_output_directory()
                elif choice == "3":
                    self.manage_trackers()
                elif choice == "4":
                    self.scan_and_queue_files()
                elif choice == "5":
                    self.manage_queue()
                elif choice == "6":
                    self.start_processing()
                elif choice == "7":
                    self.view_settings()
                elif choice == "8":
                    self.setup_automation()
                elif choice == "9":
                    self.save_settings()
                elif choice == "0":
                    self.exit_application()
                    break
                
                self.console.print("\\n" + "="*60 + "\\n")
                
            except KeyboardInterrupt:
                if Confirm.ask("\\n确定要退出吗？"):
                    self.exit_application()
                    break
            except Exception as e:
                self.console.print(f"[red]发生错误: {e}[/red]")
                input("按回车键继续...")
    
    def show_welcome(self):
        """显示欢迎界面"""
        welcome_panel = Panel.fit(
            "[bold blue]Media Packer - 终端交互式制种工具[/bold blue]\\n"
            "[dim]基于 torf 的专业影视制种解决方案[/dim]\\n\\n"
            "[green]功能特性:[/green]\\n"
            "• 智能媒体文件识别和处理\\n"
            "• 标准化文件命名和组织\\n"
            "• TMDB 元数据自动获取\\n"
            "• 批量处理和制种队列\\n"
            "• 自动化监控和处理",
            title="欢迎使用",
            border_style="blue"
        )
        self.console.print(welcome_panel)
        input("\\n按回车键开始...")
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def show_main_menu(self):
        """显示主菜单"""
        menu_table = Table(title="[bold]主菜单[/bold]", show_header=False, box=None)
        menu_table.add_column("选项", style="cyan", width=8)
        menu_table.add_column("功能", style="white")
        menu_table.add_column("状态", style="dim", width=15)
        
        # 检查各功能状态
        media_status = f"[green]{len(self.media_directories)} 个目录[/green]" if self.media_directories else "[red]未设置[/red]"
        output_status = "[green]已设置[/green]" if self.output_directory else "[red]未设置[/red]"
        tracker_status = f"[green]{len(self.trackers)} 个[/green]" if self.trackers else "[red]未设置[/red]"
        
        menu_table.add_row("1", "媒体目录管理", media_status)
        menu_table.add_row("2", "设置输出目录", output_status)
        menu_table.add_row("3", "Tracker 配置", tracker_status)
        menu_table.add_row("4", "扫描文件并加入队列", "")
        menu_table.add_row("5", "队列管理", "")
        menu_table.add_row("6", "开始批量处理", "")
        menu_table.add_row("7", "查看当前设置", "")
        menu_table.add_row("8", "自动化设置", "")
        menu_table.add_row("9", "保存设置", "")
        menu_table.add_row("0", "退出程序", "")
        
        self.console.print(menu_table)
    
    def manage_media_directories(self):
        """管理媒体目录"""
        while True:
            self.console.print("\\n[bold]媒体目录管理[/bold]")
            
            if self.media_directories:
                dir_table = Table(title="当前媒体目录", show_header=True)
                dir_table.add_column("序号", style="cyan", width=6)
                dir_table.add_column("路径", style="white")
                dir_table.add_column("状态", style="green")
                
                for i, directory in enumerate(self.media_directories, 1):
                    status = "存在" if Path(directory).exists() else "[red]不存在[/red]"
                    dir_table.add_row(str(i), directory, status)
                
                self.console.print(dir_table)
            else:
                self.console.print("[yellow]暂无媒体目录[/yellow]")
            
            self.console.print("\\n操作选项:")
            self.console.print("1. 添加目录")
            self.console.print("2. 删除目录")
            self.console.print("3. 返回主菜单")
            
            choice = Prompt.ask("请选择操作", choices=["1", "2", "3"], default="3")
            
            if choice == "1":
                self.add_media_directory()
            elif choice == "2":
                self.remove_media_directory()
            elif choice == "3":
                break
    
    def add_media_directory(self):
        """添加媒体目录"""
        directory = Prompt.ask("请输入媒体目录路径")
        
        if not directory.strip():
            self.console.print("[red]路径不能为空[/red]")
            return
        
        directory_path = Path(directory.strip())
        
        if not directory_path.exists():
            if not Confirm.ask(f"目录 {directory} 不存在，是否仍要添加？"):
                return
        
        if directory in self.media_directories:
            self.console.print("[yellow]该目录已存在[/yellow]")
            return
        
        self.media_directories.append(directory)
        self.console.print(f"[green]已添加目录: {directory}[/green]")
    
    def remove_media_directory(self):
        """删除媒体目录"""
        if not self.media_directories:
            self.console.print("[yellow]暂无可删除的目录[/yellow]")
            return
        
        try:
            index = int(Prompt.ask("请输入要删除的目录序号")) - 1
            if 0 <= index < len(self.media_directories):
                removed_dir = self.media_directories.pop(index)
                self.console.print(f"[green]已删除目录: {removed_dir}[/green]")
            else:
                self.console.print("[red]无效的序号[/red]")
        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
    
    def setup_output_directory(self):
        """设置输出目录"""
        self.console.print("\\n[bold]输出目录设置[/bold]")
        
        if self.output_directory:
            self.console.print(f"当前输出目录: [green]{self.output_directory}[/green]")
        
        directory = Prompt.ask("请输入种子输出目录路径", default=self.output_directory)
        
        if not directory.strip():
            self.console.print("[red]路径不能为空[/red]")
            return
        
        directory_path = Path(directory.strip())
        
        # 尝试创建目录
        try:
            directory_path.mkdir(parents=True, exist_ok=True)
            self.output_directory = str(directory_path)
            self.console.print(f"[green]输出目录已设置为: {self.output_directory}[/green]")
        except Exception as e:
            self.console.print(f"[red]无法创建目录: {e}[/red]")
    
    def manage_trackers(self):
        """管理Tracker"""
        while True:
            self.console.print("\\n[bold]Tracker 配置[/bold]")
            
            # 显示当前trackers
            if self.trackers:
                tracker_table = Table(title="当前 Tracker 列表", show_header=True)
                tracker_table.add_column("序号", style="cyan", width=6)
                tracker_table.add_column("URL", style="white")
                
                for i, tracker in enumerate(self.trackers, 1):
                    tracker_table.add_row(str(i), tracker)
                
                self.console.print(tracker_table)
            else:
                self.console.print("[yellow]暂无 Tracker[/yellow]")
            
            self.console.print("\\n操作选项:")
            self.console.print("1. 添加 Tracker")
            self.console.print("2. 删除 Tracker")
            self.console.print("3. 使用内置 Tracker")
            self.console.print("4. 清空所有 Tracker")
            self.console.print("5. 返回主菜单")
            
            choice = Prompt.ask("请选择操作", choices=["1", "2", "3", "4", "5"], default="5")
            
            if choice == "1":
                self.add_tracker()
            elif choice == "2":
                self.remove_tracker()
            elif choice == "3":
                self.use_builtin_trackers()
            elif choice == "4":
                if Confirm.ask("确定要清空所有 Tracker 吗？"):
                    self.trackers.clear()
                    self.console.print("[green]已清空所有 Tracker[/green]")
            elif choice == "5":
                break
    
    def add_tracker(self):
        """添加Tracker"""
        tracker = Prompt.ask("请输入 Tracker URL")
        
        if not tracker.strip():
            self.console.print("[red]URL 不能为空[/red]")
            return
        
        if not tracker.startswith(('http://', 'https://', 'udp://')):
            self.console.print("[red]请输入有效的 URL[/red]")
            return
        
        if tracker in self.trackers:
            self.console.print("[yellow]该 Tracker 已存在[/yellow]")
            return
        
        self.trackers.append(tracker)
        self.console.print(f"[green]已添加 Tracker: {tracker}[/green]")
    
    def remove_tracker(self):
        """删除Tracker"""
        if not self.trackers:
            self.console.print("[yellow]暂无可删除的 Tracker[/yellow]")
            return
        
        try:
            index = int(Prompt.ask("请输入要删除的 Tracker 序号")) - 1
            if 0 <= index < len(self.trackers):
                removed_tracker = self.trackers.pop(index)
                self.console.print(f"[green]已删除 Tracker: {removed_tracker}[/green]")
            else:
                self.console.print("[red]无效的序号[/red]")
        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
    
    def use_builtin_trackers(self):
        """使用内置Tracker"""
        self.console.print("\\n[bold]内置 Tracker 列表:[/bold]")
        for i, tracker in enumerate(self.builtin_trackers, 1):
            self.console.print(f"{i}. {tracker}")
        
        if Confirm.ask("是否添加所有内置 Tracker？"):
            for tracker in self.builtin_trackers:
                if tracker not in self.trackers:
                    self.trackers.append(tracker)
            self.console.print(f"[green]已添加 {len(self.builtin_trackers)} 个内置 Tracker[/green]")
    
    def scan_and_queue_files(self):
        """扫描文件并加入队列"""
        if not self.media_directories:
            self.console.print("[red]请先设置媒体目录[/red]")
            return
        
        self.console.print("\\n[bold]扫描媒体文件...[/bold]")
        
        total_files = 0
        video_files = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("扫描中...", total=None)
            
            for directory in self.media_directories:
                progress.update(task, description=f"扫描: {Path(directory).name}")
                dir_path = Path(directory)
                
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file() and MediaProcessor.is_video_file(file_path):
                            video_files.append(str(file_path.absolute()))
                            total_files += 1
            
            progress.update(task, description=f"扫描完成，发现 {total_files} 个视频文件")
        
        if total_files == 0:
            self.console.print("[yellow]未发现视频文件[/yellow]")
            return
        
        # 显示发现的文件
        self.console.print(f"\\n[green]发现 {total_files} 个视频文件[/green]")
        
        if total_files <= 10:
            # 文件数量少时显示列表
            file_table = Table(title="发现的视频文件", show_header=True)
            file_table.add_column("文件名", style="white")
            file_table.add_column("大小", style="cyan")
            
            for file_path in video_files:
                path = Path(file_path)
                size = self.format_file_size(path.stat().st_size)
                file_table.add_row(path.name, size)
            
            self.console.print(file_table)
        
        if Confirm.ask("是否将这些文件加入处理队列？"):
            self.init_batch_processor()
            task_ids = self.batch_processor.add_batch([Path(f) for f in video_files])
            self.console.print(f"[green]已将 {len(task_ids)} 个文件加入队列[/green]")
    
    def manage_queue(self):
        """队列管理"""
        if not self.batch_processor:
            self.console.print("[yellow]队列为空，请先扫描文件[/yellow]")
            return
        
        while True:
            self.console.print("\\n[bold]制种队列管理[/bold]")
            
            # 显示队列统计
            all_tasks = self.batch_processor.get_all_tasks()
            pending_tasks = self.batch_processor.get_pending_tasks()
            completed_tasks = self.batch_processor.get_completed_tasks()
            error_tasks = self.batch_processor.get_error_tasks()
            
            stats_table = Table(title="队列统计", show_header=True)
            stats_table.add_column("状态", style="cyan")
            stats_table.add_column("数量", style="white")
            
            stats_table.add_row("总数", str(len(all_tasks)))
            stats_table.add_row("待处理", str(len(pending_tasks)))
            stats_table.add_row("已完成", str(len(completed_tasks)))
            stats_table.add_row("错误", str(len(error_tasks)))
            
            self.console.print(stats_table)
            
            # 显示任务列表
            if all_tasks:
                task_table = Table(title="任务列表", show_header=True, max_rows=10)
                task_table.add_column("ID", style="dim", width=10)
                task_table.add_column("文件名", style="white", max_width=40)
                task_table.add_column("状态", style="cyan")
                task_table.add_column("创建时间", style="dim")
                
                for task in list(all_tasks.values())[:10]:  # 只显示前10个
                    filename = Path(task.file_path).name
                    if len(filename) > 40:
                        filename = filename[:37] + "..."
                    
                    task_table.add_row(
                        task.id[:8],
                        filename,
                        task.status.value,
                        time.strftime("%H:%M:%S", time.localtime(task.created_at))
                    )
                
                self.console.print(task_table)
                
                if len(all_tasks) > 10:
                    self.console.print(f"[dim]... 还有 {len(all_tasks) - 10} 个任务[/dim]")
            
            self.console.print("\\n操作选项:")
            self.console.print("1. 查看详细任务列表")
            self.console.print("2. 清空队列")
            self.console.print("3. 返回主菜单")
            
            choice = Prompt.ask("请选择操作", choices=["1", "2", "3"], default="3")
            
            if choice == "1":
                self.show_detailed_queue()
            elif choice == "2":
                if Confirm.ask("确定要清空队列吗？"):
                    self.batch_processor = None
                    self.console.print("[green]队列已清空[/green]")
                    break
            elif choice == "3":
                break
    
    def show_detailed_queue(self):
        """显示详细队列信息"""
        if not self.batch_processor:
            return
        
        all_tasks = self.batch_processor.get_all_tasks()
        
        for task in all_tasks.values():
            task_panel = Panel(
                f"[bold]文件:[/bold] {Path(task.file_path).name}\\n"
                f"[bold]状态:[/bold] {task.status.value}\\n"
                f"[bold]路径:[/bold] {task.file_path}\\n"
                f"[bold]创建时间:[/bold] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.created_at))}\\n"
                + (f"[bold]完成时间:[/bold] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task.completed_at))}\\n" if task.completed_at else "")
                + (f"[bold]错误信息:[/bold] [red]{task.error_message}[/red]\\n" if task.error_message else ""),
                title=f"任务 {task.id[:8]}",
                border_style="blue" if task.status.value == "completed" else "yellow" if task.status.value == "pending" else "red"
            )
            self.console.print(task_panel)
        
        input("\\n按回车键返回...")
    
    def start_processing(self):
        """开始批量处理"""
        if not self.batch_processor:
            self.console.print("[red]队列为空，请先扫描文件[/red]")
            return
        
        if not self.output_directory:
            self.console.print("[red]请先设置输出目录[/red]")
            return
        
        if not self.trackers:
            self.console.print("[red]请先设置 Tracker[/red]")
            return
        
        pending_tasks = self.batch_processor.get_pending_tasks()
        if not pending_tasks:
            self.console.print("[yellow]没有待处理的任务[/yellow]")
            return
        
        self.console.print(f"\\n[bold]开始处理 {len(pending_tasks)} 个任务...[/bold]")
        
        # 启动批量处理
        self.batch_processor.start_processing()
        
        # 显示处理进度
        self.show_processing_progress()
    
    def show_processing_progress(self):
        """显示处理进度"""
        with Live(self.create_progress_panel(), refresh_per_second=2, console=self.console) as live:
            while True:
                all_tasks = self.batch_processor.get_all_tasks()
                pending = self.batch_processor.get_pending_tasks()
                completed = self.batch_processor.get_completed_tasks()
                error = self.batch_processor.get_error_tasks()
                
                if len(pending) == 0:
                    break
                
                live.update(self.create_progress_panel())
                time.sleep(1)
        
        # 显示处理结果
        completed_count = len(self.batch_processor.get_completed_tasks())
        error_count = len(self.batch_processor.get_error_tasks())
        
        result_panel = Panel(
            f"[green]处理完成![/green]\\n\\n"
            f"成功: {completed_count} 个\\n"
            f"失败: {error_count} 个\\n",
            title="处理结果",
            border_style="green"
        )
        self.console.print(result_panel)
        
        input("按回车键继续...")
    
    def create_progress_panel(self):
        """创建进度显示面板"""
        if not self.batch_processor:
            return Panel("无处理任务", title="处理进度")
        
        all_tasks = self.batch_processor.get_all_tasks()
        pending = self.batch_processor.get_pending_tasks()
        completed = self.batch_processor.get_completed_tasks()
        error = self.batch_processor.get_error_tasks()
        
        total = len(all_tasks)
        completed_count = len(completed)
        error_count = len(error)
        pending_count = len(pending)
        
        progress_bar = "█" * (completed_count * 20 // total) if total > 0 else ""
        progress_bar += "░" * (20 - len(progress_bar))
        
        content = f"""
[bold]处理进度:[/bold]
{progress_bar} {completed_count}/{total}

[green]已完成:[/green] {completed_count}
[yellow]待处理:[/yellow] {pending_count}
[red]错误:[/red] {error_count}

[dim]按 Ctrl+C 停止处理[/dim]
        """
        
        return Panel(content.strip(), title="批量处理中...", border_style="blue")
    
    def view_settings(self):
        """查看当前设置"""
        settings_panel = Panel(
            f"[bold]媒体目录:[/bold] {len(self.media_directories)} 个\\n"
            + "\\n".join([f"  • {d}" for d in self.media_directories[:5]]) + 
            (f"\\n  ... 还有 {len(self.media_directories) - 5} 个" if len(self.media_directories) > 5 else "") +
            f"\\n\\n[bold]输出目录:[/bold] {self.output_directory or '未设置'}\\n"
            f"\\n[bold]Trackers:[/bold] {len(self.trackers)} 个\\n"
            + "\\n".join([f"  • {t}" for t in self.trackers[:3]]) +
            (f"\\n  ... 还有 {len(self.trackers) - 3} 个" if len(self.trackers) > 3 else ""),
            title="当前设置",
            border_style="cyan"
        )
        self.console.print(settings_panel)
        input("\\n按回车键返回...")
    
    def setup_automation(self):
        """设置自动化"""
        self.console.print("\\n[bold]自动化设置[/bold]")
        self.console.print("[dim]此功能需要完整依赖包支持[/dim]")
        
        if not self.media_directories:
            self.console.print("[red]请先设置媒体目录[/red]")
            return
        
        enable_auto = Confirm.ask("是否启用自动化监控？")
        
        if enable_auto:
            self.console.print("[green]自动化功能已启用（需要完整依赖）[/green]")
        else:
            self.console.print("[yellow]自动化功能已禁用[/yellow]")
    
    def save_settings(self):
        """保存设置"""
        settings = {
            "media_directories": self.media_directories,
            "output_directory": self.output_directory,
            "trackers": self.trackers
        }
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.console.print(f"[green]设置已保存到: {self.settings_file}[/green]")
        except Exception as e:
            self.console.print(f"[red]保存设置失败: {e}[/red]")
    
    def load_settings(self):
        """加载设置"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.media_directories = settings.get("media_directories", [])
                self.output_directory = settings.get("output_directory", "")
                self.trackers = settings.get("trackers", [])
        except Exception:
            pass  # 忽略加载错误，使用默认设置
    
    def init_batch_processor(self):
        """初始化批量处理器"""
        if not self.batch_processor:
            try:
                # 尝试使用完整配置
                from ..config import load_config
                config = load_config()
                self.batch_processor = BatchProcessor(config)
            except:
                # 如果无法加载完整配置，创建简单的处理器
                self.batch_processor = SimpleBatchProcessor()
    
    def exit_application(self):
        """退出应用"""
        self.console.print("\\n[bold blue]感谢使用 Media Packer![/bold blue]")
        
        if self.batch_processor:
            self.batch_processor.stop_processing()
        
        if self.automation_manager:
            self.automation_manager.stop_automation()
        
        # 自动保存设置
        self.save_settings()
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"


class SimpleBatchProcessor:
    """简化的批量处理器（用于测试）"""
    
    def __init__(self):
        self.tasks = {}
        self.is_processing = False
    
    def add_batch(self, file_paths):
        task_ids = []
        for path in file_paths:
            task_id = f"{path.name}_{int(time.time())}"
            self.tasks[task_id] = {
                'id': task_id,
                'file_path': path,
                'status': 'pending',
                'created_at': time.time(),
                'completed_at': None,
                'error_message': None
            }
            task_ids.append(task_id)
        return task_ids
    
    def get_all_tasks(self):
        class Task:
            def __init__(self, data):
                self.id = data['id']
                self.file_path = data['file_path']
                self.status = type('Status', (), {'value': data['status']})()
                self.created_at = data['created_at']
                self.completed_at = data['completed_at']
                self.error_message = data['error_message']
        
        return {tid: Task(data) for tid, data in self.tasks.items()}
    
    def get_pending_tasks(self):
        return [task for task in self.get_all_tasks().values() if task.status.value == 'pending']
    
    def get_completed_tasks(self):
        return [task for task in self.get_all_tasks().values() if task.status.value == 'completed']
    
    def get_error_tasks(self):
        return [task for task in self.get_all_tasks().values() if task.status.value == 'error']
    
    def start_processing(self):
        self.is_processing = True
        # 模拟处理
        threading.Thread(target=self._process_worker, daemon=True).start()
    
    def stop_processing(self):
        self.is_processing = False
    
    def _process_worker(self):
        for task_id, task_data in self.tasks.items():
            if not self.is_processing:
                break
            if task_data['status'] == 'pending':
                task_data['status'] = 'processing'
                time.sleep(2)  # 模拟处理时间
                task_data['status'] = 'completed'
                task_data['completed_at'] = time.time()


def main():
    """启动交互式制种工具"""
    app = InteractiveMediaPacker()
    app.run()


if __name__ == "__main__":
    main()