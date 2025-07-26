#!/usr/bin/env python3
"""
演示新的种子命名功能
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def demonstrate_naming_feature():
    """演示种子命名功能"""
    
    console.print(Panel.fit(
        "[bold blue]🎯 种子命名功能演示[/bold blue]\n\n"
        "[green]新功能:[/green] 种子名称现在基于选择的文件夹名称！",
        title="Media Packer 更新",
        border_style="blue"
    ))
    
    # 创建对比表格
    table = Table(title="命名规则对比")
    table.add_column("场景", style="cyan", width=20)
    table.add_column("文件路径", style="yellow", width=35)
    table.add_column("旧命名方式", style="red", width=20)
    table.add_column("新命名方式", style="green", width=20)
    
    # 添加示例
    examples = [
        {
            "scenario": "电影文件",
            "path": "/Movies/阿凡达.2009/Avatar.mkv",
            "old": "Avatar.torrent",
            "new": "阿凡达.2009.torrent"
        },
        {
            "scenario": "电视剧集",
            "path": "/TV/权力的游戏.S01/episode1.mp4",
            "old": "episode1.torrent",
            "new": "权力的游戏.S01.torrent"
        },
        {
            "scenario": "整个文件夹",
            "path": "/Downloads/复仇者联盟.2012/",
            "old": "复仇者联盟.2012.torrent",
            "new": "复仇者联盟.2012.torrent"
        }
    ]
    
    for example in examples:
        table.add_row(
            example["scenario"],
            example["path"],
            example["old"],
            example["new"]
        )
    
    console.print(table)
    
    # 功能说明
    console.print()
    console.print(Panel(
        "[bold]功能说明:[/bold]\n\n"
        "• [green]自动识别:[/green] 对于文件，使用其父目录名称作为种子名称\n"
        "• [green]目录处理:[/green] 对于目录，直接使用目录名称\n"
        "• [green]CLI 支持:[/green] 命令行模式支持 --name 参数自定义名称\n"
        "• [green]交互模式:[/green] 交互界面自动使用文件夹名称\n"
        "• [green]向后兼容:[/green] 不指定 custom_name 时使用原有逻辑",
        title="更新详情",
        border_style="green"
    ))
    
    # 使用示例
    console.print()
    console.print(Panel(
        "[bold]使用示例:[/bold]\n\n"
        "[cyan]命令行模式:[/cyan]\n"
        "  # 自动使用文件夹名称\n"
        "  python3 media_packer_all_in_one.py pack /Movies/阿凡达.2009/Avatar.mkv\n"
        "  # 输出: 阿凡达.2009.torrent\n\n"
        "  # 或指定自定义名称\n"
        "  python3 media_packer_all_in_one.py pack /Movies/Avatar.mkv --name \"阿凡达导演剪辑版\"\n"
        "  # 输出: 阿凡达导演剪辑版.torrent\n\n"
        "[cyan]交互模式:[/cyan]\n"
        "  # 直接运行，自动使用文件夹名称\n"
        "  python3 media_packer_all_in_one.py",
        title="使用指南",
        border_style="cyan"
    ))

if __name__ == '__main__':
    demonstrate_naming_feature()
