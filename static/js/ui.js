/**
 * AdaptVideo UI 相關函數
 */

// 初始化函數
function initializeNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            const page = document.getElementById(`page-${item.dataset.page}`);
            page.classList.add('active');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            if (item.dataset.page === 'history') loadHistoryPage();
        });
    });
}

function initializeTabs() {
    document.querySelectorAll('.tab-nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const tabId = `tab-${item.dataset.tab}`;
            document.querySelectorAll('.tab-content').forEach(p => p.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            document.querySelectorAll('.tab-nav-item').forEach(n => n.classList.remove('active'));
            item.classList.add('active');
            if (item.dataset.tab === 'manual' && fileId) setupManualTab();
        });
    });
}

function initializeModal() {
    const modal = document.getElementById('videoHistoryModal');
    const showHistoryBtn = document.getElementById('showHistoryBtn');
    const closeBtn = document.querySelector('.close-btn');

    showHistoryBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        window.AdaptVideo && window.AdaptVideo.resetUIForNewVideo ? window.AdaptVideo.resetUIForNewVideo() : null;
        modal.style.display = 'block';
        if (window.AdaptVideoAPI && window.AdaptVideoAPI.loadVideoHistory) {
            window.AdaptVideoAPI.loadVideoHistory();
        } else {
            console.error('loadVideoHistory function not found');
        }
    });
    
    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (event) => {
        if (event.target == modal) modal.style.display = 'none';
    }
}

function initializeFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        fileInput.click();
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0]);
        }
    });
    
    // 拖拽上傳處理
    ['dragover', 'dragleave', 'drop'].forEach(evt => {
        uploadArea.addEventListener(evt, (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (evt === 'dragover') {
                uploadArea.classList.add('dragover');
            } else if (evt === 'dragleave') {
                uploadArea.classList.remove('dragover');
            } else if (evt === 'drop') {
                uploadArea.classList.remove('dragover');
                if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                    handleFile(e.dataTransfer.files[0]);
                }
            }
        });
    });
}

function initializeEventListeners() {
    document.getElementById('convertBtnManual').addEventListener('click', () => {
        const cropMode = document.querySelector('input[name="cropModeManual"]:checked').value;
        let center = null;
        if (cropMode === 'llm') {
            const selectedSubjectRadio = document.querySelector('input[name="manualSubjectSelect"]:checked');
            if (selectedSubjectRadio) {
                center = JSON.parse(selectedSubjectRadio.value);
            } else if (allSubjects.length > 0) {
                center = allSubjects[0].center;
            }
        }
        if (window.AdaptVideoAPI && window.AdaptVideoAPI.startConversion) {
            window.AdaptVideoAPI.startConversion(selectedTemplate, center);
        } else {
            console.error('startConversion function not found');
        }
    });

    document.getElementById('originalPreviewBtn').addEventListener('click', async () => {
        if (!fileId) {
            if (window.AdaptVideo && window.AdaptVideo.showStatus) {
                window.AdaptVideo.showStatus('請先選擇影片', 'error');
            }
            return;
        }
        if (window.AdaptVideoAPI && window.AdaptVideoAPI.generateOriginalPreview) {
            await window.AdaptVideoAPI.generateOriginalPreview();
        } else {
            console.error('generateOriginalPreview function not found');
        }
    });
}

// 檔案處理函數
function handleFile(file) {
    if (!file) {
        console.log('沒有選擇檔案');
        return;
    }
    
    if (file.size > 500 * 1024 * 1024) {
        if (window.AdaptVideo && window.AdaptVideo.showStatus) {
            window.AdaptVideo.showStatus('檔案大小超過500MB限制', 'error');
        }
        return;
    }
    
    console.log('處理檔案:', file.name, '大小:', (file.size / 1024 / 1024).toFixed(2) + 'MB');
    
    window.AdaptVideo && window.AdaptVideo.resetUIForNewVideo ? window.AdaptVideo.resetUIForNewVideo() : null;
    selectedFile = file;
    fileId = null;
    
    if (window.AdaptVideoAPI && window.AdaptVideoAPI.uploadAndAnalyze) {
        window.AdaptVideoAPI.uploadAndAnalyze(file);
    } else {
        console.error('uploadAndAnalyze function not found');
    }
}

async function handleExistingVideo(fId, thumb, vInfo, filename) {
    console.log('選擇歷史影片:', filename, 'fileId:', fId);
    
    window.AdaptVideo && window.AdaptVideo.resetUIForNewVideo ? window.AdaptVideo.resetUIForNewVideo() : null;
    selectedFile = null;
    fileId = fId;
    originalFilename = filename || '';
    
    if (thumb) {
        originalThumbnail = thumb;
        const videoThumbnailEl = document.getElementById('videoThumbnail');
        videoThumbnailEl.src = originalThumbnail;
        videoThumbnailEl.style.display = 'block';
    }
    
    if (vInfo) {
        videoInfo = vInfo;
        displayVideoInfo(videoInfo, originalFilename);
    }
    
    document.getElementById('videoPreview').style.display = 'block';
    if (window.AdaptVideo && window.AdaptVideo.showStatus) {
        window.AdaptVideo.showStatus('正在重新分析影片...', 'info');
    }
    
    if (window.AdaptVideoAPI && window.AdaptVideoAPI.triggerVideoAnalysis) {
        await window.AdaptVideoAPI.triggerVideoAnalysis();
    } else {
        console.error('triggerVideoAnalysis function not found');
    }
}

// 顯示函數
function displayVideoInfo(info, filename) {
    document.getElementById('videoPreview').style.display = 'block';
    
    const videoInfoDiv = document.getElementById('videoInfo');
    videoInfoDiv.innerHTML = `
        <div class="video-info-section">
            <div class="video-info-grid">
                <div class="info-item filename">
                    <span class="info-label">檔案名稱</span>
                    <span class="info-value">${filename || '未知檔案'}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">尺寸</span>
                    <span class="info-value">${info.width} × ${info.height}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">長寬比</span>
                    <span class="info-value">${(info.width / info.height).toFixed(2)}:1</span>
                </div>
                <div class="info-item">
                    <span class="info-label">時長</span>
                    <span class="info-value">${info.duration} 秒</span>
                </div>
                <div class="info-item">
                    <span class="info-label">幀率</span>
                    <span class="info-value">${info.fps} FPS</span>
                </div>
            </div>
        </div>
    `;
}

function handleAnalysisResult(result) {
    if (window.AdaptVideo && window.AdaptVideo.showStatus) {
        window.AdaptVideo.showStatus('AI 分析完成！', 'success');
    }
    
    if (result.analysis_options && result.analysis_options.length > 0) {
        allSubjects = result.analysis_options;
        displaySubjects(result.analysis_options);
    }
    
    if (result.suggestions) {
        displayAIAnalysis(result.suggestions);
    }
    
    if (result.recommended_template_names && result.recommended_template_names.length > 0) {
        displayRecommendedTemplates(result.recommended_template_names, result.analysis_options);
    }
    
    document.getElementById('templatesSection').style.display = 'block';
}

function displaySubjects(subjects) {
    const container = document.getElementById('subjectChoices');
    container.innerHTML = '<div class="multi-select-info">💡 您可以選擇多個主體，系統會計算最佳的中心點位置</div>';
    
    subjects.forEach((subject, index) => {
        const div = document.createElement('div');
        div.className = 'subject-choice';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.name = 'subjectSelect';
        checkbox.value = JSON.stringify(subject.center);
        checkbox.id = `subject-${index}`;
        
        const thumbnail = subject.thumbnail || '';
        const confidenceText = subject.confidence ? `(信心度: ${(subject.confidence * 100).toFixed(0)}%)` : '';
        
        div.innerHTML = `
            ${checkbox.outerHTML}
            ${thumbnail ? `<img src="${thumbnail}" alt="${subject.subject}">` : ''}
            <span>
                ${subject.subject}
                <br><small>${subject.importance || 'medium'} 重要性 ${confidenceText}</small>
            </span>
        `;
        
        checkbox.addEventListener('change', updateSelectedSubjects);
        container.appendChild(div);
        
        const actualCheckbox = div.querySelector('input');
        actualCheckbox.addEventListener('change', updateSelectedSubjects);
    });
}

function updateSelectedSubjects() {
    const checkboxes = document.querySelectorAll('input[name="subjectSelect"]:checked');
    selectedLLMSubjects = Array.from(checkboxes).map(cb => JSON.parse(cb.value));
    console.log('Selected subjects:', selectedLLMSubjects);
}

function displayAIAnalysis(suggestions) {
    const container = document.getElementById('aiAnalysisContent');
    const markdownContent = marked.parse(suggestions);
    container.innerHTML = `
        <div class="ai-analysis-section ai-analysis-overview">
            <div class="ai-analysis-header">
                🤖 AI 專業建議
            </div>
            <div class="ai-analysis-content markdown-content">
                ${markdownContent}
            </div>
        </div>
    `;
}

function displayRecommendedTemplates(templateNames, analysisOptions) {
    const container = document.getElementById('recommendedTemplates');
    container.innerHTML = '<div class="templates-title">🎯 AI 推薦模板</div>';
    
    templateNames.forEach(templateName => {
        const template = allTemplates.find(t => t.name === templateName);
        if (!template) return;
        
        const card = createTemplateCard(template, analysisOptions, true);
        container.appendChild(card);
    });
}

function createTemplateCard(template, analysisOptions, isRecommended = false) {
    const card = document.createElement('div');
    card.className = 'template-card';
    card.dataset.template = JSON.stringify(template);
    
    const aspectRatio = (template.width / template.height).toFixed(2);
    const isPortrait = template.height > template.width;
    const orientationEmoji = isPortrait ? '📱' : '🖥️';
    
    card.innerHTML = `
        <div class="template-name">${orientationEmoji} ${template.name}</div>
        <div class="template-size">${template.width} × ${template.height} (${aspectRatio}:1)</div>
        <div class="template-desc">${template.description}</div>
        ${isRecommended ? '<div class="recommendation-success">✨ AI 推薦</div>' : ''}
    `;
    
    card.addEventListener('click', () => {
        document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedTemplate = template;
        
        if (analysisOptions && analysisOptions.length > 0) {
            generateAndDisplayPreview(template, analysisOptions);
        }
    });
    
    return card;
}

async function generateAndDisplayPreview(template, analysisOptions) {
    const previewContainer = document.getElementById('templatePreview');
    previewContainer.innerHTML = '<div class="spinner"></div>';
    
    const center = selectedLLMSubjects.length > 0 ? null : (analysisOptions[0]?.center || null);
    const result = window.AdaptVideoAPI && window.AdaptVideoAPI.generatePreview ? 
        await window.AdaptVideoAPI.generatePreview(template.name, center) : null;
    
    if (!result && !window.AdaptVideoAPI) {
        console.error('generatePreview function not found');
        return;
    }
    
    if (result && result.preview_frames) {
        displayPreviewFrames(result, template);
    }
}

function displayPreviewFrames(result, template) {
    const container = document.getElementById('templatePreview');
    const isAdjusted = result.is_adjusted;
    
    let previewHtml = `
        <div class="preview-section">
            <h4>📱 ${template.name} 預覽</h4>
            <div class="preview-frames">
    `;
    
    result.preview_frames.forEach((frame, index) => {
        previewHtml += `<img src="${frame}" alt="Preview ${index + 1}" style="max-width: 200px; margin: 4px; border-radius: 4px;">`;
    });
    
    previewHtml += '</div>';
    
    if (isAdjusted) {
        previewHtml += `
            <div class="recommendation-warning">
                ${ICONS.warning} 主體位置已調整以適應模板尺寸
            </div>
        `;
    } else {
        previewHtml += `
            <div class="recommendation-success">
                ${ICONS.check} 完美適配，主體位置無需調整
            </div>
        `;
    }
    
    previewHtml += `
        <button class="btn btn-primary" id="previewConvertBtn">
            ${ICONS.download} 開始轉換
        </button>
    </div>`;
    
    container.innerHTML = previewHtml;
    
    // 為預覽轉換按鈕添加事件監聽器
    const previewConvertBtn = document.getElementById('previewConvertBtn');
    if (previewConvertBtn) {
        previewConvertBtn.addEventListener('click', () => {
            const center = selectedLLMSubjects.length > 0 ? null : (selectedLLMSubjects[0] || null);
            if (window.AdaptVideoAPI && window.AdaptVideoAPI.startConversion) {
                window.AdaptVideoAPI.startConversion(selectedTemplate, center);
            } else {
                console.error('startConversion function not found');
            }
        });
    }
}

function displayOriginalPreview(result) {
    const container = document.getElementById('originalPreviewContainer');
    if (!container) return;
    
    let previewHtml = `
        <div class="preview-section">
            <h4>🎬 原始影片預覽</h4>
            <div class="preview-frames">
    `;
    
    result.preview_frames.forEach((frame, index) => {
        previewHtml += `<img src="${frame}" alt="Original Preview ${index + 1}" style="max-width: 250px; margin: 4px; border-radius: 4px;">`;
    });
    
    previewHtml += '</div></div>';
    container.innerHTML = previewHtml;
}

function loadHistoryPage() {
    if (window.AdaptVideoAPI && window.AdaptVideoAPI.loadVideoHistory) {
        window.AdaptVideoAPI.loadVideoHistory();
    } else {
        console.error('loadVideoHistory function not found');
    }
}

function setupManualTab() {
    const container = document.getElementById('manualSubjectChoices');
    if (!allSubjects || allSubjects.length === 0) {
        container.innerHTML = '<p>尚未進行 AI 分析</p>';
        return;
    }
    
    container.innerHTML = '';
    allSubjects.forEach((subject, index) => {
        const div = document.createElement('div');
        div.className = 'subject-choice';
        
        const radio = document.createElement('input');
        radio.type = 'radio';
        radio.name = 'manualSubjectSelect';
        radio.value = JSON.stringify(subject.center);
        radio.id = `manual-subject-${index}`;
        
        const thumbnail = subject.thumbnail || '';
        const confidenceText = subject.confidence ? `(信心度: ${(subject.confidence * 100).toFixed(0)}%)` : '';
        
        div.innerHTML = `
            ${radio.outerHTML}
            ${thumbnail ? `<img src="${thumbnail}" alt="${subject.subject}">` : ''}
            <span>
                ${subject.subject}
                <br><small>${subject.importance || 'medium'} 重要性 ${confidenceText}</small>
            </span>
        `;
        
        container.appendChild(div);
    });
}

// 導出到全域作用域
window.AdaptVideoUI = {
    initializeNavigation,
    initializeTabs,
    initializeModal,
    initializeFileUpload,
    initializeEventListeners,
    handleFile,
    handleExistingVideo,
    displayVideoInfo,
    handleAnalysisResult,
    displaySubjects,
    updateSelectedSubjects,
    displayAIAnalysis,
    displayRecommendedTemplates,
    createTemplateCard,
    generateAndDisplayPreview,
    displayPreviewFrames,
    displayOriginalPreview,
    loadHistoryPage,
    setupManualTab
};