#!/usr/bin/env python3
"""
Media Packer - 简化版种子生成工具
专注于种子文件创建，不包含元数据获取和NFO生成功能
版本: 2.1.0
"""

import os
import sys
import time
import logging
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

# 版本信息
try:
    from version import __version__
except ImportError:
    __version__ = "unknown"
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 依赖检查和自动安装
def check_and_install_dependencies():
    """检查并自动安装依赖"""
    required_packages = {
        'torf': 'torf>=4.0.0',
        'click': 'click>=8.0.0', 
        'rich': 'rich>=13.0.0',
        'psutil': 'psutil>=5.8.0'  # 性能监控依赖
    }
    
    missing_packages = []
    
    # 检查依赖
    for package_name, package_spec in required_packages.items():
        try:
            __import__(package_name)
            print(f"✓ {package_name} 已安装")
        except ImportError:
            missing_packages.append(package_spec)
            print(f"✗ {package_name} 未安装")
    
    # 如果有缺失的包，询问是否自动安装
    if missing_packages:
        print(f"\n发现 {len(missing_packages)} 个缺失的依赖包:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        
        # 在非交互环境中自动安装
        if not sys.stdin.isatty():
            install_choice = 'y'
        else:
            install_choice = input("\n是否自动安装缺失的依赖? (y/n): ").lower().strip()
        
        if install_choice in ['y', 'yes', '']:
            print("\n正在安装依赖...")
            try:
                for package_spec in missing_packages:
                    print(f"安装 {package_spec}...")
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', package_spec
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✓ {package_spec} 安装成功")
                    else:
                        print(f"✗ {package_spec} 安装失败: {result.stderr}")
                        return False
                
                print("\n所有依赖安装完成！正在重新启动程序...")
                # 重新启动脚本
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
            except Exception as e:
                print(f"安装依赖时出错: {e}")
                print("请手动安装依赖: pip install torf click rich")
                return False
        else:
            print("请手动安装依赖后再运行:")
            print("pip install torf click rich")
            return False
    
    return True

# 检查并安装依赖
if not check_and_install_dependencies():
    sys.exit(1)

# 现在可以安全地导入依赖
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track, Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
import click
import torf

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
    
    # 性能优化配置
    auto_optimize: bool = True  # 自动优化性能配置
    max_workers: Optional[int] = None  # 最大工作线程数
    
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
        # 添加缓存来存储已计算的值
        self._cache = {}
    
    def _get_optimal_piece_size(self, total_size: int) -> int:
        """根据文件大小获取最优piece size - 性能优化版本"""
        if not self.config.auto_optimize:
            return self.config.piece_size if self.config.piece_size else 0
        
        # VPS优化的Piece Size配置 - 更大的piece size提升性能
        if total_size < 50 * 1024 * 1024:  # < 50MB
            return 256 * 1024  # 256KB - 小文件适中配置
        elif total_size < 500 * 1024 * 1024:  # < 500MB
            return 1024 * 1024  # 1MB - 中小文件
        elif total_size < 1 * 1024 * 1024 * 1024:  # < 1GB
            return 2 * 1024 * 1024  # 2MB - 1GB以下文件
        elif total_size < 4 * 1024 * 1024 * 1024:  # < 4GB
            return 4 * 1024 * 1024  # 4MB - VPS环境下4GB文件最优
        elif total_size < 16 * 1024 * 1024 * 1024:  # < 16GB
            return 8 * 1024 * 1024  # 8MB - 大文件
        elif total_size < 64 * 1024 * 1024 * 1024:  # < 64GB
            return 16 * 1024 * 1024  # 16MB - 超大文件
        else:  # >= 64GB
            return 8 * 1024 * 1024  # 8MB - 巨大文件
    
    def _get_optimal_workers(self) -> int:
        """获取最优工作线程数 - 自动检测CPU核心数并优化"""
        if not self.config.auto_optimize:
            return self.config.max_workers if self.config.max_workers else 1
        
        import multiprocessing
        import psutil
        
        # 获取物理CPU核心数（更准确）
        try:
            physical_cores = psutil.cpu_count(logical=False) or multiprocessing.cpu_count()
            logical_cores = psutil.cpu_count(logical=True) or multiprocessing.cpu_count()
        except:
            physical_cores = logical_cores = multiprocessing.cpu_count()
        
        # 检测系统负载
        try:
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
            cpu_percent = psutil.cpu_percent(interval=0.1)
        except:
            load_avg = 0
            cpu_percent = 0
        
        # 智能线程数计算 - VPS优化版本
        if physical_cores >= 32:  # 超高性能CPU（如双路服务器）
            optimal_workers = min(20, physical_cores // 2)
        elif physical_cores >= 16:  # 高性能CPU（如至强E5、AMD EPYC）
            optimal_workers = min(16, physical_cores // 2 + 2)
        elif physical_cores >= 10:  # 10核心VPS优化（如Xeon 5115）
            optimal_workers = min(12, physical_cores + 2)  # 10核用12线程
        elif physical_cores >= 8:  # 中高端CPU
            optimal_workers = min(8, physical_cores + 1)
        elif physical_cores >= 4:  # 主流CPU
            optimal_workers = physical_cores + 1
        else:  # 低端CPU
            optimal_workers = max(3, physical_cores)
        
        # VPS环境特殊优化 - 更激进的线程策略
        if cpu_percent < 50:  # CPU使用率低，可以使用更多线程
            optimal_workers = min(optimal_workers + 2, 16)
        elif cpu_percent > 80 or load_avg > physical_cores * 0.8:
            optimal_workers = max(2, optimal_workers // 2)
        
        # 添加内存限制检查
        try:
            memory = psutil.virtual_memory()
            # 如果内存小于4GB，限制线程数
            if memory.total < 4 * 1024 * 1024 * 1024:
                optimal_workers = min(optimal_workers, 4)
            # 如果内存充足，可以使用更多线程
            elif memory.total >= 32 * 1024 * 1024 * 1024:  # 32GB+内存
                optimal_workers = min(optimal_workers + 4, 20)
        except:
            pass
        
        return min(optimal_workers, 20)  # 最大20线程，充分利用高性能CPU
    
    def _calculate_total_size(self, content_path: Path) -> int:
        """计算内容总大小"""
        # 使用缓存避免重复计算
        cache_key = f"size_{content_path}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        total_size = 0
        if content_path.is_file():
            total_size = content_path.stat().st_size
        else:
            for file_path in content_path.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        continue
                        
        # 缓存结果
        self._cache[cache_key] = total_size
        return total_size
    
    def create_torrent(self, content_path: Path, torrent_path: Path) -> None:
        """创建种子文件"""
        try:
            # 计算总大小用于优化配置
            total_size = self._calculate_total_size(content_path)
            console.print(f"[cyan]内容总大小: {total_size / (1024**3):.2f} GB[/cyan]")
            
            # 获取最优配置
            optimal_piece_size = self._get_optimal_piece_size(total_size)
            optimal_workers = self._get_optimal_workers()
            
            if self.config.auto_optimize:
                # 显示详细的性能优化信息
                size_mb = total_size / (1024 * 1024)
                piece_mb = optimal_piece_size / (1024 * 1024) if optimal_piece_size >= 1024*1024 else optimal_piece_size / 1024
                piece_unit = "MB" if optimal_piece_size >= 1024*1024 else "KB"
                
                console.print(f"[green]🚀 智能性能优化[/green]")
                console.print(f"[cyan]  📁 文件大小: {size_mb:.1f} MB[/cyan]")
                console.print(f"[cyan]  🧩 Piece Size: {piece_mb:.0f} {piece_unit}[/cyan]")
                console.print(f"[cyan]  🔥 线程数: {optimal_workers}[/cyan]")
                
                # 获取CPU信息
                try:
                    import psutil
                    cpu_count = psutil.cpu_count(logical=False) or 1
                    console.print(f"[dim]  💻 检测到 {cpu_count} 核心CPU[/dim]")
                except:
                    pass
            
            # 创建种子
            torrent = torf.Torrent(
                path=str(content_path),
                trackers=self.config.trackers,
                private=self.config.private,
                comment=self.config.comment,
                created_by=self.config.created_by
            )
            
            # 设置piece size
            if optimal_piece_size > 0:
                torrent.piece_size = optimal_piece_size
            elif self.config.piece_size:
                torrent.piece_size = self.config.piece_size
            
            # 生成种子
            console.print(f"[cyan]正在生成种子文件...[/cyan]")
            
            # 多线程将在torrent.generate()中通过threads参数设置
            console.print(f"[green]🚀 将使用 {optimal_workers} 线程进行哈希计算[/green]")
            
            # 显示进度 - 使用独立控制台避免冲突
            import time
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
            from rich.console import Console
            
            # 创建独立的进度条控制台，避免与主控制台冲突
            progress_console = Console()
            console.print("")  # 空行，为进度条预留空间
            start_time = time.time()
            
            # 使用独立控制台的进度条
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=progress_console,
                refresh_per_second=2,  # 限制刷新频率
                transient=False,  # 进度条完成后保留显示
                disable=False  # 确保进度条启用
            ) as progress:
                
                task = progress.add_task(f"[cyan]制种进度 ({optimal_workers} 线程)", total=100)
                
                # 添加进度回调函数 - 静默版本
                last_update_time = 0
                last_percent = 0
                def progress_callback(torrent, filepath, pieces_done, pieces_total):
                    nonlocal last_update_time, last_percent
                    current_time = time.time()
                    
                    # 限制刷新频率，避免闪烁（每1秒更新一次）
                    if current_time - last_update_time < 1.0 and pieces_done < pieces_total:
                        return
                    
                    last_update_time = current_time
                    
                    if pieces_total > 0:
                        percent = (pieces_done / pieces_total) * 100
                        
                        # 只在进度有明显变化时更新
                        if abs(percent - last_percent) >= 1.0 or pieces_done == pieces_total:
                            progress.update(task, completed=percent)
                            last_percent = percent
                            
                            if pieces_done > 0:
                                elapsed = current_time - start_time
                                speed = (pieces_done / elapsed) if elapsed > 0 else 0
                                progress.update(task, description=f"[cyan]制种进度 ({optimal_workers} 线程) - {speed:.1f} pieces/s")
                
                # 使用正确的torf多线程参数
                try:
                    # 使用threads参数启用多线程，interval降低回调频率
                    torrent.generate(
                        callback=progress_callback, 
                        interval=1.0,  # 每秒回调一次
                        threads=optimal_workers  # 关键：使用threads参数而不是其他方法
                    )
                except TypeError:
                    # 降级到无回调的多线程模式
                    try:
                        torrent.generate(threads=optimal_workers)
                        progress.update(task, completed=100)
                    except TypeError:
                        # 最后降级到单线程模式
                        progress.update(task, description="[cyan]正在生成种子文件（单线程模式）...")
                        torrent.generate()
                        progress.update(task, completed=100)
            
            end_time = time.time()
            duration = end_time - start_time
            throughput = (total_size / (1024**2)) / duration if duration > 0 else 0
            
            # 确保进度条完成后有清晰的分隔
            console.print("")
            console.print(f"[green]✅ 哈希计算完成 - 用时: {duration:.1f}s, 吞吐量: {throughput:.1f} MB/s[/green]")
            
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

# ================= 并行处理优化 =================

class ParallelMediaPacker(MediaPacker):
    """支持并行处理的媒体打包器"""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.lock = threading.Lock()  # 用于线程安全
    
    def process_files_parallel(self, file_paths: List[Path], max_workers: int = 4) -> List[ProcessResult]:
        """并行处理多个文件"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_path = {
                executor.submit(self.process_file, path): path 
                for path in file_paths
            }
            
            # 收集结果
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    console.print(f"[red]处理失败 {path}: {e}[/red]")
        
        return results

# ================= 交互式界面 =================

class InteractiveMediaPacker:
    """交互式媒体打包器"""
    
    def __init__(self):
        self.console = Console()
        self.config_file = Path.home() / ".media_packer_config.json"
        self.media_directories = []
        self.output_directory = None
        self.trackers = []
        self.task_queue = []
        
        # 加载配置
        self.load_config()
        
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.media_directories = config_data.get('media_directories', [])
                    self.output_directory = config_data.get('output_directory', None)
                    self.trackers = config_data.get('trackers', [])
                    self.console.print(f"[green]✓ 已加载配置文件: {self.config_file}[/green]")
        except Exception as e:
            self.console.print(f"[yellow]加载配置文件失败: {e}[/yellow]")
    
    def save_config(self):
        """保存配置文件"""
        try:
            config_data = {
                'media_directories': self.media_directories,
                'output_directory': self.output_directory,
                'trackers': self.trackers,
                'saved_at': time.time()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            self.console.print(f"[green]✓ 配置已保存: {self.config_file}[/green]")
        except Exception as e:
            self.console.print(f"[red]保存配置文件失败: {e}[/red]")
        
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
            f"[bold blue]Media Packer - 简化版种子生成工具[/bold blue]\n"
            f"[dim]版本: v{__version__}[/dim]\n\n"
            "[green]功能特性:[/green]\n"
            "• 智能媒体文件识别\n"
            "• 种子文件生成\n"
            "• 批量处理支持\n"
            "• 交互式操作界面\n"
            "• [bold cyan]自动性能优化 (默认启用)[/bold cyan]\n\n"
            "[cyan]性能优化特性:[/cyan]\n"
            "• 智能 piece size 选择\n"
            "• 多线程加速制种\n"
            "• VPS 环境优化\n\n"
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
        
        menu_table.add_row("1", "智能扫描媒体文件夹（支持片名搜索）")
        menu_table.add_row("2", "查看处理队列")
        menu_table.add_row("3", "开始处理")
        menu_table.add_row("4", "制种性能测试")
        menu_table.add_row("5", "设置")
        menu_table.add_row("6", "快速配置向导")
        menu_table.add_row("0", "退出")
        
        self.console.print(menu_table)
        
        choice = Prompt.ask("请选择", choices=["0", "1", "2", "3", "4", "5", "6"])
        
        if choice == "1":
            self.scan_files()
        elif choice == "2":
            self.show_queue()
        elif choice == "3":
            self.start_processing()
        elif choice == "4":
            self.performance_test()
        elif choice == "5":
            self.show_settings_menu()
        elif choice == "6":
            self.quick_setup_wizard()
        elif choice == "0":
            self.console.print("[green]感谢使用 Media Packer![/green]")
            sys.exit(0)
    
    def scan_files(self):
        """扫描媒体文件"""
        if not self.media_directories:
            self.console.print("[red]请先设置媒体目录[/red]")
            return
        
        self.console.print("\n[bold]媒体文件扫描[/bold]")
        
        # 获取用户输入的片名
        search_term = Prompt.ask(
            "请输入要搜索的片名（支持模糊匹配，留空显示所有）", 
            default=""
        ).strip()
        
        self.console.print(f"[cyan]正在扫描媒体目录... {'搜索: ' + search_term if search_term else '显示所有'}[/cyan]")
        
        # 显示要扫描的目录
        for i, directory in enumerate(self.media_directories):
            self.console.print(f"[dim]扫描目录 {i+1}: {directory}[/dim]")
        
        # 扫描并分析媒体文件夹
        media_folders = self._scan_media_folders(search_term)
        
        if media_folders:
            self._display_media_folders(media_folders, search_term)
            self._handle_folder_selection(media_folders)
        else:
            if search_term:
                self.console.print(f"[yellow]未找到包含 '{search_term}' 的媒体文件夹[/yellow]")
            else:
                self.console.print("[yellow]未找到任何媒体文件夹[/yellow]")
        
        input("按回车键继续...")
    
    def performance_test(self):
        """制种性能测试"""
        self.console.print("\n[bold]制种性能测试[/bold]")
        
        # 检查基本配置
        if not self.trackers:
            self.console.print("[red]请先设置 Tracker[/red]")
            return
        
        test_panel = Panel(
            "[yellow]性能测试功能[/yellow]\n\n"
            "此功能将：\n"
            "• 分析系统配置（CPU、内存）\n"
            "• 创建测试文件进行制种性能测试\n"
            "• 测试不同参数的制种速度\n"
            "• 给出针对您系统的优化建议\n\n"
            "[red]注意：测试将创建临时文件进行测试[/red]",
            title="制种性能测试",
            border_style="yellow"
        )
        self.console.print(test_panel)
        
        if not Confirm.ask("是否开始性能测试？"):
            return
        
        # 系统信息检测
        self._show_system_info()
        
        # 创建测试配置
        test_config = Config(
            trackers=self.trackers,
            output_dir=Path("./performance_test"),
            auto_optimize=True
        )
        
        # 创建测试文件
        test_files = self._create_test_files()
        
        if not test_files:
            self.console.print("[red]创建测试文件失败[/red]")
            return
        
        # 运行性能测试
        self._run_performance_tests(test_config, test_files)
        
        # 清理测试文件
        if Confirm.ask("是否删除测试文件？", default=True):
            self._cleanup_test_files(test_files)
        
        input("按回车键继续...")
    
    def _show_system_info(self):
        """显示系统信息"""
        import multiprocessing
        
        self.console.print("\n[bold]系统信息检测[/bold]")
        
        cpu_count = multiprocessing.cpu_count()
        self.console.print(f"CPU 核心数: {cpu_count}")
        
        try:
            # 尝试获取内存信息
            import psutil
            memory = psutil.virtual_memory()
            self.console.print(f"内存大小: {memory.total / (1024**3):.1f} GB")
            self.console.print(f"可用内存: {memory.available / (1024**3):.1f} GB")
        except ImportError:
            self.console.print("内存信息: 无法获取（需要 psutil 包）")
        except Exception:
            self.console.print("内存信息: 无法获取")
        
        # VPS检测
        try:
            # 简单的VPS检测方法
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = f.read()
                if 'hypervisor' in cpu_info or 'Xeon' in cpu_info:
                    self.console.print("[yellow]检测到可能是VPS环境（至强处理器）[/yellow]")
        except:
            pass
    
    def _create_test_files(self) -> List[Path]:
        """创建性能测试文件"""
        test_dir = Path("./performance_test")
        test_dir.mkdir(exist_ok=True)
        
        test_files = []
        test_sizes = [
            (50, "50MB"),
            (200, "200MB"),
            (1000, "1GB")
        ]
        
        self.console.print("\n[cyan]创建测试文件...[/cyan]")
        
        for size_mb, name in test_sizes:
            file_path = test_dir / f"test_{name.lower()}.dat"
            
            if file_path.exists() and file_path.stat().st_size == size_mb * 1024 * 1024:
                self.console.print(f"[green]✓ 使用现有测试文件: {name}[/green]")
                test_files.append(file_path)
                continue
            
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
                ) as progress:
                    task = progress.add_task(f"创建 {name} 测试文件", total=None)
                    
                    with open(file_path, 'wb') as f:
                        data = b'0' * (1024 * 1024)  # 1MB chunk
                        for _ in range(size_mb):
                            f.write(data)
                    
                    progress.remove_task(task)
                
                self.console.print(f"[green]✓ 创建完成: {name}[/green]")
                test_files.append(file_path)
                
            except Exception as e:
                self.console.print(f"[red]✗ 创建失败 {name}: {e}[/red]")
        
        return test_files
    
    def _run_performance_tests(self, config: Config, test_files: List[Path]):
        """运行性能测试"""
        self.console.print("\n[bold]开始性能测试[/bold]")
        
        packer = MediaPacker(config)
        results = []
        
        for test_file in test_files:
            file_size_mb = test_file.stat().st_size / (1024 * 1024)
            
            self.console.print(f"\n[cyan]测试文件: {test_file.name} ({file_size_mb:.0f} MB)[/cyan]")
            
            try:
                import time
                start_time = time.time()
                
                # 创建测试种子
                torrent_path = config.output_dir / f"{test_file.stem}.torrent"
                packer.torrent_creator.create_torrent(test_file, torrent_path)
                
                end_time = time.time()
                duration = end_time - start_time
                throughput = file_size_mb / duration if duration > 0 else 0
                
                result = {
                    'file_size_mb': file_size_mb,
                    'duration': duration,
                    'throughput': throughput,
                    'success': True
                }
                
                self.console.print(f"[green]✓ 完成 - 用时: {duration:.1f}s, 速度: {throughput:.1f} MB/s[/green]")
                
            except Exception as e:
                result = {
                    'file_size_mb': file_size_mb,
                    'duration': 0,
                    'throughput': 0,
                    'success': False,
                    'error': str(e)
                }
                self.console.print(f"[red]✗ 失败: {e}[/red]")
            
            results.append(result)
        
        # 显示测试结果
        self._show_performance_results(results)
    
    def _show_performance_results(self, results: List[Dict]):
        """显示性能测试结果"""
        self.console.print("\n[bold]性能测试结果[/bold]")
        
        table = Table(title="制种性能测试")
        table.add_column("文件大小", style="cyan")
        table.add_column("用时 (s)", style="yellow")
        table.add_column("速度 (MB/s)", style="green")
        table.add_column("状态", style="blue")
        
        successful_results = [r for r in results if r['success']]
        
        for result in results:
            status = "成功" if result['success'] else f"失败: {result.get('error', '未知错误')}"
            status_color = "green" if result['success'] else "red"
            
            table.add_row(
                f"{result['file_size_mb']:.0f} MB",
                f"{result['duration']:.1f}" if result['success'] else "-",
                f"{result['throughput']:.1f}" if result['success'] else "-",
                f"[{status_color}]{status}[/{status_color}]"
            )
        
        self.console.print(table)
        
        # 性能分析和建议
        if successful_results:
            avg_throughput = sum(r['throughput'] for r in successful_results) / len(successful_results)
            max_throughput = max(r['throughput'] for r in successful_results)
            
            # 生成建议
            suggestions = []
            
            if avg_throughput < 100:
                suggestions.append("• 性能较低，建议检查磁盘I/O性能")
                suggestions.append("• 考虑使用SSD存储")
                suggestions.append("• 检查CPU使用率是否过高")
            elif avg_throughput < 500:
                suggestions.append("• 性能中等，可考虑优化系统配置")
                suggestions.append("• VPS环境建议检查磁盘I/O限制")
            else:
                suggestions.append("• 性能良好！")
            
            # VPS特殊建议
            import multiprocessing
            cpu_count = multiprocessing.cpu_count()
            if cpu_count >= 16:  # 多核VPS
                suggestions.append("• 检测到多核CPU，已自动优化线程配置")
                suggestions.append("• 对于大文件（>10GB），建议使用4MB Piece Size")
                suggestions.append("• VPS环境建议监控CPU和内存使用率")
                suggestions.append("• 至强5115适合高性能制种，应该有良好表现")
            
            analysis_text = (
                f"[bold]性能分析[/bold]\n"
                f"平均速度: {avg_throughput:.1f} MB/s\n"
                f"最高速度: {max_throughput:.1f} MB/s\n\n"
                f"[bold]优化建议:[/bold]\n" + "\n".join(suggestions)
            )
            
            analysis_panel = Panel(
                analysis_text,
                title="性能分析与建议",
                border_style="green" if avg_throughput >= 100 else "yellow"
            )
            self.console.print(analysis_panel)
            
            # 针对36GB文件的预估
            if avg_throughput > 0:
                estimated_time = (36 * 1024) / avg_throughput
                hours = int(estimated_time // 3600)
                minutes = int((estimated_time % 3600) // 60)
                
                estimate_text = f"[bold cyan]36GB文件制种预估时间: "
                if hours > 0:
                    estimate_text += f"{hours}小时{minutes}分钟"
                else:
                    estimate_text += f"{minutes}分钟"
                estimate_text += "[/bold cyan]"
                
                self.console.print(estimate_text)
        else:
            self.console.print("[red]所有测试均失败，请检查配置[/red]")
    
    def _cleanup_test_files(self, test_files: List[Path]):
        """清理测试文件"""
        import shutil
        
        for test_file in test_files:
            try:
                if test_file.exists():
                    test_file.unlink()
            except Exception as e:
                self.console.print(f"[yellow]删除测试文件失败 {test_file.name}: {e}[/yellow]")
        
        # 删除测试目录
        try:
            test_dir = Path("./performance_test")
            if test_dir.exists():
                shutil.rmtree(test_dir)
            self.console.print("[green]✓ 测试文件已清理[/green]")
        except Exception as e:
            self.console.print(f"[yellow]清理测试目录失败: {e}[/yellow]")
    
    def _scan_media_folders(self, search_term: str = "") -> List[Dict]:
        """扫描媒体文件夹并分析内容"""
        import re
        from collections import defaultdict
        
        media_folders = []
        processed_folders = set()  # 避免重复处理
        
        for directory in self.media_directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue
                
            # 遍历子目录寻找媒体文件夹
            for item in dir_path.iterdir():
                if not item.is_dir() or item in processed_folders:
                    continue
                
                processed_folders.add(item)
                
                # 统计文件夹内的视频文件
                video_files = []
                total_size = 0
                
                try:
                    for file_path in item.rglob("*"):
                        if file_path.is_file() and MediaProcessor.is_video_file(file_path):
                            video_files.append(file_path)
                            total_size += file_path.stat().st_size
                except (PermissionError, OSError):
                    continue
                
                # 如果文件夹包含视频文件
                if video_files:
                    folder_name = item.name
                    
                    # 如果有搜索条件，进行模糊匹配
                    if search_term:
                        # 支持多种匹配方式
                        search_lower = search_term.lower()
                        folder_lower = folder_name.lower()
                        
                        # 直接包含匹配
                        direct_match = search_lower in folder_lower
                        
                        # 分词匹配（支持中文和英文）
                        search_words = re.findall(r'[\w\u4e00-\u9fff]+', search_lower)
                        word_match = False
                        if search_words:
                            # 至少有一个词匹配就算匹配成功
                            word_match = any(word in folder_lower for word in search_words)
                        
                        # 如果不匹配，跳过此文件夹
                        if not (direct_match or word_match):
                            continue
                    
                    # 分析剧集信息
                    episode_info = self._analyze_episodes(video_files)
                    
                    folder_info = {
                        'name': folder_name,
                        'path': str(item),
                        'video_files': video_files,
                        'episode_count': len(video_files),
                        'total_size': total_size,
                        'episode_info': episode_info,
                        'folder_path': item
                    }
                    
                    media_folders.append(folder_info)
        
        # 按文件夹名称排序
        media_folders.sort(key=lambda x: x['name'].lower())
        return media_folders
    
    def _analyze_episodes(self, video_files: List[Path]) -> Dict:
        """分析剧集信息"""
        import re
        
        episodes = []
        seasons = set()
        
        for file_path in video_files:
            filename = file_path.stem.lower()
            
            # 尝试提取剧集编号（支持多种格式）
            episode_patterns = [
                r'e(\d+)',           # E01, e01
                r'ep(\d+)',          # EP01, ep01
                r'第(\d+)集',         # 第01集
                r'第(\d+)话',         # 第01话
                r'(\d+)\.mp4',       # 01.mp4
                r'(\d+)\.mkv',       # 01.mkv
                r'[^\d](\d{2,3})(?!\d)',  # 两到三位数字
            ]
            
            episode_num = None
            for pattern in episode_patterns:
                match = re.search(pattern, filename)
                if match:
                    episode_num = int(match.group(1))
                    break
            
            # 尝试提取季度信息
            season_patterns = [
                r's(\d+)',           # S01, s01
                r'season(\d+)',      # Season01
                r'第(\d+)季',         # 第1季
            ]
            
            season_num = 1  # 默认第一季
            for pattern in season_patterns:
                match = re.search(pattern, filename)
                if match:
                    season_num = int(match.group(1))
                    break
            
            seasons.add(season_num)
            
            episodes.append({
                'file_path': file_path,
                'episode_num': episode_num,
                'season_num': season_num,
                'filename': file_path.name
            })
        
        # 按剧集编号排序
        episodes.sort(key=lambda x: (x['season_num'], x['episode_num'] or 999))
        
        # 分析剧集范围和断集情况
        episode_ranges = self._analyze_episode_ranges(episodes)
        
        return {
            'episodes': episodes,
            'season_count': len(seasons),
            'seasons': sorted(seasons),
            'has_episode_numbers': any(ep['episode_num'] for ep in episodes),
            'episode_ranges': episode_ranges,
            'total_count': len(episodes)
        }
    
    def _analyze_episode_ranges(self, episodes: List[Dict]) -> Dict:
        """分析剧集范围和断集情况"""
        if not episodes:
            return {'ranges': [], 'missing': [], 'display': '无'}
        
        # 按季分组
        seasons = {}
        for ep in episodes:
            season = ep['season_num']
            if season not in seasons:
                seasons[season] = []
            if ep['episode_num']:
                seasons[season].append(ep['episode_num'])
        
        all_ranges = []
        all_missing = []
        
        for season in sorted(seasons.keys()):
            episode_nums = sorted(set(seasons[season]))  # 去重并排序
            if not episode_nums:
                continue
                
            # 找连续范围
            ranges = []
            missing = []
            current_start = episode_nums[0]
            current_end = episode_nums[0]
            
            for i in range(1, len(episode_nums)):
                if episode_nums[i] == current_end + 1:
                    current_end = episode_nums[i]
                else:
                    # 找到断集
                    if current_end > current_start:
                        ranges.append(f"E{current_start:02d}-E{current_end:02d}")
                    else:
                        ranges.append(f"E{current_start:02d}")
                    
                    # 记录缺失的集数
                    for missing_ep in range(current_end + 1, episode_nums[i]):
                        missing.append(f"E{missing_ep:02d}")
                    
                    current_start = episode_nums[i]
                    current_end = episode_nums[i]
            
            # 添加最后一个范围
            if current_end > current_start:
                ranges.append(f"E{current_start:02d}-E{current_end:02d}")
            else:
                ranges.append(f"E{current_start:02d}")
            
            # 如果有多季，添加季标识
            if len(seasons) > 1:
                ranges = [f"S{season} {r}" for r in ranges]
                missing = [f"S{season} {m}" for m in missing]
            
            all_ranges.extend(ranges)
            all_missing.extend(missing)
        
        # 生成显示文本
        if all_ranges:
            display = ", ".join(all_ranges)
            if all_missing:
                display += f" (缺: {', '.join(all_missing)})"
        else:
            # 没有识别到剧集编号，显示总数
            total = len(episodes)
            display = f"{total} 集"
        
        return {
            'ranges': all_ranges,
            'missing': all_missing,
            'display': display
        }
    
    def _display_media_folders(self, media_folders: List[Dict], search_term: str = ""):
        """显示媒体文件夹列表"""
        title = f"发现的媒体文件夹"
        if search_term:
            title += f" (搜索: {search_term})"
        
        table = Table(title=title)
        table.add_column("序号", style="blue", width=4)
        table.add_column("文件夹名称", style="cyan", min_width=20)
        table.add_column("剧集范围", style="green", min_width=15)
        table.add_column("季数", style="yellow", width=6)
        table.add_column("总大小", style="magenta", width=10)
        table.add_column("路径", style="dim", min_width=30)
        
        for i, folder in enumerate(media_folders, 1):
            size_gb = folder['total_size'] / (1024**3)
            episode_info = folder['episode_info']
            
            # 格式化大小显示
            if size_gb >= 1:
                size_str = f"{size_gb:.1f} GB"
            else:
                size_mb = folder['total_size'] / (1024**2)
                size_str = f"{size_mb:.0f} MB"
            
            # 季数显示
            season_str = f"{episode_info['season_count']} 季" if episode_info['season_count'] > 1 else "1 季"
            
            # 剧集范围显示
            episode_display = episode_info['episode_ranges']['display']
            
            table.add_row(
                str(i),
                folder['name'],
                episode_display,
                season_str,
                size_str,
                folder['path']
            )
        
        self.console.print(table)
        
        # 显示统计信息
        total_folders = len(media_folders)
        total_episodes = sum(folder['episode_info']['total_count'] for folder in media_folders)
        total_size_gb = sum(folder['total_size'] for folder in media_folders) / (1024**3)
        
        # 统计缺失剧集
        total_missing = sum(len(folder['episode_info']['episode_ranges']['missing']) for folder in media_folders)
        
        stats_text = (
            f"[bold]统计信息[/bold]\n"
            f"文件夹数量: {total_folders}\n"
            f"总剧集数: {total_episodes}\n"
            f"总大小: {total_size_gb:.1f} GB\n"
        )
        
        if total_missing > 0:
            stats_text += f"\n[yellow]缺失剧集: {total_missing} 集[/yellow]\n"
        
        stats_panel = Panel(
            stats_text,
            title="扫描结果",
            border_style="green" if total_missing == 0 else "yellow"
        )
        self.console.print(stats_panel)
    
    def _handle_folder_selection(self, media_folders: List[Dict]):
        """处理文件夹选择和操作"""
        if not media_folders:
            return
        
        self.console.print("\n[bold]操作选项[/bold]")
        action_table = Table(show_header=False, box=None)
        action_table.add_column("选项", style="cyan")
        action_table.add_column("说明", style="white")
        
        action_table.add_row("1", "查看指定文件夹的详细信息")
        action_table.add_row("2", "将指定文件夹添加到处理队列")
        action_table.add_row("3", "将所有文件夹添加到处理队列")
        action_table.add_row("4", "批量选择文件夹添加到队列")
        action_table.add_row("0", "返回")
        
        self.console.print(action_table)
        
        choice = Prompt.ask("请选择操作", choices=["0", "1", "2", "3", "4"])
        
        if choice == "1":
            self._show_folder_details(media_folders)
        elif choice == "2":
            self._add_single_folder_to_queue(media_folders)
        elif choice == "3":
            self._add_all_folders_to_queue(media_folders)
        elif choice == "4":
            self._batch_select_folders(media_folders)
    
    def _show_folder_details(self, media_folders: List[Dict]):
        """显示文件夹详细信息"""
        try:
            folder_num = int(Prompt.ask(f"请输入文件夹序号 (1-{len(media_folders)})")) - 1
            if 0 <= folder_num < len(media_folders):
                folder = media_folders[folder_num]
                self._display_folder_details(folder)
            else:
                self.console.print("[red]无效的序号[/red]")
        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
    
    def _display_folder_details(self, folder: Dict):
        """显示单个文件夹的详细信息"""
        episode_info = folder['episode_info']
        episode_ranges = episode_info['episode_ranges']
        
        detail_text = (
            f"[bold cyan]文件夹: {folder['name']}[/bold cyan]\n"
            f"[bold]路径:[/bold] {folder['path']}\n"
            f"[bold]剧集范围:[/bold] {episode_ranges['display']}\n"
            f"[bold]总剧集数:[/bold] {episode_info['total_count']} 集\n"
            f"[bold]季数:[/bold] {episode_info['season_count']} 季\n"
            f"[bold]总大小:[/bold] {folder['total_size'] / (1024**3):.2f} GB\n"
            f"[bold]剧集编号规范:[/bold] {'是' if episode_info['has_episode_numbers'] else '否'}"
        )
        
        # 如果有缺失剧集，特别显示
        if episode_ranges['missing']:
            detail_text += f"\n[bold red]缺失剧集:[/bold red] {', '.join(episode_ranges['missing'])}"
        
        detail_panel = Panel(
            detail_text,
            title="文件夹详情",
            border_style="cyan"
        )
        self.console.print(detail_panel)
        
        # 显示剧集列表
        if episode_info['episodes']:
            episode_table = Table(title="剧集列表")
            episode_table.add_column("集数", style="green")
            episode_table.add_column("季度", style="yellow")
            episode_table.add_column("文件名", style="cyan")
            episode_table.add_column("大小", style="magenta")
            
            for ep in episode_info['episodes'][:20]:  # 最多显示20集
                size_mb = ep['file_path'].stat().st_size / (1024**2)
                
                episode_num_str = str(ep['episode_num']) if ep['episode_num'] else "未知"
                
                episode_table.add_row(
                    episode_num_str,
                    f"S{ep['season_num']}",
                    ep['filename'],
                    f"{size_mb:.0f} MB"
                )
            
            if len(episode_info['episodes']) > 20:
                episode_table.add_row("...", "...", f"还有 {len(episode_info['episodes']) - 20} 集", "...")
            
            self.console.print(episode_table)
    
    def _add_single_folder_to_queue(self, media_folders: List[Dict]):
        """添加单个文件夹到处理队列"""
        try:
            folder_num = int(Prompt.ask(f"请输入文件夹序号 (1-{len(media_folders)})")) - 1
            if 0 <= folder_num < len(media_folders):
                folder = media_folders[folder_num]
                self._add_folder_to_queue(folder)
                self.console.print(f"[green]已添加文件夹 '{folder['name']}' 到处理队列[/green]")
            else:
                self.console.print("[red]无效的序号[/red]")
        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
    
    def _add_all_folders_to_queue(self, media_folders: List[Dict]):
        """添加所有文件夹到处理队列"""
        if Confirm.ask(f"确定要将所有 {len(media_folders)} 个文件夹添加到处理队列吗？"):
            for folder in media_folders:
                self._add_folder_to_queue(folder)
            self.console.print(f"[green]已添加 {len(media_folders)} 个文件夹到处理队列[/green]")
    
    def _batch_select_folders(self, media_folders: List[Dict]):
        """批量选择文件夹"""
        self.console.print("\n[yellow]批量选择模式[/yellow]")
        self.console.print("请输入要添加的文件夹序号，用逗号分隔（例如：1,3,5-8）")
        
        selection = Prompt.ask("文件夹序号", default="")
        if not selection.strip():
            return
        
        selected_indices = self._parse_selection(selection, len(media_folders))
        
        if selected_indices:
            selected_folders = [media_folders[i] for i in selected_indices]
            
            # 显示选择的文件夹
            self.console.print(f"\n[cyan]已选择 {len(selected_folders)} 个文件夹:[/cyan]")
            for folder in selected_folders:
                self.console.print(f"  • {folder['name']}")
            
            if Confirm.ask("确定要添加这些文件夹到处理队列吗？"):
                for folder in selected_folders:
                    self._add_folder_to_queue(folder)
                self.console.print(f"[green]已添加 {len(selected_folders)} 个文件夹到处理队列[/green]")
        else:
            self.console.print("[red]无效的选择[/red]")
    
    def _parse_selection(self, selection: str, max_count: int) -> List[int]:
        """解析用户的选择字符串"""
        indices = []
        
        try:
            parts = selection.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # 范围选择，如 "5-8"
                    start, end = map(int, part.split('-'))
                    indices.extend(range(start-1, min(end, max_count)))
                else:
                    # 单个选择
                    num = int(part)
                    if 1 <= num <= max_count:
                        indices.append(num-1)
            
            # 去重并排序
            return sorted(list(set(indices)))
            
        except ValueError:
            return []
    
    def _add_folder_to_queue(self, folder: Dict):
        """添加文件夹到处理队列"""
        # 添加整个文件夹作为一个任务
        self.task_queue.append({
            'file_path': folder['path'],
            'folder_name': folder['name'],
            'episode_count': folder['episode_count'],
            'is_folder': True,
            'status': 'pending',
            'added_at': time.time()
        })
    
    def show_queue(self):
        """显示处理队列"""
        if not self.task_queue:
            self.console.print("[yellow]队列为空[/yellow]")
            input("按回车键继续...")
            return
        
        table = Table(title="处理队列")
        table.add_column("序号", style="blue", width=4)
        table.add_column("名称", style="cyan", min_width=20)
        table.add_column("类型", style="yellow", width=8)
        table.add_column("剧集数", style="green", width=8)
        table.add_column("状态", style="yellow", width=10)
        table.add_column("添加时间", style="green", width=10)
        
        for i, task in enumerate(self.task_queue[:20], 1):  # 显示前20个
            if task.get('is_folder', False):
                # 文件夹任务
                name = task.get('folder_name', Path(task['file_path']).name)
                task_type = "文件夹"
                episode_info = f"{task.get('episode_count', 0)} 集"
            else:
                # 单文件任务
                file_path = Path(task['file_path'])
                name = file_path.name
                task_type = "文件"
                episode_info = "-"
            
            status_color = {
                'pending': 'yellow',
                'processing': 'blue',
                'completed': 'green',
                'error': 'red'
            }.get(task['status'], 'white')
            
            table.add_row(
                str(i),
                name,
                task_type,
                episode_info,
                f"[{status_color}]{task['status']}[/{status_color}]",
                time.strftime("%H:%M", time.localtime(task['added_at']))
            )
        
        if len(self.task_queue) > 20:
            table.add_row("...", f"还有 {len(self.task_queue) - 20} 个任务", "...", "...", "...", "...")
        
        self.console.print(table)
        
        # 显示队列统计
        total_folders = sum(1 for task in self.task_queue if task.get('is_folder', False))
        total_files = len(self.task_queue) - total_folders
        total_episodes = sum(task.get('episode_count', 1) for task in self.task_queue)
        
        stats_panel = Panel(
            f"[bold]队列统计[/bold]\n"
            f"文件夹: {total_folders} 个\n"
            f"单文件: {total_files} 个\n"
            f"总剧集: {total_episodes} 集",
            title="队列信息",
            border_style="cyan"
        )
        self.console.print(stats_panel)
        
        # 队列操作
        self.console.print("\n[bold]队列操作[/bold]")
        action_table = Table(show_header=False, box=None)
        action_table.add_column("选项", style="cyan")
        action_table.add_column("说明", style="white")
        
        action_table.add_row("1", "清空队列")
        action_table.add_row("2", "删除指定任务")
        action_table.add_row("3", "查看任务详情")
        action_table.add_row("0", "返回")
        
        self.console.print(action_table)
        
        choice = Prompt.ask("请选择操作", choices=["0", "1", "2", "3"], default="0")
        
        if choice == "1":
            # 清空队列
            if Confirm.ask("确定要清空队列吗？"):
                self.task_queue.clear()
                self.console.print("[green]队列已清空[/green]")
        elif choice == "2":
            # 删除指定任务
            self._remove_task_from_queue()
        elif choice == "3":
            # 查看任务详情
            self._show_task_details()
        
        if choice != "0":
            input("按回车键继续...")
    
    def _remove_task_from_queue(self):
        """从队列中删除指定任务"""
        if not self.task_queue:
            return
        
        try:
            task_num = int(Prompt.ask(f"请输入要删除的任务序号 (1-{len(self.task_queue)})")) - 1
            if 0 <= task_num < len(self.task_queue):
                removed_task = self.task_queue.pop(task_num)
                name = removed_task.get('folder_name', Path(removed_task['file_path']).name)
                self.console.print(f"[green]已删除任务: {name}[/green]")
            else:
                self.console.print("[red]无效的序号[/red]")
        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
    
    def _show_task_details(self):
        """显示任务详情"""
        if not self.task_queue:
            return
        
        try:
            task_num = int(Prompt.ask(f"请输入任务序号 (1-{len(self.task_queue)})")) - 1
            if 0 <= task_num < len(self.task_queue):
                task = self.task_queue[task_num]
                
                if task.get('is_folder', False):
                    # 文件夹任务详情
                    detail_text = (
                        f"[bold cyan]文件夹任务[/bold cyan]\n"
                        f"[bold]名称:[/bold] {task.get('folder_name', '未知')}\n"
                        f"[bold]路径:[/bold] {task['file_path']}\n"
                        f"[bold]剧集数:[/bold] {task.get('episode_count', 0)} 集\n"
                        f"[bold]状态:[/bold] {task['status']}\n"
                        f"[bold]添加时间:[/bold] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task['added_at']))}"
                    )
                else:
                    # 单文件任务详情
                    file_path = Path(task['file_path'])
                    detail_text = (
                        f"[bold cyan]文件任务[/bold cyan]\n"
                        f"[bold]文件名:[/bold] {file_path.name}\n"
                        f"[bold]路径:[/bold] {task['file_path']}\n"
                        f"[bold]状态:[/bold] {task['status']}\n"
                        f"[bold]添加时间:[/bold] {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(task['added_at']))}"
                    )
                
                # 添加错误信息（如果有）
                if task.get('error_message'):
                    detail_text += f"\n[bold red]错误信息:[/bold red] {task['error_message']}"
                
                detail_panel = Panel(
                    detail_text,
                    title="任务详情",
                    border_style="cyan"
                )
                self.console.print(detail_panel)
            else:
                self.console.print("[red]无效的序号[/red]")
        except ValueError:
            self.console.print("[red]请输入有效的数字[/red]")
    
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
        
        # 创建配置 - 默认启用性能优化
        config = Config(
            trackers=self.trackers,
            output_dir=Path(self.output_directory),
            auto_optimize=True,  # 默认启用性能优化
            max_workers=4,  # 默认4线程（根据性能测试的最佳配置）
            piece_size=None  # 让系统自动选择最优piece size
        )
        
        packer = MediaPacker(config)
        
        # 处理任务
        success_count = 0
        error_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            for task in pending_tasks:
                try:
                    task['status'] = 'processing'
                    
                    file_path = Path(task['file_path'])
                    
                    if task.get('is_folder', False):
                        # 处理文件夹任务
                        folder_name = task.get('folder_name', file_path.name)
                        
                        task_progress = progress.add_task(
                            f"[cyan]制种: {folder_name} ({task.get('episode_count', 0)} 集)[/cyan]",
                            total=None
                        )
                        
                        # 直接为文件夹创建种子（不重复打印）
                        torrent_path = packer.create_torrent_for_file(
                            file_path,
                            custom_name=folder_name,
                            organize=False  # 文件夹已经是组织好的
                        )
                        
                        progress.remove_task(task_progress)
                        
                    else:
                        # 处理单文件任务
                        file_name = file_path.name
                        
                        task_progress = progress.add_task(
                            f"[cyan]制种: {file_name}[/cyan]",
                            total=None
                        )
                        
                        # 获取文件夹名称（不重复打印）
                        if file_path.is_file():
                            folder_name = file_path.parent.name
                        else:
                            folder_name = file_path.name
                        
                        # 创建种子
                        torrent_path = packer.create_torrent_for_file(
                            file_path,
                            custom_name=folder_name,
                            organize=True
                        )
                        
                        progress.remove_task(task_progress)
                    
                    task['status'] = 'completed'
                    task['completed_at'] = time.time()
                    task['torrent_path'] = str(torrent_path)
                    success_count += 1
                    
                    self.console.print(f"[green]✓ 完成: {torrent_path.name}[/green]")
                    
                except Exception as e:
                    task['status'] = 'error'
                    task['error_message'] = str(e)
                    error_count += 1
                    self.console.print(f"[red]✗ 错误: {e}[/red]")
        
        # 显示处理结果
        result_text = (
            f"[bold green]处理完成![/bold green]\n\n"
            f"[green]成功: {success_count} 个[/green]\n"
            f"[red]失败: {error_count} 个[/red]\n"
        )
        
        if success_count > 0:
            result_text += f"\n[cyan]种子文件保存在: {self.output_directory}[/cyan]\n"
        
        result_panel = Panel(
            result_text,
            title="处理结果",
            border_style="green" if error_count == 0 else "yellow"
        )
        self.console.print(result_panel)
        
        # 询问是否查看详细结果
        if success_count > 0 and Confirm.ask("是否查看生成的种子文件列表？"):
            self._show_generated_torrents()
        
        input("按回车键继续...")
    
    def _show_generated_torrents(self):
        """显示生成的种子文件列表"""
        completed_tasks = [t for t in self.task_queue if t['status'] == 'completed']
        
        if not completed_tasks:
            self.console.print("[yellow]没有已完成的任务[/yellow]")
            return
        
        table = Table(title="生成的种子文件")
        table.add_column("种子文件", style="cyan")
        table.add_column("源文件/文件夹", style="yellow")
        table.add_column("类型", style="green")
        table.add_column("完成时间", style="magenta")
        
        for task in completed_tasks:
            torrent_name = Path(task.get('torrent_path', '')).name if task.get('torrent_path') else '未知'
            
            if task.get('is_folder', False):
                source_name = task.get('folder_name', '未知文件夹')
                task_type = f"文件夹 ({task.get('episode_count', 0)} 集)"
            else:
                source_name = Path(task['file_path']).name
                task_type = "文件"
            
            completed_time = time.strftime(
                "%m-%d %H:%M",
                time.localtime(task.get('completed_at', task['added_at']))
            )
            
            table.add_row(
                torrent_name,
                source_name,
                task_type,
                completed_time
            )
        
        self.console.print(table)
    
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
                    self.save_config()  # 自动保存配置
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
                self.save_config()  # 自动保存配置
                self.console.print(f"[green]✓ 输出目录已设置: {directory}[/green]")
        else:
            self.output_directory = directory
            self.save_config()  # 自动保存配置
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
                self.save_config()  # 自动保存配置
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
        
        # 保存所有配置
        self.save_config()
        
        self.console.print("\n[green]✓ 快速配置完成！[/green]")
        input("按回车键继续...")

# ================= 命令行接口 =================

@click.group()
@click.option('--config', '-c', type=click.Path(), help='配置文件路径')
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx, config):
    """Media Packer - 简化版种子生成工具 v{__version__}"""
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
        
        info_table.add_row("名称", torrent.name or "未知")
        info_table.add_row("大小", f"{torrent.size / (1024**3):.2f} GB" if torrent.size else "未知")
        info_table.add_row("文件数", str(len(torrent.files)) if torrent.files else "未知")
        
        # 安全地处理 trackers
        trackers_str = "无"
        if torrent.trackers:
            try:
                trackers_str = "\n".join(str(t) for t in torrent.trackers)
            except:
                trackers_str = "无法显示"
        info_table.add_row("Tracker", trackers_str)
        
        info_table.add_row("私有", "是" if torrent.private else "否")
        info_table.add_row("注释", torrent.comment or "无")
        info_table.add_row("创建者", torrent.created_by or "未知")
        info_table.add_row("创建时间", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(torrent.creation_date)) if torrent.creation_date else "未知")
        info_table.add_row("Piece大小", f"{torrent.piece_size / 1024} KB" if torrent.piece_size else "未知")
        
        console.print(info_table)
        
    except Exception as e:
        console.print(f"[red]读取种子文件失败: {e}[/red]")


@cli.command()
@click.argument('torrent_path', type=click.Path(exists=True))
@click.option('--content-path', '-c', type=click.Path(exists=True), help='原始内容路径（如果与种子中记录的不同）')
@click.option('--verbose', '-v', is_flag=True, help='显示详细验证信息')
def verify(torrent_path, content_path, verbose):
    """验证种子文件"""
    try:
        torrent = torf.Torrent.read(torrent_path)
        
        console.print(f"[cyan]正在验证种子文件: {Path(torrent_path).name}[/cyan]")
        
        # 显示基本信息
        if verbose:
            console.print(f"[green]种子名称:[/green] {torrent.name}")
            console.print(f"[green]文件总数:[/green] {len(torrent.files)}")
            console.print(f"[green]总大小:[/green] {torrent.size / (1024**3):.2f} GB")
        
        # 确定要验证的内容路径
        if content_path:
            verify_path = Path(content_path)
        elif torrent.path:
            verify_path = Path(torrent.path)
        else:
            console.print("[red]错误: 无法确定要验证的内容路径[/red]")
            console.print("[yellow]提示: 请使用 --content-path 参数指定原始内容路径[/yellow]")
            return
        
        if not verify_path.exists():
            console.print(f"[red]错误: 内容路径不存在: {verify_path}[/red]")
            return
        
        # 验证文件
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("验证文件...", total=None)
            
            try:
                # 验证种子文件
                is_valid = torrent.verify(verify_path)
                progress.remove_task(task)
                
                if is_valid:
                    console.print("[bold green]✓ 种子文件验证通过[/bold green]")
                else:
                    console.print("[bold red]✗ 种子文件验证失败[/bold red]")
                    
            except Exception as e:
                progress.remove_task(task)
                console.print(f"[bold red]✗ 验证过程中出错: {e}[/bold red]")
                
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


@cli.command()
def system_info():
    """显示系统信息和推荐配置"""
    try:
        import multiprocessing
        import psutil
        
        console.print("[bold cyan]系统信息[/bold cyan]")
        
        # CPU信息
        cpu_count_logical = multiprocessing.cpu_count()
        try:
            cpu_count_physical = psutil.cpu_count(logical=False)
        except:
            cpu_count_physical = cpu_count_logical
            
        console.print(f"[green]CPU核心数:[/green] {cpu_count_physical} 物理核心, {cpu_count_logical} 逻辑核心")
        
        # 内存信息
        memory = psutil.virtual_memory()
        console.print(f"[green]总内存:[/green] {memory.total / (1024**3):.1f} GB")
        console.print(f"[green]可用内存:[/green] {memory.available / (1024**3):.1f} GB")
        
        # 推荐配置
        console.print("\n[bold cyan]推荐配置[/bold cyan]")
        
        # 推荐线程数（使用与实际制种相同的算法）
        if cpu_count_physical >= 32:  # 超高性能CPU（如双路服务器）
            recommended_workers = min(16, cpu_count_physical // 3)
        elif cpu_count_physical >= 16:  # 高性能CPU（如至强E5、AMD EPYC）
            recommended_workers = min(12, cpu_count_physical // 2)
        elif cpu_count_physical >= 8:  # 中高端CPU
            recommended_workers = min(6, cpu_count_physical // 2 + 1)
        elif cpu_count_physical >= 4:  # 主流CPU
            recommended_workers = cpu_count_physical // 2 + 1
        else:  # 低端CPU
            recommended_workers = max(2, cpu_count_physical)
        
        # 内存优化调整
        if memory.total >= 32 * 1024 * 1024 * 1024:  # 32GB+内存
            recommended_workers = min(recommended_workers + 4, 20)
        
        console.print(f"[green]推荐线程数:[/green] {recommended_workers} (针对{cpu_count_physical}核心CPU优化)")
        
        # 显示CPU类型判断
        if cpu_count_physical >= 16:
            console.print("[green]CPU类型:[/green] 高性能服务器CPU (如至强E5/EPYC)")
        elif cpu_count_physical >= 8:
            console.print("[green]CPU类型:[/green] 中高端CPU")
        else:
            console.print("[green]CPU类型:[/green] 主流/入门级CPU")
        
        # 推荐Piece Size
        if memory.total >= 16 * 1024 * 1024 * 1024:  # 16GB以上内存
            console.print("[green]推荐Piece Size:[/green] 4MB (适用于大文件)")
        elif memory.total >= 8 * 1024 * 1024 * 1024:  # 8GB以上内存
            console.print("[green]推荐Piece Size:[/green] 2MB (适用于中等文件)")
        else:
            console.print("[green]推荐Piece Size:[/green] 1MB (适用于小文件)")
            
        # 系统负载
        try:
            load_avg = psutil.getloadavg()
            console.print(f"[green]系统负载:[/green] {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}")
        except:
            console.print("[green]系统负载:[/green] 无法获取")
            
    except ImportError:
        console.print("[red]需要安装 psutil: pip install psutil[/red]")
    except Exception as e:
        console.print(f"[red]获取系统信息失败: {e}[/red]")

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