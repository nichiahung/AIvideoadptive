#!/usr/bin/env python3
"""測試 API 端點"""

import requests
import json

def test_api():
    # 測試 generate_converted_preview API
    test_data = {'file_id': '24f5bb16-f264-4aac-a800-61d44e83b982'}
    url = 'http://127.0.0.1:5001/api/generate_converted_preview'

    print('🧪 測試 API 端點:', url)
    print('📤 發送數據:', test_data)

    try:
        response = requests.post(url, json=test_data, timeout=10)
        print('📥 響應狀態碼:', response.status_code)
        print('📥 響應標頭:', dict(response.headers))
        
        # 檢查響應內容類型
        content_type = response.headers.get('content-type', '')
        print('📥 內容類型:', content_type)
        
        if 'application/json' in content_type:
            try:
                json_data = response.json()
                print('📥 JSON 響應:', json_data)
            except:
                print('❌ 無法解析 JSON 響應')
                print('📥 原始響應:', response.text[:500])
        else:
            print('📥 非 JSON 響應 (前500字符):', response.text[:500])
        
    except requests.exceptions.ConnectionError:
        print('❌ 連接失敗 - Flask 伺服器可能未運行')
        print('💡 請確保 Flask 應用正在 http://127.0.0.1:5001 運行')
    except requests.exceptions.Timeout:
        print('❌ 請求超時')
    except Exception as e:
        print('❌ 請求錯誤:', str(e))

if __name__ == '__main__':
    test_api()