#!/usr/bin/env python3
"""檢查 Flask 應用程序的路由"""

from app import create_app

def main():
    app = create_app()
    print("=== 已註冊的 API 路由 ===")
    
    api_routes = []
    for rule in app.url_map.iter_rules():
        if 'api' in rule.rule:
            api_routes.append({
                'methods': sorted(rule.methods - {'HEAD', 'OPTIONS'}),
                'rule': rule.rule,
                'endpoint': rule.endpoint
            })
    
    # 按路由排序
    api_routes.sort(key=lambda x: x['rule'])
    
    for route in api_routes:
        methods_str = ', '.join(route['methods'])
        print(f"{methods_str:8} {route['rule']:35} -> {route['endpoint']}")
    
    print(f"\n總共找到 {len(api_routes)} 個 API 路由")
    
    # 特別檢查 generate_converted_preview 路由
    converted_preview_route = None
    for route in api_routes:
        if 'generate_converted_preview' in route['rule']:
            converted_preview_route = route
            break
    
    if converted_preview_route:
        print(f"\n✅ 找到 generate_converted_preview 路由:")
        print(f"   方法: {converted_preview_route['methods']}")
        print(f"   路徑: {converted_preview_route['rule']}")
        print(f"   端點: {converted_preview_route['endpoint']}")
    else:
        print("\n❌ 未找到 generate_converted_preview 路由!")

if __name__ == '__main__':
    main()