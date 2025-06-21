#!/usr/bin/env python3
"""診斷影片比較失敗的原因"""

import requests
import json
import os
from config import config
from database import get_video_data

def check_server_routes():
    """檢查伺服器路由是否正確註冊"""
    print("🔍 檢查伺服器路由...")
    
    try:
        # 測試基本路由
        response = requests.get('http://127.0.0.1:5001/api/templates', timeout=3)
        if response.status_code == 200:
            print("✅ 伺服器基本功能正常")
        else:
            print(f"❌ 伺服器基本功能異常: {response.status_code}")
            return False
            
        # 測試新的比較路由
        test_data = {'file_id': 'test'}
        response = requests.post(
            'http://127.0.0.1:5001/api/get_video_comparison_data',
            json=test_data,
            timeout=3
        )
        
        if response.status_code == 404:
            print("❌ 新的比較路由未註冊 - 需要重啟伺服器")
            return False
        elif response.status_code in [400, 500]:
            print("✅ 新的比較路由已註冊 (收到預期的錯誤響應)")
            return True
        else:
            print(f"⚠️  比較路由狀態碼: {response.status_code}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到伺服器")
        return False
    except Exception as e:
        print(f"❌ 檢查路由時發生錯誤: {e}")
        return False

def check_file_structure():
    """檢查檔案結構和權限"""
    print("\n🔍 檢查檔案結構...")
    
    # 檢查資料夾
    folders_to_check = [
        ('上傳資料夾', config.UPLOAD_FOLDER),
        ('輸出資料夾', config.OUTPUT_FOLDER)
    ]
    
    for name, folder in folders_to_check:
        if os.path.exists(folder):
            files = os.listdir(folder)
            print(f"✅ {name} 存在: {folder} ({len(files)} 個檔案)")
            
            # 顯示檔案列表
            if files:
                print(f"   檔案:")
                for f in files[:3]:
                    file_path = os.path.join(folder, f)
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    print(f"     {f} ({size_mb:.1f} MB)")
                if len(files) > 3:
                    print(f"     ... 還有 {len(files) - 3} 個檔案")
        else:
            print(f"❌ {name} 不存在: {folder}")

def check_database_data(file_id='24f5bb16-f264-4aac-a800-61d44e83b982'):
    """檢查資料庫中的檔案資料"""
    print(f"\n🔍 檢查資料庫資料 (file_id: {file_id})...")
    
    try:
        video_data = get_video_data(file_id)
        if video_data:
            print("✅ 找到影片資料")
            
            # 檢查關鍵欄位
            required_fields = ['original_path', 'video_info']
            for field in required_fields:
                if field in video_data:
                    print(f"   ✅ {field}: 存在")
                else:
                    print(f"   ❌ {field}: 缺少")
            
            # 檢查轉換記錄
            if 'converted_videos' in video_data:
                conversions = video_data['converted_videos']
                print(f"   ✅ 轉換記錄: {len(conversions)} 個")
                if conversions:
                    latest = conversions[-1]
                    print(f"     最新轉換: {latest.get('filename', '未知')}")
                    path = latest.get('path')
                    if path and os.path.exists(path):
                        print(f"     檔案存在: ✅")
                    else:
                        print(f"     檔案存在: ❌ ({path})")
            else:
                print(f"   ❌ 轉換記錄: 缺少")
                
        else:
            print("❌ 未找到影片資料")
            
    except Exception as e:
        print(f"❌ 檢查資料庫時發生錯誤: {e}")

def test_comparison_api_directly(file_id='24f5bb16-f264-4aac-a800-61d44e83b982'):
    """直接測試比較 API"""
    print(f"\n🧪 直接測試比較 API...")
    
    try:
        url = 'http://127.0.0.1:5001/api/get_video_comparison_data'
        data = {'file_id': file_id}
        
        print(f"請求 URL: {url}")
        print(f"請求資料: {data}")
        
        response = requests.post(url, json=data, timeout=10)
        print(f"響應狀態碼: {response.status_code}")
        print(f"響應標頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API 成功響應")
            
            # 檢查返回資料
            if 'original' in result and 'converted' in result:
                print("✅ 資料結構正確")
                
                # 測試影片 URL
                for video_type in ['original', 'converted']:
                    video_info = result[video_type]
                    video_url = f"http://127.0.0.1:5001{video_info['url']}"
                    
                    try:
                        video_response = requests.head(video_url, timeout=5)
                        if video_response.status_code == 200:
                            print(f"   ✅ {video_type} 影片 URL 可訪問: {video_info['url']}")
                        else:
                            print(f"   ❌ {video_type} 影片 URL 無法訪問: {video_info['url']} ({video_response.status_code})")
                    except Exception as e:
                        print(f"   ❌ {video_type} 影片 URL 測試失敗: {e}")
                        
            else:
                print("❌ 資料結構不正確")
                print(f"返回的鍵: {list(result.keys())}")
                
        else:
            print(f"❌ API 失敗 ({response.status_code})")
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    error_data = response.json()
                    print(f"錯誤訊息: {error_data}")
                except:
                    print(f"響應內容: {response.text}")
            else:
                print(f"響應內容: {response.text[:500]}")
                
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到伺服器")
    except Exception as e:
        print(f"❌ 測試 API 時發生錯誤: {e}")

def check_javascript_console():
    """提供檢查前端錯誤的指導"""
    print(f"\n🔍 前端診斷建議:")
    print("1. 開啟瀏覽器開發者工具 (F12)")
    print("2. 切換到 Console 標籤")
    print("3. 點擊「原始vs轉換對比」按鈕")
    print("4. 查看是否有 JavaScript 錯誤或網路請求失敗")
    print("5. 切換到 Network 標籤查看 API 請求狀態")

def main():
    print("🚨 診斷影片比較失敗原因")
    print("=" * 50)
    
    # 1. 檢查伺服器路由
    server_ok = check_server_routes()
    
    # 2. 檢查檔案結構
    check_file_structure()
    
    # 3. 檢查資料庫
    check_database_data()
    
    # 4. 測試 API
    if server_ok:
        test_comparison_api_directly()
    
    # 5. 前端診斷建議
    check_javascript_console()
    
    print("\n" + "=" * 50)
    print("🔧 可能的解決方案:")
    print("1. 如果路由未註冊 → 重啟 Flask 伺服器")
    print("2. 如果檔案不存在 → 重新上傳和轉換影片")
    print("3. 如果 API 錯誤 → 檢查伺服器日誌")
    print("4. 如果前端錯誤 → 檢查瀏覽器 Console")

if __name__ == '__main__':
    main()