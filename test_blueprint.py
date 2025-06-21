#!/usr/bin/env python3
"""測試藍圖註冊"""

def test_blueprint_imports():
    print("=== 測試藍圖導入 ===")
    
    try:
        from routes_extended import api_extended
        print("✅ routes_extended 藍圖導入成功")
        print(f"藍圖名稱: {api_extended.name}")
        
        # 檢查藍圖中的路由
        print("\n藍圖中的路由:")
        for rule in api_extended.url_map.iter_rules():
            print(f"  {rule.methods} {rule.rule} -> {rule.endpoint}")
            
    except Exception as e:
        print(f"❌ routes_extended 藍圖導入失敗: {e}")
        import traceback
        traceback.print_exc()
        
    try:
        from routes import api
        print("✅ routes 藍圖導入成功")
        print(f"藍圖名稱: {api.name}")
    except Exception as e:
        print(f"❌ routes 藍圖導入失敗: {e}")
        import traceback
        traceback.print_exc()

def test_app_creation():
    print("\n=== 測試應用創建 ===")
    
    try:
        from app import create_app
        app = create_app()
        print("✅ 應用創建成功")
        
        # 檢查應用中的藍圖
        print("\n已註冊的藍圖:")
        for blueprint_name, blueprint in app.blueprints.items():
            print(f"  {blueprint_name}: {blueprint}")
            
    except Exception as e:
        print(f"❌ 應用創建失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_blueprint_imports()
    test_app_creation()