#!/usr/bin/env python3
"""
Torf 制种性能分析工具
分析不同参数设置对torf制种性能的影响
"""

import os
import sys
import time
import threading
import multiprocessing
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
import hashlib

# 检查并导入依赖
try:
    import torf
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.prompt import Prompt, Confirm
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请运行: pip install torf rich")
    sys.exit(1)

console = Console()

@dataclass
class PerformanceTest:
    """性能测试结果"""
    test_name: str
    file_path: str
    file_size: int
    piece_size: int
    thread_count: Optional[int]
    creation_time: float
    hash_time: float
    total_time: float
    throughput_mbps: float
    piece_count: int
    memory_usage: float
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None

class TorfPerformanceAnalyzer:
    """Torf性能分析器"""
    
    def __init__(self):
        self.console = Console()
        self.test_results: List[PerformanceTest] = []
        self.test_files: List[Path] = []
        
    def run_analysis(self):
        """运行性能分析"""
        self.show_welcome()
        
        while True:
            choice = self.show_main_menu()
            
            if choice == "1":
                self.prepare_test_files()
            elif choice == "2":
                self.run_piece_size_analysis()
            elif choice == "3":
                self.run_thread_count_analysis()
            elif choice == "4":
                self.run_comprehensive_analysis()
            elif choice == "5":
                self.show_results()
            elif choice == "6":
                self.export_results()
            elif choice == "7":
                self.show_torf_info()
            elif choice == "0":
                break
    
    def show_welcome(self):
        """显示欢迎界面"""
        welcome_panel = Panel(
            "[bold blue]Torf 制种性能分析工具[/bold blue]\n\n"
            "[green]功能特性:[/green]\n"
            "• Piece Size 对性能的影响分析\n"
            "• 多线程性能测试\n"
            "• 内存和CPU使用率监控\n"
            "• 吞吐量和效率分析\n"
            "• 不同文件大小的性能对比\n\n"
            "[yellow]注意: 性能测试可能需要较长时间[/yellow]",
            title="Torf 性能分析",
            border_style="blue"
        )
        self.console.print(welcome_panel)
    
    def show_main_menu(self) -> str:
        """显示主菜单"""
        self.console.print("\n[bold]主菜单[/bold]")
        
        menu_table = Table(show_header=False, box=None)
        menu_table.add_column("选项", style="cyan")
        menu_table.add_column("说明", style="white")
        
        menu_table.add_row("1", "准备测试文件")
        menu_table.add_row("2", "Piece Size 性能分析")
        menu_table.add_row("3", "多线程性能分析")
        menu_table.add_row("4", "综合性能分析")
        menu_table.add_row("5", "查看测试结果")
        menu_table.add_row("6", "导出结果报告")
        menu_table.add_row("7", "Torf 版本信息")
        menu_table.add_row("0", "退出")
        
        self.console.print(menu_table)
        
        return Prompt.ask("请选择", choices=["0", "1", "2", "3", "4", "5", "6", "7"])
    
    def prepare_test_files(self):
        """准备测试文件"""
        self.console.print("\n[bold]准备测试文件[/bold]")
        
        # 检查现有测试文件
        test_dir = Path("./test_files")
        if test_dir.exists():
            existing_files = list(test_dir.glob("*.dat"))
            if existing_files:
                self.console.print(f"[green]发现 {len(existing_files)} 个现有测试文件[/green]")
                for file in existing_files:
                    size_mb = file.stat().st_size / (1024**2)
                    self.console.print(f"  • {file.name}: {size_mb:.1f} MB")
                
                if Confirm.ask("是否使用现有文件？"):
                    self.test_files = existing_files
                    return
        
        # 创建新的测试文件
        if Confirm.ask("是否创建新的测试文件？"):
            self.create_test_files()
    
    def create_test_files(self):
        """创建测试文件"""
        test_dir = Path("./test_files")
        test_dir.mkdir(exist_ok=True)
        
        # 定义不同大小的测试文件
        file_sizes = [
            (10, "10MB"),
            (50, "50MB"),
            (100, "100MB"),
            (500, "500MB"),
            (1024, "1GB")
        ]
        
        self.console.print("\n[cyan]创建测试文件...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=self.console
        ) as progress:
            
            for size_mb, name in file_sizes:
                file_path = test_dir / f"test_{name.lower()}.dat"
                
                if file_path.exists():
                    self.console.print(f"[yellow]跳过已存在的文件: {file_path.name}[/yellow]")
                    self.test_files.append(file_path)
                    continue
                
                task = progress.add_task(f"创建 {name} 文件", total=size_mb)
                
                try:
                    with open(file_path, 'wb') as f:
                        chunk_size = 1024 * 1024  # 1MB chunks
                        data = os.urandom(chunk_size)
                        
                        for i in range(size_mb):
                            f.write(data)
                            progress.update(task, advance=1)
                    
                    self.test_files.append(file_path)
                    self.console.print(f"[green]✓ 创建完成: {file_path.name}[/green]")
                    
                except Exception as e:
                    self.console.print(f"[red]✗ 创建失败 {file_path.name}: {e}[/red]")
        
        self.console.print(f"\n[green]测试文件准备完成，共 {len(self.test_files)} 个文件[/green]")
    
    def run_piece_size_analysis(self):
        """运行Piece Size性能分析"""
        if not self.test_files:
            self.console.print("[red]请先准备测试文件[/red]")
            return
        
        self.console.print("\n[bold]Piece Size 性能分析[/bold]")
        
        # 不同的piece size设置
        piece_sizes = [
            16 * 1024,      # 16 KB
            32 * 1024,      # 32 KB
            64 * 1024,      # 64 KB
            128 * 1024,     # 128 KB
            256 * 1024,     # 256 KB
            512 * 1024,     # 512 KB
            1024 * 1024,    # 1 MB
            2048 * 1024,    # 2 MB
            4096 * 1024,    # 4 MB
        ]
        
        # 选择测试文件
        selected_file = self.select_test_file()
        if not selected_file:
            return
        
        self.console.print(f"\n[cyan]使用文件: {selected_file.name} ({selected_file.stat().st_size / (1024**2):.1f} MB)[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Piece Size 分析", total=len(piece_sizes))
            
            for piece_size in piece_sizes:
                piece_size_str = self.format_size(piece_size)
                progress.update(task, description=f"测试 Piece Size: {piece_size_str}")
                
                test_result = self.run_single_test(
                    f"piece_size_{piece_size_str}",
                    selected_file,
                    piece_size=piece_size
                )
                
                if test_result:
                    self.test_results.append(test_result)
                
                progress.update(task, advance=1)
        
        # 显示结果
        self.show_piece_size_results()
    
    def run_thread_count_analysis(self):
        """运行多线程性能分析"""
        if not self.test_files:
            self.console.print("[red]请先准备测试文件[/red]")
            return
        
        self.console.print("\n[bold]多线程性能分析[/bold]")
        
        # 不同的线程数设置
        max_threads = multiprocessing.cpu_count()
        thread_counts = [1, 2, 4, max_threads // 2, max_threads, max_threads * 2]
        thread_counts = sorted(list(set(thread_counts)))  # 去重并排序
        
        # 选择测试文件
        selected_file = self.select_test_file()
        if not selected_file:
            return
        
        self.console.print(f"\n[cyan]使用文件: {selected_file.name} ({selected_file.stat().st_size / (1024**2):.1f} MB)[/cyan]")
        self.console.print(f"[dim]CPU核心数: {max_threads}[/dim]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("多线程分析", total=len(thread_counts))
            
            for thread_count in thread_counts:
                progress.update(task, description=f"测试线程数: {thread_count}")
                
                test_result = self.run_single_test(
                    f"threads_{thread_count}",
                    selected_file,
                    thread_count=thread_count
                )
                
                if test_result:
                    self.test_results.append(test_result)
                
                progress.update(task, advance=1)
        
        # 显示结果
        self.show_thread_count_results()
    
    def run_comprehensive_analysis(self):
        """运行综合性能分析"""
        if not self.test_files:
            self.console.print("[red]请先准备测试文件[/red]")
            return
        
        self.console.print("\n[bold]综合性能分析[/bold]")
        self.console.print("[dim]这将测试所有文件的默认参数性能...[/dim]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("综合分析", total=len(self.test_files))
            
            for test_file in self.test_files:
                file_size_str = self.format_size(test_file.stat().st_size)
                progress.update(task, description=f"测试文件: {test_file.name}")
                
                test_result = self.run_single_test(
                    f"comprehensive_{file_size_str}",
                    test_file
                )
                
                if test_result:
                    self.test_results.append(test_result)
                
                progress.update(task, advance=1)
        
        # 显示结果
        self.show_comprehensive_results()
    
    def run_single_test(self, test_name: str, file_path: Path, 
                       piece_size: Optional[int] = None, 
                       thread_count: Optional[int] = None) -> Optional[PerformanceTest]:
        """运行单个性能测试"""
        try:
            # 准备输出文件
            output_dir = Path("./performance_test_output")
            output_dir.mkdir(exist_ok=True)
            torrent_path = output_dir / f"{test_name}_{file_path.stem}.torrent"
            
            # 删除已存在的torrent文件
            if torrent_path.exists():
                torrent_path.unlink()
            
            # 获取文件信息
            file_size = file_path.stat().st_size
            
            # 创建torrent对象
            torrent = torf.Torrent(
                path=str(file_path),
                trackers=["http://tracker.example.com:8080/announce"],
                private=True,
                comment=f"Performance test: {test_name}",
                created_by="Torf Performance Analyzer"
            )
            
            # 设置piece size
            if piece_size:
                torrent.piece_size = piece_size
            
            # 记录开始时间和资源使用
            start_time = time.time()
            start_memory = self.get_memory_usage()
            start_cpu = self.get_cpu_usage()
            
            # 生成torrent（这里包含了哈希计算）
            hash_start = time.time()
            
            # 如果支持多线程，设置线程数
            if thread_count and hasattr(torf, 'set_max_workers'):
                torf.set_max_workers(thread_count)
            
            torrent.generate()
            
            hash_end = time.time()
            
            # 写入文件
            torrent.write(str(torrent_path))
            
            end_time = time.time()
            end_memory = self.get_memory_usage()
            end_cpu = self.get_cpu_usage()
            
            # 计算性能指标
            total_time = end_time - start_time
            hash_time = hash_end - hash_start
            creation_time = total_time - hash_time
            throughput_mbps = (file_size / (1024**2)) / total_time if total_time > 0 else 0
            
            # 计算piece数量 - 使用更安全的方法
            try:
                if hasattr(torrent, 'pieces') and torrent.pieces:
                    piece_count = len(torrent.pieces)
                else:
                    # 计算理论piece数量
                    piece_count = (file_size + torrent.piece_size - 1) // torrent.piece_size
            except (TypeError, AttributeError):
                piece_count = (file_size + torrent.piece_size - 1) // torrent.piece_size
            
            memory_usage = max(end_memory - start_memory, 0)
            cpu_usage = (end_cpu - start_cpu) / total_time if total_time > 0 else 0
            
            return PerformanceTest(
                test_name=test_name,
                file_path=str(file_path),
                file_size=file_size,
                piece_size=torrent.piece_size,
                thread_count=thread_count,
                creation_time=creation_time,
                hash_time=hash_time,
                total_time=total_time,
                throughput_mbps=throughput_mbps,
                piece_count=piece_count,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                success=True
            )
            
        except Exception as e:
            self.console.print(f"[red]测试失败 {test_name}: {e}[/red]")
            return PerformanceTest(
                test_name=test_name,
                file_path=str(file_path),
                file_size=file_size,
                piece_size=piece_size or 0,
                thread_count=thread_count,
                creation_time=0,
                hash_time=0,
                total_time=0,
                throughput_mbps=0,
                piece_count=0,
                memory_usage=0,
                cpu_usage=0,
                success=False,
                error_message=str(e)
            )
    
    def select_test_file(self) -> Optional[Path]:
        """选择测试文件"""
        if len(self.test_files) == 1:
            return self.test_files[0]
        
        self.console.print("\n[bold]选择测试文件:[/bold]")
        for i, file in enumerate(self.test_files, 1):
            size_mb = file.stat().st_size / (1024**2)
            self.console.print(f"  {i}. {file.name} ({size_mb:.1f} MB)")
        
        try:
            choice = int(Prompt.ask("请选择文件", default="1")) - 1
            if 0 <= choice < len(self.test_files):
                return self.test_files[choice]
        except ValueError:
            pass
        
        self.console.print("[red]无效选择[/red]")
        return None
    
    def show_piece_size_results(self):
        """显示Piece Size分析结果"""
        piece_size_results = [r for r in self.test_results if r.test_name.startswith("piece_size_")]
        if not piece_size_results:
            return
        
        self.console.print("\n[bold]Piece Size 性能分析结果[/bold]")
        
        table = Table(title="Piece Size vs Performance")
        table.add_column("Piece Size", style="cyan")
        table.add_column("总时间 (s)", style="yellow")
        table.add_column("哈希时间 (s)", style="green")
        table.add_column("吞吐量 (MB/s)", style="magenta")
        table.add_column("Piece数量", style="blue")
        table.add_column("内存使用 (MB)", style="red")
        
        # 按piece size排序
        piece_size_results.sort(key=lambda x: x.piece_size)
        
        # 获取成功测试的最佳吞吐量
        successful_results = [r for r in piece_size_results if r.success]
        if not successful_results:
            self.console.print("[red]没有成功的测试结果[/red]")
            return
        
        best_throughput = max(r.throughput_mbps for r in successful_results)
        
        for result in piece_size_results:
            if not result.success:
                continue
                
            piece_size_str = self.format_size(result.piece_size)
            throughput_color = "bold green" if result.throughput_mbps == best_throughput else "white"
            
            table.add_row(
                piece_size_str,
                f"{result.total_time:.2f}",
                f"{result.hash_time:.2f}",
                f"[{throughput_color}]{result.throughput_mbps:.2f}[/{throughput_color}]",
                str(result.piece_count),
                f"{result.memory_usage:.1f}"
            )
        
        self.console.print(table)
        
        # 显示最佳配置建议
        successful_results = [r for r in piece_size_results if r.success]
        if successful_results:
            best_result = max(successful_results, key=lambda x: x.throughput_mbps)
            self.console.print(f"\n[bold green]最佳 Piece Size: {self.format_size(best_result.piece_size)}[/bold green]")
            self.console.print(f"[green]最高吞吐量: {best_result.throughput_mbps:.2f} MB/s[/green]")
        else:
            self.console.print(f"\n[red]所有测试均失败，无法给出建议[/red]")
    
    def show_thread_count_results(self):
        """显示多线程分析结果"""
        thread_results = [r for r in self.test_results if r.test_name.startswith("threads_")]
        if not thread_results:
            return
        
        self.console.print("\n[bold]多线程性能分析结果[/bold]")
        
        table = Table(title="Thread Count vs Performance")
        table.add_column("线程数", style="cyan")
        table.add_column("总时间 (s)", style="yellow")
        table.add_column("哈希时间 (s)", style="green")
        table.add_column("吞吐量 (MB/s)", style="magenta")
        table.add_column("CPU使用率 (%)", style="blue")
        table.add_column("效率", style="red")
        
        # 按线程数排序
        thread_results.sort(key=lambda x: x.thread_count or 1)
        
        # 获取成功测试的结果
        successful_results = [r for r in thread_results if r.success]
        if not successful_results:
            self.console.print("[red]没有成功的测试结果[/red]")
            return
        
        single_thread_time = next((r.total_time for r in successful_results if (r.thread_count or 1) == 1), 0)
        best_throughput = max(r.throughput_mbps for r in successful_results)
        
        for result in thread_results:
            if not result.success:
                continue
            
            thread_count = result.thread_count or 1
            efficiency = (single_thread_time / result.total_time) / thread_count if single_thread_time > 0 else 0
            throughput_color = "bold green" if result.throughput_mbps == best_throughput else "white"
            
            table.add_row(
                str(thread_count),
                f"{result.total_time:.2f}",
                f"{result.hash_time:.2f}",
                f"[{throughput_color}]{result.throughput_mbps:.2f}[/{throughput_color}]",
                f"{result.cpu_usage:.1f}",
                f"{efficiency:.2f}"
            )
        
        self.console.print(table)
        
        # 显示最佳配置建议
        best_result = max(thread_results, key=lambda x: x.throughput_mbps if x.success else 0)
        if best_result.success:
            self.console.print(f"\n[bold green]最佳线程数: {best_result.thread_count or 1}[/bold green]")
            self.console.print(f"[green]最高吞吐量: {best_result.throughput_mbps:.2f} MB/s[/green]")
    
    def show_comprehensive_results(self):
        """显示综合分析结果"""
        comp_results = [r for r in self.test_results if r.test_name.startswith("comprehensive_")]
        if not comp_results:
            return
        
        self.console.print("\n[bold]综合性能分析结果[/bold]")
        
        table = Table(title="File Size vs Performance")
        table.add_column("文件大小", style="cyan")
        table.add_column("总时间 (s)", style="yellow")
        table.add_column("哈希时间 (s)", style="green")
        table.add_column("吞吐量 (MB/s)", style="magenta")
        table.add_column("Piece Size", style="blue")
        table.add_column("Piece数量", style="red")
        
        # 按文件大小排序
        comp_results.sort(key=lambda x: x.file_size)
        
        for result in comp_results:
            if not result.success:
                continue
            
            file_size_str = self.format_size(result.file_size)
            piece_size_str = self.format_size(result.piece_size)
            
            table.add_row(
                file_size_str,
                f"{result.total_time:.2f}",
                f"{result.hash_time:.2f}",
                f"{result.throughput_mbps:.2f}",
                piece_size_str,
                str(result.piece_count)
            )
        
        self.console.print(table)
    
    def show_results(self):
        """显示所有测试结果"""
        if not self.test_results:
            self.console.print("[yellow]暂无测试结果[/yellow]")
            return
        
        self.console.print("\n[bold]所有测试结果[/bold]")
        
        table = Table(title="Performance Test Results")
        table.add_column("测试名称", style="cyan")
        table.add_column("文件大小", style="yellow")
        table.add_column("Piece Size", style="green")
        table.add_column("总时间 (s)", style="magenta")
        table.add_column("吞吐量 (MB/s)", style="blue")
        table.add_column("状态", style="red")
        
        for result in self.test_results:
            file_size_str = self.format_size(result.file_size)
            piece_size_str = self.format_size(result.piece_size)
            status = "✓ 成功" if result.success else "✗ 失败"
            status_color = "green" if result.success else "red"
            
            table.add_row(
                result.test_name,
                file_size_str,
                piece_size_str,
                f"{result.total_time:.2f}",
                f"{result.throughput_mbps:.2f}",
                f"[{status_color}]{status}[/{status_color}]"
            )
        
        self.console.print(table)
        
        # 显示统计信息
        successful_tests = [r for r in self.test_results if r.success]
        if successful_tests:
            avg_throughput = sum(r.throughput_mbps for r in successful_tests) / len(successful_tests)
            max_throughput = max(r.throughput_mbps for r in successful_tests)
            min_throughput = min(r.throughput_mbps for r in successful_tests)
            
            stats_panel = Panel(
                f"[bold]统计信息[/bold]\n"
                f"总测试数: {len(self.test_results)}\n"
                f"成功测试: {len(successful_tests)}\n"
                f"平均吞吐量: {avg_throughput:.2f} MB/s\n"
                f"最高吞吐量: {max_throughput:.2f} MB/s\n"
                f"最低吞吐量: {min_throughput:.2f} MB/s",
                title="测试统计",
                border_style="green"
            )
            self.console.print(stats_panel)
    
    def export_results(self):
        """导出结果报告"""
        if not self.test_results:
            self.console.print("[yellow]暂无测试结果可导出[/yellow]")
            return
        
        timestamp = int(time.time())
        report_file = Path(f"torf_performance_report_{timestamp}.json")
        
        # 准备导出数据
        export_data = {
            "timestamp": timestamp,
            "torf_version": getattr(torf, '__version__', 'unknown'),
            "cpu_count": multiprocessing.cpu_count(),
            "test_results": []
        }
        
        for result in self.test_results:
            export_data["test_results"].append({
                "test_name": result.test_name,
                "file_path": result.file_path,
                "file_size": result.file_size,
                "piece_size": result.piece_size,
                "thread_count": result.thread_count,
                "creation_time": result.creation_time,
                "hash_time": result.hash_time,
                "total_time": result.total_time,
                "throughput_mbps": result.throughput_mbps,
                "piece_count": result.piece_count,
                "memory_usage": result.memory_usage,
                "cpu_usage": result.cpu_usage,
                "success": result.success,
                "error_message": result.error_message
            })
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"[green]✓ 报告已导出: {report_file}[/green]")
            
            # 同时生成简化的文本报告
            text_report = report_file.with_suffix('.txt')
            self.generate_text_report(text_report, export_data)
            self.console.print(f"[green]✓ 文本报告已生成: {text_report}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]导出失败: {e}[/red]")
    
    def generate_text_report(self, report_file: Path, data: Dict):
        """生成文本格式的报告"""
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("Torf 性能分析报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['timestamp']))}\n")
            f.write(f"Torf版本: {data['torf_version']}\n")
            f.write(f"CPU核心数: {data['cpu_count']}\n\n")
            
            # 成功的测试结果
            successful_tests = [r for r in data["test_results"] if r["success"]]
            if successful_tests:
                f.write("性能摘要\n")
                f.write("-" * 20 + "\n")
                
                avg_throughput = sum(r["throughput_mbps"] for r in successful_tests) / len(successful_tests)
                max_throughput = max(r["throughput_mbps"] for r in successful_tests)
                best_test = max(successful_tests, key=lambda x: x["throughput_mbps"])
                
                f.write(f"平均吞吐量: {avg_throughput:.2f} MB/s\n")
                f.write(f"最高吞吐量: {max_throughput:.2f} MB/s\n")
                f.write(f"最佳配置: {best_test['test_name']}\n")
                f.write(f"  - Piece Size: {self.format_size(best_test['piece_size'])}\n")
                f.write(f"  - 文件大小: {self.format_size(best_test['file_size'])}\n")
                f.write(f"  - 总时间: {best_test['total_time']:.2f}s\n\n")
            
            # 详细结果
            f.write("详细测试结果\n")
            f.write("-" * 20 + "\n")
            for result in data["test_results"]:
                f.write(f"测试: {result['test_name']}\n")
                f.write(f"  文件大小: {self.format_size(result['file_size'])}\n")
                f.write(f"  Piece Size: {self.format_size(result['piece_size'])}\n")
                f.write(f"  总时间: {result['total_time']:.2f}s\n")
                f.write(f"  哈希时间: {result['hash_time']:.2f}s\n")
                f.write(f"  吞吐量: {result['throughput_mbps']:.2f} MB/s\n")
                f.write(f"  Piece数量: {result['piece_count']}\n")
                f.write(f"  成功: {'是' if result['success'] else '否'}\n")
                if result['error_message']:
                    f.write(f"  错误: {result['error_message']}\n")
                f.write("\n")
    
    def show_torf_info(self):
        """显示Torf版本和能力信息"""
        self.console.print("\n[bold]Torf 版本信息[/bold]")
        
        info_table = Table(title="Torf Information")
        info_table.add_column("属性", style="cyan")
        info_table.add_column("值", style="yellow")
        
        info_table.add_row("版本", getattr(torf, '__version__', '未知'))
        info_table.add_row("默认Piece Size", self.format_size(torf.Torrent().piece_size))
        
        # 检查多线程支持
        has_threading = hasattr(torf, 'set_max_workers')
        info_table.add_row("多线程支持", "是" if has_threading else "否")
        
        # 系统信息
        info_table.add_row("CPU核心数", str(multiprocessing.cpu_count()))
        
        self.console.print(info_table)
        
        # 显示默认配置建议
        recommendations_panel = Panel(
            "[bold]性能优化建议[/bold]\n\n"
            "1. [cyan]Piece Size选择:[/cyan]\n"
            "   • 小文件 (<100MB): 64KB - 256KB\n"
            "   • 中等文件 (100MB-1GB): 256KB - 1MB\n"
            "   • 大文件 (>1GB): 1MB - 4MB\n\n"
            "2. [cyan]多线程设置:[/cyan]\n"
            "   • 通常设置为CPU核心数\n"
            "   • 对于I/O密集型可以适当增加\n\n"
            "3. [cyan]内存考虑:[/cyan]\n"
            "   • 较小的Piece Size会增加内存使用\n"
            "   • 权衡速度和内存占用",
            title="优化建议",
            border_style="green"
        )
        self.console.print(recommendations_panel)
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / (1024**2):.1f} MB"
        else:
            return f"{size_bytes / (1024**3):.1f} GB"
    
    @staticmethod
    def get_memory_usage() -> float:
        """获取当前内存使用量（MB）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024**2)
        except ImportError:
            return 0.0
    
    @staticmethod
    def get_cpu_usage() -> float:
        """获取当前CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent()
        except ImportError:
            return 0.0

def main():
    """主函数"""
    try:
        analyzer = TorfPerformanceAnalyzer()
        analyzer.run_analysis()
    except KeyboardInterrupt:
        console.print("\n[yellow]程序被用户中断[/yellow]")
    except Exception as e:
        console.print(f"[red]程序运行错误: {e}[/red]")

if __name__ == "__main__":
    main()
