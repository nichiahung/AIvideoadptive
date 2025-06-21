#!/usr/bin/env python3
"""深度診斷載入影片比較失敗的問題"""

import requests
import json
import os
import time

def test_server_status():
    """測試伺服器狀態"""
    print("🔍 測試伺服器狀態...")
    
    endpoints_to_test = [
        ('GET', '/api/templates', None),
        ('POST', '/api/get_video_comparison_data', {'file_id': '24f5bb16-f264-4aac-a800-61d44e83b982'}),
        ('GET', '/uploads/24f5bb16-f264-4aac-a800-61d44e83b982_original.mp4', None),
        ('GET', '/outputs/24f5bb16-f264-4aac-a800-61d44e83b982_converted.mp4', None),
    ]
    
    base_url = 'http://127.0.0.1:5001'
    
    for method, path, data in endpoints_to_test:
        url = f"{base_url}{path}"
        print(f"\n📡 測試 {method} {path}")
        
        try:
            if method == 'GET':
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=10)
            
            print(f"   狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ 成功")
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        json_data = response.json()
                        if path == '/api/get_video_comparison_data':
                            # 詳細檢查比較資料
                            print(f"   📊 比較資料:")
                            if 'original' in json_data:
                                orig = json_data['original']
                                print(f"     原始影片: {orig.get('filename')}")
                                print(f"     原始 URL: {orig.get('url')}")
                                print(f"     原始尺寸: {orig.get('info', {}).get('width')}x{orig.get('info', {}).get('height')}")
                            if 'converted' in json_data:
                                conv = json_data['converted']
                                print(f"     轉換影片: {conv.get('filename')}")
                                print(f"     轉換 URL: {conv.get('url')}")
                                print(f"     轉換尺寸: {conv.get('info', {}).get('width')}x{conv.get('info', {}).get('height')}")
                        else:
                            print(f"   📄 JSON 響應 (前100字符): {str(json_data)[:100]}...")
                    except Exception as e:
                        print(f"   ⚠️  JSON 解析錯誤: {e}")
                elif 'video' in content_type or 'octet-stream' in content_type:
                    size = len(response.content)
                    print(f"   📹 影片檔案大小: {size / (1024*1024):.1f} MB")
                else:
                    print(f"   📄 內容類型: {content_type}")
            else:
                print(f"   ❌ 失敗 ({response.status_code})")
                if response.status_code == 404:
                    print("   💡 可能原因: 路由未註冊或檔案不存在")
                elif response.status_code == 500:
                    print("   💡 可能原因: 伺服器內部錯誤")
                    print(f"   📄 錯誤內容: {response.text[:200]}")
                else:
                    print(f"   📄 響應內容: {response.text[:200]}")
                    
        except requests.exceptions.ConnectionError:
            print("   ❌ 連接失敗 - 伺服器可能未運行")
        except requests.exceptions.Timeout:
            print("   ❌ 請求超時")
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")

def check_browser_console_simulation():
    """模擬瀏覽器中可能發生的錯誤"""
    print("\n🌐 模擬前端請求...")
    
    # 模擬前端的完整請求流程
    file_id = '24f5bb16-f264-4aac-a800-61d44e83b982'
    
    try:
        # 1. 模擬 showVideoComparison 函數的請求
        url = 'http://127.0.0.1:5001/api/get_video_comparison_data'
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        data = {'file_id': file_id}
        
        print(f"📤 發送請求:")
        print(f"   URL: {url}")
        print(f"   Headers: {headers}")
        print(f"   Data: {data}")
        
        response = requests.post(url, json=data, headers=headers, timeout=15)
        
        print(f"📥 收到響應:")
        print(f"   狀態碼: {response.status_code}")
        print(f"   響應標頭: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ JSON 解析成功")
            
            # 檢查前端所需的資料結構
            required_fields = ['original', 'converted']
            for field in required_fields:
                if field in result:
                    video_data = result[field]
                    print(f"   ✅ {field}:")
                    print(f"     - url: {video_data.get('url')}")
                    print(f"     - filename: {video_data.get('filename')}")
                    print(f"     - info: {bool(video_data.get('info'))}")
                    
                    # 檢查 info 中的必要欄位
                    info = video_data.get('info', {})
                    if info:
                        print(f"     - width: {info.get('width')}")
                        print(f"     - height: {info.get('height')}")
                        print(f"     - duration: {info.get('duration')}")
                else:
                    print(f"   ❌ 缺少 {field} 欄位")
                    
        else:
            print(f"   ❌ 請求失敗")
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    error_data = response.json()
                    print(f"   錯誤訊息: {error_data}")
                except:
                    print(f"   原始響應: {response.text}")
            else:
                print(f"   原始響應: {response.text[:300]}")
                
    except Exception as e:
        print(f"❌ 模擬請求失敗: {e}")

def check_javascript_variables():
    """檢查可能的 JavaScript 變數問題"""
    print("\n🔧 JavaScript 變數檢查建議:")
    print("在瀏覽器 Console 中執行以下命令來檢查:")
    print("1. console.log('fileId:', window.getGlobalVar ? window.getGlobalVar('fileId') : 'getGlobalVar not found');")
    print("2. console.log('convertedFileId:', window.convertedFileId);")
    print("3. console.log('AdaptVideoAPI:', typeof window.AdaptVideoAPI);")
    print("4. console.log('showVideoComparison:', typeof window.AdaptVideoAPI?.showVideoComparison);")
    
def provide_frontend_debug_code():
    """提供前端除錯代碼"""
    print("\n💻 前端除錯代碼 - 在瀏覽器 Console 中執行:")
    
    debug_code = """
// 測試比較功能
async function debugComparison() {
    console.log('=== 除錯影片比較功能 ===');
    
    // 1. 檢查全域變數
    const fileId = window.getGlobalVar ? window.getGlobalVar('fileId') : null;
    console.log('FileId:', fileId);
    console.log('ConvertedFileId:', window.convertedFileId);
    
    if (!fileId) {
        console.error('❌ FileId 不存在');
        return;
    }
    
    // 2. 直接測試 API
    try {
        console.log('📤 發送 API 請求...');
        const response = await fetch('/api/get_video_comparison_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: fileId })
        });
        
        console.log('📥 API 響應狀態:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API 資料:', data);
            
            // 3. 測試影片 URL
            if (data.original && data.converted) {
                console.log('🎬 測試影片 URL...');
                
                for (const [type, video] of Object.entries(data)) {
                    const testResponse = await fetch(video.url, { method: 'HEAD' });
                    console.log(`${type} 影片 (${video.url}):`, testResponse.status);
                }
            }
        } else {
            const errorText = await response.text();
            console.error('❌ API 錯誤:', errorText);
        }
    } catch (error) {
        console.error('❌ 請求失敗:', error);
    }
}

// 執行除錯
debugComparison();
"""
    
    print(debug_code)

def main():
    print("🔍 深度診斷載入影片比較失敗問題")
    print("=" * 60)
    
    # 1. 測試伺服器狀態
    test_server_status()
    
    # 2. 模擬前端請求
    check_browser_console_simulation()
    
    # 3. JavaScript 變數檢查
    check_javascript_variables()
    
    # 4. 前端除錯代碼
    provide_frontend_debug_code()
    
    print("\n" + "=" * 60)
    print("🎯 除錯步驟總結:")
    print("1. 確認上面的伺服器測試都通過")
    print("2. 在瀏覽器中打開開發者工具 (F12)")
    print("3. 複製上面的除錯代碼到 Console 執行")
    print("4. 查看具體的錯誤訊息")
    print("5. 如果仍有問題，請提供 Console 的錯誤訊息")

if __name__ == '__main__':
    main()