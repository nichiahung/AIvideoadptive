"""
AdaptVideo 擴展 API 路由
"""
import os
import base64
import traceback
from io import BytesIO
from flask import Blueprint, request, jsonify
from PIL import Image

from config import config
from utils import find_video_file, validate_json_request, format_error_response
from video_processing import extract_frames_generic, apply_smart_crop
from database import get_video_data, calculate_multi_subject_center_backend

# 創建擴展路由藍圖
api_extended = Blueprint('api_extended', __name__)

@api_extended.route('/api/smart_crop_analysis', methods=['POST'])
@validate_json_request(['file_id', 'template_name'])
def smart_crop_analysis():
    """智慧裁切分析 - 分析主體在特定尺寸下的最佳裁切方案"""
    data = request.json
    file_id = data.get('file_id')
    template_name = data.get('template_name')
    center = data.get('center')
    centers = data.get('centers')  # 支援多個中心點

    # 處理多選中心點
    if centers and len(centers) > 0:
        center = calculate_multi_subject_center_backend(centers, file_id)
        if center:
            center = list(center)  # 轉換為列表格式

    if not center:
        return format_error_response("缺少中心點參數")

    # 找到模板
    template = next((t for t in config.DOOH_TEMPLATES if t['name'] == template_name), None)
    if not template:
        return format_error_response(f"找不到模板: {template_name}", 404)

    # 獲取影片資料
    video_data = get_video_data(file_id)
    if not video_data:
        return format_error_response(f"找不到影片資料: {file_id}", 404)

    video_info = video_data.get('video_info', {})
    original_width = video_info.get('width', 1920)
    original_height = video_info.get('height', 1080)
    
    # 分析裁切可行性
    target_width, target_height = template['width'], template['height']
    target_ratio = target_width / target_height
    original_ratio = original_width / original_height
    
    # 計算縮放比例
    scale = max(target_width / original_width, target_height / original_height)
    scaled_width = original_width * scale
    scaled_height = original_height * scale
    
    # 分析中心點的可行性
    desired_center_x = center[0] * scale
    desired_center_y = center[1] * scale
    
    half_w, half_h = target_width / 2, target_height / 2
    min_x, max_x = half_w, scaled_width - half_w
    min_y, max_y = half_h, scaled_height - half_h
    
    final_crop_x = max(min_x, min(desired_center_x, max_x))
    final_crop_y = max(min_y, min(desired_center_y, max_y))
    
    # 計算偏移量
    offset_x = abs(final_crop_x - desired_center_x)
    offset_y = abs(final_crop_y - desired_center_y)
    
    # 分析結果
    is_perfect_fit = offset_x < 1 and offset_y < 1
    coverage_x = min(1.0, target_width / scaled_width) * 100
    coverage_y = min(1.0, target_height / scaled_height) * 100
    
    # 生成建議
    analysis = {
        "is_perfect_fit": is_perfect_fit,
        "offset_x": round(offset_x, 1),
        "offset_y": round(offset_y, 1),
        "coverage_x": round(coverage_x, 1),
        "coverage_y": round(coverage_y, 1),
        "scale_factor": round(scale, 2),
        "recommendation": "完美適配" if is_perfect_fit else "需要調整" if (offset_x > 10 or offset_y > 10) else "良好適配"
    }
    
    return jsonify(analysis)

@api_extended.route('/api/generate_preview', methods=['POST'])
@validate_json_request(['file_id', 'template_name'])
def generate_preview():
    """為 AI 推薦的模板生成多幀預覽動畫"""
    data = request.json
    file_id = data.get('file_id')
    template_name = data.get('template_name')
    center = data.get('center')
    centers = data.get('centers')  # 支援多個中心點

    # 找到模板
    template = next((t for t in config.DOOH_TEMPLATES if t['name'] == template_name), None)
    if not template:
        return format_error_response(f"找不到模板: {template_name}", 404)

    upload_path = find_video_file(file_id)
    if not upload_path:
        return format_error_response(f"找不到影片檔案: {file_id}", 404)

    # 獲取影片資料和 LLM 分析結果
    video_data = get_video_data(file_id)
    if not video_data:
        return format_error_response(f"找不到影片資料: {file_id}", 404)

    # 處理多選中心點
    if centers and len(centers) > 0:
        center = calculate_multi_subject_center_backend(centers, file_id)
        if center:
            center = list(center)  # 轉換為列表格式
    
    # 使用預設中心點如果沒有提供
    if not center:
        video_info = video_data.get('video_info', {})
        center = [video_info.get('width', 1920) / 2, video_info.get('height', 1080) / 2]

    # 獲取 LLM 分析的物體資訊
    llm_analysis_options = video_data.get('llm_analysis_options', [])
    selected_subject_name = None
    
    # 找到當前選中主體的名稱
    for option in llm_analysis_options:
        if option.get('center') == center:
            selected_subject_name = option.get('subject', 'Unknown')
            print(f"🎯 找到選中的主體: {selected_subject_name}")
            break

    try:
        # 計算需要提取的幀數
        import cv2
        cap = cv2.VideoCapture(upload_path)
        if not cap.isOpened():
            return format_error_response("無法開啟影片檔案", 500)
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if total_frames <= 0:
            return format_error_response("影片無有效幀", 500)
            
        num_preview_frames = min(6, max(3, max(1, total_frames // 30)))
        if total_frames < 30:
            num_preview_frames = min(total_frames, 3)
        
        # 使用共用函數提取幀
        pil_frames = extract_frames_generic(upload_path, num_preview_frames, return_pil=True)
        
        if not pil_frames:
            return format_error_response("無法提取預覽幀", 500)
        
        preview_frames = []
        target_width, target_height = template['width'], template['height']
        is_adjusted = False
        
        # 獲取原始影片尺寸
        video_info = video_data.get('video_info', {})
        original_width = video_info.get('width', 1920)
        original_height = video_info.get('height', 1080)
        
        for i, img in enumerate(pil_frames):
            print(f"🎬 處理第 {i+1}/{len(pil_frames)} 幀")
            
            # 使用共用的裁切函數
            cropped_img, frame_adjusted = apply_smart_crop(
                img, target_width, target_height, center,
                original_width=original_width, original_height=original_height
            )
            
            # 記錄是否有調整
            if not is_adjusted and frame_adjusted:
                is_adjusted = True
            
            # 調整預覽圖大小以便顯示（最大寬度250px）
            preview_scale = min(config.DEFAULT_CROP_PREVIEW_MAX_WIDTH / target_width, 180 / target_height)
            if preview_scale < 1:
                preview_w = int(target_width * preview_scale)
                preview_h = int(target_height * preview_scale)
                cropped_img = cropped_img.resize((preview_w, preview_h), Image.LANCZOS)

            # 將結果轉為 Base64
            buffered = BytesIO()
            cropped_img.save(buffered, format="JPEG", quality=80)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            preview_frames.append(f"data:image/jpeg;base64,{img_str}")
        
        print(f"✅ 成功生成 {len(preview_frames)} 個預覽幀")
        return jsonify({
            "preview_frames": preview_frames,
            "is_adjusted": is_adjusted,
            "template": template,
            "frame_count": len(preview_frames),
            "subject_name": selected_subject_name
        })

    except Exception as e:
        print(f"❌ 生成多幀預覽失敗: {e}")
        traceback.print_exc()
        return format_error_response("生成預覽失敗", 500)

@api_extended.route('/api/generate_original_preview', methods=['POST'])
@validate_json_request(['file_id'])
def generate_original_preview():
    """為原始影片生成動態預覽"""
    data = request.json
    file_id = data.get('file_id')

    upload_path = find_video_file(file_id)
    if not upload_path:
        return format_error_response(f"找不到影片檔案: {file_id}", 404)

    try:
        # 計算需要提取的幀數
        import cv2
        cap = cv2.VideoCapture(upload_path)
        if not cap.isOpened():
            return format_error_response("無法開啟影片檔案", 500)
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if total_frames <= 0:
            return format_error_response("影片無有效幀", 500)
            
        num_preview_frames = min(8, max(4, max(1, total_frames // 20)))
        if total_frames < 20:
            num_preview_frames = min(total_frames, 4)
        
        # 使用共用函數提取幀，並設定最大寬度為300px
        pil_frames = extract_frames_generic(
            upload_path, num_preview_frames, 
            return_pil=True, max_width=config.DEFAULT_PREVIEW_MAX_WIDTH, quality=85
        )
        
        if not pil_frames:
            return format_error_response("無法提取預覽幀", 500)
        
        # 將PIL圖像轉為base64
        preview_frames = []
        for img in pil_frames:
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            preview_frames.append(f"data:image/jpeg;base64,{img_str}")
        
        print(f"✅ 成功生成原始影片 {len(preview_frames)} 個預覽幀")
        return jsonify({
            "preview_frames": preview_frames,
            "frame_count": len(preview_frames)
        })

    except Exception as e:
        print(f"❌ 生成原始影片預覽失敗: {e}")
        traceback.print_exc()
        return format_error_response("生成原始影片預覽失敗", 500)