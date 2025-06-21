/**
 * AdaptVideo API 相關函數
 */

// API 呼叫函數
async function loadAllTemplates() {
    try {
        const response = await fetch('/api/templates');
        allTemplates = await response.json();
    } catch (error) {
        console.error("Failed to load templates", error);
    }
}

async function loadVideoHistory() {
    const grid = document.getElementById('videoHistoryGrid');
    grid.innerHTML = '<div class="spinner"></div>';
    try {
        const response = await fetch('/api/uploaded_videos');
        const videos = await response.json();
        grid.innerHTML = '';
        if (videos.length === 0) {
            grid.innerHTML = '<p>暫無歷史紀錄</p>';
            return;
        }
        videos.forEach(v => {
            const card = document.createElement('div');
            card.className = 'history-thumb-card';
            card.innerHTML = `<img src="${v.thumbnail}" alt="${v.filename}"><p>${v.filename}</p>`;
            card.addEventListener('click', () => {
                if (window.AdaptVideoUI && window.AdaptVideoUI.handleExistingVideo) {
                    window.AdaptVideoUI.handleExistingVideo(v.file_id, v.thumbnail, v.video_info, v.filename);
                } else {
                    console.error('handleExistingVideo function not found');
                }
                document.getElementById('videoHistoryModal').style.display = 'none';
            });
            grid.appendChild(card);
        });
    } catch (error) {
        console.error("Failed to load video history", error);
        grid.innerHTML = '<p style="color:red;">載入失敗</p>';
    }
}

async function uploadAndAnalyze(file) {
    if (!file) return;
    
    if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('正在上傳影片...', 'info');
    
    try {
        const formData = new FormData();
        formData.append('video', file);
        
        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) {
            throw new Error(`上傳失敗: ${uploadResponse.status}`);
        }
        
        const uploadResult = await uploadResponse.json();
        fileId = uploadResult.file_id;
        originalFilename = file.name;
        
        if (uploadResult.thumbnail) {
            originalThumbnail = uploadResult.thumbnail;
            const videoThumbnailEl = document.getElementById('videoThumbnail');
            videoThumbnailEl.src = originalThumbnail;
            videoThumbnailEl.style.display = 'block';
        }
        
        if (uploadResult.video_info) {
            videoInfo = uploadResult.video_info;
            if (window.AdaptVideoUI && window.AdaptVideoUI.displayVideoInfo) {
                window.AdaptVideoUI.displayVideoInfo(videoInfo, originalFilename);
            } else {
                console.error('displayVideoInfo function not found');
            }
        }
        
        document.getElementById('videoPreview').style.display = 'block';
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('影片上傳成功！正在進行 AI 分析...', 'info');
        
        await triggerVideoAnalysis();
        
    } catch (error) {
        console.error('Upload error:', error);
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('上傳失敗: ' + error.message, 'error');
    }
}

async function triggerVideoAnalysis() {
    if (!fileId) return;
    
    try {
        const analysisResponse = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                file_id: fileId,
                conversation_history: conversationHistory
            })
        });
        
        if (!analysisResponse.ok) {
            throw new Error(`分析失敗: ${analysisResponse.status}`);
        }
        
        const analysisResult = await analysisResponse.json();
        if (window.AdaptVideoUI && window.AdaptVideoUI.handleAnalysisResult) {
            window.AdaptVideoUI.handleAnalysisResult(analysisResult);
        } else {
            console.error('handleAnalysisResult function not found');
        }
        
    } catch (error) {
        console.error('Analysis error:', error);
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('AI 分析失敗: ' + error.message, 'error');
    }
}

async function startConversion(template, center) {
    if (!fileId || !template) {
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('請選擇影片和模板', 'error');
        return;
    }
    
    if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('正在轉換影片...', 'info');
    
    try {
        const requestBody = {
            file_id: fileId,
            width: template.width,
            height: template.height,
            crop_mode: center ? 'llm' : 'center'
        };
        
        if (center) {
            if (Array.isArray(selectedLLMSubjects) && selectedLLMSubjects.length > 0) {
                requestBody.centers = selectedLLMSubjects;
            } else {
                requestBody.center = center;
            }
        }
        
        const response = await fetch('/api/convert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`轉換失敗: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('轉換完成！', 'success');
            const downloadBtn = document.getElementById('downloadBtn');
            downloadBtn.href = result.download_url;
            downloadBtn.style.display = 'inline-flex';
        } else {
            throw new Error('轉換失敗');
        }
        
    } catch (error) {
        console.error('Conversion error:', error);
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('轉換失敗: ' + error.message, 'error');
    }
}

async function generatePreview(templateName, center) {
    if (!fileId || !templateName) return;
    
    try {
        const requestBody = {
            file_id: fileId,
            template_name: templateName
        };
        
        if (center) {
            if (Array.isArray(selectedLLMSubjects) && selectedLLMSubjects.length > 0) {
                requestBody.centers = selectedLLMSubjects;
            } else {
                requestBody.center = center;
            }
        }
        
        const response = await fetch('/api/generate_preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`預覽生成失敗: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('Preview generation error:', error);
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('預覽生成失敗: ' + error.message, 'error');
        return null;
    }
}

async function generateOriginalPreview() {
    if (!fileId) {
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('請先選擇影片', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/generate_original_preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: fileId })
        });
        
        if (!response.ok) {
            throw new Error(`原始預覽生成失敗: ${response.status}`);
        }
        
        const result = await response.json();
        if (window.AdaptVideoUI && window.AdaptVideoUI.displayOriginalPreview) {
            window.AdaptVideoUI.displayOriginalPreview(result);
        } else {
            console.error('displayOriginalPreview function not found');
        }
        
    } catch (error) {
        console.error('Original preview generation error:', error);
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('原始預覽生成失敗: ' + error.message, 'error');
    }
}

// 導出到全域作用域
window.AdaptVideoAPI = {
    loadAllTemplates,
    loadVideoHistory,
    uploadAndAnalyze,
    triggerVideoAnalysis,
    startConversion,
    generatePreview,
    generateOriginalPreview
};