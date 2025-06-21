#!/usr/bin/env python3
"""直接測試 API 端點"""

import requests

def test_all_endpoints():
    """測試所有端點"""
    base_url = 'http://127.0.0.1:5001'
    
    endpoints_to_test = [
        # 確認工作的端點
        ('GET', '/api/templates'),
        # 新的端點
        ('POST', '/api/get_video_comparison_data', {'file_id': '24f5bb16-f264-4aac-a800-61d44e83b982'}),
        # 靜態檔案端點
        ('GET', '/uploads/'),
        ('GET', '/outputs/'),
    ]
    
    for test in endpoints_to_test:
        method = test[0]
        path = test[1]
        data = test[2] if len(test) > 2 else None
        
        url = f"{base_url}{path}"
        print(f"\n🧪 測試 {method} {path}")
        
        try:
            if method == 'GET':
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, json=data, timeout=5)
            
            print(f"   狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ 成功")
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        json_data = response.json()
                        if isinstance(json_data, dict) and len(str(json_data)) < 100:
                            print(f"   響應: {json_data}")
                        else:
                            print("   響應: JSON 資料 (太大，不顯示)")
                    except:
                        print("   響應: 無法解析 JSON")
                elif 'text/html' in content_type:
                    if len(response.text) < 200:
                        print(f"   響應: {response.text}")
                    else:
                        print("   響應: HTML 內容")
            elif response.status_code == 404:
                print("   ❌ 404 Not Found")
            elif response.status_code == 400:
                print("   ❌ 400 Bad Request")
                print(f"   響應: {response.text[:200]}")
            else:
                print(f"   ❌ 錯誤 {response.status_code}")
                print(f"   響應: {response.text[:200]}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ 連接失敗")
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")

if __name__ == '__main__':
    test_all_endpoints()