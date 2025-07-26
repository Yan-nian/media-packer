# 种子命名功能更新

## 🎯 更新概述

根据用户需求 "对于种子名称的命名我希望以选择的文件夹的名称来"，我们已经成功实现了基于文件夹名称的种子命名功能。

## ✨ 新功能

### 智能命名逻辑
- **文件处理**: 对于单个媒体文件，使用其父目录名称作为种子名称
- **目录处理**: 对于整个目录，直接使用目录名称作为种子名称
- **自动识别**: 程序会自动判断输入类型并应用相应的命名规则

### 命名规则对比

| 场景 | 文件路径 | 旧命名方式 | 新命名方式 |
|------|----------|------------|------------|
| 电影文件 | `/Movies/阿凡达.2009/Avatar.mkv` | `Avatar.torrent` | `阿凡达.2009.torrent` |
| 电视剧集 | `/TV/权力的游戏.S01/episode1.mp4` | `episode1.torrent` | `权力的游戏.S01.torrent` |
| 整个文件夹 | `/Downloads/复仇者联盟.2012/` | `复仇者联盟.2012.torrent` | `复仇者联盟.2012.torrent` |

## 🔧 技术实现

### 核心更改

1. **create_torrent_for_file 方法**
   ```python
   def create_torrent_for_file(self, file_path: Path, custom_name: Optional[str] = None, **kwargs) -> Path:
   ```
   - 添加了 `custom_name` 参数
   - 支持自定义种子名称
   - 保持向后兼容性

2. **交互界面更新**
   ```python
   # 获取文件夹名称用作种子名称
   folder_name = file_path.parent.name if file_path.is_file() else file_path.name
   console.print(f"[cyan]种子文件名将使用: {folder_name}[/cyan]")
   
   # 使用文件夹名称创建种子
   torrent_path = self.media_packer.create_torrent_for_file(
       file_path, 
       custom_name=folder_name,
       create_nfo=True
   )
   ```

3. **CLI 命令增强**
   ```bash
   # 新增 --name 参数
   python3 media_packer_all_in_one.py pack /path/to/file --name "自定义名称"
   ```

## 📖 使用指南

### 命令行模式

```bash
# 自动使用文件夹名称
python3 media_packer_all_in_one.py pack /Movies/阿凡达.2009/Avatar.mkv
# 输出: 阿凡达.2009.torrent

# 指定自定义名称
python3 media_packer_all_in_one.py pack /Movies/Avatar.mkv --name "阿凡达导演剪辑版"
# 输出: 阿凡达导演剪辑版.torrent
```

### 交互模式

```bash
# 直接运行，自动使用文件夹名称
python3 media_packer_all_in_one.py
```

交互界面会自动：
1. 识别选中文件的父目录名称
2. 显示将要使用的种子名称
3. 使用该名称创建种子文件

## 🧪 测试验证

### 测试文件
- `test_naming_simple.py`: 验证命名逻辑和参数
- `demo_naming.py`: 功能演示和使用指南

### 测试结果
```
测试完成: 2/2 个测试通过
✓ 所有命名逻辑测试通过
```

## 🔄 向后兼容性

- 不指定 `custom_name` 参数时，使用原有的命名逻辑
- 现有的 CLI 命令和交互界面完全兼容
- 批量处理功能保持不变

## 📝 更新日志

**版本**: 2024年12月更新
**类型**: 功能增强
**影响**: 种子命名方式改进，用户体验提升

### 更改内容
1. ✅ 实现基于文件夹名称的种子命名
2. ✅ 添加 CLI --name 参数支持
3. ✅ 更新交互界面显示种子名称提示
4. ✅ 创建测试和演示脚本
5. ✅ 维护向后兼容性

### 用户收益
- 🎯 种子名称更有意义，基于文件夹而非文件名
- 🔧 CLI 模式支持自定义种子名称
- 👁️ 交互模式显示即将使用的种子名称
- 📁 更好的文件组织和识别能力

## 🚀 下一步计划

- 考虑添加种子名称模板功能
- 支持批量重命名现有种子
- 添加名称格式验证和清理功能
