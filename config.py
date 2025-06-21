"""
AdaptVideo 配置設定
"""
import os
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

class Config:
    """應用程式配置類別"""
    
    # 路徑設定
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
    OUTPUT_FOLDER = os.path.join(APP_ROOT, 'outputs')
    SHELVE_FILE = os.path.join(APP_ROOT, 'video_data.db')
    
    # 檔案限制
    MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    # API 設定
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 影片處理設定
    MAX_FRAMES_FOR_ANALYSIS = 90
    DEFAULT_JPEG_QUALITY = 75
    DEFAULT_PREVIEW_MAX_WIDTH = 300
    DEFAULT_CROP_PREVIEW_MAX_WIDTH = 250
    
    # DOOH 模板
    DOOH_TEMPLATES = [
        {"name": "高雄版位", "width": 3840, "height": 1526, "description": "高雄LED看板專用尺寸"},
        {"name": "忠孝商圈", "width": 1440, "height": 960, "description": "忠孝商圈數位看板"},
        {"name": "標準16:9", "width": 1920, "height": 1080, "description": "標準Full HD尺寸"},
        {"name": "4K橫屏", "width": 3840, "height": 2160, "description": "4K Ultra HD橫屏"},
        {"name": "豎屏9:16", "width": 1080, "height": 1920, "description": "手機豎屏比例"},
        {"name": "方形1:1", "width": 1080, "height": 1080, "description": "正方形顯示"},
        {"name": "超寬屏", "width": 2560, "height": 1080, "description": "21:9超寬屏幕"}
    ]
    
    # Flask 設定
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5001
    
    @classmethod
    def init_directories(cls):
        """初始化必要的目錄"""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.OUTPUT_FOLDER, exist_ok=True)

# 全域配置實例
config = Config()