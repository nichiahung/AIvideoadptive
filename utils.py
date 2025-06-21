"""
AdaptVideo 工具函數
"""
import os
import uuid
from functools import wraps
from werkzeug.utils import secure_filename
from flask import request, jsonify
from config import config

def find_video_file(file_id, folder=None):
    """根據 file_id 查找影片檔案路徑"""
    if folder is None:
        folder = config.UPLOAD_FOLDER
    
    for filename in os.listdir(folder):
        if filename.startswith(file_id):
            return os.path.join(folder, filename)
    return None

def validate_json_request(required_params=None):
    """驗證 JSON 請求的裝飾器"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "請求的 Content-Type 必須是 application/json"}), 415
            
            if required_params:
                data = request.get_json()
                missing = [p for p in required_params if p not in data or data[p] is None]
                if missing:
                    return jsonify({"error": f"缺少必要參數: {', '.join(missing)}"}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def generate_unique_filename(original_filename, file_id=None):
    """生成唯一的檔案名稱"""
    if file_id is None:
        file_id = str(uuid.uuid4())
    
    secure_name = secure_filename(original_filename)
    file_ext = os.path.splitext(secure_name)[1]
    return f"{file_id}_original{file_ext}", file_id

def validate_file_type(filename):
    """驗證檔案類型是否被允許"""
    if not filename:
        return False
    
    file_ext = os.path.splitext(filename.lower())[1]
    return file_ext in config.ALLOWED_EXTENSIONS

def get_file_size_mb(file_path):
    """獲取檔案大小（MB）"""
    if not os.path.exists(file_path):
        return 0
    return os.path.getsize(file_path) / (1024 * 1024)

def validate_file_size(file_path):
    """驗證檔案大小是否在限制內"""
    size_mb = get_file_size_mb(file_path)
    max_size_mb = config.MAX_FILE_SIZE / (1024 * 1024)
    return size_mb <= max_size_mb

def calculate_multi_subject_center(selected_centers, analysis_options):
    """計算多個主體的加權中心點"""
    if not selected_centers or len(selected_centers) == 0:
        return None
    
    if len(selected_centers) == 1:
        return tuple(selected_centers[0])
    
    total_weighted_x = 0
    total_weighted_y = 0
    total_weight = 0
    
    for center in selected_centers:
        # 找到對應的分析選項以獲取重要性和信心度
        importance = 'medium'  # 預設值
        confidence = 0.8       # 預設值
        
        for option in analysis_options:
            if option.get('center') == center:
                importance = option.get('importance', 'medium')
                confidence = option.get('confidence', 0.8)
                break
        
        # 重要性權重
        importance_weights = {'high': 3, 'medium': 2, 'low': 1}
        importance_weight = importance_weights.get(importance, 2)
        
        # 最終權重 = 重要性權重 × 信心度
        weight = importance_weight * confidence
        
        total_weighted_x += center[0] * weight
        total_weighted_y += center[1] * weight
        total_weight += weight
        
        print(f"🎯 主體中心 {center}: 重要性={importance}, 信心度={confidence}, 權重={weight}")
    
    if total_weight > 0:
        final_center = (total_weighted_x / total_weight, total_weighted_y / total_weight)
        print(f"✅ 多主體加權中心點: {final_center}")
        return final_center
    else:
        # 如果無法計算權重，則使用簡單平均
        avg_x = sum(center[0] for center in selected_centers) / len(selected_centers)
        avg_y = sum(center[1] for center in selected_centers) / len(selected_centers)
        return (avg_x, avg_y)

def format_error_response(message, code=400):
    """格式化錯誤回應"""
    return jsonify({"error": message}), code

def format_success_response(data, message=None):
    """格式化成功回應"""
    response = {"success": True}
    if message:
        response["message"] = message
    if data:
        response.update(data)
    return jsonify(response)