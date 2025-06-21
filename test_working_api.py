#!/usr/bin/env python3
"""測試不同的 API 端點"""

import requests
import json

def test_multiple_endpoints():
    endpoints_to_test = [
        # 測試一個我們知道存在且工作的端點
        {
            'name': 'get_templates',
            'url': 'http://127.0.0.1:5001/api/templates',
            'method': 'GET'
        },
        # 測試 generate_original_preview (應該工作)
        {
            'name': 'generate_original_preview',
            'url': 'http://127.0.0.1:5001/api/generate_original_preview',
            'method': 'POST',
            'data': {'file_id': '24f5bb16-f264-4aac-a800-61d44e83b982'}
        },
        # 測試有問題的端點
        {
            'name': 'generate_converted_preview',
            'url': 'http://127.0.0.1:5001/api/generate_converted_preview',
            'method': 'POST',
            'data': {'file_id': '24f5bb16-f264-4aac-a800-61d44e83b982'}
        },
        # 測試調試端點
        {
            'name': 'debug_conversions',
            'url': 'http://127.0.0.1:5001/api/debug_conversions/24f5bb16-f264-4aac-a800-61d44e83b982',
            'method': 'GET'
        }
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 測試 {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        print(f"   方法: {endpoint['method']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'], timeout=5)
            else:
                response = requests.post(endpoint['url'], json=endpoint.get('data', {}), timeout=5)
            
            print(f"   狀態碼: {response.status_code}")
            content_type = response.headers.get('content-type', '')
            print(f"   內容類型: {content_type}")
            
            if response.status_code == 200:
                print("   ✅ 成功")
                if 'application/json' in content_type:
                    try:
                        json_data = response.json()
                        if isinstance(json_data, dict) and len(str(json_data)) < 200:
                            print(f"   響應: {json_data}")
                        else:
                            print(f"   響應: (太大，不顯示完整內容)")
                    except:
                        print("   響應: (無法解析 JSON)")
            else:
                print("   ❌ 失敗")
                if 'text/html' in content_type:
                    print("   響應: HTML 404 頁面")
                else:
                    print(f"   響應: {response.text[:100]}")
                    
        except requests.exceptions.ConnectionError:
            print("   ❌ 連接失敗")
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")

if __name__ == '__main__':
    test_multiple_endpoints()