#!/bin/bash

# Media Packer VPS 快速启动脚本
# 适用于 Ubuntu/Debian/CentOS 系统

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="Media Packer"
GITHUB_REPO="https://github.com/Yan-nian/media-packer.git"
PROJECT_DIR="media-packer"

# 打印彩色信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
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

print_header() {
    echo -e "${GREEN}${BOLD}"
    echo "=================================================="
    echo "    $PROJECT_NAME VPS 快速启动脚本"
    echo "=================================================="
    echo -e "${NC}"
}

# 检测操作系统
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    elif [ -f /etc/redhat-release ]; then
        OS="Red Hat Enterprise Linux"
    elif [ -f /etc/debian_version ]; then
        OS="Debian"
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    print_info "检测到操作系统: $OS $VER"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "检测到root用户，建议使用普通用户运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 检查网络连接
check_network() {
    print_info "检查网络连接..."
    if ! ping -c 1 github.com &> /dev/null; then
        print_error "无法连接到GitHub，请检查网络连接"
        print_info "你可以尝试使用VPN或更换DNS服务器"
        exit 1
    fi
    print_success "网络连接正常"
}

# 更新系统包
update_system() {
    print_info "更新系统包..."
    
    if [[ "$OS" =~ "Ubuntu" ]] || [[ "$OS" =~ "Debian" ]]; then
        sudo apt update -qq
        print_success "系统包列表已更新"
    elif [[ "$OS" =~ "CentOS" ]] || [[ "$OS" =~ "Red Hat" ]] || [[ "$OS" =~ "Rocky" ]] || [[ "$OS" =~ "AlmaLinux" ]]; then
        sudo yum check-update -q || true
        print_success "系统包列表已更新"
    else
        print_warning "未识别的操作系统，跳过系统更新"
    fi
}

# 安装必要软件
install_dependencies() {
    print_info "安装必要软件包..."
    
    if [[ "$OS" =~ "Ubuntu" ]] || [[ "$OS" =~ "Debian" ]]; then
        # 检查并安装缺失的包
        packages=("python3" "python3-pip" "python3-venv" "git" "curl" "wget")
        missing_packages=()
        
        for package in "${packages[@]}"; do
            if ! dpkg -l | grep -q "^ii  $package "; then
                missing_packages+=("$package")
            fi
        done
        
        if [ ${#missing_packages[@]} -gt 0 ]; then
            print_info "安装缺失的包: ${missing_packages[*]}"
            sudo apt install -y "${missing_packages[@]}"
        else
            print_success "所有必要的包已安装"
        fi
        
    elif [[ "$OS" =~ "CentOS" ]] || [[ "$OS" =~ "Red Hat" ]] || [[ "$OS" =~ "Rocky" ]] || [[ "$OS" =~ "AlmaLinux" ]]; then
        # 安装EPEL仓库（如果需要）
        if ! yum repolist | grep -q epel; then
            print_info "安装EPEL仓库..."
            sudo yum install -y epel-release
        fi
        
        packages=("python3" "python3-pip" "git" "curl" "wget")
        for package in "${packages[@]}"; do
            if ! rpm -q "$package" &>/dev/null; then
                print_info "安装 $package..."
                sudo yum install -y "$package"
            fi
        done
    else
        print_error "不支持的操作系统: $OS"
        print_info "请手动安装: python3, python3-pip, python3-venv, git, curl, wget"
        exit 1
    fi
    
    print_success "必要软件包安装完成"
}

# 检查Python版本
check_python() {
    print_info "检查Python版本..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        PYTHON_VERSION_NUM=$(python3 -c "import sys; print(sys.version_info.major * 10 + sys.version_info.minor)")
        
        print_info "Python版本: $PYTHON_VERSION"
        
        if [ "$PYTHON_VERSION_NUM" -lt 38 ]; then
            print_error "Python版本过低（需要3.8+），当前版本: $PYTHON_VERSION"
            
            # 尝试安装更新的Python版本
            if [[ "$OS" =~ "Ubuntu" ]] || [[ "$OS" =~ "Debian" ]]; then
                print_info "尝试安装Python 3.9..."
                sudo apt install -y python3.9 python3.9-pip
                if command -v python3.9 &> /dev/null; then
                    PYTHON_CMD="python3.9"
                    print_success "成功安装Python 3.9"
                else
                    print_error "无法安装Python 3.9，请手动升级Python"
                    exit 1
                fi
            else
                print_error "请手动升级Python到3.8或更高版本"
                exit 1
            fi
        else
            PYTHON_CMD="python3"
            print_success "Python版本符合要求"
        fi
    else
        print_error "未找到Python3，请安装Python 3.8或更高版本"
        exit 1
    fi
}

# 下载或更新项目
download_project() {
    print_info "下载项目文件..."
    
    if [ -d "$PROJECT_DIR" ]; then
        print_info "项目目录已存在，更新代码..."
        cd "$PROJECT_DIR"
        git pull
        cd ..
        print_success "项目代码已更新"
    else
        print_info "克隆项目仓库..."
        git clone "$GITHUB_REPO" "$PROJECT_DIR"
        print_success "项目下载完成"
    fi
}

# 设置项目权限
setup_permissions() {
    print_info "设置项目权限..."
    chmod +x "$PROJECT_DIR/setup.sh" 2>/dev/null || true
    chmod +x "$PROJECT_DIR"/*.py 2>/dev/null || true
    print_success "权限设置完成"
}

# 创建输出目录
create_directories() {
    print_info "创建工作目录..."
    
    # 创建输出目录
    mkdir -p output
    mkdir -p temp
    mkdir -p logs
    
    print_success "工作目录创建完成"
}

# 检查磁盘空间
check_disk_space() {
    print_info "检查磁盘空间..."
    
    available_space=$(df . | awk 'NR==2 {print $4}')
    available_gb=$((available_space / 1024 / 1024))
    
    if [ "$available_gb" -lt 1 ]; then
        print_warning "可用磁盘空间不足1GB，当前可用: ${available_gb}GB"
        print_warning "建议确保有足够的空间存储种子文件"
    else
        print_success "磁盘空间充足: ${available_gb}GB"
    fi
}

# 启动程序
start_program() {
    print_info "启动 $PROJECT_NAME..."
    cd "$PROJECT_DIR"
    
    # 选择启动方式
    echo -e "${YELLOW}选择启动方式:${NC}"
    echo "1. 交互式启动 (推荐)"
    echo "2. 简化版直接启动"
    echo "3. 完整版直接启动"
    echo "4. 安装依赖后退出"
    
    read -p "请选择 (1-4): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            print_info "启动交互式界面..."
            $PYTHON_CMD start.py
            ;;
        2)
            print_info "启动简化版..."
            $PYTHON_CMD media_packer_simple.py
            ;;
        3)
            print_info "启动完整版..."
            $PYTHON_CMD media_packer_all_in_one.py
            ;;
        4)
            print_info "仅安装依赖..."
            $PYTHON_CMD install_deps.py --mode simple
            print_success "依赖安装完成，你可以稍后手动启动程序"
            ;;
        *)
            print_error "无效选择，使用默认交互式启动"
            $PYTHON_CMD start.py
            ;;
    esac
}

# 显示使用帮助
show_help() {
    echo -e "${BLUE}VPS快速启动脚本帮助${NC}"
    echo
    echo "使用方法:"
    echo "  $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -u, --update   仅更新项目代码"
    echo "  -s, --silent   静默模式（跳过确认）"
    echo "  -d, --deps     仅安装依赖"
    echo
    echo "VPS使用建议:"
    echo "  1. 确保有至少1GB可用磁盘空间"
    echo "  2. 建议使用非root用户运行"
    echo "  3. 首次运行会自动安装所有依赖"
    echo "  4. 支持Ubuntu、Debian、CentOS等主流发行版"
    echo
    echo "故障排除:"
    echo "  - 网络连接问题: 检查DNS设置或使用VPN"
    echo "  - Python版本问题: 手动安装Python 3.8+"
    echo "  - 权限问题: 确保对项目目录有读写权限"
}

# 清理函数
cleanup() {
    if [ $? -ne 0 ]; then
        print_error "脚本执行过程中发生错误"
        print_info "请检查上述错误信息并重试"
        print_info "如需帮助，请运行: $0 --help"
    fi
}

# 主函数
main() {
    # 设置错误处理
    trap cleanup EXIT
    
    # 解析命令行参数
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--update)
            print_header
            print_info "仅更新模式"
            download_project
            print_success "更新完成"
            exit 0
            ;;
        -s|--silent)
            SILENT_MODE=true
            ;;
        -d|--deps)
            DEPS_ONLY=true
            ;;
    esac
    
    # 开始执行
    print_header
    
    # 系统检查
    detect_os
    check_root
    check_network
    
    # 系统准备
    update_system
    install_dependencies
    check_python
    
    # 项目设置
    download_project
    setup_permissions
    create_directories
    check_disk_space
    
    # 启动程序
    if [ "${DEPS_ONLY:-false}" = "true" ]; then
        print_info "仅安装依赖模式"
        cd "$PROJECT_DIR"
        $PYTHON_CMD install_deps.py --mode simple
        print_success "依赖安装完成"
    else
        start_program
    fi
    
    print_success "脚本执行完成！"
    print_info "项目位置: $(pwd)/$PROJECT_DIR"
    print_info "日志目录: $(pwd)/logs"
    print_info "输出目录: $(pwd)/output"
}

# 脚本入口点
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
