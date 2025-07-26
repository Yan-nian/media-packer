#!/bin/bash

# Media Packer 一键安装和使用脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/install.sh | bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# 项目信息
PROJECT_NAME="Media Packer"
GITHUB_RAW="https://raw.githubusercontent.com/Yan-nian/media-packer/main"
INSTALL_DIR="$HOME/.media-packer"

# 打印函数
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_header() {
    echo -e "${GREEN}${BOLD}"
    echo "=================================================="
    echo "    $PROJECT_NAME 一键安装脚本"
    echo "=================================================="
    echo -e "${NC}"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt &> /dev/null; then
            DISTRO="debian"
        elif command -v yum &> /dev/null; then
            DISTRO="redhat"
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        DISTRO="windows"
    else
        OS="unknown"
        DISTRO="unknown"
    fi
    
    print_info "检测到系统: $OS ($DISTRO)"
}

# 检查Python
check_python() {
    print_info "检查Python环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_VERSION_NUM=$(python3 -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
        
        if [ "$PYTHON_VERSION_NUM" -ge 38 ]; then
            PYTHON_CMD="python3"
            print_success "Python版本符合要求: $PYTHON_VERSION"
        else
            print_error "Python版本过低: $PYTHON_VERSION (需要3.8+)"
            install_python
        fi
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_VERSION_NUM=$(python -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
        
        if [ "$PYTHON_VERSION_NUM" -ge 38 ]; then
            PYTHON_CMD="python"
            print_success "Python版本符合要求: $PYTHON_VERSION"
        else
            print_error "Python版本过低: $PYTHON_VERSION (需要3.8+)"
            install_python
        fi
    else
        print_error "未找到Python"
        install_python
    fi
}

# 安装Python
install_python() {
    print_info "尝试安装Python..."
    
    case $DISTRO in
        "debian")
            sudo apt update -qq
            sudo apt install -y python3 python3-pip
            PYTHON_CMD="python3"
            ;;
        "redhat")
            sudo yum install -y python3 python3-pip
            PYTHON_CMD="python3"
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install python3
                PYTHON_CMD="python3"
            else
                print_error "请安装Homebrew或手动安装Python 3.8+"
                exit 1
            fi
            ;;
        *)
            print_error "无法自动安装Python，请手动安装Python 3.8+"
            exit 1
            ;;
    esac
}

# 创建安装目录
create_install_dir() {
    print_info "创建安装目录: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
}

# 下载核心文件
download_files() {
    print_info "下载项目文件..."
    
    # 下载核心Python文件
    curl -fsSL "$GITHUB_RAW/media_packer_simple.py" -o media_packer_simple.py
    curl -fsSL "$GITHUB_RAW/install_deps.py" -o install_deps.py
    curl -fsSL "$GITHUB_RAW/requirements.txt" -o requirements.txt
    
    # 设置执行权限
    chmod +x *.py
    
    print_success "文件下载完成"
}

# 安装依赖
install_dependencies() {
    print_info "安装Python依赖..."
    
    # 尝试使用内置的依赖安装工具
    if [ -f "install_deps.py" ]; then
        $PYTHON_CMD install_deps.py --mode simple
    else
        # 直接安装核心依赖
        $PYTHON_CMD -m pip install --user torf click rich
    fi
    
    print_success "依赖安装完成"
}

# 创建启动脚本
create_launcher() {
    print_info "创建启动脚本..."
    
    # 创建命令行启动脚本
    cat > media-packer << 'EOF'
#!/bin/bash
# Media Packer 启动脚本
SCRIPT_DIR="$HOME/.media-packer"
cd "$SCRIPT_DIR"

if command -v python3 &> /dev/null; then
    python3 media_packer_simple.py "$@"
elif command -v python &> /dev/null; then
    python media_packer_simple.py "$@"
else
    echo "错误: 未找到Python"
    exit 1
fi
EOF
    
    chmod +x media-packer
    
    # 尝试添加到PATH
    if [[ ":$PATH:" != *":$HOME/.media-packer:"* ]]; then
        echo 'export PATH="$HOME/.media-packer:$PATH"' >> ~/.bashrc
        echo 'export PATH="$HOME/.media-packer:$PATH"' >> ~/.zshrc 2>/dev/null || true
        print_info "已添加到PATH，重新打开终端后可直接使用 'media-packer' 命令"
    fi
    
    print_success "启动脚本创建完成"
}

# 显示使用说明
show_usage() {
    echo -e "${GREEN}${BOLD}"
    echo "=================================================="
    echo "          安装完成！使用方法："
    echo "=================================================="
    echo -e "${NC}"
    
    echo -e "${YELLOW}方式1: 直接使用（当前会话）${NC}"
    echo "cd $INSTALL_DIR"
    echo "$PYTHON_CMD media_packer_simple.py"
    echo
    
    echo -e "${YELLOW}方式2: 使用启动脚本${NC}"
    echo "$INSTALL_DIR/media-packer"
    echo
    
    echo -e "${YELLOW}方式3: 全局命令（重新打开终端后）${NC}"
    echo "media-packer"
    echo
    
    echo -e "${YELLOW}命令行示例：${NC}"
    echo "# 交互式使用"
    echo "media-packer"
    echo
    echo "# 直接生成种子"
    echo "media-packer pack /path/to/video.mkv --name 'My_Torrent'"
    echo
    echo "# 批量处理"
    echo "media-packer batch /path/to/videos/* --name 'Batch_Upload'"
    echo
    
    echo -e "${BLUE}更多帮助：${NC}"
    echo "media-packer --help"
    echo
    echo -e "${GREEN}享受使用 Media Packer！${NC} 🎉"
}

# 主函数
main() {
    print_header
    detect_os
    check_python
    create_install_dir
    download_files
    install_dependencies
    create_launcher
    show_usage
}

# 错误处理
trap 'echo -e "\n${RED}安装过程中发生错误，请检查网络连接和权限设置${NC}"' ERR

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
