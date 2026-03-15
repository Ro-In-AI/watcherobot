#!/bin/bash
# Watcher Server 启动脚本 (Linux/Mac)

echo "========================================"
echo "  Watcher Server 启动脚本"
echo "========================================"
echo ""

# 检查conda是否可用
if ! command -v conda &> /dev/null; then
    echo "[错误] 未找到conda，请先安装Miniconda或Anaconda"
    exit 1
fi

# 激活conda环境
echo "[1/3] 激活conda环境: watcher-server..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate watcher-server

if [ $? -ne 0 ]; then
    echo "[错误] 环境 watcher-server 不存在"
    echo "请先运行: conda env create -f environment.yml"
    exit 1
fi

# 检查.env文件
echo "[2/3] 检查配置文件..."
if [ ! -f .env ]; then
    echo "[警告] .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
    echo "[提示] 请编辑 .env 文件填入实际配置"
fi

# 启动服务
echo "[3/3] 启动服务..."
echo ""
python src/main.py
