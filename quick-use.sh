#!/bin/bash

# Media Packer 一键使用脚本 (无需安装)
# 使用方法: curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- [参数]

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# 项目信息
GITHUB_RAW="https://raw.githubusercontent.com/Yan-nian/media-packer/main"
TEMP_DIR="/tmp/media-packer-$$"

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION_NUM=$(python3 -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)" 2>/dev/null || echo "0")
        if [ "$PYTHON_VERSION_NUM" -ge 38 ]; then
            PYTHON_CMD="python3"
            return 0
        fi
    fi
    
    if command -v python &> /dev/null; then
        PYTHON_VERSION_NUM=$(python -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)" 2>/dev/null || echo "0")
        if [ "$PYTHON_VERSION_NUM" -ge 38 ]; then
            PYTHON_CMD="python"
            return 0
        fi
    fi
    
    print_error "未找到Python 3.8+，请先安装Python"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
}

# 安装依赖
install_deps() {
    print_info "检查和安装依赖..."
    
    # 检查是否已安装
    if $PYTHON_CMD -c "import torf, click, rich" 2>/dev/null; then
        print_success "依赖已安装"
        return 0
    fi
    
    print_info "安装缺失的依赖包..."
    
    # 尝试多种安装方式
    if $PYTHON_CMD -m pip install --user torf click rich 2>/dev/null; then
        print_success "使用 --user 模式安装成功"
    elif $PYTHON_CMD -m pip install --user --break-system-packages torf click rich 2>/dev/null; then
        print_success "使用 --break-system-packages 模式安装成功"
    else
        print_error "依赖安装失败"
        echo
        echo "请尝试以下方法之一："
        echo "1. 使用虚拟环境："
        echo "   python3 -m venv /tmp/media-packer-env"
        echo "   source /tmp/media-packer-env/bin/activate"
        echo "   pip install torf click rich"
        echo
        echo "2. 使用 --break-system-packages："
        echo "   python3 -m pip install --user --break-system-packages torf click rich"
        echo
        echo "3. 使用系统包管理器："
        echo "   sudo apt install python3-pip python3-venv"
        echo
        exit 1
    fi
}

# 下载并运行
run_media_packer() {
    print_info "创建临时目录..."
    mkdir -p "$TEMP_DIR"
    cd "$TEMP_DIR"
    
    print_info "下载Media Packer..."
    curl -fsSL "$GITHUB_RAW/media_packer_simple.py" -o media_packer_simple.py
    
    print_info "启动Media Packer..."
    $PYTHON_CMD media_packer_simple.py "$@"
    
    # 清理临时文件
    cd /
    rm -rf "$TEMP_DIR"
}

# 显示帮助
show_help() {
    echo -e "${GREEN}Media Packer 一键使用工具${NC}"
    echo
    echo "使用方法:"
    echo "curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash"
    echo
    echo "带参数使用:"
    echo "curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack /path/to/video.mkv"
    echo "curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- batch /path/to/videos/*"
    echo
    echo "示例:"
    echo "# 交互式使用"
    echo "curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash"
    echo
    echo "# 直接生成种子"
    echo "curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-use.sh | bash -s -- pack ./video.mkv --name 'MyTorrent'"
    echo
    echo "注意: 首次使用会自动安装Python依赖包"
}

# 主函数
main() {
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    echo -e "${GREEN}Media Packer 一键使用工具${NC}"
    echo "无需下载仓库，直接使用！"
    echo
    
    check_python
    install_deps
    run_media_packer "$@"
    
    print_success "完成！"
}

# 错误处理
trap 'print_error "执行过程中发生错误"' ERR

# 脚本入口
main "$@"
