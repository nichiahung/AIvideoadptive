#!/usr/bin/env python3
"""重新啟動 Flask 伺服器"""

import subprocess
import time
import sys
import requests

def check_server_running():
    """檢查伺服器是否正在運行"""
    try:
        response = requests.get('http://127.0.0.1:5001/api/templates', timeout=2)
        return response.status_code == 200
    except:
        return False

def main():
    print("🔄 重新啟動 Flask 伺服器...")
    
    # 檢查伺服器狀態
    if check_server_running():
        print("⚠️  伺服器仍在運行，請手動停止舊的伺服器進程")
        print("💡 在命令行中按 Ctrl+C 停止舊伺服器，然後重新運行此腳本")
        return
    
    print("✅ 舊伺服器已停止")
    
    # 啟動新伺服器
    print("🚀 啟動新伺服器...")
    from app import create_app
    
    app = create_app()
    
    # 顯示所有路由
    print("\n註冊的路由:")
    routes = []
    for rule in app.url_map.iter_rules():
        if 'api' in rule.rule or rule.rule.startswith('/uploads') or rule.rule.startswith('/outputs'):
            methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})
            routes.append({
                'methods': methods,
                'rule': rule.rule,
                'endpoint': rule.endpoint
            })
    
    routes.sort(key=lambda x: x['rule'])
    for route in routes:
        methods_str = ', '.join(route['methods'])
        print(f"  {methods_str:8} {route['rule']:35} -> {route['endpoint']}")
    
    print(f"\n總共 {len(routes)} 個路由")
    
    # 檢查新路由
    comparison_route = next((r for r in routes if 'get_video_comparison_data' in r['rule']), None)
    if comparison_route:
        print(f"\n✅ 找到影片比較路由: {comparison_route['rule']}")
    else:
        print(f"\n❌ 未找到影片比較路由")
    
    print(f"\n🚀 伺服器啟動中... http://127.0.0.1:5001")
    print("按 Ctrl+C 停止伺服器")
    
    # 啟動伺服器
    app.run(debug=True, host='127.0.0.1', port=5001, use_reloader=False)

if __name__ == '__main__':
    main()