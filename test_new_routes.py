#!/usr/bin/env python3
"""直接測試新路由功能"""

from app import create_app
from flask import Flask
import json
import os

def test_comparison_route():
    """直接測試比較路由功能"""
    print("🧪 直接測試影片比較路由...")
    
    # 創建 Flask 應用
    app = create_app()
    
    with app.test_client() as client:
        # 測試影片比較資料端點
        test_data = {
            'file_id': '24f5bb16-f264-4aac-a800-61d44e83b982'
        }
        
        print(f"📤 測試資料: {test_data}")
        
        response = client.post(
            '/api/get_video_comparison_data',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"📥 響應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print("✅ 路由測試成功!")
            
            if data and 'original' in data and 'converted' in data:
                print("📊 返回資料結構正確:")
                
                original = data['original']
                print(f"  原始影片:")
                print(f"    URL: {original.get('url')}")
                print(f"    檔名: {original.get('filename')}")
                
                converted = data['converted']
                print(f"  轉換後影片:")
                print(f"    URL: {converted.get('url')}")
                print(f"    檔名: {converted.get('filename')}")
            else:
                print("❌ 資料結構不正確")
                print(f"返回資料: {data}")
        else:
            print(f"❌ 路由測試失敗")
            print(f"響應內容: {response.get_data(as_text=True)}")

def test_static_routes():
    """測試靜態檔案路由"""
    print("\n🧪 測試靜態檔案路由...")
    
    app = create_app()
    
    with app.test_client() as client:
        # 測試上傳檔案路由
        response = client.get('/uploads/test.mp4')
        print(f"📥 /uploads/test.mp4 狀態碼: {response.status_code}")
        
        # 測試輸出檔案路由
        response = client.get('/outputs/test.mp4')
        print(f"📥 /outputs/test.mp4 狀態碼: {response.status_code}")

def check_file_existence():
    """檢查測試檔案是否存在"""
    print("\n🔍 檢查測試檔案...")
    
    from config import config
    
    # 檢查上傳資料夾
    if os.path.exists(config.UPLOAD_FOLDER):
        files = os.listdir(config.UPLOAD_FOLDER)
        print(f"📂 上傳資料夾 ({config.UPLOAD_FOLDER}):")
        for f in files[:5]:  # 只顯示前5個
            print(f"   {f}")
        if len(files) > 5:
            print(f"   ... 還有 {len(files) - 5} 個檔案")
    else:
        print(f"❌ 上傳資料夾不存在: {config.UPLOAD_FOLDER}")
    
    # 檢查輸出資料夾
    if os.path.exists(config.OUTPUT_FOLDER):
        files = os.listdir(config.OUTPUT_FOLDER)
        print(f"📂 輸出資料夾 ({config.OUTPUT_FOLDER}):")
        for f in files[:5]:  # 只顯示前5個
            print(f"   {f}")
        if len(files) > 5:
            print(f"   ... 還有 {len(files) - 5} 個檔案")
    else:
        print(f"❌ 輸出資料夾不存在: {config.OUTPUT_FOLDER}")

if __name__ == '__main__':
    check_file_existence()
    test_comparison_route()
    test_static_routes()