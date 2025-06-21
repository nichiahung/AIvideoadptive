#!/usr/bin/env python3
"""測試影片比較功能"""

import requests
import json

def test_video_comparison_api():
    print("🎬 測試影片比較 API")
    
    # 測試獲取影片比較資料
    test_data = {'file_id': '24f5bb16-f264-4aac-a800-61d44e83b982'}
    url = 'http://127.0.0.1:5001/api/get_video_comparison_data'
    
    print(f"📤 測試 URL: {url}")
    print(f"📤 發送資料: {test_data}")
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        print(f"📥 響應狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API 成功響應")
            
            # 檢查返回資料結構
            if 'original' in data and 'converted' in data:
                print("📊 資料結構檢查:")
                
                original = data['original']
                print(f"  原始影片:")
                print(f"    URL: {original.get('url')}")
                print(f"    檔名: {original.get('filename')}")
                print(f"    尺寸: {original.get('info', {}).get('width')} x {original.get('info', {}).get('height')}")
                
                converted = data['converted']
                print(f"  轉換後影片:")
                print(f"    URL: {converted.get('url')}")
                print(f"    檔名: {converted.get('filename')}")
                print(f"    尺寸: {converted.get('info', {}).get('width')} x {converted.get('info', {}).get('height')}")
                
                # 測試影片 URL 是否可訪問
                print(f"\n🔗 測試影片 URL 訪問:")
                
                for name, video_data in [('原始', original), ('轉換後', converted)]:
                    video_url = f"http://127.0.0.1:5001{video_data.get('url')}"
                    try:
                        video_response = requests.head(video_url, timeout=5)
                        if video_response.status_code == 200:
                            print(f"  {name}影片 URL ✅ 可訪問: {video_url}")
                            content_length = video_response.headers.get('content-length')
                            if content_length:
                                size_mb = int(content_length) / (1024 * 1024)
                                print(f"    檔案大小: {size_mb:.1f} MB")
                        else:
                            print(f"  {name}影片 URL ❌ 無法訪問: {video_url} (狀態碼: {video_response.status_code})")
                    except Exception as e:
                        print(f"  {name}影片 URL ❌ 測試失敗: {e}")
                
            else:
                print("❌ 返回資料結構不正確")
                print(f"返回的鍵: {list(data.keys())}")
        else:
            print(f"❌ API 失敗，狀態碼: {response.status_code}")
            print(f"錯誤響應: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 連接失敗 - Flask 伺服器可能未運行")
    except Exception as e:
        print(f"❌ 測試錯誤: {e}")

if __name__ == '__main__':
    test_video_comparison_api()