#!/bin/bash
# Media Packer 一键安装和启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 显示横幅
show_banner() {
    echo -e "${BLUE}"
    echo "╭─────────────────────────────────────────────────╮"
    echo "│              Media Packer 安装器               │"
    echo "│          一键安装依赖和启动应用程序             │"
    echo "╰─────────────────────────────────────────────────╯"
    echo -e "${NC}"
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    echo -e "${GREEN}✓ 检测到操作系统: $OS${NC}"
}

# 检查Python
check_python() {
    echo "检查 Python 环境..."
    
    # 尝试不同的Python命令
    for cmd in python3 python; do
        if command -v $cmd &> /dev/null; then
            PYTHON_CMD=$cmd
            PYTHON_VERSION=$($cmd --version 2>&1)
            echo -e "${GREEN}✓ 找到 Python: $PYTHON_VERSION${NC}"
            
            # 检查版本
            VERSION_CHECK=$($cmd -c "import sys; print(sys.version_info >= (3, 8))")
            if [ "$VERSION_CHECK" = "True" ]; then
                echo -e "${GREEN}✓ Python 版本满足要求 (>= 3.8)${NC}"
                return 0
            else
                echo -e "${RED}✗ Python 版本过低，需要 3.8 或更高版本${NC}"
                return 1
            fi
        fi
    done
    
    echo -e "${RED}✗ 未找到 Python，请先安装 Python 3.8+${NC}"
    return 1
}

# 检查pip
check_pip() {
    echo "检查 pip..."
    if $PYTHON_CMD -m pip --version &> /dev/null; then
        echo -e "${GREEN}✓ pip 可用${NC}"
        return 0
    else
        echo -e "${RED}✗ pip 不可用${NC}"
        return 1
    fi
}

# 安装依赖
install_dependencies() {
    echo "使用依赖安装脚本..."
    
    echo "请选择安装模式:"
    echo "1. 简化版 (推荐) - 只安装基础依赖"
    echo "2. 完整版 - 安装所有依赖"
    
    while true; do
        read -p "请输入选择 (1-2): " choice
        case $choice in
            1)
                MODE="simple"
                break
                ;;
            2)
                MODE="full"
                break
                ;;
            *)
                echo "请输入有效的选择 (1-2)"
                ;;
        esac
    done
    
    echo -e "${YELLOW}正在安装 $MODE 模式的依赖...${NC}"
    
    if $PYTHON_CMD install_deps.py --mode $MODE; then
        echo -e "${GREEN}✓ 依赖安装成功${NC}"
        return 0
    else
        echo -e "${RED}✗ 依赖安装失败${NC}"
        return 1
    fi
}

# 启动应用
start_application() {
    echo -e "${BLUE}启动 Media Packer...${NC}"
    $PYTHON_CMD start.py
}

# 主函数
main() {
    show_banner
    
    echo "开始检查系统环境..."
    
    # 检测系统
    detect_os
    
    # 检查Python
    if ! check_python; then
        echo -e "${RED}Python 环境检查失败，请先安装 Python 3.8+${NC}"
        exit 1
    fi
    
    # 检查pip
    if ! check_pip; then
        echo -e "${RED}pip 检查失败，请确保 pip 可用${NC}"
        exit 1
    fi
    
    # 询问是否安装依赖
    echo ""
    read -p "是否需要安装/更新依赖? (y/n): " install_deps
    
    if [[ $install_deps =~ ^[Yy]$ ]]; then
        if ! install_dependencies; then
            echo -e "${RED}依赖安装失败，退出${NC}"
            exit 1
        fi
    fi
    
    # 启动应用
    echo ""
    start_application
}

# 运行主函数
main "$@"
