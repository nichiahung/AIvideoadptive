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
        
        // 更新全域變數
        if (window.setGlobalVar) {
            window.setGlobalVar('fileId', fileId);
            window.setGlobalVar('originalFilename', originalFilename);
        }
        
        if (uploadResult.thumbnail) {
            originalThumbnail = uploadResult.thumbnail;
            if (window.setGlobalVar) {
                window.setGlobalVar('originalThumbnail', originalThumbnail);
            }
            const videoThumbnailEl = document.getElementById('videoThumbnail');
            videoThumbnailEl.src = originalThumbnail;
            videoThumbnailEl.style.display = 'block';
        }
        
        if (uploadResult.video_info) {
            videoInfo = uploadResult.video_info;
            if (window.setGlobalVar) {
                window.setGlobalVar('videoInfo', videoInfo);
            }
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
        
        console.log('轉換API完整響應:', result); // 調試：查看完整響應
        
        if (result.success) {
            if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('轉換完成！', 'success');
            const downloadSection = document.getElementById('downloadSection');
            const downloadBtn = document.getElementById('downloadBtn');
            const compareBtn = document.getElementById('compareBtn');
            
            downloadBtn.href = result.download_url;
            downloadSection.style.display = 'block';
            
            // 保存 file_id 供比較使用
            window.convertedFileId = result.file_id;
            window.fileId = result.file_id; // 確保全局 fileId 可用
            console.log('轉換完成，file_id:', result.file_id);
            console.log('響應中的所有鍵:', Object.keys(result)); // 調試：查看所有返回的鍵
            
            // 初始化比較按鈕事件
            if (compareBtn && !compareBtn.dataset.initialized) {
                compareBtn.addEventListener('click', showVideoComparison);
                compareBtn.dataset.initialized = 'true';
                console.log('比較按鈕已初始化');
            }
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

async function fetchOriginalPreviewData() {
    // 嘗試多種方式獲取 fileId
    let currentFileId = null;
    if (window.getGlobalVar) {
        currentFileId = window.getGlobalVar('fileId');
    }
    if (!currentFileId && typeof fileId !== 'undefined') {
        currentFileId = fileId;
    }
    if (!currentFileId && window.fileId) {
        currentFileId = window.fileId;
    }
    
    if (!currentFileId) {
        throw new Error('請先選擇影片');
    }
    
    try {
        const response = await fetch('/api/generate_original_preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: currentFileId })
        });
        
        if (!response.ok) {
            throw new Error(`原始預覽生成失敗: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('Original preview data fetch error:', error);
        throw error;
    }
}

async function generateConvertedPreview(fileId) {
    console.log('🎬 開始生成轉換後預覽，fileId:', fileId);
    try {
        const response = await fetch('/api/generate_converted_preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: fileId })
        });
        
        console.log('🎬 API 響應狀態:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('🎬 API 錯誤響應:', errorText);
            throw new Error(`轉換後預覽生成失敗: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('Converted preview generation error:', error);
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus('轉換後預覽生成失敗: ' + error.message, 'error');
        return null;
    }
}

async function getVideoComparisonData(fileId) {
    console.log('🎬 獲取影片比較資料，fileId:', fileId);
    try {
        const response = await fetch('/api/get_video_comparison_data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ file_id: fileId })
        });
        
        if (!response.ok) {
            throw new Error(`獲取影片比較資料失敗: ${response.status}`);
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        console.error('Video comparison data fetch error:', error);
        throw error;
    }
}

async function showVideoComparison() {
    // 嘗試多種方式獲取 fileId
    let currentFileId = null;
    if (window.getGlobalVar) {
        currentFileId = window.getGlobalVar('fileId');
    }
    if (!currentFileId && typeof fileId !== 'undefined') {
        currentFileId = fileId;
    }
    if (!currentFileId && window.fileId) {
        currentFileId = window.fileId;
    }
    
    // 調試信息
    console.log('比較檢查:', {
        currentFileId: currentFileId,
        convertedFileId: window.convertedFileId,
        hasGetGlobalVar: !!window.getGlobalVar,
        windowFileId: window.fileId,
        localFileId: typeof fileId !== 'undefined' ? fileId : 'undefined'
    });
    
    if (!currentFileId) {
        const errorMsg = `缺少比較所需的資料 - fileId: ${currentFileId ? '有' : '無'}`;
        if (window.AdaptVideo && window.AdaptVideo.showStatus) window.AdaptVideo.showStatus(errorMsg, 'error');
        console.error('比較失敗:', errorMsg);
        return;
    }
    
    const comparisonSection = document.getElementById('comparisonSection');
    const comparisonContent = document.getElementById('comparisonContent');
    
    if (!comparisonSection || !comparisonContent) return;
    
    // 顯示比較區域
    comparisonSection.style.display = 'block';
    comparisonContent.innerHTML = '<div style="text-align: center; padding: 20px;">正在載入影片比較...</div>';
    
    try {
        // 獲取影片比較資料
        const comparisonData = await getVideoComparisonData(currentFileId);
        
        if (comparisonData) {
            if (window.AdaptVideoUI && window.AdaptVideoUI.displayVideoComparison) {
                window.AdaptVideoUI.displayVideoComparison(comparisonData);
            }
        }
        
    } catch (error) {
        console.error('Comparison error:', error);
        
        // 調試：當比較失敗時，自動檢查檔案狀態
        if (currentFileId) {
            try {
                const debugResponse = await fetch(`/api/debug_conversions/${currentFileId}`);
                const debugInfo = await debugResponse.json();
                console.log('🔧 調試信息:', debugInfo);
                
            } catch (debugError) {
                console.error('調試請求失敗:', debugError);
            }
        }
        
        comparisonContent.innerHTML = '<div style="text-align: center; padding: 20px; color: red;">載入影片比較失敗</div>';
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
    generateOriginalPreview,
    fetchOriginalPreviewData,
    generateConvertedPreview,
    getVideoComparisonData,
    showVideoComparison
};