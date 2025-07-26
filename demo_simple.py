#!/usr/bin/env python3
"""
简化版 Media Packer 功能演示
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def demonstrate_simple_version():
    """演示简化版功能"""
    
    console.print(Panel.fit(
        "[bold blue]🎯 Media Packer 简化版[/bold blue]\n\n"
        "[green]专注核心功能:[/green] 纯粹的种子生成工具！\n\n"
        "[yellow]移除功能:[/yellow] 元数据获取、NFO生成、复杂依赖",
        title="简化版介绍",
        border_style="blue"
    ))
    
    # 功能对比表格
    table = Table(title="版本功能对比")
    table.add_column("功能", style="cyan", width=20)
    table.add_column("完整版", style="yellow", width=10)
    table.add_column("简化版", style="green", width=10)
    table.add_column("说明", style="white", width=30)
    
    features = [
        ("种子创建", "✅", "✅", "基于torf的高效种子生成"),
        ("智能命名", "✅", "✅", "基于文件夹名称命名"),
        ("批量处理", "✅", "✅", "支持多文件批量制种"),
        ("交互界面", "✅", "✅", "友好的终端交互"),
        ("命令行工具", "✅", "✅", "完整的CLI支持"),
        ("文件识别", "✅", "✅", "自动识别视频文件"),
        ("TMDB元数据", "✅", "❌", "移除外部API依赖"),
        ("NFO生成", "✅", "❌", "不再生成NFO文件"),
        ("媒体信息分析", "✅", "❌", "移除pymediainfo"),
        ("复杂命名规则", "✅", "❌", "简化命名逻辑")
    ]
    
    for feature, full, simple, desc in features:
        table.add_row(feature, full, simple, desc)
    
    console.print(table)
    
    # 依赖对比
    console.print("\n" + Panel(
        "[bold]依赖对比:[/bold]\n\n"
        "[red]完整版依赖 (6个):[/red]\n"
        "• torf (种子创建)\n"
        "• pymediainfo (媒体信息)\n"
        "• tmdbv3api (元数据API)\n"
        "• requests (HTTP请求)\n"
        "• click (命令行)\n"
        "• rich (终端美化)\n\n"
        "[green]简化版依赖 (3个):[/green]\n"
        "• torf (种子创建)\n"
        "• click (命令行)\n"
        "• rich (终端美化)\n\n"
        "[blue]减少 50% 依赖！[/blue]",
        title="依赖对比",
        border_style="green"
    ))
    
    # 使用示例
    console.print("\n" + Panel(
        "[bold]使用示例:[/bold]\n\n"
        "[cyan]简化版 - 交互模式:[/cyan]\n"
        "  python3 media_packer_simple.py\n"
        "  # 启动简洁的交互界面\n\n"
        "[cyan]简化版 - 命令行:[/cyan]\n"
        "  python3 media_packer_simple.py pack /Movies/电影/movie.mkv\n"
        "  # 输出: 电影.torrent\n\n"
        "  python3 media_packer_simple.py batch /TV/剧集/* --name \"完整剧集\"\n"
        "  # 输出: 完整剧集.torrent\n\n"
        "[yellow]完整版 - 如需元数据:[/yellow]\n"
        "  python3 media_packer_all_in_one.py pack movie.mkv --fetch-metadata --create-nfo\n"
        "  # 包含完整的元数据和NFO",
        title="使用指南",
        border_style="cyan"
    ))
    
    # 适用场景
    console.print("\n" + Panel(
        "[bold]推荐使用简化版的场景:[/bold]\n\n"
        "✅ [green]只需创建种子文件[/green]\n"
        "✅ [green]服务器或自动化环境[/green]\n"
        "✅ [green]希望快速部署[/green]\n"
        "✅ [green]减少依赖和复杂性[/green]\n"
        "✅ [green]批量种子生成[/green]\n\n"
        "[bold]推荐使用完整版的场景:[/bold]\n\n"
        "✅ [yellow]需要详细影视信息[/yellow]\n"
        "✅ [yellow]生成NFO给Kodi/Plex[/yellow]\n"
        "✅ [yellow]标准化文件命名[/yellow]\n"
        "✅ [yellow]完整媒体管理工作流[/yellow]",
        title="适用场景",
        border_style="magenta"
    ))

if __name__ == '__main__':
    demonstrate_simple_version()
