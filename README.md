# AdaptVideo 本地部署版 - 快速開始指南

## 🎯 系統需求

### Windows系統
- Windows 10 或更高版本
- Python 3.8 或更高版本
- 至少 2GB 可用磁碟空間

### macOS系統
- macOS 10.14 或更高版本
- Python 3.8 或更高版本
- 至少 2GB 可用磁碟空間

### Linux系統
- Ubuntu 18.04+ / CentOS 7+ 或其他主流發行版
- Python 3.8 或更高版本
- 至少 2GB 可用磁碟空間

## 🚀 一鍵安裝和啟動

### Windows用戶
1. 雙擊 `start_windows.bat` 檔案
2. 等待自動安裝完成
3. 瀏覽器會自動開啟 http://localhost:5000

### macOS/Linux用戶
1. 開啟終端機
2. 進入AdaptVideo目錄
3. 執行：`./start_unix.sh`
4. 在瀏覽器中訪問 http://localhost:5000

## 📁 檔案結構

```
adaptvideo-local-simple/
├── app.py                 # 主應用程式
├── requirements.txt       # Python依賴套件
├── start_windows.bat      # Windows啟動腳本
├── start_unix.sh         # macOS/Linux啟動腳本
├── uploads/              # 上傳檔案目錄
├── outputs/              # 轉換後檔案目錄
└── README.md             # 說明文檔
```

## 🎬 使用方法

1. **上傳影片**：拖拽或點擊選擇影片檔案
2. **選擇尺寸**：選擇目標DOOH尺寸（包含高雄版位3840×1526）
3. **開始轉換**：點擊轉換按鈕
4. **下載結果**：轉換完成後下載新影片

## 🔧 故障排除

### Python未安裝
- Windows：從 https://www.python.org/downloads/ 下載安裝
- macOS：使用 `brew install python3`
- Linux：使用 `sudo apt install python3 python3-pip`

### 套件安裝失敗
- 檢查網路連接
- 嘗試使用：`pip3 install --user -r requirements.txt`
- 更新pip：`pip3 install --upgrade pip`

### 服務無法啟動
- 檢查5000端口是否被占用
- 確認Python版本是否符合要求
- 查看錯誤訊息並重新安裝依賴

## 📞 技術支援

如遇到問題，請檢查：
1. Python版本是否正確
2. 網路連接是否正常
3. 磁碟空間是否充足
4. 防火牆是否阻擋5000端口

