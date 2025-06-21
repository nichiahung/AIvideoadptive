@echo off
chcp 65001 >nul
echo ========================================
echo    AdaptVideo 本地部署工具 (Windows)
echo ========================================
echo.

:: 檢查Python是否已安裝
echo [1/5] 檢查Python環境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 錯誤：未找到Python
    echo 請先安裝Python 3.8或更高版本
    echo 下載地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo ✅ Python已安裝

:: 檢查pip是否可用
echo.
echo [2/5] 檢查pip套件管理器...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 錯誤：pip不可用
    pause
    exit /b 1
)
echo ✅ pip可用

:: 安裝依賴套件
echo.
echo [3/5] 安裝必要套件...
echo 這可能需要幾分鐘時間，請耐心等待...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 錯誤：套件安裝失敗
    pause
    exit /b 1
)
echo ✅ 套件安裝完成

:: 創建必要目錄
echo.
echo [4/5] 創建工作目錄...
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
echo ✅ 目錄創建完成

:: 啟動應用
echo.
echo [5/5] 啟動AdaptVideo服務...
echo.
echo 🚀 AdaptVideo正在啟動...
echo 📱 請在瀏覽器中訪問：http://localhost:5000
echo 💡 按Ctrl+C可停止服務
echo.
python app.py

pause

