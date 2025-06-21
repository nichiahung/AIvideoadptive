"""
AdaptVideo 資料庫操作模組
"""
import shelve
from contextlib import closing
from datetime import datetime
from config import config
from utils import calculate_multi_subject_center

def get_video_data(file_id):
    """從資料庫獲取影片資料"""
    with closing(shelve.open(config.SHELVE_FILE)) as db:
        return db.get(file_id)

def update_video_data(file_id, data):
    """更新資料庫中的影片資料"""
    with closing(shelve.open(config.SHELVE_FILE, writeback=True)) as db:
        if file_id not in db:
            db[file_id] = {}
        db[file_id].update(data)
        db[file_id]['timestamp'] = datetime.now().isoformat()

def save_video_data(file_id, data):
    """保存新的影片資料到資料庫"""
    data['timestamp'] = datetime.now().isoformat()
    with closing(shelve.open(config.SHELVE_FILE, writeback=True)) as db:
        db[file_id] = data

def get_all_videos():
    """獲取所有影片的列表，按時間倒序排列"""
    videos = []
    with closing(shelve.open(config.SHELVE_FILE)) as db:
        # 將資料庫中的項目按時間倒序排列
        sorted_keys = sorted(db.keys(), key=lambda k: db[k].get('timestamp', ''), reverse=True)
        for key in sorted_keys:
            video_data = db.get(key)
            if video_data and 'original_path' in video_data:
                videos.append({
                    "file_id": key,
                    "filename": video_data.get('original_filename', ''),
                    "thumbnail": video_data.get('thumbnail_b64'),
                    "video_info": video_data.get('video_info'),
                    "converted_videos": video_data.get('converted_videos', [])
                })
    return videos

def add_conversion_record(file_id, conversion_data):
    """為影片添加轉換記錄"""
    video_data = get_video_data(file_id) or {}
    
    if 'converted_videos' not in video_data:
        video_data['converted_videos'] = []
    
    video_data['converted_videos'].append({
        **conversion_data,
        "timestamp": datetime.now().isoformat()
    })
    
    update_video_data(file_id, video_data)

def save_llm_analysis(file_id, analysis_result):
    """保存 LLM 分析結果"""
    analysis_data = {
        'llm_analysis': analysis_result,
        'llm_analysis_options': analysis_result.get('analysis_options', [])
    }
    update_video_data(file_id, analysis_data)

def calculate_multi_subject_center_backend(selected_centers, file_id):
    """計算多個主體的加權中心點（後端版本）"""
    if not selected_centers or len(selected_centers) == 0:
        return None
    
    if len(selected_centers) == 1:
        return tuple(selected_centers[0])
    
    # 獲取 LLM 分析結果以取得重要性和信心度資訊
    video_data = get_video_data(file_id)
    if not video_data:
        return None
    
    analysis_options = video_data.get('llm_analysis_options', [])
    return calculate_multi_subject_center(selected_centers, analysis_options)

def video_exists(file_id):
    """檢查影片是否存在於資料庫中"""
    with closing(shelve.open(config.SHELVE_FILE)) as db:
        return file_id in db

def delete_video_data(file_id):
    """從資料庫中刪除影片資料"""
    with closing(shelve.open(config.SHELVE_FILE, writeback=True)) as db:
        if file_id in db:
            del db[file_id]
            return True
    return False

def get_video_analysis_options(file_id):
    """獲取影片的 LLM 分析選項"""
    video_data = get_video_data(file_id)
    if video_data:
        return video_data.get('llm_analysis_options', [])
    return []

def update_video_thumbnail(file_id, thumbnail_b64):
    """更新影片縮圖"""
    update_video_data(file_id, {'thumbnail_b64': thumbnail_b64})

def get_video_path(file_id):
    """獲取影片的原始路徑"""
    video_data = get_video_data(file_id)
    if video_data:
        return video_data.get('original_path')
    return None