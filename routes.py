"""
AdaptVideo API 路由
"""
import os
import base64
import traceback
from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, send_from_directory
from PIL import Image, ImageDraw

from config import config
from utils import (
    find_video_file, validate_json_request, generate_unique_filename,
    validate_file_type, validate_file_size, format_error_response,
    format_success_response
)
from video_processing import (
    get_video_info, extract_thumbnail, analyze_video_with_llm,
    extract_frames_generic, apply_smart_crop, crop_frame_for_thumbnail,
    perform_video_conversion
)
from database import (
    get_video_data, update_video_data, save_video_data, get_all_videos,
    add_conversion_record, save_llm_analysis, calculate_multi_subject_center_backend,
    video_exists
)

# 創建藍圖
api = Blueprint('api', __name__)

@api.route('/')
def index():
    """主頁"""
    return render_template('index.html')

@api.route('/api/templates')
def get_templates():
    """獲取 DOOH 模板列表"""
    return jsonify(config.DOOH_TEMPLATES)

@api.route('/api/upload', methods=['POST'])
def upload_video():
    """上傳影片"""
    if 'video' not in request.files:
        return format_error_response("沒有選擇檔案")
    
    file = request.files['video']
    if file.filename == '':
        return format_error_response("沒有選擇檔案")

    # 驗證檔案類型
    if not validate_file_type(file.filename):
        return format_error_response("不支援的檔案類型")

    # 生成檔案名稱和路徑
    upload_filename, file_id = generate_unique_filename(file.filename)
    upload_path = os.path.join(config.UPLOAD_FOLDER, upload_filename)
    
    # 保存檔案
    file.save(upload_path)
    
    # 驗證檔案大小
    if not validate_file_size(upload_path):
        os.remove(upload_path)
        max_size_mb = config.MAX_FILE_SIZE / (1024 * 1024)
        return format_error_response(f"檔案大小超過 {max_size_mb}MB 限制")
    
    # 使用絕對路徑以增加 OpenCV 的穩定性
    abs_upload_path = os.path.abspath(upload_path)

    # 獲取影片資訊和縮圖
    video_info = get_video_info(abs_upload_path)
    thumbnail = extract_thumbnail(abs_upload_path)
    
    # 保存到資料庫
    video_data = {
        "original_path": upload_path,  # 儲存相對路徑以保持可攜性
        "original_filename": file.filename,
        "video_info": video_info,
        "thumbnail_b64": thumbnail
    }
    save_video_data(file_id, video_data)

    return jsonify({
        "file_id": file_id,
        "video_info": video_info,
        "thumbnail": thumbnail
    })

@api.route('/api/analyze', methods=['POST'])
@validate_json_request(['file_id'])
def analyze_video_api():
    """分析影片並返回 LLM 分析結果"""
    data = request.get_json()
    file_id = data['file_id']
    conversation_history = data.get('conversation_history', [])

    # 檢查影片是否存在
    video_record = get_video_data(file_id)
    if not video_record:
        return format_error_response("找不到檔案", 404)

    video_path = video_record['original_path']
    if not os.path.exists(video_path):
        return format_error_response("影片檔案不存在", 404)
    
    video_info = video_record.get('video_info', {})
    
    # 使用 LLM 分析影片
    analysis_result = analyze_video_with_llm(
        video_path, conversation_history, 
        video_info.get('width'), video_info.get('height')
    )
    
    if not analysis_result:
        return format_error_response("AI分析影片時發生錯誤", 500)
        
    # 確保 analysis_options 存在
    if 'analysis_options' not in analysis_result:
        analysis_result['analysis_options'] = []

    # 為每個分析選項生成縮圖
    if video_info.get('width', 0) > 0 and video_info.get('height', 0) > 0:
        for option in analysis_result.get('analysis_options', []):
            center = option.get('center')
            if center:
                # 假設box是相對於原始影片尺寸
                box_size = 200  # 縮圖大小
                x, y = center
                
                # 確保裁切框在影片範圍內
                x1 = max(0, int(x - box_size / 2))
                y1 = max(0, int(y - box_size / 2))
                x2 = min(video_info['width'], int(x + box_size / 2))
                y2 = min(video_info['height'], int(y + box_size / 2))
                
                box = (x1, y1, x2, y2)
                thumbnail_b64 = crop_frame_for_thumbnail(video_path, box)
                option['thumbnail'] = thumbnail_b64

    # 保存分析結果到資料庫
    save_llm_analysis(file_id, analysis_result)
    print(f"✅ 已將 LLM 分析結果儲存至資料庫: {file_id}")

    return jsonify(analysis_result)

@api.route('/api/uploaded_videos', methods=['GET'])
def get_uploaded_videos():
    """獲取已上傳影片的列表"""
    videos = get_all_videos()
    return jsonify(videos)

@api.route('/api/convert', methods=['POST'])
@validate_json_request(['file_id', 'width', 'height'])
def convert_video_api():
    """處理影片轉換請求"""
    print("--- 收到 /api/convert 請求 ---")
    print(f"請求標頭 (Headers): {request.headers}")

    data = request.json
    file_id = data.get('file_id')
    target_width = data.get('width')
    target_height = data.get('height')
    crop_mode = data.get('crop_mode', 'center')
    selected_subject_centers = data.get('centers')  # 支援多個中心點
    selected_subject_center = data.get('center')    # 向後相容單一中心點

    print(f"收到轉換請求: file_id={file_id}, mode={crop_mode}, centers={selected_subject_centers}, center={selected_subject_center}")

    # 找到原始檔案
    upload_path = find_video_file(file_id)
    if not upload_path:
        return format_error_response(f"找不到 file_id 為 {file_id} 的原始檔案", 404)
    
    original_file_ext = os.path.splitext(upload_path)[1]
    output_filename = f"{file_id}_converted{original_file_ext}"
    output_path = os.path.join(config.OUTPUT_FOLDER, output_filename)
    
    # 處理中心點選擇
    manual_center = None
    if crop_mode == 'llm':
        # 優先使用多個中心點，如果沒有則使用單一中心點
        if selected_subject_centers and len(selected_subject_centers) > 0:
            # 計算多個主體的加權中心點
            manual_center = calculate_multi_subject_center_backend(selected_subject_centers, file_id)
            print(f"🎯 計算多主體中心點: {manual_center}")
        elif selected_subject_center:
            manual_center = tuple(selected_subject_center)
            print(f"🎯 使用單一主體中心點: {manual_center}")
        else:
            # 如果使用者選了LLM但沒有選主體，就退回到標準置中
            print("⚠️ LLM模式下未提供中心點，將退回至中心裁切。")
            crop_mode = 'center'
    
    print(f"🚀 開始轉換: input={os.path.basename(upload_path)}, output={output_filename}, mode={crop_mode}, center={manual_center}")
    
    # 執行轉換
    perform_video_conversion(
        input_path=upload_path,
        output_path=output_path,
        target_width=int(target_width),
        target_height=int(target_height),
        crop_mode=crop_mode,
        manual_center=manual_center
    )

    # 檢查轉換結果
    if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
        print(f"❌ 轉換後檔案不存在或檔案過小: {output_path}")
        return format_error_response("影片轉換失敗，請檢查伺服器日誌以了解詳情。", 500)
        
    # 更新資料庫
    conversion_data = {
        "original_path": upload_path,
        "converted_path": output_path,
        "converted_filename": output_filename
    }
    
    # 添加轉換記錄
    add_conversion_record(file_id, {
        "path": output_path,
        "filename": os.path.basename(output_path),
        "template_name": f"{target_width}x{target_height}"
    })
    
    print(f"✅ 已將影片轉換資料儲存至資料庫: {file_id}")

    return format_success_response({
        "file_id": file_id,
        "download_url": f"/outputs/{output_filename}",
        "filename": output_filename
    })

@api.route('/api/preview_crop', methods=['POST'])
@validate_json_request(['thumbnail_data', 'target_width', 'target_height', 'original_width', 'original_height', 'center'])
def preview_crop():
    """產生裁切預覽圖"""
    data = request.json
    base64_image = data.get('thumbnail_data')
    target_width = data.get('target_width')
    target_height = data.get('target_height')
    original_width = data.get('original_width')
    original_height = data.get('original_height')
    center = data.get('center')
    centers = data.get('centers')  # 支援多個中心點
    file_id = data.get('file_id')  # 需要 file_id 來計算多主體中心點

    # 處理多選中心點
    if centers and len(centers) > 0 and file_id:
        center = calculate_multi_subject_center_backend(centers, file_id)
        if center:
            center = list(center)  # 轉換為列表格式

    try:
        # 解碼圖片
        image_data = base64.b64decode(base64_image.split(',')[1])
        img = Image.open(BytesIO(image_data))

        # 使用共用的智慧裁切函數
        cropped_img, is_subject_cropped = apply_smart_crop(
            img, target_width, target_height, center,
            original_width=original_width, original_height=original_height
        )
        
        # 如果主角被裁切，疊加一個紅色警告圖層
        if is_subject_cropped:
            overlay = Image.new('RGBA', cropped_img.size, (255, 0, 0, 0))  # 透明
            draw = ImageDraw.Draw(overlay)
            draw.rectangle([(0, 0), (cropped_img.width, cropped_img.height)], 
                          outline=(255, 80, 80, 200), width=10)  # 紅色邊框
            cropped_img = Image.alpha_composite(cropped_img.convert("RGBA"), overlay)

        # 將結果轉回 Base64
        buffered = BytesIO()
        cropped_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return jsonify({
            "preview_image": f"data:image/png;base64,{img_str}",
            "is_cropped": is_subject_cropped
        })

    except Exception as e:
        print(f"❌ 預覽裁切失敗: {e}")
        traceback.print_exc()
        return format_error_response("產生預覽圖失敗", 500)

@api.route('/uploads/<path:filename>')
def serve_upload_video(filename):
    """提供原始上傳的影片檔案"""
    return send_from_directory(config.UPLOAD_FOLDER, filename)

@api.route('/outputs/<path:filename>')
def serve_output_video(filename):
    """提供轉換後的影片檔案"""
    return send_from_directory(config.OUTPUT_FOLDER, filename)