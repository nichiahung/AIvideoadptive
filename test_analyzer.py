import os
import sys
from app import analyze_video_with_llm, UPLOAD_FOLDER

def run_test():
    """
    獨立測試 analyze_video_with_llm 函式。
    """
    print("--- 開始獨立分析測試 ---")

    # 在 uploads 文件夾中尋找一個影片檔案
    test_video_filename = None
    for f in os.listdir(UPLOAD_FOLDER):
        if f.endswith((".mp4", ".mov", ".avi")):
            test_video_filename = f
            break

    if not test_video_filename:
        print("❌ 在 'uploads' 文件夾中找不到任何影片檔案 (.mp4, .mov, .avi) 可供測試。")
        sys.exit(1)

    video_path = os.path.join(UPLOAD_FOLDER, test_video_filename)
    print(f"📄 測試目標影片: {video_path}")

    if not os.path.exists(video_path):
        print(f"❌ 錯誤: 影片檔案不存在於路徑: {video_path}")
        sys.exit(1)

    try:
        print("\n▶️ 正在呼叫 analyze_video_with_llm...")
        # 為了看到詳細的錯誤，我們在這裡直接呼叫，並加上詳細的錯誤追蹤
        import traceback
        analysis_result = analyze_video_with_llm(video_path)
        
        print("\n--- 測試完成 ---")
        if analysis_result:
            print("✅ 分析成功！")
            print("🔍 結果:")
            import json
            print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
        else:
            print("⚠️ 分析完成，但沒有回傳任何結果。")
            print("   這可能表示 LLM 未能識別出任何主體，或是在過程中發生了非致命錯誤。")
            print("   請檢查 app.py 的日誌輸出以獲得更多線索。")

    except Exception as e:
        print("\n--- 測試失敗 ---")
        print("‼️ 在執行 anaylze_video_with_llm 時捕獲到一個致命錯誤:")
        traceback.print_exc()

if __name__ == '__main__':
    run_test() 