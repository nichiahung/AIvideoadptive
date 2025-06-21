#!/usr/bin/env python3
"""詳細調試路由註冊"""

import sys
import traceback

def debug_blueprint_registration():
    print("=== 調試藍圖註冊過程 ===")
    
    # 1. 逐步導入和檢查
    try:
        print("1. 導入 routes_extended...")
        from routes_extended import api_extended
        print("   ✅ 成功")
        
        print("2. 檢查藍圖的基本屬性...")
        print(f"   藍圖名稱: {api_extended.name}")
        print(f"   藍圖 URL 前綴: {api_extended.url_prefix}")
        
        print("3. 嘗試訪問藍圖的內部函數...")
        # 檢查函數是否存在
        import routes_extended
        functions_to_check = [
            'generate_original_preview',  # 這個工作
            'generate_converted_preview', # 這個不工作
            'debug_conversions',          # 這個不工作
            'test_converted_preview'      # 這個不工作
        ]
        
        for func_name in functions_to_check:
            if hasattr(routes_extended, func_name):
                func = getattr(routes_extended, func_name)
                print(f"   ✅ 找到函數 {func_name}: {func}")
            else:
                print(f"   ❌ 未找到函數 {func_name}")
        
    except Exception as e:
        print(f"   ❌ 導入失敗: {e}")
        traceback.print_exc()
        return
    
    # 2. 檢查應用註冊
    try:
        print("\n4. 創建 Flask 應用並註冊藍圖...")
        from flask import Flask
        from flask_cors import CORS
        
        app = Flask(__name__)
        CORS(app)
        
        # 檢查註冊前
        print(f"   註冊前的路由數量: {len(list(app.url_map.iter_rules()))}")
        
        # 註冊藍圖
        app.register_blueprint(api_extended)
        
        # 檢查註冊後
        all_rules = list(app.url_map.iter_rules())
        print(f"   註冊後的路由數量: {len(all_rules)}")
        
        # 檢查特定路由
        extended_routes = [rule for rule in all_rules if 'api_extended' in rule.endpoint]
        print(f"   來自 api_extended 的路由數量: {len(extended_routes)}")
        
        print("\n   詳細的 api_extended 路由:")
        for rule in extended_routes:
            methods = sorted(rule.methods - {'HEAD', 'OPTIONS'})
            print(f"     {methods} {rule.rule} -> {rule.endpoint}")
        
        # 檢查問題路由是否存在
        problem_routes = [
            '/api/generate_converted_preview',
            '/api/debug_conversions/<file_id>',
            '/api/test_converted_preview'
        ]
        
        print(f"\n   檢查問題路由:")
        for problem_route in problem_routes:
            found = any(rule.rule == problem_route for rule in all_rules)
            print(f"     {problem_route}: {'✅ 存在' if found else '❌ 不存在'}")
        
    except Exception as e:
        print(f"   ❌ 應用註冊失敗: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    debug_blueprint_registration()