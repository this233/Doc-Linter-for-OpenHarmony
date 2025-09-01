#!/bin/bash

# RAG API 服务器启动脚本

# 设置默认参数
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-8001}
RELOAD=${RELOAD:-"false"}

# 显示启动信息
echo "======================================"
echo "      启动 RAG API 服务器"
echo "======================================"
echo "主机地址: $HOST"
echo "端口号: $PORT"
echo "自动重载: $RELOAD"
echo "======================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查是否安装了依赖
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "⚠️  警告: 未检测到 fastapi，正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 检查是否存在必要的文件
if [ ! -f "RAG/rag_system.py" ]; then
    echo "❌ 错误: 未找到 RAG/rag_system.py 文件"
    exit 1
fi

if [ ! -f "RAG/rag_api.py" ]; then
    echo "❌ 错误: 未找到 RAG/rag_api.py 文件"
    exit 1
fi

# 启动服务器
echo "🚀 正在启动服务器..."

if [ "$RELOAD" = "true" ]; then
    python3 RAG/rag_api.py --host $HOST --port $PORT --reload
else
    python3 RAG/rag_api.py --host $HOST --port $PORT
fi 