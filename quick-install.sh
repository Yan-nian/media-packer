#!/bin/bash
#
# Media Packer - 一键安装脚本
# 适用于 VPS 和本地环境快速部署
#
# 使用方法:
#   curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --path /opt/media-packer
#   curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --simple
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 默认配置
INSTALL_DIR="$HOME/media-packer"
MODE="simple"
QUIET=false
CREATE_SYMLINK=true
SKIP_DEPS=false

# 帮助信息
show_help() {
    echo "Media Packer 一键安装脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --path PATH     安装目录 (默认: $HOME/media-packer)"
    echo "  --simple        只安装简化版依赖 (默认)"
    echo "  --full          安装完整版依赖"
    echo "  --quiet         静默安装"
    echo "  --no-symlink    不创建系统命令链接"
    echo "  --skip-deps     跳过依赖安装"
    echo "  --help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash"
    echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --path /opt/media-packer"
    echo "  curl -fsSL https://raw.githubusercontent.com/Yan-nian/media-packer/main/quick-install.sh | bash -s -- --full --quiet"
}

# 打印带颜色的信息
print_info() {
    if [ "$QUIET" != "true" ]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示横幅
show_banner() {
    if [ "$QUIET" != "true" ]; then
        echo -e "${CYAN}"
        echo "╭─────────────────────────────────────────────────╮"
        echo "│            Media Packer 一键安装器             │"
        echo "│              VPS/本地环境适配版                 │"
        echo "╰─────────────────────────────────────────────────╯"
        echo -e "${NC}"
    fi
}

# 检测系统环境
detect_system() {
    print_info "检测系统环境..."
    
    # 检测操作系统
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
            VERSION=$VERSION_ID
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    else
        print_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    print_info "检测到系统: $DISTRO"
    
    # 检测Python版本
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        print_info "Python版本: $PYTHON_VERSION"
        
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python版本检查通过"
        else
            print_error "需要Python 3.8或更高版本"
            install_python
        fi
    else
        print_error "未找到Python3"
        install_python
    fi
    
    # 检测pip
    if ! command -v pip3 >/dev/null 2>&1; then
        print_warning "未找到pip3，尝试安装..."
        install_pip
    fi
}

# 安装Python (如果需要)
install_python() {
    print_info "安装Python 3.8+..."
    
    case $DISTRO in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv
            ;;
        centos|rhel|fedora)
            if command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y python3 python3-pip
            else
                sudo yum install -y python3 python3-pip
            fi
            ;;
        macos)
            if command -v brew >/dev/null 2>&1; then
                brew install python3
            else
                print_error "请先安装Homebrew或手动安装Python 3.8+"
                exit 1
            fi
            ;;
        *)
            print_error "不支持的系统，请手动安装Python 3.8+"
            exit 1
            ;;
    esac
}

# 安装pip (如果需要)
install_pip() {
    case $DISTRO in
        ubuntu|debian)
            sudo apt install -y python3-pip
            ;;
        centos|rhel|fedora)
            if command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y python3-pip
            else
                sudo yum install -y python3-pip
            fi
            ;;
    esac
}

# 创建安装目录
create_install_dir() {
    print_info "创建安装目录: $INSTALL_DIR"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
}

# 下载项目文件
download_files() {
    print_info "下载Media Packer文件..."
    
    # 核心文件列表
    FILES=(
        "media_packer_simple.py"
        "media_packer_all_in_one.py"
        "start.py"
        "install_deps.py"
        "requirements.txt"
        "pyproject.toml"
        "README.md"
        "CLAUDE.md"
    )
    
    # 这里使用实际的GitHub仓库地址
    BASE_URL="https://raw.githubusercontent.com/Yan-nian/media-packer/main"
    
    for file in "${FILES[@]}"; do
        print_info "下载 $file..."
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL "$BASE_URL/$file" -o "$file" || {
                print_error "下载 $file 失败"
                exit 1
            }
        elif command -v wget >/dev/null 2>&1; then
            wget -q "$BASE_URL/$file" || {
                print_error "下载 $file 失败"
                exit 1
            }
        else
            print_error "需要curl或wget来下载文件"
            exit 1
        fi
    done
    
    # 设置执行权限
    chmod +x *.py
    
    # 创建输出目录
    mkdir -p output
}

# 安装Python依赖
install_dependencies() {
    if [ "$SKIP_DEPS" = "true" ]; then
        print_info "跳过依赖安装"
        return
    fi
    
    print_info "安装Python依赖..."
    
    # 检测是否需要虚拟环境 (针对现代Python环境限制)
    if python3 -m pip install --dry-run torf 2>&1 | grep -q "externally-managed-environment"; then
        print_warning "检测到Python环境限制，创建虚拟环境..."
        python3 -m venv venv
        source venv/bin/activate
        VENV_CREATED=true
    fi
    
    # 根据模式安装依赖
    if [ "$MODE" = "full" ]; then
        print_info "安装完整版依赖..."
        python3 -m pip install --user torf click rich psutil requests tmdbv3api pymediainfo
    else
        print_info "安装简化版依赖..."
        python3 -m pip install --user torf click rich psutil
    fi
    
    print_success "依赖安装完成"
}

# 创建系统命令链接
create_symlinks() {
    if [ "$CREATE_SYMLINK" != "true" ]; then
        return
    fi
    
    print_info "创建系统命令链接..."
    
    # 创建启动脚本
    cat > media-packer << 'EOF'
#!/bin/bash
INSTALL_DIR="$(dirname "$(readlink -f "$0")")"
cd "$INSTALL_DIR"

# 如果有虚拟环境，先激活
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

python3 start.py "$@"
EOF
    
    chmod +x media-packer
    
    # 尝试创建系统链接
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$INSTALL_DIR/media-packer" /usr/local/bin/media-packer
        print_success "创建系统命令: media-packer"
    elif command -v sudo >/dev/null 2>&1; then
        sudo ln -sf "$INSTALL_DIR/media-packer" /usr/local/bin/media-packer
        print_success "创建系统命令: media-packer"
    else
        print_warning "无法创建系统命令链接，请手动添加到PATH: $INSTALL_DIR"
    fi
}

# 创建配置文件
create_config() {
    print_info "创建默认配置..."
    
    cat > config.json << 'EOF'
{
    "auto_optimize": true,
    "output_dir": "./output",
    "private": true,
    "comment": "Created by Media Packer",
    "created_by": "Media Packer v2.0"
}
EOF
}

# 运行测试
run_test() {
    print_info "运行功能测试..."
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    
    if python3 media_packer_simple.py --help >/dev/null 2>&1; then
        print_success "功能测试通过"
    else
        print_error "功能测试失败"
        exit 1
    fi
}

# 显示安装完成信息
show_completion() {
    print_success "Media Packer 安装完成！"
    echo ""
    echo -e "${CYAN}安装位置:${NC} $INSTALL_DIR"
    echo -e "${CYAN}配置文件:${NC} $INSTALL_DIR/config.json"
    echo ""
    echo -e "${GREEN}使用方法:${NC}"
    
    if [ "$CREATE_SYMLINK" = "true" ] && [ -f "/usr/local/bin/media-packer" ]; then
        echo "  media-packer                          # 启动交互界面"
        echo "  media-packer pack /path/to/video.mkv  # 直接制种"
        echo "  media-packer batch /path/to/videos/*  # 批量制种"
    else
        echo "  cd $INSTALL_DIR"
        echo "  python3 start.py                      # 启动交互界面"
        echo "  python3 media_packer_simple.py pack /path/to/video.mkv  # 直接制种"
    fi
    
    echo ""
    echo -e "${YELLOW}提示:${NC}"
    echo "  • 首次运行会自动检查和安装缺失依赖"
    echo "  • 支持自动CPU线程优化和智能Piece Size选择"
    echo "  • 配置文件位于: $INSTALL_DIR/config.json"
    
    if [ "$VENV_CREATED" = "true" ]; then
        echo "  • 已创建Python虚拟环境，无需担心依赖冲突"
    fi
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --path)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --simple)
                MODE="simple"
                shift
                ;;
            --full)
                MODE="full"
                shift
                ;;
            --quiet)
                QUIET=true
                shift
                ;;
            --no-symlink)
                CREATE_SYMLINK=false
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 主函数
main() {
    parse_args "$@"
    
    show_banner
    
    detect_system
    create_install_dir
    download_files
    install_dependencies
    create_config
    create_symlinks
    run_test
    show_completion
}

# 运行主函数
main "$@"