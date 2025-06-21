#!/usr/bin/env python3
"""啟動 Flask 伺服器並顯示所有註冊的路由"""

from app import create_app

def main():
    print("=== 啟動 AdaptVideo Flask 伺服器 ===")
    
    # 創建應用
    app = create_app()
    
    # 顯示所有路由
    print("\n註冊的路由:")
    routes = []
    for rule in app.url_map.iter_rules():
        if 'api' in rule.rule:
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
    
    print(f"\n總共 {len(routes)} 個 API 路由")
    
    # 特別檢查問題路由
    problem_routes = [
        '/api/generate_converted_preview',
        '/api/debug_conversions/<file_id>',
        '/api/test_converted_preview'
    ]
    
    print("\n檢查問題路由:")
    for problem_route in problem_routes:
        found = any(route['rule'] == problem_route for route in routes)
        print(f"  {problem_route}: {'✅ 已註冊' if found else '❌ 未註冊'}")
    
    print(f"\n🚀 伺服器啟動中... http://127.0.0.1:5001")
    print("按 Ctrl+C 停止伺服器")
    
    # 啟動伺服器
    app.run(debug=True, host='127.0.0.1', port=5001, use_reloader=False)

if __name__ == '__main__':
    main()