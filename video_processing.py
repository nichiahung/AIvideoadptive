"""
AdaptVideo 影片處理模組
"""
import os
import cv2
import numpy as np
import base64
import json
import uuid
import shutil
import time
from io import BytesIO
from PIL import Image
import httpx
from openai import OpenAI
from config import config

# 初始化 OpenAI 用戶端
try:
    api_key = config.OPENAI_API_KEY
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

# 嘗試導入 MoviePy
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
    print("✅ MoviePy 已載入，支援完整影片轉換功能")
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy 未安裝，將使用基本功能")

def get_video_info(file_path):
    """獲取影片基本信息"""
    try:
        with VideoFileClip(file_path) as clip:
            return {
                "duration": round(clip.duration, 2),
                "width": clip.w,
                "height": clip.h,
                "fps": clip.fps
            }
    except Exception as e:
        print(f"獲取影片信息失敗: {e}")
        return {"duration": 0, "width": 0, "height": 0, "fps": 0}

def extract_thumbnail(video_path):
    """從影片中間提取一幀作為縮圖"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, config.DEFAULT_JPEG_QUALITY])
        return f"data:image/jpeg;base64,{base64.b64encode(buffer).decode('utf-8')}"
    except Exception as e:
        print(f"❌ 提取縮圖失敗: {e}")
        return None

def analyze_video_for_face_crop(video_path):
    """分析影片，找到主要人臉的平均中心位置"""
    if not OPENCV_AI_AVAILABLE:
        return None
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    face_positions = []
    max_frames_to_check = config.MAX_FRAMES_FOR_ANALYSIS
    frame_count = 0
    
    while cap.isOpened() and frame_count < max_frames_to_check:
        ret, frame = cap.read()
        if not ret:
            break
        
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

def analyze_video_with_llm(video_path, conversation_history, original_width=None, original_height=None):
    """使用多模態LLM分析影片，基於提供的對話歷史"""
    if not LLM_AI_AVAILABLE:
        return None
    
    base64_frames = extract_frames_from_video(video_path, max_frames=5)
    if not base64_frames:
        print("❌ 無法提取幀進行LLM分析")
        return None
        
    print(f"🧠 已提取 {len(base64_frames)} 幀，準備基於對話歷史進行LLM分析...")

    template_descriptions = "\\n".join([f"- {t['name']}: {t['width']}x{t['height']} ({t['description']})" for t in config.DOOH_TEMPLATES])
    
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
        else:
            # 如果歷史中沒有用戶消息，創建一個新的
            messages.append({"role": "user", "content": [{"type": "text", "text": "請分析這些畫面。"}] + [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{frame}"}} for frame in base64_frames]})
    else:
        # 如果沒有歷史記錄，創建初始用戶消息
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
                _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, config.DEFAULT_JPEG_QUALITY])
                base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
        
        cap.release()
        return base64_frames
    
    # 標準提取邏輯（第一次和第二次嘗試）
    count = 0
    for i in range(start_offset, total_frames, frame_interval):
        if count >= max_frames:
            break
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, config.DEFAULT_JPEG_QUALITY])
            base64_frames.append(base64.b64encode(buffer).decode("utf-8"))
            count += 1
    
    cap.release()
    return base64_frames

def crop_frame_for_thumbnail(video_path, box):
    """從影片中間幀裁切一個區域作為縮圖"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Seek to middle frame, which is usually representative
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return None
        
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
                if ai_center is not None:
                    crop_center = ai_center
            
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