#!/usr/bin/env python3
"""檢查 Python 檔案語法"""

import py_compile
import traceback

def check_file_syntax(filename):
    print(f"檢查 {filename} 語法...")
    try:
        py_compile.compile(filename, doraise=True)
        print(f"✅ {filename} 語法檢查通過")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ {filename} 語法錯誤:")
        print(e)
        return False
    except Exception as e:
        print(f"❌ {filename} 檢查時發生錯誤:")
        print(e)
        traceback.print_exc()
        return False

def test_import(module_name):
    print(f"\n測試導入 {module_name}...")
    try:
        __import__(module_name)
        print(f"✅ {module_name} 導入成功")
        return True
    except Exception as e:
        print(f"❌ {module_name} 導入失敗:")
        print(e)
        traceback.print_exc()
        return False

if __name__ == '__main__':
    files_to_check = ['routes_extended.py', 'routes.py', 'app.py']
    
    all_syntax_ok = True
    for filename in files_to_check:
        if not check_file_syntax(filename):
            all_syntax_ok = False
    
    if all_syntax_ok:
        print("\n=== 測試模組導入 ===")
        test_import('routes_extended')
        test_import('routes')
        test_import('app')