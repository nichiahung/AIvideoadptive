#!/bin/bash

# AdaptVideo 本地部署工具 (macOS/Linux)
# 設置UTF-8編碼
export LANG=UTF-8
export LC_ALL=UTF-8

echo "========================================"
echo "   AdaptVideo 本地部署工具 (macOS/Linux)"
echo "========================================"
echo

# 檢查Python是否已安裝
echo "[1/5] 檢查Python環境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤：未找到Python3"
    echo "請先安裝Python 3.8或更高版本"
    echo "macOS: brew install python3"
    echo "Ubuntu: sudo apt install python3 python3-pip"
    echo "CentOS: sudo yum install python3 python3-pip"
    exit 1
fi

python3 --version
echo "✅ Python3已安裝"

# 檢查pip是否可用
echo
echo "[2/5] 檢查pip套件管理器..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ 錯誤：pip3不可用"
    echo "請安裝pip3套件管理器"
    exit 1
fi
echo "✅ pip3可用"

# 安裝依賴套件
echo
echo "[3/5] 安裝必要套件..."
echo "這可能需要幾分鐘時間，請耐心等待..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 錯誤：套件安裝失敗"
    echo "嘗試使用用戶模式安裝..."
    pip3 install --user -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 套件安裝仍然失敗，請檢查網路連接或Python環境"
        exit 1
    fi
fi
echo "✅ 套件安裝完成"

# 創建必要目錄
echo
echo "[4/5] 創建工作目錄..."
mkdir -p uploads
mkdir -p outputs
echo "✅ 目錄創建完成"

# 啟動應用
echo
echo "[5/5] 啟動AdaptVideo服務..."
echo
echo "🚀 AdaptVideo正在啟動..."
echo "📱 請在瀏覽器中訪問：http://localhost:5000"
echo "💡 按Ctrl+C可停止服務"
echo

python3 app.py

