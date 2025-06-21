#!/usr/bin/env python3
"""快速重啟伺服器並測試比較功能"""

import time
import requests
from app import create_app

def test_routes_after_restart():
    """重啟後測試路由"""
    print("⏳ 等待伺服器啟動...")
    time.sleep(3)
    
    try:
        # 測試新路由
        response = requests.post(
            'http://127.0.0.1:5001/api/get_video_comparison_data',
            json={'file_id': 'test'},
            timeout=5
        )
        
        if response.status_code == 404:
            print("❌ 新路由仍未註冊")
            return False
        else:
            print("✅ 新路由已成功註冊")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到新伺服器")
        return False

def main():
    print("🚀 重啟 Flask 伺服器...")
    
    # 創建新的應用實例
    app = create_app()
    
    # 顯示已註冊的路由
    print("\n📋 已註冊的路由:")
    api_routes = []
    for rule in app.url_map.iter_rules():
        if 'api' in rule.rule or rule.rule.startswith('/uploads') or rule.rule.startswith('/outputs'):
            methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})
            api_routes.append(f"  {', '.join(methods):8} {rule.rule}")
    
    for route in sorted(api_routes):
        print(route)
    
    print(f"\n✅ 總共 {len(api_routes)} 個路由已註冊")
    
    # 檢查關鍵路由
    comparison_route_found = any('/api/get_video_comparison_data' in route for route in api_routes)
    static_routes_found = any('/uploads' in route or '/outputs' in route for route in api_routes)
    
    if comparison_route_found:
        print("✅ 影片比較路由已註冊")
    else:
        print("❌ 影片比較路由未找到")
        
    if static_routes_found:
        print("✅ 靜態檔案路由已註冊")
    else:
        print("❌ 靜態檔案路由未找到")
    
    print(f"\n🌐 啟動伺服器在 http://127.0.0.1:5001")
    print("現在可以測試影片比較功能了！")
    
    # 啟動伺服器
    app.run(debug=True, host='127.0.0.1', port=5001, use_reloader=False)

if __name__ == '__main__':
    main()