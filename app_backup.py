#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdaptVideo - DOOH影片尺寸轉換工具 (本地部署版)
"""

import os
import sys
import shutil
from datetime import datetime
import uuid
import cv2
import numpy as np
import base64
import json
import shelve
from contextlib import closing
from functools import wraps
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template, send_from_directory, abort
from flask_cors import CORS
from dotenv import load_dotenv
import httpx
from openai import OpenAI
import tempfile
import time
from io import BytesIO
from PIL import Image, ImageDraw

# --- 初始化與設定 ---

# 加載 .env 文件
load_dotenv()

# 常數設定
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
OUTPUT_FOLDER = os.path.join(APP_ROOT, 'outputs')
SHELVE_FILE = os.path.join(APP_ROOT, 'video_data.db')
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

# 確保目錄存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 嘗試導入 MoviePy
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
    print("✅ MoviePy 已載入，支援完整影片轉換功能")
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy 未安裝，將使用基本功能")

# 初始化 OpenAI 用戶端
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("在 .env 文件或環境變數中找不到 OPENAI_API_KEY。")
    http_client = httpx.Client(proxies={})
    client = OpenAI(api_key=api_key, http_client=http_client)
    LLM_AI_AVAILABLE = True
    print("✅ OpenAI 用戶端已成功初始化。")
except Exception as e:
    client = None
    LLM_AI_AVAILABLE = False
    print(f"⚠️ 無法初始化 OpenAI 用戶端: {e}")

# 加載 OpenCV 人臉偵測模型
try:
    face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(face_cascade_path)
    if face_cascade.empty():
        raise IOError(f"無法從路徑加載 haarcascade: {face_cascade_path}")
    OPENCV_AI_AVAILABLE = True
    print("✅ OpenCV 人臉偵測模型已載入")
except Exception as e:
    OPENCV_AI_AVAILABLE = False
    print(f"⚠️ 無法載入OpenCV人臉偵測模型: {e}")

# DOOH 尺寸模板
DOOH_TEMPLATES = [
    {"name": "高雄版位", "width": 3840, "height": 1526, "description": "高雄LED看板專用尺寸"},
    {"name": "忠孝商圈", "width": 1440, "height": 960, "description": "忠孝商圈數位看板"},
    {"name": "標準16:9", "width": 1920, "height": 1080, "description": "標準Full HD尺寸"},
    {"name": "4K橫屏", "width": 3840, "height": 2160, "description": "4K Ultra HD橫屏"},
    {"name": "豎屏9:16", "width": 1080, "height": 1920, "description": "手機豎屏比例"},
    {"name": "方形1:1", "width": 1080, "height": 1080, "description": "正方形顯示"},
    {"name": "超寬屏", "width": 2560, "height": 1080, "description": "21:9超寬屏幕"}
]

# --- Flask App ---
app = Flask(__name__)
CORS(app)

# --- 核心分析與轉換函式 ---

def get_video_info(file_path):
    """獲取影片基本信息"""
    try:
        with VideoFileClip(file_path) as clip:
            return { "duration": round(clip.duration, 2), "width": clip.w, "height": clip.h, "fps": clip.fps }
    except Exception as e:
        print(f"獲取影片信息失敗: {e}")
        return { "duration": 0, "width": 0, "height": 0, "fps": 0 }

def extract_thumbnail(video_path):
    """從影片中間提取一幀作為縮圖"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): return None
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
        ret, frame = cap.read()
        cap.release()
        if not ret: return None
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
    except Exception as e:
        print(f"❌ 提取縮圖失敗: {e}")
        return None

def analyze_video_for_face_crop(video_path):
    """分析影片，找到主要人臉的平均中心位置"""
    if not OPENCV_AI_AVAILABLE: return None
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): return None

    face_positions = []
    max_frames_to_check = 90  # 最多分析90幀
    frame_count = 0
    while cap.isOpened() and frame_count < max_frames_to_check:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        if len(faces) > 0:
            main_face = max(faces, key=lambda r: r[2] * r[3])
            face_positions.append((main_face[0] + main_face[2] / 2, main_face[1] + main_face[3] / 2))
        frame_count += 1
    cap.release()

    if not face_positions:
        print("ℹ️ 在影片中未偵測到人臉")
        return None
    
    avg_pos = np.mean(face_positions, axis=0)
    print(f"✅ AI分析完成，平均人臉中心: ({avg_pos[0]:.0f}, {avg_pos[1]:.0f})")
    return avg_pos

def extract_frames_from_video(video_path, max_frames=5, attempt=1):
    """從影片中提取幀，支援多次嘗試以獲得不同的幀"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): 
        return []

    base64_frames = []
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    if total_frames <= 0:
        cap.release()
        return []
    
    # 根據嘗試次數調整幀提取策略
    if attempt == 1:
        # 第一次嘗試：均勻分佈
        frame_interval = max(1, total_frames // max_frames)
        start_offset = 0
    elif attempt == 2:
        # 第二次嘗試：從影片中間開始
        frame_interval = max(1, total_frames // (max_frames * 2))
        start_offset = total_frames // 4
    else:
        # 第三次嘗試：隨機選擇幀
        import random
        frame_indices = random.sample(range(total_frames), min(max_frames, total_frames))
        frame_indices.sort()
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
        
        cap.release()
        return base64_frames
    
    # 標準提取邏輯（第一次和第二次嘗試）
    count = 0
    for i in range(start_offset, total_frames, frame_interval):
        if count >= max_frames: break
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
            count += 1
    
    cap.release()
    return base64_frames

def extract_frames_generic(video_path, num_frames, return_pil=False, max_width=None, quality=85):
    """通用的幀提取函數，可返回 base64 或 PIL Image"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames <= 0:
        cap.release()
        return []
    
    # 計算要提取的幀索引
    frame_indices = []
    if num_frames > 1 and total_frames > 1:
        for i in range(num_frames):
            frame_idx = int(i * (total_frames - 1) / (num_frames - 1))
            frame_indices.append(min(frame_idx, total_frames - 1))
    else:
        frame_indices = [0]
    
    frames = []
    for frame_idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue
        
        if return_pil:
            # 轉換為 PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            # 如果指定最大寬度，調整大小
            if max_width and img.width > max_width:
                scale = max_width / img.width
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            frames.append(img)
        else:
            # 返回 base64
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            frames.append(base64.b64encode(buffer).decode("utf-8"))
    
    cap.release()
    return frames

def apply_smart_crop(image, target_width, target_height, center, original_width=None, original_height=None):
    """應用智慧裁切邏輯，返回裁切後的圖像和是否被調整的標記"""
    if isinstance(image, np.ndarray):
        # OpenCV 格式轉 PIL
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    # 獲取原始尺寸
    if original_width is None:
        original_width = image.width
    if original_height is None:
        original_height = image.height
    
    # 計算縮放比例
    scale = max(target_width / original_width, target_height / original_height)
    resized_w = int(original_width * scale)
    resized_h = int(original_height * scale)
    
    # 縮放圖像
    resized_img = image.resize((resized_w, resized_h), Image.LANCZOS)
    
    # 計算裁切中心點
    desired_center_x = center[0] * scale
    desired_center_y = center[1] * scale
    
    # 計算安全範圍
    half_w = target_width / 2
    half_h = target_height / 2
    min_x = half_w
    max_x = resized_w - half_w
    min_y = half_h
    max_y = resized_h - half_h
    
    # 確保中心點在安全範圍內
    final_crop_x = max(min_x, min(desired_center_x, max_x))
    final_crop_y = max(min_y, min(desired_center_y, max_y))
    
    # 檢查是否被調整
    is_adjusted = abs(final_crop_x - desired_center_x) > 1 or abs(final_crop_y - desired_center_y) > 1
    
    # 進行裁切
    left = int(final_crop_x - half_w)
    top = int(final_crop_y - half_h)
    right = int(final_crop_x + half_w)
    bottom = int(final_crop_y + half_h)
    
    cropped_img = resized_img.crop((left, top, right, bottom))
    
    return cropped_img, is_adjusted

def find_video_file(file_id, folder=UPLOAD_FOLDER):
    """根據 file_id 查找影片檔案路徑"""
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

def get_video_data(file_id):
    """從資料庫獲取影片資料"""
    with closing(shelve.open(SHELVE_FILE)) as db:
        return db.get(file_id)

def update_video_data(file_id, data):
    """更新資料庫中的影片資料"""
    with closing(shelve.open(SHELVE_FILE, writeback=True)) as db:
        if file_id not in db:
            db[file_id] = {}
        db[file_id].update(data)
        db[file_id]['timestamp'] = datetime.now().isoformat()

def analyze_video_with_llm(video_path, conversation_history, original_width=None, original_height=None):
    """使用多模態LLM分析影片，基於提供的對話歷史"""
    if not LLM_AI_AVAILABLE: return None
    
    base64_frames = extract_frames_from_video(video_path, max_frames=5)
    if not base64_frames:
        print("❌ 無法提取幀進行LLM分析")
        return None
        
    print(f"🧠 已提取 {len(base64_frames)} 幀，準備基於對話歷史進行LLM分析...")

    template_descriptions = "\\n".join([f"- {t['name']}: {t['width']}x{t['height']} ({t['description']})" for t in DOOH_TEMPLATES])
    
    # 如果有提供原始影片尺寸，則加入到提示中
    original_video_info = ""
    if original_width and original_height:
        original_video_info = f"**用戶的原始影片尺寸為 {original_width}x{original_height}。**"
    
    # 構建傳送給OpenAI的messages
    messages = [
        {
            "role": "system",
            "content": f"""
你是一位專業的**數位戶外廣告 (DOOH) 版位策略顧問**。你的任務是分析用戶提供的影片，並根據其**原生特性（內容、風格、原始尺寸）**，推薦最有效的 DOOH 廣告版位。

{original_video_info}

**你的核心職責:**
1.  **分析影片原生特性**: 評估影片的原始尺寸、長寬比、內容風格（例如：快節奏、靜態、視覺焦點是否集中），以及核心行銷訊息。
2.  **優先推薦無損版位**: 根據影片的**原始長寬比**，從下方的可用尺寸模板中找出**最相近或完全相符**的版位。你應該優先推薦這些可以**無需裁切、直接投放**的版位。在推薦時，必須說明為什麼這些 DOOH 場景（例如：機場的超寬螢幕、百貨公司的直式螢幕）特別適合這支影片的風格與內容。
3.  **提供轉製裁切建議 (次要)**: 如果你認為透過**智慧裁切**可以讓影片在更多主流、但長寬比不同的 DOOH 版位上取得更好的效果，你可以**額外**建議 1-2 個需要轉換的尺寸。當你提出這類建議時，必須：
    *   明確告知用戶這需要對影片進行**二次處理**。
    *   解釋為什麼這樣的裁切是值得的（例如：更能聚焦在產品上、更符合特定場景的視覺震撼力）。
4.  **識別行銷主體**: 在影片畫面中找出最重要的行銷主體（例如：產品、Logo、關鍵人物、標語），這將作為你提出智慧裁切建議時的依據。
5.  **重要限制**: 你的推薦應嚴格限制在 DOOH 應用場景，並主動避免提出任何社群媒體平台（如 Instagram, TikTok, YouTube）的建議。
6.  **格式化輸出**: 你的回應必須是格式完整的 JSON 物件。

**可用尺寸模板:**
{template_descriptions}

**JSON 輸出格式範例 (專注於 DOOH):**
{{
  "suggestions": "### AI 專業建議\\n\\n您的影片風格動感十足，非常適合戶外大型螢幕。根據您的原始影片尺寸 (1920x1080)，我為您規劃了以下投放策略：\\n\\n**【策略一：原尺寸直接投放】**\\n*   **推薦尺寸：標準16:9 (1920x1080)**\\n    *   **最佳版位**：這與您的影片尺寸完美相符，無需任何修改即可直接投放於 **信義區商圈的 LED 大螢幕** 或 **交通樞紐的橫幅螢幕**。這樣可以完整保留影片的視覺衝擊力，最大化廣告效益。\\n\\n**【策略二：智慧裁切投放】**\\n*   **推薦尺寸：豎屏9:16 (1080x1920)**\\n    *   **最佳版位**：雖然這需要進行智慧裁切，但將視覺焦點鎖定在奔跑的人物上，非常適合投放在 **捷運站月台的直式螢幕** 或 **電梯內的廣告螢幕**，能在近距離吸引乘客目光。",
  "recommended_template_names": ["標準16:9", "豎屏9:16"],
  "analysis_options": [
    {{
      "subject": "奔跑中的人物",
      "importance": "high",
      "confidence": 0.95,
      "center": [960, 540],
      "thumbnail": "data:image/jpeg;base64,..."
    }}
  ]
}}

**請嚴格遵循以上 JSON 格式進行輸出。**
"""
        }
    ]

    # 將圖像幀添加到第一條用戶消息（如果歷史為空）或最新的用戶消息
    user_content = []
    
    # 首先添加歷史記錄
    if conversation_history:
        messages.extend(conversation_history)
        # 找到最後一個用戶消息來附加圖像
        last_user_message = next((msg for msg in reversed(messages) if msg['role'] == 'user'), None)
        if last_user_message:
            # 如果是字串，轉換為列表
            if isinstance(last_user_message['content'], str):
                last_user_message['content'] = [{"type": "text", "text": last_user_message['content']}]
            # 附加圖像
            for frame in base64_frames:
                last_user_message['content'].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame}"}})
        else: # 如果歷史中沒有用戶消息，創建一個新的
             messages.append({"role": "user", "content": [{"type": "text", "text": "請分析這些畫面。"}] + [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame}"}} for frame in base64_frames]})

    else: # 如果沒有歷史記錄，創建初始用戶消息
        user_content.append({"type": "text", "text": "這是要分析的影片，請提供初始專業建議。"})
        for frame in base64_frames:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame}"}})
        messages.append({"role": "user", "content": user_content})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        response_content = response.choices[0].message.content
        print("✅ LLM分析成功")
        return json.loads(response_content)
    except Exception as e:
        print(f"❌ LLM分析失敗: {e}")
        return None

def crop_frame_for_thumbnail(video_path, box):
    """從影片中間幀裁切一個區域作為縮圖"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Seek to middle frame, which is usually representative
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2) 
        ret, frame = cap.read()
        cap.release()
        
        if not ret: return None
        
        # 進行裁切
        x1, y1, x2, y2 = box
        cropped_frame = frame[y1:y2, x1:x2]
        
        # 檢查裁切後的影格是否有效
        if cropped_frame.size == 0:
            print(f"⚠️ 裁切區域無效: {box}, 導致縮圖生成失敗。")
            return None

        _, buffer = cv2.imencode(".jpg", cropped_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
    except Exception as e:
        print(f"❌ 為縮圖裁切幀時發生錯誤: {e}")
        return None

def calculate_multi_subject_center_backend(selected_centers, file_id):
    """計算多個主體的加權中心點（後端版本）"""
    if not selected_centers or len(selected_centers) == 0:
        return None
    
    if len(selected_centers) == 1:
        return tuple(selected_centers[0])
    
    # 獲取 LLM 分析結果以取得重要性和信心度資訊
    with closing(shelve.open(SHELVE_FILE)) as db:
        video_data = db.get(file_id, {})
        analysis_options = video_data.get('llm_analysis_options', [])
    
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

def perform_video_conversion(input_path, output_path, target_width, target_height, crop_mode='center', manual_center=None):
    """核心轉換函式"""
    try:
        if not MOVIEPY_AVAILABLE:
            print("MoviePy 不可用，執行檔案複製。")
            shutil.copy2(input_path, output_path)
            return

        print(f"▶️ MoviePy: 開始轉換，輸出至: {output_path}")
            
        with VideoFileClip(input_path) as clip:
            crop_center = (clip.w / 2, clip.h / 2)

            if manual_center:
                print(f"🧠 使用手動選擇的中心點: {manual_center}")
                crop_center = manual_center
            elif crop_mode == 'face':
                print("🧠 MoviePy: 啟用AI人臉辨識...")
                ai_center = analyze_video_for_face_crop(input_path)
                if ai_center is not None: crop_center = ai_center
            
            print("📏 MoviePy: 計算縮放與裁切參數...")
            
            # 使用共用的智慧裁切邏輯
            # 先從影片中提取一幀來計算裁切參數
            cap = cv2.VideoCapture(input_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # 使用共用裁切函數計算參數
                _, is_adjusted = apply_smart_crop(
                    frame, target_width, target_height, crop_center,
                    original_width=clip.w, original_height=clip.h
                )
                
                # 計算MoviePy需要的裁切參數
                scale = max(target_width / clip.w, target_height / clip.h)
                resized_clip = clip.resize(scale)
                
                # 重新計算裁切中心點（與apply_smart_crop相同的邏輯）
                desired_center_x = crop_center[0] * scale
                desired_center_y = crop_center[1] * scale
                
                half_w = target_width / 2
                half_h = target_height / 2
                min_x = half_w
                max_x = resized_clip.w - half_w
                min_y = half_h
                max_y = resized_clip.h - half_h
                
                final_crop_x = max(min_x, min(desired_center_x, max_x))
                final_crop_y = max(min_y, min(desired_center_y, max_y))
                
                if is_adjusted:
                    print(f"⚠️ 裁切中心點已調整以避免超出邊界。")
                    print(f"   原始中心: ({desired_center_x:.0f}, {desired_center_y:.0f}) -> 調整後: ({final_crop_x:.0f}, {final_crop_y:.0f})")
                
                final_clip = resized_clip.crop(
                    x_center=final_crop_x, y_center=final_crop_y,
                    width=target_width, height=target_height
                )
            else:
                # 如果無法讀取幀，使用原始邏輯
                scale = max(target_width / clip.w, target_height / clip.h)
                resized_clip = clip.resize(scale)
                final_clip = resized_clip.crop(
                    x_center=resized_clip.w / 2, y_center=resized_clip.h / 2,
                    width=target_width, height=target_height
                )
            
            temp_audio_filename = f"temp-audio-{uuid.uuid4()}.m4a"
            temp_audio_path = os.path.join(os.path.dirname(output_path), temp_audio_filename)

            print(f"✍️ MoviePy: 開始寫入輸出檔案至 {output_path}")
            final_clip.write_videofile(
                str(output_path),
                codec='libx264', audio_codec='aac',
                temp_audiofile=str(temp_audio_path),
                remove_temp=True,
                verbose=False,
                logger=None
            )
            print("✅ MoviePy: 檔案寫入完成。")
            
            final_clip.close()
            resized_clip.close()
            
    except Exception as e:
        import traceback
        print(f"‼️‼️ MoviePy 轉換核心發生致命錯誤 ‼️‼️")
        print(traceback.format_exc())

    print("⏳ 等待文件系統同步...")
    time.sleep(1)

# --- API Endpoints ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/templates')
def get_templates():
    return jsonify(DOOH_TEMPLATES)

@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "沒有選擇檔案"}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({"error": "沒有選擇檔案"}), 400

    original_filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    upload_filename = f"{file_id}_original{os.path.splitext(file.filename)[1]}"
    upload_path = os.path.join(UPLOAD_FOLDER, upload_filename)
    file.save(upload_path)
    
    # 使用絕對路徑以增加 OpenCV 的穩定性
    abs_upload_path = os.path.abspath(upload_path)

    video_info = get_video_info(abs_upload_path)
    thumbnail = extract_thumbnail(abs_upload_path)
    
    # 將影片資料存入資料庫
    with closing(shelve.open(SHELVE_FILE, writeback=True)) as db:
        db[file_id] = {
            "original_path": upload_path, # 儲存相對路徑以保持可攜性
            "video_info": video_info,
            "thumbnail_b64": thumbnail,
            "timestamp": datetime.now().isoformat()
        }

    return jsonify({
        "file_id": file_id,
        "video_info": video_info,
        "thumbnail": thumbnail
    })

@app.route('/api/analyze', methods=['POST'])
@validate_json_request(['file_id'])
def analyze_video_api():
    """接收影片ID和對話歷史，返回LLM分析結果"""
    data = request.get_json()
    file_id = data['file_id']
    conversation_history = data.get('conversation_history', []) # 獲取對話歷史

    video_record = get_video_data(file_id)
    if not video_record:
        return jsonify({"error": "找不到檔案"}), 404

    video_path = video_record['original_path']
    if not os.path.exists(video_path):
        return jsonify({"error": "影片檔案不存在"}), 404
    
    video_info = video_record.get('video_info', {})
    
    # 傳遞對話歷史和影片原始尺寸給分析函數
    analysis_result = analyze_video_with_llm(video_path, conversation_history, video_info.get('width'), video_info.get('height'))
    
    if not analysis_result:
        return jsonify({"error": "AI分析影片時發生錯誤"}), 500
        
    # 確保 analysis_options 存在
    if 'analysis_options' not in analysis_result:
        analysis_result['analysis_options'] = []

    # 為每個分析選項生成縮圖
    if video_info.get('width', 0) > 0 and video_info.get('height', 0) > 0:
        for option in analysis_result.get('analysis_options', []):
            center = option.get('center')
            if center:
                # 假設box是相對於原始影片尺寸
                box_size = 200 # 縮圖大小
                x, y = center
                
                # 確保裁切框在影片範圍內
                x1 = max(0, int(x - box_size / 2))
                y1 = max(0, int(y - box_size / 2))
                x2 = min(video_info['width'], int(x + box_size / 2))
                y2 = min(video_info['height'], int(y + box_size / 2))
                
                box = (x1, y1, x2, y2)
                thumbnail_b64 = crop_frame_for_thumbnail(video_path, box)
                option['thumbnail'] = thumbnail_b64

    # 將 LLM 分析結果存回資料庫，以供後續使用（例如多主體裁切）
    analysis_data = {
        'llm_analysis': analysis_result,
        'llm_analysis_options': analysis_result.get('analysis_options', [])
    }
    update_video_data(file_id, analysis_data)
    print(f"✅ 已將 LLM 分析結果儲存至資料庫: {file_id}")

    return jsonify(analysis_result)

@app.route('/api/uploaded_videos', methods=['GET'])
def get_uploaded_videos():
    """獲取已上傳影片的列表"""
    videos = []
    with closing(shelve.open(SHELVE_FILE)) as db:
        # 將資料庫中的項目按時間倒序排列
        sorted_keys = sorted(db.keys(), key=lambda k: db[k].get('timestamp', ''), reverse=True)
        for key in sorted_keys:
            video_data = db.get(key)
            if video_data and 'original_path' in video_data:
                # 在此我們直接從 video_info 或一個預設路徑獲取
                # 這裡我們簡化處理，直接回傳 file_id 和原始檔名
                 videos.append({
                    "file_id": key,
                    "filename": os.path.basename(video_data['original_path']),
                    "thumbnail": video_data.get('thumbnail_b64'),
                    "video_info": video_data.get('video_info'),
                    "converted_videos": video_data.get('converted_videos', [])
                })
    return jsonify(videos)

@app.route('/api/convert', methods=['POST'])
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

    upload_path = find_video_file(file_id)
    if not upload_path:
        return jsonify({"error": f"找不到 file_id 為 {file_id} 的原始檔案"}), 404
    
    original_file_ext = os.path.splitext(upload_path)[1]

    output_filename = f"{file_id}_converted{original_file_ext}"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    
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
    
    perform_video_conversion(
        input_path=upload_path,
        output_path=output_path,
        target_width=int(target_width),
        target_height=int(target_height),
        crop_mode=crop_mode,
        manual_center=manual_center
    )

    if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
        print(f"❌ 轉換後檔案不存在或檔案過小: {output_path}")
        return jsonify({"error": "影片轉換失敗，請檢查伺服器日誌以了解詳情。"}), 500
        
    # 更新資料庫
    conversion_data = {
        "original_path": upload_path,
        "converted_path": output_path,
        "converted_filename": output_filename
    }
    
    # 處理 converted_videos 列表
    video_data = get_video_data(file_id) or {}
    if 'converted_videos' not in video_data:
        video_data['converted_videos'] = []
    
    video_data['converted_videos'].append({
        "path": output_path,
        "filename": os.path.basename(output_path),
        "template_name": f"{target_width}x{target_height}",
        "timestamp": datetime.now().isoformat()
    })
    
    conversion_data.update(video_data)
    update_video_data(file_id, conversion_data)
    print(f"✅ 已將影片轉換資料儲存至資料庫: {file_id}")

    return jsonify({
        "success": True,
        "file_id": file_id,
        "download_url": f"/outputs/{output_filename}",
        "filename": output_filename
    })

@app.route('/api/preview_crop', methods=['POST'])
def preview_crop():
    """產生裁切預覽圖"""
    if not request.is_json:
        return jsonify({"error": "請求的 Content-Type 必須是 application/json"}), 415

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

    if not all([base64_image, target_width, target_height, original_width, original_height, center]):
        return jsonify({"error": "缺少必要參數"}), 400

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
            overlay = Image.new('RGBA', cropped_img.size, (255, 0, 0, 0)) # 透明
            draw = ImageDraw.Draw(overlay)
            draw.rectangle([(0, 0), (cropped_img.width, cropped_img.height)], 
                          outline=(255, 80, 80, 200), width=10) # 紅色邊框
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
        import traceback
        print(f"❌ 預覽裁切失敗: {e}")
        traceback.print_exc()
        return jsonify({"error": "產生預覽圖失敗"}), 500

@app.route('/api/smart_crop_analysis', methods=['POST'])
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
        return jsonify({"error": "缺少中心點參數"}), 400

    # 找到模板
    template = next((t for t in DOOH_TEMPLATES if t['name'] == template_name), None)
    if not template:
        return jsonify({"error": f"找不到模板: {template_name}"}), 404

    # 獲取影片資料
    video_data = get_video_data(file_id)
    if not video_data:
        return jsonify({"error": f"找不到影片資料: {file_id}"}), 404

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

@app.route('/api/generate_preview', methods=['POST'])
def generate_preview():
    """為 AI 推薦的模板生成多幀預覽動畫"""
    if not request.is_json:
        return jsonify({"error": "請求的 Content-Type 必須是 application/json"}), 415

    data = request.json
    file_id = data.get('file_id')
    template_name = data.get('template_name')
    center = data.get('center')
    centers = data.get('centers')  # 支援多個中心點

    if not all([file_id, template_name]):
        return jsonify({"error": "缺少必要參數 (file_id, template_name)"}), 400

    # 找到模板
    template = next((t for t in DOOH_TEMPLATES if t['name'] == template_name), None)
    if not template:
        return jsonify({"error": f"找不到模板: {template_name}"}), 404

    upload_path = find_video_file(file_id)
    if not upload_path:
        return jsonify({"error": f"找不到影片檔案: {file_id}"}), 404

    # 獲取影片資料和 LLM 分析結果
    video_data = get_video_data(file_id)
    if not video_data:
        return jsonify({"error": f"找不到影片資料: {file_id}"}), 404

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
        cap = cv2.VideoCapture(upload_path)
        if not cap.isOpened():
            return jsonify({"error": "無法開啟影片檔案"}), 500
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if total_frames <= 0:
            return jsonify({"error": "影片無有效幀"}), 500
            
        num_preview_frames = min(6, max(3, max(1, total_frames // 30)))
        if total_frames < 30:
            num_preview_frames = min(total_frames, 3)
        
        # 使用共用函數提取幀
        pil_frames = extract_frames_generic(upload_path, num_preview_frames, return_pil=True)
        
        if not pil_frames:
            return jsonify({"error": "無法提取預覽幀"}), 500
        
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
            preview_scale = min(250 / target_width, 180 / target_height)
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
        import traceback
        print(f"❌ 生成多幀預覽失敗: {e}")
        traceback.print_exc()
        return jsonify({"error": "生成預覽失敗"}), 500

@app.route('/api/generate_original_preview', methods=['POST'])
def generate_original_preview():
    """為原始影片生成動態預覽"""
    if not request.is_json:
        return jsonify({"error": "請求的 Content-Type 必須是 application/json"}), 415

    data = request.json
    file_id = data.get('file_id')

    if not file_id:
        return jsonify({"error": "缺少必要參數 (file_id)"}), 400

    upload_path = find_video_file(file_id)
    if not upload_path:
        return jsonify({"error": f"找不到影片檔案: {file_id}"}), 404

    try:
        # 計算需要提取的幀數
        cap = cv2.VideoCapture(upload_path)
        if not cap.isOpened():
            return jsonify({"error": "無法開啟影片檔案"}), 500
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        
        if total_frames <= 0:
            return jsonify({"error": "影片無有效幀"}), 500
            
        num_preview_frames = min(8, max(4, max(1, total_frames // 20)))
        if total_frames < 20:
            num_preview_frames = min(total_frames, 4)
        
        # 使用共用函數提取幀，並設定最大寬度為300px
        pil_frames = extract_frames_generic(
            upload_path, num_preview_frames, 
            return_pil=True, max_width=300, quality=85
        )
        
        if not pil_frames:
            return jsonify({"error": "無法提取預覽幀"}), 500
        
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
        import traceback
        print(f"❌ 生成原始影片預覽失敗: {e}")
        traceback.print_exc()
        return jsonify({"error": "生成原始影片預覽失敗"}), 500

@app.route('/uploads/<path:filename>')
def serve_upload_video(filename):
    """提供原始上傳的影片檔案"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/outputs/<path:filename>')
def serve_output_video(filename):
    """提供轉換後的影片檔案"""
    return send_from_directory(OUTPUT_FOLDER, filename)

# --- Main ---
if __name__ == '__main__':
    # try:
    #     from waitress import serve
    #     print("🚀 使用 Waitress 生產環境伺服器啟動於 http://0.0.0.0:5001")
    #     serve(app, host='0.0.0.0', port=5001, threads=8)
    # except ImportError:
    #     print("⚠️ Waitress 未安裝，使用 Flask 開發伺服器。")
    #     print("👉 建議安裝以獲得更佳性能: pip install waitress")
    print("🚀 使用 Flask 開發伺服器啟動 (除錯模式)")
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)