#!/usr/bin/env python3
"""
Media Packer - 简化版种子生成工具
专注于种子文件创建，不包含元数据获取和NFO生成功能
"""

import os
import sys
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track, Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
import click

# 检查依赖
try:
    import torf
except ImportError:
    print("错误: 缺少 torf 库")
    print("请安装依赖: pip install torf click rich")
    sys.exit(1)

# 设置控制台
console = Console()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ================= 数据模型 =================

@dataclass
class ProcessResult:
    """处理结果"""
    original_path: Path
    organized_path: Path
    file_type: str

@dataclass
class Config:
    """配置类"""
    # Torrent 配置
    trackers: List[str] = field(default_factory=list)
    private: bool = True
    piece_size: Optional[int] = None
    comment: str = "Created with Media Packer"
    created_by: str = "Media Packer"
    
    # 路径配置
    output_dir: Path = Path("./output")

# ================= 核心处理器 =================

class MediaProcessor:
    """媒体文件处理器"""
    
    VIDEO_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    
    @staticmethod
    def is_video_file(file_path: Path) -> bool:
        """检查是否为视频文件"""
        return file_path.suffix.lower() in MediaProcessor.VIDEO_EXTENSIONS
    
    @staticmethod
    def detect_media_type(file_path: Path) -> str:
        """检测媒体类型"""
        if MediaProcessor.is_video_file(file_path):
            return "video"
        return "unknown"
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """分析文件基本信息"""
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_type = self.detect_media_type(file_path)
        file_size = file_path.stat().st_size
        
        return {
            'file_type': file_type,
            'file_size': file_size,
            'extension': file_path.suffix.lower()
        }

class FileOrganizer:
    """文件组织器"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
    
    def organize_file(self, file_path: Path, custom_name: Optional[str] = None) -> Path:
        """组织文件到指定结构"""
        if custom_name:
            # 使用自定义名称创建目录
            target_dir = self.base_path / custom_name
        else:
            # 使用文件夹名称
            if file_path.is_file():
                folder_name = file_path.parent.name
            else:
                folder_name = file_path.name
            target_dir = self.base_path / folder_name
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        if file_path.is_file():
            target_file = target_dir / file_path.name
            if not target_file.exists():
                # 创建硬链接或复制文件
                try:
                    target_file.hardlink_to(file_path)
                except OSError:
                    import shutil
                    shutil.copy2(file_path, target_file)
            return target_file
        else:
            # 如果是目录，直接返回目标目录
            return target_dir

class TorrentCreator:
    """种子创建器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def create_torrent(self, content_path: Path, torrent_path: Path) -> None:
        """创建种子文件"""
        try:
            # 创建种子
            torrent = torf.Torrent(
                path=str(content_path),
                trackers=self.config.trackers,
                private=self.config.private,
                comment=self.config.comment,
                created_by=self.config.created_by
            )
            
            if self.config.piece_size:
                torrent.piece_size = self.config.piece_size
            
            # 生成种子
            console.print(f"[cyan]正在生成种子文件...[/cyan]")
            torrent.generate()
            
            # 保存种子文件
            torrent_path.parent.mkdir(parents=True, exist_ok=True)
            torrent.write(str(torrent_path))
            
            console.print(f"[green]种子创建成功: {torrent_path}[/green]")
            
        except Exception as e:
            console.print(f"[red]创建种子失败: {e}[/red]")
            raise

# ================= 主要功能类 =================

class MediaPacker:
    """媒体打包器主类"""
    
    def __init__(self, config: Config):
        self.config = config
        self.processor = MediaProcessor()
        self.file_organizer = FileOrganizer(config.output_dir)
        self.torrent_creator = TorrentCreator(config)
        
        # 确保输出目录存在
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_file(self, file_path: Path, organize: bool = False, custom_name: Optional[str] = None) -> ProcessResult:
        """处理单个文件"""
        console.print(f"[blue]处理文件: {file_path.name}[/blue]")
        
        # 分析文件
        analysis = self.processor.analyze_file(file_path)
        
        # 组织文件（如果需要）
        if organize:
            organized_path = self.file_organizer.organize_file(file_path, custom_name)
        else:
            organized_path = file_path
        
        return ProcessResult(
            original_path=file_path,
            organized_path=organized_path,
            file_type=analysis['file_type']
        )
    
    def create_torrent_for_file(self, file_path: Path, custom_name: Optional[str] = None, **kwargs) -> Path:
        """为文件创建种子"""
        result = self.process_file(file_path, **kwargs)
        organized_path = result.organized_path
        
        # 确定种子文件名和路径
        if custom_name:
            # 使用自定义名称（通常是文件夹名称）
            torrent_name = custom_name
            if organized_path.is_file():
                content_path = organized_path.parent
            else:
                content_path = organized_path
        else:
            # 使用默认逻辑
            if organized_path.is_file():
                torrent_name = organized_path.stem
                content_path = organized_path.parent
            else:
                torrent_name = organized_path.name
                content_path = organized_path
        
        torrent_path = self.config.output_dir / f"{torrent_name}.torrent"
        
        # 创建种子
        self.torrent_creator.create_torrent(content_path, torrent_path)
        console.print(f"[green]种子文件已创建: {torrent_path}[/green]")
        
        return torrent_path
    
    def batch_process(self, file_paths: List[Path], torrent_name: str) -> Path:
        """批量处理文件"""
        console.print(f"[cyan]批量处理 {len(file_paths)} 个文件[/cyan]")
        
        processed_paths = []
        for file_path in track(file_paths, description="处理文件..."):
            try:
                result = self.process_file(file_path)
                processed_paths.append(result.organized_path)
            except Exception as e:
                console.print(f"[red]处理失败 {file_path}: {e}[/red]")
        
        # 创建批量种子
        if processed_paths:
            # 找到共同父目录
            common_parent = self._find_common_parent(processed_paths)
            torrent_path = self.config.output_dir / f"{torrent_name}.torrent"
            
            self.torrent_creator.create_torrent(common_parent, torrent_path)
            console.print(f"[green]批量种子已创建: {torrent_path}[/green]")
            
            return torrent_path
        
        raise ValueError("没有成功处理的文件")
    
    def _find_common_parent(self, paths: List[Path]) -> Path:
        """查找共同父目录"""
        if not paths:
            raise ValueError("路径列表为空")
        
        if len(paths) == 1:
            return paths[0].parent if paths[0].is_file() else paths[0]
        
        common_parts = None
        for path in paths:
            parts = path.parts
            if common_parts is None:
                common_parts = parts
            else:
                # 找到共同部分
                common_length = 0
                for i, (a, b) in enumerate(zip(common_parts, parts)):
                    if a == b:
                        common_length = i + 1
                    else:
                        break
                common_parts = common_parts[:common_length]
        
        if common_parts:
            return Path(*common_parts)
        else:
            # 如果没有共同父目录，使用输出目录
            return self.config.output_dir

# ================= 交互式界面 =================

class InteractiveMediaPacker:
    """交互式媒体打包器"""
    
    def __init__(self):
        self.console = Console()
        self.media_directories = []
        self.output_directory = None
        self.trackers = []
        self.task_queue = []
        
    def run(self):
        """运行交互式界面"""
        self.show_welcome()
        
        # 检查配置
        if not self.check_basic_config():
            if Confirm.ask("需要进行基本配置，是否启动快速配置向导？"):
                self.quick_setup_wizard()
        
        # 主菜单循环
        while True:
            self.show_main_menu()
    
    def show_welcome(self):
        """显示欢迎界面"""
        welcome_panel = Panel(
            "[bold blue]Media Packer - 简化版种子生成工具[/bold blue]\n\n"
            "[green]功能特性:[/green]\n"
            "• 智能媒体文件识别\n"
            "• 种子文件生成\n"
            "• 批量处理支持\n"
            "• 交互式操作界面\n\n"
            "[yellow]注意: 此版本专注于种子生成，不包含元数据获取功能[/yellow]",
            title="欢迎使用 Media Packer",
            border_style="blue"
        )
        self.console.print(welcome_panel)
    
    def check_basic_config(self) -> bool:
        """检查基本配置"""
        return bool(self.media_directories and self.output_directory and self.trackers)
    
    def show_main_menu(self):
        """显示主菜单"""
        self.console.print("\n[bold]主菜单[/bold]")
        
        menu_table = Table(show_header=False, box=None)
        menu_table.add_column("选项", style="cyan")
        menu_table.add_column("说明", style="white")
        
        menu_table.add_row("1", "扫描媒体文件")
        menu_table.add_row("2", "查看处理队列")
        menu_table.add_row("3", "开始处理")
        menu_table.add_row("4", "设置")
        menu_table.add_row("5", "快速配置向导")
        menu_table.add_row("0", "退出")
        
        self.console.print(menu_table)
        
        choice = Prompt.ask("请选择", choices=["0", "1", "2", "3", "4", "5"])
        
        if choice == "1":
            self.scan_files()
        elif choice == "2":
            self.show_queue()
        elif choice == "3":
            self.start_processing()
        elif choice == "4":
            self.show_settings_menu()
        elif choice == "5":
            self.quick_setup_wizard()
        elif choice == "0":
            self.console.print("[green]感谢使用 Media Packer![/green]")
            sys.exit(0)
    
    def scan_files(self):
        """扫描媒体文件"""
        if not self.media_directories:
            self.console.print("[red]请先设置媒体目录[/red]")
            return
        
        self.console.print("[cyan]正在扫描媒体文件...[/cyan]")
        
        found_files = []
        for directory in self.media_directories:
            dir_path = Path(directory)
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if MediaProcessor.is_video_file(file_path):
                        found_files.append(file_path)
        
        if found_files:
            self.console.print(f"[green]找到 {len(found_files)} 个视频文件[/green]")
            
            # 显示文件列表
            table = Table(title="发现的视频文件")
            table.add_column("文件名", style="cyan")
            table.add_column("路径", style="yellow")
            table.add_column("大小", style="green")
            
            for file_path in found_files[:10]:  # 只显示前10个
                size_mb = file_path.stat().st_size / (1024 * 1024)
                table.add_row(
                    file_path.name,
                    str(file_path.parent),
                    f"{size_mb:.1f} MB"
                )
            
            if len(found_files) > 10:
                table.add_row("...", f"还有 {len(found_files) - 10} 个文件", "...")
            
            self.console.print(table)
            
            if Confirm.ask("是否将这些文件添加到处理队列？"):
                for file_path in found_files:
                    self.task_queue.append({
                        'file_path': str(file_path),
                        'status': 'pending',
                        'added_at': time.time()
                    })
                self.console.print(f"[green]已添加 {len(found_files)} 个文件到队列[/green]")
        else:
            self.console.print("[yellow]未找到视频文件[/yellow]")
        
        input("按回车键继续...")
    
    def show_queue(self):
        """显示处理队列"""
        if not self.task_queue:
            self.console.print("[yellow]队列为空[/yellow]")
            input("按回车键继续...")
            return
        
        table = Table(title="处理队列")
        table.add_column("文件名", style="cyan")
        table.add_column("状态", style="yellow")
        table.add_column("添加时间", style="green")
        
        for task in self.task_queue[:20]:  # 显示前20个
            file_path = Path(task['file_path'])
            status_color = {
                'pending': 'yellow',
                'processing': 'blue',
                'completed': 'green',
                'error': 'red'
            }.get(task['status'], 'white')
            
            table.add_row(
                file_path.name,
                f"[{status_color}]{task['status']}[/{status_color}]",
                time.strftime("%H:%M:%S", time.localtime(task['added_at']))
            )
        
        if len(self.task_queue) > 20:
            table.add_row("...", f"还有 {len(self.task_queue) - 20} 个任务", "...")
        
        self.console.print(table)
        
        # 队列操作
        self.console.print("\n[bold]队列操作[/bold]")
        choice = Prompt.ask("操作", choices=["1", "2"], default="2")
        
        if choice == "1":
            # 清空队列
            if Confirm.ask("确定要清空队列吗？"):
                self.task_queue.clear()
                self.console.print("[green]队列已清空[/green]")
        elif choice == "2":
            pass
        
        input("按回车键继续...")
    
    def start_processing(self):
        """开始批量处理"""
        if not self.task_queue:
            self.console.print("[red]队列为空，请先扫描文件[/red]")
            return
        
        if not self.output_directory:
            self.console.print("[red]请先设置输出目录[/red]")
            return
        
        if not self.trackers:
            self.console.print("[red]请先设置 Tracker[/red]")
            return
        
        pending_tasks = [t for t in self.task_queue if t['status'] == 'pending']
        if not pending_tasks:
            self.console.print("[yellow]没有待处理的任务[/yellow]")
            return
        
        self.console.print(f"\n[bold]开始处理 {len(pending_tasks)} 个任务...[/bold]")
        
        # 创建配置
        config = Config(
            trackers=self.trackers,
            output_dir=Path(self.output_directory)
        )
        
        packer = MediaPacker(config)
        
        # 处理任务
        for task in pending_tasks:
            try:
                task['status'] = 'processing'
                self.console.print(f"[cyan]处理: {Path(task['file_path']).name}[/cyan]")
                
                # 处理文件
                file_path = Path(task['file_path'])
                
                # 获取文件夹名称
                if file_path.is_file():
                    folder_name = file_path.parent.name
                else:
                    folder_name = file_path.name
                
                self.console.print(f"[cyan]种子文件名将使用: {folder_name}[/cyan]")
                
                # 使用更新后的方法创建种子
                torrent_path = packer.create_torrent_for_file(
                    file_path,
                    custom_name=folder_name,
                    organize=True
                )
                
                task['status'] = 'completed'
                task['completed_at'] = time.time()
                
                self.console.print(f"[green]完成: {torrent_path.name}[/green]")
                
            except Exception as e:
                task['status'] = 'error'
                task['error_message'] = str(e)
                self.console.print(f"[red]错误: {e}[/red]")
        
        completed_count = len([t for t in self.task_queue if t['status'] == 'completed'])
        error_count = len([t for t in self.task_queue if t['status'] == 'error'])
        
        result_panel = Panel(
            f"[green]处理完成![/green]\n\n"
            f"成功: {completed_count} 个\n"
            f"失败: {error_count} 个\n",
            title="处理结果",
            border_style="green"
        )
        self.console.print(result_panel)
        
        input("按回车键继续...")
    
    def show_settings_menu(self):
        """显示设置菜单"""
        while True:
            self.console.print("\n[bold]设置[/bold]")
            
            settings_table = Table(show_header=False, box=None)
            settings_table.add_column("选项", style="cyan")
            settings_table.add_column("说明", style="white")
            
            settings_table.add_row("1", "媒体目录设置")
            settings_table.add_row("2", "输出目录设置")
            settings_table.add_row("3", "Tracker 设置")
            settings_table.add_row("4", "查看当前配置")
            settings_table.add_row("0", "返回主菜单")
            
            self.console.print(settings_table)
            
            choice = Prompt.ask("请选择", choices=["0", "1", "2", "3", "4"])
            
            if choice == "1":
                self.setup_media_directories()
            elif choice == "2":
                self.setup_output_directory()
            elif choice == "3":
                self.setup_trackers()
            elif choice == "4":
                self.show_current_config()
            elif choice == "0":
                break
    
    def setup_media_directories(self):
        """设置媒体目录"""
        self.console.print("\n[bold]媒体目录设置[/bold]")
        
        if self.media_directories:
            self.console.print("[green]当前目录:[/green]")
            for i, directory in enumerate(self.media_directories, 1):
                self.console.print(f"  {i}. {directory}")
        
        while True:
            directory = Prompt.ask("输入媒体目录路径（留空结束）", default="")
            if not directory.strip():
                break
            
            directory_path = Path(directory.strip())
            if directory_path.exists() or Confirm.ask(f"目录 {directory} 不存在，是否仍要添加？"):
                if directory not in self.media_directories:
                    self.media_directories.append(directory)
                    self.console.print(f"[green]✓ 已添加: {directory}[/green]")
                else:
                    self.console.print("[yellow]该目录已存在[/yellow]")
    
    def setup_output_directory(self):
        """设置输出目录"""
        self.console.print("\n[bold]输出目录设置[/bold]")
        
        if self.output_directory:
            self.console.print(f"[green]当前输出目录: {self.output_directory}[/green]")
        
        directory = Prompt.ask("输入输出目录路径", default=self.output_directory or "./output")
        
        directory_path = Path(directory)
        if not directory_path.exists():
            if Confirm.ask(f"目录 {directory} 不存在，是否创建？"):
                directory_path.mkdir(parents=True, exist_ok=True)
                self.output_directory = directory
                self.console.print(f"[green]✓ 输出目录已设置: {directory}[/green]")
        else:
            self.output_directory = directory
            self.console.print(f"[green]✓ 输出目录已设置: {directory}[/green]")
    
    def setup_trackers(self):
        """设置 Tracker"""
        self.console.print("\n[bold]Tracker 设置[/bold]")
        
        if self.trackers:
            self.console.print("[green]当前 Tracker:[/green]")
            for i, tracker in enumerate(self.trackers, 1):
                self.console.print(f"  {i}. {tracker}")
        
        # 预设的 tracker 示例
        example_trackers = [
            "http://tracker.example.com:8080/announce",
            "udp://tracker.example.com:1337/announce"
        ]
        
        self.console.print("\n[yellow]示例 Tracker (仅供参考):[/yellow]")
        for tracker in example_trackers:
            self.console.print(f"  {tracker}")
        
        while True:
            tracker = Prompt.ask("输入 Tracker URL（留空结束）", default="")
            if not tracker.strip():
                break
            
            if tracker not in self.trackers:
                self.trackers.append(tracker)
                self.console.print(f"[green]✓ 已添加: {tracker}[/green]")
            else:
                self.console.print("[yellow]该 Tracker 已存在[/yellow]")
    
    def show_current_config(self):
        """显示当前配置"""
        config_panel = Panel(
            f"[bold]媒体目录:[/bold]\n"
            f"{chr(10).join(self.media_directories) if self.media_directories else '未设置'}\n\n"
            f"[bold]输出目录:[/bold]\n"
            f"{self.output_directory or '未设置'}\n\n"
            f"[bold]Tracker:[/bold]\n"
            f"{chr(10).join(self.trackers) if self.trackers else '未设置'}",
            title="当前配置",
            border_style="cyan"
        )
        self.console.print(config_panel)
        input("按回车键继续...")
    
    def quick_setup_wizard(self):
        """快速配置向导"""
        self.console.print("\n[bold blue]快速配置向导[/bold blue]")
        self.console.print("[dim]帮助您快速完成基本设置[/dim]\n")
        
        # 步骤1：设置媒体目录
        if not self.media_directories:
            self.console.print("[yellow]步骤 1/3: 设置媒体目录[/yellow]")
            self.console.print("请输入存放视频文件的目录路径")
            
            directory = Prompt.ask("媒体目录路径", default="")
            if directory.strip():
                if Path(directory).exists() or Confirm.ask(f"目录 {directory} 不存在，是否仍要添加？"):
                    self.media_directories.append(directory)
                    self.console.print(f"[green]✓ 已添加: {directory}[/green]")
        else:
            self.console.print("[green]✓ 媒体目录已配置[/green]")
        
        # 步骤2：设置输出目录
        if not self.output_directory:
            self.console.print("\n[yellow]步骤 2/3: 设置输出目录[/yellow]")
            directory = Prompt.ask("输出目录路径", default="./output")
            
            directory_path = Path(directory)
            if not directory_path.exists():
                directory_path.mkdir(parents=True, exist_ok=True)
            
            self.output_directory = directory
            self.console.print(f"[green]✓ 输出目录已设置: {directory}[/green]")
        else:
            self.console.print("[green]✓ 输出目录已配置[/green]")
        
        # 步骤3：设置 Tracker
        if not self.trackers:
            self.console.print("\n[yellow]步骤 3/3: 设置 Tracker[/yellow]")
            self.console.print("请输入至少一个 Tracker URL")
            
            tracker = Prompt.ask("Tracker URL", default="http://tracker.example.com:8080/announce")
            if tracker.strip():
                self.trackers.append(tracker)
                self.console.print(f"[green]✓ 已添加: {tracker}[/green]")
        else:
            self.console.print("[green]✓ Tracker 已配置[/green]")
        
        self.console.print("\n[green]✓ 快速配置完成！[/green]")
        input("按回车键继续...")

# ================= 命令行接口 =================

@click.group()
@click.option('--config', '-c', type=click.Path(), help='配置文件路径')
@click.pass_context
def cli(ctx, config):
    """Media Packer - 简化版种子生成工具"""
    ctx.ensure_object(dict)
    
    # 使用默认配置
    default_config = Config(
        trackers=["http://tracker.example.com:8080/announce"],
        output_dir=Path("./output")
    )
    
    ctx.obj['config'] = default_config
    ctx.obj['packer'] = MediaPacker(default_config)

@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--organize', is_flag=True, help='组织文件结构')
@click.option('--name', '-n', help='种子名称（默认使用文件夹名称）')
@click.pass_context
def pack(ctx, input_path, output, organize, name):
    """打包文件"""
    packer = ctx.obj['packer']
    
    if output:
        packer.config.output_dir = Path(output)
        packer.file_organizer.base_path = Path(output)
    
    try:
        input_file = Path(input_path)
        
        # 如果没有指定名称，使用文件夹名称
        if not name:
            if input_file.is_file():
                name = input_file.parent.name
            else:
                name = input_file.name
        
        console.print(f"[cyan]种子文件名将使用: {name}[/cyan]")
        
        torrent_path = packer.create_torrent_for_file(
            input_file,
            custom_name=name,
            organize=organize
        )
        console.print(f"[bold green]成功创建种子: {torrent_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('input_paths', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--name', '-n', required=True, help='种子名称')
@click.pass_context
def batch(ctx, input_paths, output, name):
    """批量制种"""
    packer = ctx.obj['packer']
    
    if output:
        packer.config.output_dir = Path(output)
        packer.file_organizer.base_path = Path(output)
    
    try:
        file_paths = [Path(p) for p in input_paths]
        torrent_path = packer.batch_process(file_paths, name)
        console.print(f"[bold green]成功创建批量种子: {torrent_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]错误: {e}[/bold red]")
        raise click.ClickException(str(e))

@cli.command()
@click.argument('torrent_path', type=click.Path(exists=True))
def info(torrent_path):
    """显示种子信息"""
    try:
        torrent = torf.Torrent.read(torrent_path)
        
        info_table = Table(title="种子信息")
        info_table.add_column("属性", style="cyan")
        info_table.add_column("值", style="yellow")
        
        info_table.add_row("名称", torrent.name)
        info_table.add_row("大小", f"{torrent.size / (1024**3):.2f} GB")
        info_table.add_row("文件数", str(len(torrent.files)))
        info_table.add_row("Tracker", "\n".join(torrent.trackers))
        info_table.add_row("私有", "是" if torrent.private else "否")
        info_table.add_row("注释", torrent.comment or "无")
        
        console.print(info_table)
        
    except Exception as e:
        console.print(f"[red]读取种子文件失败: {e}[/red]")

@cli.command()
def interactive():
    """启动交互式界面"""
    try:
        app = InteractiveMediaPacker()
        app.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]程序被用户中断[/yellow]")
    except Exception as e:
        console.print(f"[red]启动交互界面失败: {e}[/red]")

if __name__ == '__main__':
    import sys
    
    # 如果没有命令行参数，默认启动交互界面
    if len(sys.argv) == 1:
        try:
            console.print("[green]启动 Media Packer 简化版交互式界面...[/green]")
            console.print("[dim]提示: 使用 'python media_packer_simple.py --help' 查看命令行模式[/dim]\n")
            app = InteractiveMediaPacker()
            app.run()
        except KeyboardInterrupt:
            console.print("\n[yellow]程序被用户中断[/yellow]")
        except ImportError as e:
            console.print(f"[red]缺少依赖: {e}[/red]")
            console.print("[yellow]请运行: pip install torf click rich[/yellow]")
        except Exception as e:
            console.print(f"[red]启动交互界面失败: {e}[/red]")
            console.print("[yellow]尝试使用命令行模式: python media_packer_simple.py --help[/yellow]")
    else:
        # 有命令行参数时运行CLI
        try:
            cli()
        except Exception as e:
            console.print(f"[red]程序执行失败: {e}[/red]")
            sys.exit(1)
