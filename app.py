#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdaptVideo - DOOH影片尺寸轉換工具 (本地部署版)
模組化重構版本
"""

from flask import Flask
from flask_cors import CORS

from config import config
from routes import api
from routes_extended import api_extended

def create_app():
    """應用程式工廠函數"""
    app = Flask(__name__)
    CORS(app)
    
    # 初始化配置
    config.init_directories()
    
    # 註冊藍圖
    app.register_blueprint(api)
    app.register_blueprint(api_extended)
    
    return app

def main():
    """主函數"""
    app = create_app()
    
    print("🚀 使用 Flask 開發伺服器啟動 (除錯模式)")
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        use_reloader=False
    )

if __name__ == '__main__':
    main()