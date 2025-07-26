"""简化的交互式制种工具测试版"""
import os
import json
import time
from pathlib import Path
from typing import List

class SimpleInteractive:
    def __init__(self):
        self.media_directories: List[str] = []
        self.output_directory = ""
        self.trackers = [
            "https://tracker1.example.com/announce",
            "https://tracker2.example.com/announce"
        ]
        self.queue = []
        
        # 设置文件
        self.settings_file = Path.home() / ".media_packer_simple.json"
        self.load_settings()
    
    def run(self):
        """运行交互式界面"""
        print("="*60)
        print(" 🎬 Media Packer - 终端交互式制种工具")
        print("="*60)
        print()
        
        while True:
            self.show_menu()
            try:
                choice = input("请选择操作 (0-8): ").strip()
                print()
                
                if choice == "1":
                    self.manage_directories()
                elif choice == "2":
                    self.set_output_directory()
                elif choice == "3":
                    self.manage_trackers()
                elif choice == "4":
                    self.scan_files()
                elif choice == "5":
                    self.view_queue()
                elif choice == "6":
                    self.start_processing()
                elif choice == "7":
                    self.view_settings()
                elif choice == "8":
                    self.save_settings()
                    print("✅ 设置已保存")
                elif choice == "0":
                    self.save_settings()
                    print("👋 再见！")
                    break
                else:
                    print("❌ 无效选择，请重试")
                
                print()
                input("按回车键继续...")
                print()
                
            except KeyboardInterrupt:
                print("\\n\\n👋 再见！")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
    
    def show_menu(self):
        """显示主菜单"""
        print("📋 主菜单")
        print("-" * 40)
        print(f"1. 媒体目录管理    ({len(self.media_directories)} 个)")
        print(f"2. 设置输出目录    ({'✅' if self.output_directory else '❌'})")
        print(f"3. Tracker配置     ({len(self.trackers)} 个)")
        print(f"4. 扫描媒体文件    ({len(self.queue)} 个排队)")
        print("5. 查看处理队列")
        print("6. 开始批量处理")
        print("7. 查看当前设置")
        print("8. 保存设置")
        print("0. 退出程序")
        print()
    
    def manage_directories(self):
        """管理媒体目录"""
        while True:
            print("📁 媒体目录管理")
            print("-" * 30)
            
            if self.media_directories:
                for i, directory in enumerate(self.media_directories, 1):
                    exists = "✅" if Path(directory).exists() else "❌"
                    print(f"{i}. {exists} {directory}")
            else:
                print("暂无媒体目录")
            
            print()
            print("1. 添加目录")
            print("2. 删除目录")
            print("0. 返回主菜单")
            
            choice = input("请选择: ").strip()
            
            if choice == "1":
                directory = input("请输入目录路径: ").strip()
                if directory and directory not in self.media_directories:
                    self.media_directories.append(directory)
                    print(f"✅ 已添加: {directory}")
                else:
                    print("❌ 无效路径或已存在")
            
            elif choice == "2":
                if self.media_directories:
                    try:
                        index = int(input("请输入要删除的序号: ")) - 1
                        if 0 <= index < len(self.media_directories):
                            removed = self.media_directories.pop(index)
                            print(f"✅ 已删除: {removed}")
                        else:
                            print("❌ 无效序号")
                    except ValueError:
                        print("❌ 请输入数字")
                else:
                    print("❌ 暂无可删除的目录")
            
            elif choice == "0":
                break
            
            print()
    
    def set_output_directory(self):
        """设置输出目录"""
        print("📤 输出目录设置")
        print("-" * 20)
        
        if self.output_directory:
            print(f"当前: {self.output_directory}")
        
        directory = input("请输入输出目录路径 (留空保持不变): ").strip()
        
        if directory:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
                self.output_directory = directory
                print(f"✅ 输出目录设置为: {directory}")
            except Exception as e:
                print(f"❌ 设置失败: {e}")
    
    def manage_trackers(self):
        """管理Tracker"""
        while True:
            print("🔗 Tracker配置")
            print("-" * 20)
            
            for i, tracker in enumerate(self.trackers, 1):
                print(f"{i}. {tracker}")
            
            print()
            print("1. 添加Tracker")
            print("2. 删除Tracker")
            print("3. 重置为默认")
            print("0. 返回主菜单")
            
            choice = input("请选择: ").strip()
            
            if choice == "1":
                tracker = input("请输入Tracker URL: ").strip()
                if tracker and tracker not in self.trackers:
                    self.trackers.append(tracker)
                    print(f"✅ 已添加: {tracker}")
                else:
                    print("❌ 无效URL或已存在")
            
            elif choice == "2":
                if self.trackers:
                    try:
                        index = int(input("请输入要删除的序号: ")) - 1
                        if 0 <= index < len(self.trackers):
                            removed = self.trackers.pop(index)
                            print(f"✅ 已删除: {removed}")
                        else:
                            print("❌ 无效序号")
                    except ValueError:
                        print("❌ 请输入数字")
                else:
                    print("❌ 暂无可删除的Tracker")
            
            elif choice == "3":
                self.trackers = [
                    "https://tracker1.example.com/announce",
                    "https://tracker2.example.com/announce"
                ]
                print("✅ 已重置为默认Tracker")
            
            elif choice == "0":
                break
            
            print()
    
    def scan_files(self):
        """扫描媒体文件"""
        if not self.media_directories:
            print("❌ 请先添加媒体目录")
            return
        
        print("🔍 扫描媒体文件...")
        
        video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        found_files = []
        
        for directory in self.media_directories:
            dir_path = Path(directory)
            if dir_path.exists():
                print(f"扫描: {directory}")
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                        found_files.append(str(file_path))
        
        print(f"\\n✅ 发现 {len(found_files)} 个视频文件")
        
        if found_files:
            if len(found_files) <= 10:
                print("\\n文件列表:")
                for i, file_path in enumerate(found_files, 1):
                    print(f"{i}. {Path(file_path).name}")
            
            add_to_queue = input("\\n是否添加到处理队列? (y/N): ").strip().lower()
            if add_to_queue == 'y':
                self.queue.extend(found_files)
                self.queue = list(set(self.queue))  # 去重
                print(f"✅ 已添加 {len(found_files)} 个文件到队列")
    
    def view_queue(self):
        """查看处理队列"""
        print("📋 处理队列")
        print("-" * 20)
        
        if not self.queue:
            print("队列为空")
            return
        
        print(f"队列中有 {len(self.queue)} 个文件:\\n")
        
        for i, file_path in enumerate(self.queue[:10], 1):  # 只显示前10个
            print(f"{i}. {Path(file_path).name}")
        
        if len(self.queue) > 10:
            print(f"... 还有 {len(self.queue) - 10} 个文件")
        
        print("\\n操作:")
        print("1. 清空队列")
        print("0. 返回")
        
        choice = input("请选择: ").strip()
        
        if choice == "1":
            confirm = input("确定要清空队列吗? (y/N): ").strip().lower()
            if confirm == 'y':
                self.queue.clear()
                print("✅ 队列已清空")
    
    def start_processing(self):
        """开始处理"""
        if not self.queue:
            print("❌ 队列为空，请先扫描文件")
            return
        
        if not self.output_directory:
            print("❌ 请先设置输出目录")
            return
        
        if not self.trackers:
            print("❌ 请先设置Tracker")
            return
        
        print(f"🚀 开始处理 {len(self.queue)} 个文件")
        print(f"📤 输出目录: {self.output_directory}")
        print(f"🔗 使用 {len(self.trackers)} 个Tracker")
        print()
        
        # 模拟处理过程
        processed = 0
        for i, file_path in enumerate(self.queue, 1):
            filename = Path(file_path).name
            print(f"[{i}/{len(self.queue)}] 处理: {filename}")
            
            # 模拟处理时间
            for step in ["分析文件", "提取信息", "创建种子", "保存文件"]:
                print(f"  → {step}...")
                time.sleep(0.5)
            
            processed += 1
            print(f"  ✅ 完成")
            print()
        
        print(f"🎉 批量处理完成！")
        print(f"✅ 成功处理: {processed} 个文件")
        print(f"📁 输出位置: {self.output_directory}")
        
        # 清空队列
        if input("\\n是否清空已处理的队列? (Y/n): ").strip().lower() != 'n':
            self.queue.clear()
            print("✅ 队列已清空")
    
    def view_settings(self):
        """查看设置"""
        print("⚙️  当前设置")
        print("=" * 40)
        
        print(f"📁 媒体目录: {len(self.media_directories)} 个")
        for directory in self.media_directories:
            exists = "✅" if Path(directory).exists() else "❌"
            print(f"   {exists} {directory}")
        
        print(f"\\n📤 输出目录: {self.output_directory or '未设置'}")
        
        print(f"\\n🔗 Trackers: {len(self.trackers)} 个")
        for tracker in self.trackers:
            print(f"   • {tracker}")
        
        print(f"\\n📋 队列: {len(self.queue)} 个文件")
    
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
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    def load_settings(self):
        """加载设置"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.media_directories = settings.get("media_directories", [])
                self.output_directory = settings.get("output_directory", "")
                self.trackers = settings.get("trackers", self.trackers)
        except Exception:
            pass  # 使用默认设置


def main():
    """启动简化交互式工具"""
    app = SimpleInteractive()
    app.run()


if __name__ == "__main__":
    main()