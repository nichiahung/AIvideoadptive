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
    // 標籤功能已移除，改為模式選擇
    console.log('Tabs have been replaced with conversion mode selection');
}

// 處理轉換模式變化
function handleConversionModeChange(event) {
    // 現在只是記錄選擇，不立即切換界面
    console.log('Selected conversion mode:', event.target.value);
}

// 處理開始轉換設定按鈕
function handleProceedWithMode() {
    const selectedMode = document.querySelector('input[name="conversionMode"]:checked').value;
    
    // 隱藏轉換模式選擇區域
    document.getElementById('conversionModeSection').style.display = 'none';
    
    // 顯示轉換設定區域
    document.getElementById('conversionSection').style.display = 'block';
    
    // 首先隱藏所有轉換內容
    document.querySelectorAll('.conversion-content').forEach(content => {
        content.style.display = 'none';
        content.classList.remove('active');
    });
    
    // 只顯示選擇的轉換內容
    const targetSection = document.getElementById(`${selectedMode}ConversionSection`);
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.classList.add('active');
        
        // 根據模式設置相應的功能
        if (selectedMode === 'manual' && fileId) {
            setupManualTab();
        } else if (selectedMode === 'position' && fileId) {
            setupPositionTab();
        } else if (selectedMode === 'smart') {
            // 設置智慧轉換模式
            setupSmartConversionMode();
            // 啟用自訂需求功能
            enableCustomRequirementsAfterUpload();
        }
    }
    
    console.log(`Proceeding with ${selectedMode} conversion mode`);
}

// 處理返回轉換模式選擇
function handleBackToModeSelection() {
    // 隱藏轉換設定區域
    document.getElementById('conversionSection').style.display = 'none';
    
    // 顯示轉換模式選擇區域
    document.getElementById('conversionModeSection').style.display = 'block';
    
    console.log('Returning to conversion mode selection');
}

function initializeModal() {
    const modal = document.getElementById('videoHistoryModal');
    const showHistoryBtn = document.getElementById('showHistoryBtn');
    const closeBtn = document.querySelector('.close-btn');

    if (!modal) {
        console.error('videoHistoryModal not found');
        return;
    }
    
    if (!showHistoryBtn) {
        console.error('showHistoryBtn not found');
        return;
    }
    
    if (!closeBtn) {
        console.error('close-btn not found');
        return;
    }

    showHistoryBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('History button clicked'); // 調試日誌
        
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
    // 轉換模式選擇監聽器
    document.querySelectorAll('input[name="conversionMode"]').forEach(radio => {
        radio.addEventListener('change', handleConversionModeChange);
    });

    // 自訂需求按鈕監聽器
    const sendRequirementsBtn = document.getElementById('sendRequirementsBtn');
    if (sendRequirementsBtn) {
        sendRequirementsBtn.addEventListener('click', handleCustomRequirements);
    }

    // 自訂需求展開/收合按鈕監聽器
    const toggleCustomRequirementsBtn = document.getElementById('toggleCustomRequirementsBtn');
    if (toggleCustomRequirementsBtn) {
        toggleCustomRequirementsBtn.addEventListener('click', toggleCustomRequirements);
    }

    // 開始轉換設定按鈕監聽器
    const proceedWithModeBtn = document.getElementById('proceedWithModeBtn');
    if (proceedWithModeBtn) {
        proceedWithModeBtn.addEventListener('click', handleProceedWithMode);
    }

    // 返回轉換模式選擇按鈕監聽器
    const backToModeSelectionSmart = document.getElementById('backToModeSelectionSmart');
    if (backToModeSelectionSmart) {
        backToModeSelectionSmart.addEventListener('click', handleBackToModeSelection);
    }
    
    const backToModeSelectionManual = document.getElementById('backToModeSelectionManual');
    if (backToModeSelectionManual) {
        backToModeSelectionManual.addEventListener('click', handleBackToModeSelection);
    }
    
    const backToModeSelectionPosition = document.getElementById('backToModeSelectionPosition');
    if (backToModeSelectionPosition) {
        backToModeSelectionPosition.addEventListener('click', handleBackToModeSelection);
    }

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

    // 手動選版位的轉換按鈕
    document.getElementById('convertBtnPosition').addEventListener('click', () => {
        const center = getManualSelectedPosition();
        if (!center) {
            updatePositionStatus('請先在影片縮圖上點擊選擇版位', 'error');
            return;
        }
        if (!currentTemplate) {
            updatePositionStatus('請先選擇輸出尺寸模板', 'error');
            return;
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
    
    // 顯示轉換模式選擇區域
    document.getElementById('conversionModeSection').style.display = 'block';
    
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
    
    // 更新全域變數
    if (window.setGlobalVar) {
        window.setGlobalVar('selectedFile', null);
        window.setGlobalVar('fileId', fileId);
        window.setGlobalVar('originalFilename', originalFilename);
    }
    
    if (thumb) {
        originalThumbnail = thumb;
        if (window.setGlobalVar) {
            window.setGlobalVar('originalThumbnail', originalThumbnail);
        }
        const videoThumbnailEl = document.getElementById('videoThumbnail');
        videoThumbnailEl.src = originalThumbnail;
        videoThumbnailEl.style.display = 'block';
    }
    
    if (vInfo) {
        videoInfo = vInfo;
        if (window.setGlobalVar) {
            window.setGlobalVar('videoInfo', videoInfo);
        }
        displayVideoInfo(videoInfo, originalFilename);
    }
    
    document.getElementById('videoPreview').style.display = 'block';
    
    // 顯示轉換模式選擇區域
    const conversionModeSection = document.getElementById('conversionModeSection');
    if (conversionModeSection) {
        conversionModeSection.style.display = 'block';
    }
    
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
    // AI專業建議只在智慧轉換模式的AI推薦區塊中顯示
    const smartContent = document.getElementById('smartConversionContent');
    if (smartContent) {
        const markdownContent = marked.parse(suggestions);
        const analysisHTML = `
            <div class="ai-analysis-section ai-analysis-overview">
                <div class="ai-analysis-header">
                    🤖 AI 專業建議
                </div>
                <div class="ai-analysis-content markdown-content">
                    ${markdownContent}
                </div>
            </div>
        `;
        smartContent.innerHTML = analysisHTML;
    }
    
    // 清空舊的aiAnalysisContent區域（不再需要）
    const container = document.getElementById('aiAnalysisContent');
    if (container) {
        container.innerHTML = '';
    }
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
                ${window.AdaptVideo && window.AdaptVideo.ICONS ? window.AdaptVideo.ICONS.warning : '⚠️'} 主體位置已調整以適應模板尺寸
            </div>
        `;
    } else {
        previewHtml += `
            <div class="recommendation-success">
                ${window.AdaptVideo && window.AdaptVideo.ICONS ? window.AdaptVideo.ICONS.check : '✅'} 完美適配，主體位置無需調整
            </div>
        `;
    }
    
    previewHtml += `
        <button class="btn btn-primary" id="previewConvertBtn">
            ${window.AdaptVideo && window.AdaptVideo.ICONS ? window.AdaptVideo.ICONS.download : '📥'} 開始轉換
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
    const frames = result.preview_frames || [];
    if (frames.length === 0) return;
    
    const videoThumbnail = document.getElementById('videoThumbnail');
    const previewBtn = document.getElementById('originalPreviewBtn');
    
    if (!videoThumbnail || !previewBtn) return;
    
    // 保存原始縮圖以便恢復
    const originalSrc = videoThumbnail.src;
    let currentFrameIndex = 0;
    let animationInterval = null;
    let isPlaying = false;
    
    // 播放一輪動畫
    function playOneCycle() {
        if (isPlaying) return; // 防止重複點擊
        
        isPlaying = true;
        currentFrameIndex = 0;
        previewBtn.textContent = '⏸ 播放中...';
        previewBtn.disabled = true; // 播放時禁用按鈕
        
        // 立即顯示第一幀
        videoThumbnail.src = frames[0];
        
        let frameCount = 0;
        const totalFrames = frames.length;
        
        // 設置動畫播放
        animationInterval = setInterval(() => {
            frameCount++;
            currentFrameIndex = frameCount % totalFrames;
            videoThumbnail.src = frames[currentFrameIndex];
            
            // 播放完一輪後停止
            if (frameCount >= totalFrames) {
                setTimeout(() => {
                    stopAnimation();
                }, 200); // 等待最後一幀顯示完成
            }
        }, 200); // 固定 200ms 速度
    }
    
    // 停止動畫並恢復
    function stopAnimation() {
        if (animationInterval) {
            clearInterval(animationInterval);
            animationInterval = null;
        }
        
        // 恢復原始縮圖
        videoThumbnail.src = originalSrc;
        previewBtn.textContent = '🎬 動態預覽';
        previewBtn.disabled = false;
        isPlaying = false;
    }
    
    // 移除原始的點擊事件
    const newBtn = previewBtn.cloneNode(true);
    newBtn.id = 'originalPreviewBtn'; // 確保保留 ID
    previewBtn.parentNode.replaceChild(newBtn, previewBtn);
    
    // 添加新的點擊事件 - 每次點擊播放一輪
    newBtn.addEventListener('click', playOneCycle);
}


function loadHistoryPage() {
    if (window.AdaptVideoAPI && window.AdaptVideoAPI.loadVideoHistory) {
        window.AdaptVideoAPI.loadVideoHistory();
    } else {
        console.error('loadVideoHistory function not found');
    }
}

function setupManualTab() {
    // 設置模板網格
    setupManualTemplateGrid();
    
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

// 設置手動選版位標籤
function setupPositionTab() {
    // 設置模板網格
    setupPositionTemplateGrid();
    
    // 設置版位選擇器
    setupManualPositionSelector();
    
    // 更新狀態
    updatePositionStatus('請先選擇輸出尺寸模板');
}

// 設置手動模板網格
function setupManualTemplateGrid() {
    const gridContainer = document.getElementById('templatesGridManual');
    if (!allTemplates || allTemplates.length === 0) {
        gridContainer.innerHTML = '<p>暫無可用模板</p>';
        return;
    }
    
    gridContainer.innerHTML = '';
    allTemplates.forEach(template => {
        const card = document.createElement('div');
        card.className = 'template-card';
        card.innerHTML = `
            <div class="template-info">
                <div class="template-name">${template.name}</div>
                <div class="template-size">${template.width} × ${template.height}</div>
                <div class="template-desc">${template.description || ''}</div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            document.querySelectorAll('#templatesGridManual .template-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            
            // 更新當前選擇的模板
            updateCurrentTemplate(template);
            
            // 啟用轉換按鈕
            const convertBtn = document.getElementById('convertBtnManual');
            if (convertBtn) {
                convertBtn.disabled = false;
            }
        });
        
        gridContainer.appendChild(card);
    });
}

// 設置手動選版位模板網格
function setupPositionTemplateGrid() {
    const gridContainer = document.getElementById('templatesGridPosition');
    if (!allTemplates || allTemplates.length === 0) {
        gridContainer.innerHTML = '<p>暫無可用模板</p>';
        return;
    }
    
    gridContainer.innerHTML = '';
    allTemplates.forEach(template => {
        const card = document.createElement('div');
        card.className = 'template-card';
        card.innerHTML = `
            <div class="template-info">
                <div class="template-name">${template.name}</div>
                <div class="template-size">${template.width} × ${template.height}</div>
                <div class="template-desc">${template.description || ''}</div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            document.querySelectorAll('#templatesGridPosition .template-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            
            // 更新當前選擇的模板
            updateCurrentTemplate(template);
            
            // 更新狀態
            if (manualSelectedCenter) {
                updatePositionStatus('已選擇模板和版位，可以開始轉換', 'success');
                document.getElementById('convertBtnPosition').disabled = false;
            } else {
                updatePositionStatus('請在影片縮圖上點擊選擇版位');
            }
        });
        
        gridContainer.appendChild(card);
    });
}

// 更新手動選版位狀態
function updatePositionStatus(message, type = 'info') {
    const statusEl = document.getElementById('positionStatus');
    if (statusEl) {
        statusEl.textContent = message;
        statusEl.className = `position-status ${type}`;
        
        // 根據類型設置顏色
        switch(type) {
            case 'success':
                statusEl.style.color = 'var(--success)';
                break;
            case 'error':
                statusEl.style.color = 'var(--error)';
                break;
            default:
                statusEl.style.color = 'var(--gray-600)';
        }
    }
}

// 手動版位選擇相關變數
let manualSelectedCenter = null;
let currentTemplate = null;

// 處理版位選擇模式切換
function handlePositionModeChange(event) {
    const manualSelector = document.getElementById('manualPositionSelector');
    if (event.target.value === 'manual') {
        manualSelector.style.display = 'block';
        setupManualPositionSelector();
    } else {
        manualSelector.style.display = 'none';
    }
}

// 設置手動版位選擇器
function setupManualPositionSelector() {
    const previewImage = document.getElementById('positionPreviewImage');
    if (!originalThumbnail) {
        console.log('originalThumbnail is not available');
        return;
    }
    
    previewImage.src = originalThumbnail;
    previewImage.onload = () => {
        const cropGuide = document.getElementById('cropGuide');
        const centerPoint = document.getElementById('centerPoint');
        
        // 移除舊的事件監聽器（如果存在）
        previewImage.onclick = null;
        
        // 添加點擊事件監聽器
        previewImage.onclick = (event) => {
            const rect = previewImage.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            // 計算相對於原始圖片的位置（0-1之間）
            const relativeX = x / previewImage.clientWidth;
            const relativeY = y / previewImage.clientHeight;
            
            // 儲存選擇的中心點
            manualSelectedCenter = {
                x: relativeX,
                y: relativeY
            };
            
            // 顯示中心點
            centerPoint.style.left = `${x}px`;
            centerPoint.style.top = `${y}px`;
            centerPoint.style.display = 'block';
            
            // 如果有選擇的模板，顯示裁切預覽
            if (currentTemplate) {
                showCropPreview(relativeX, relativeY);
                
                // 更新手動選版位的狀態
                if (document.getElementById('positionConversionSection').classList.contains('active')) {
                    updatePositionStatus('已選擇版位和模板，可以開始轉換', 'success');
                    document.getElementById('convertBtnPosition').disabled = false;
                }
            } else {
                // 如果在手動選版位模式但沒有選擇模板
                if (document.getElementById('positionConversionSection').classList.contains('active')) {
                    updatePositionStatus('已選擇版位，請選擇輸出尺寸模板');
                }
            }
            
            console.log('Manual position selected:', manualSelectedCenter);
        };
    };
    
    previewImage.onerror = () => {
        console.error('Failed to load preview image:', originalThumbnail);
    };
}

// 顯示裁切預覽
function showCropPreview(centerX, centerY) {
    if (!currentTemplate) return;
    
    const previewImage = document.getElementById('positionPreviewImage');
    const cropGuide = document.getElementById('cropGuide');
    
    // 計算目標比例
    const targetAspectRatio = currentTemplate.width / currentTemplate.height;
    const imageAspectRatio = previewImage.clientWidth / previewImage.clientHeight;
    
    let cropWidth, cropHeight;
    
    if (targetAspectRatio > imageAspectRatio) {
        // 目標更寬，以寬度為準
        cropWidth = previewImage.clientWidth;
        cropHeight = cropWidth / targetAspectRatio;
    } else {
        // 目標更高，以高度為準
        cropHeight = previewImage.clientHeight;
        cropWidth = cropHeight * targetAspectRatio;
    }
    
    // 計算裁切框的位置
    const left = Math.max(0, Math.min(
        previewImage.clientWidth - cropWidth,
        centerX * previewImage.clientWidth - cropWidth / 2
    ));
    const top = Math.max(0, Math.min(
        previewImage.clientHeight - cropHeight,
        centerY * previewImage.clientHeight - cropHeight / 2
    ));
    
    // 顯示裁切框
    cropGuide.style.left = `${left}px`;
    cropGuide.style.top = `${top}px`;
    cropGuide.style.width = `${cropWidth}px`;
    cropGuide.style.height = `${cropHeight}px`;
    cropGuide.style.display = 'block';
}

// 獲取手動選擇的版位
function getManualSelectedPosition() {
    return manualSelectedCenter;
}

// 更新當前選擇的模板（需要在模板選擇時調用）
function updateCurrentTemplate(template) {
    currentTemplate = template;
    selectedTemplate = template;
    
    // 如果處於手動版位選擇模式且已選擇中心點，更新預覽
    const positionMode = document.querySelector('input[name="positionMode"]:checked');
    if (positionMode && positionMode.value === 'manual' && manualSelectedCenter) {
        showCropPreview(manualSelectedCenter.x, manualSelectedCenter.y);
    }
}

// 重置手動版位選擇狀態
function resetManualPositionState() {
    manualSelectedCenter = null;
    currentTemplate = null;
    
    // 隱藏裁切預覽和中心點
    const cropGuide = document.getElementById('cropGuide');
    const centerPoint = document.getElementById('centerPoint');
    const previewImage = document.getElementById('positionPreviewImage');
    
    if (cropGuide) cropGuide.style.display = 'none';
    if (centerPoint) centerPoint.style.display = 'none';
    if (previewImage) {
        previewImage.src = '';
        previewImage.onclick = null;
    }
    
    // 重置轉換按鈕和狀態
    const convertBtnPosition = document.getElementById('convertBtnPosition');
    if (convertBtnPosition) {
        convertBtnPosition.disabled = true;
    }
    
    updatePositionStatus('請先選擇輸出尺寸模板');
    
    // 清除模板選擇狀態
    document.querySelectorAll('#templatesGridPosition .template-card').forEach(c => c.classList.remove('selected'));
}

// 導出重置函數到全域作用域
window.resetManualPositionState = resetManualPositionState;
window.clearConversationHistory = clearConversationHistory;
window.handleConversionModeChange = handleConversionModeChange;
window.showCustomRequirementsAfterAnalysis = showCustomRequirementsAfterAnalysis;

// 啟用自訂需求功能（在AI分析完成後調用）
function enableCustomRequirementsAfterUpload() {
    // 檢查是否為智慧轉換模式
    const selectedMode = document.querySelector('input[name="conversionMode"]:checked');
    if (selectedMode && selectedMode.value === 'smart') {
        const aiRequirementsSection = document.getElementById('aiCustomRequirementsSection');
        const sendBtn = document.getElementById('sendRequirementsBtn');
        
        // 顯示自訂需求區域（但保持內容收合狀態）
        if (aiRequirementsSection) {
            aiRequirementsSection.style.display = 'block';
        }
        
        // 啟用按鈕
        if (sendBtn) {
            sendBtn.disabled = false;
        }
        
        // 確保內容區域保持收合狀態
        const customRequirementsContent = document.getElementById('customRequirementsContent');
        if (customRequirementsContent) {
            customRequirementsContent.style.display = 'none';
        }
    }
}

// 在AI分析完成時顯示自訂需求區域
function showCustomRequirementsAfterAnalysis() {
    const selectedMode = document.querySelector('input[name="conversionMode"]:checked');
    if (selectedMode && selectedMode.value === 'smart') {
        const aiRequirementsSection = document.getElementById('aiCustomRequirementsSection');
        if (aiRequirementsSection) {
            aiRequirementsSection.style.display = 'block';
        }
    }
}

// === 自訂需求展開/收合功能 ===

// 切換自訂需求區域的顯示/隱藏
function toggleCustomRequirements() {
    const content = document.getElementById('customRequirementsContent');
    const toggleIcon = document.getElementById('toggleIcon');
    const toggleBtn = document.getElementById('toggleCustomRequirementsBtn');
    
    if (!content || !toggleIcon || !toggleBtn) return;
    
    const isExpanded = content.style.display !== 'none';
    
    if (isExpanded) {
        // 收合
        content.style.display = 'none';
        toggleIcon.textContent = '▼';
        toggleBtn.innerHTML = '<span class="icon">📝</span>有特殊需求？點此展開自訂設定 <span id="toggleIcon" style="float: right;">▼</span>';
    } else {
        // 展開
        content.style.display = 'block';
        toggleIcon.textContent = '▲';
        toggleBtn.innerHTML = '<span class="icon">📝</span>收合自訂需求設定 <span id="toggleIcon" style="float: right;">▲</span>';
    }
}

// === 對話記憶功能 ===

// 處理自訂需求
async function handleCustomRequirements() {
    const requirementsText = document.getElementById('customRequirements').value.trim();
    const statusEl = document.getElementById('requirementsStatus');
    const sendBtn = document.getElementById('sendRequirementsBtn');
    
    if (!requirementsText) {
        statusEl.textContent = '請先輸入您的需求';
        statusEl.style.color = 'var(--error)';
        return;
    }
    
    if (!fileId) {
        statusEl.textContent = '請先上傳影片';
        statusEl.style.color = 'var(--error)';
        return;
    }
    
    // 更新內部對話歷史（不顯示給用戶）
    conversationHistory.push({
        type: 'user',
        message: requirementsText,
        timestamp: new Date().toLocaleTimeString('zh-TW', { 
            hour: '2-digit', 
            minute: '2-digit' 
        })
    });
    
    // 更新按鈕狀態
    sendBtn.disabled = true;
    sendBtn.textContent = '🔄 分析中...';
    statusEl.textContent = '正在處理您的需求...';
    statusEl.style.color = 'var(--primary)';
    
    try {
        // 調用 API 進行自訂需求分析
        if (window.AdaptVideoAPI && window.AdaptVideoAPI.analyzeWithCustomRequirements) {
            const response = await window.AdaptVideoAPI.analyzeWithCustomRequirements(fileId, requirementsText, conversationHistory);
            
            if (response.ai_response) {
                // 添加 AI 回應到內部對話歷史（不顯示給用戶）
                conversationHistory.push({
                    type: 'ai',
                    message: response.ai_response,
                    timestamp: new Date().toLocaleTimeString('zh-TW', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                    })
                });
            }
            
            // 更新推薦結果
            if (response.recommendations) {
                updateSmartConversionContent(response);
            }
            
            statusEl.textContent = '分析完成！';
            statusEl.style.color = 'var(--success)';
            
            // 保留需求內容，不清空輸入框
            // document.getElementById('customRequirements').value = ''; // 移除此行
            
        } else {
            throw new Error('API function not found');
        }
    } catch (error) {
        console.error('Custom requirements analysis failed:', error);
        statusEl.textContent = '分析失敗，請稍後再試';
        statusEl.style.color = 'var(--error)';
        
        // 添加錯誤訊息到內部對話歷史
        conversationHistory.push({
            type: 'ai',
            message: '抱歉，我暫時無法處理您的需求，請稍後再試。',
            timestamp: new Date().toLocaleTimeString('zh-TW', { 
                hour: '2-digit', 
                minute: '2-digit' 
            })
        });
    } finally {
        // 恢復按鈕狀態
        sendBtn.disabled = false;
        sendBtn.textContent = '🚀 重新分析並推薦';
        
        // 3秒後清除狀態訊息
        setTimeout(() => {
            statusEl.textContent = '';
        }, 3000);
    }
}


// 清除對話歷史
function clearConversationHistory() {
    conversationHistory = [];
    if (window.setGlobalVar) {
        window.setGlobalVar('conversationHistory', conversationHistory);
    }
    
    // 隱藏自訂需求區域
    const aiRequirementsSection = document.getElementById('aiCustomRequirementsSection');
    if (aiRequirementsSection) {
        aiRequirementsSection.style.display = 'none';
    }
    
    
    // 清空自訂需求輸入框
    const requirementsInput = document.getElementById('customRequirements');
    if (requirementsInput) {
        requirementsInput.value = '';
    }
    
    // 清空狀態訊息並禁用按鈕
    const statusEl = document.getElementById('requirementsStatus');
    const sendBtn = document.getElementById('sendRequirementsBtn');
    if (statusEl) {
        statusEl.textContent = '';
    }
    if (sendBtn) {
        sendBtn.disabled = true;
    }
}

// 設置智慧轉換模式
function setupSmartConversionMode() {
    const smartContent = document.getElementById('smartConversionContent');
    if (!smartContent) return;
    
    // AI專業建議只需要顯示載入狀態，實際內容由displayAIAnalysis函數處理
    if (smartContent.innerHTML.trim() === '' || smartContent.innerHTML.includes('正在分析影片內容')) {
        smartContent.innerHTML = `
            <div class="spinner"></div>
            <p style="text-align: center; color: var(--gray-500); margin-top: 12px;">正在載入 AI 專業建議...</p>
        `;
    }
}

// 更新智慧轉換內容（用於顯示自訂需求的結果）
function updateSmartConversionContent(response) {
    const contentEl = document.getElementById('smartConversionContent');
    if (!contentEl) return;
    
    // 如果有新的AI分析建議，更新顯示
    if (response.suggestions) {
        // 更新AI專業建議內容（這與AI推薦結果是同一內容）
        displayAIAnalysis(response.suggestions);
    }
    
    // 如果有新的分析選項，更新主體選擇
    if (response.analysis_options && response.analysis_options.length > 0) {
        allSubjects = response.analysis_options;
        displaySubjects(response.analysis_options);
    }
    
    // 如果有新的推薦模板，更新模板顯示
    if (response.recommended_template_names && response.recommended_template_names.length > 0) {
        displayRecommendedTemplates(response.recommended_template_names, response.analysis_options);
    }
}

function displayVideoComparison(comparisonData) {
    const comparisonContent = document.getElementById('comparisonContent');
    if (!comparisonContent) return;
    
    const original = comparisonData.original;
    const converted = comparisonData.converted;
    
    if (!original || !converted) {
        comparisonContent.innerHTML = '<div style="text-align: center; padding: 20px; color: red;">無法載入影片資料</div>';
        return;
    }
    
    // 計算影片顯示尺寸，維持原始比例但大小相近
    const maxDisplayWidth = 400;  // 最大顯示寬度
    const maxDisplayHeight = 300; // 最大顯示高度
    
    function calculateDisplaySize(width, height) {
        if (!width || !height) return { width: maxDisplayWidth, height: maxDisplayHeight };
        
        const aspectRatio = width / height;
        let displayWidth, displayHeight;
        
        if (aspectRatio > 1) {
            // 橫向影片
            displayWidth = Math.min(maxDisplayWidth, width);
            displayHeight = displayWidth / aspectRatio;
            if (displayHeight > maxDisplayHeight) {
                displayHeight = maxDisplayHeight;
                displayWidth = displayHeight * aspectRatio;
            }
        } else {
            // 直向影片
            displayHeight = Math.min(maxDisplayHeight, height);
            displayWidth = displayHeight * aspectRatio;
            if (displayWidth > maxDisplayWidth) {
                displayWidth = maxDisplayWidth;
                displayHeight = displayWidth / aspectRatio;
            }
        }
        
        return { 
            width: Math.round(displayWidth), 
            height: Math.round(displayHeight) 
        };
    }
    
    const originalDisplaySize = calculateDisplaySize(original.info.width, original.info.height);
    const convertedDisplaySize = calculateDisplaySize(converted.info.width, converted.info.height);
    
    const comparisonHtml = `
        <div class="comparison-container">
            <!-- 原始影片 -->
            <div class="comparison-video">
                <h5>📹 原始影片</h5>
                <div class="comparison-video-player">
                    <video 
                        id="originalVideo"
                        src="${original.url}"
                        style="width: ${originalDisplaySize.width}px; height: ${originalDisplaySize.height}px;"
                        controls
                        muted
                        preload="metadata"
                        onloadedmetadata="this.currentTime = 0.1">
                        您的瀏覽器不支援影片播放
                    </video>
                </div>
                <div class="comparison-controls">
                    <button class="video-control-btn" onclick="toggleVideoPlayback('originalVideo')">
                        <span>▶</span> 播放/暫停
                    </button>
                    <button class="video-control-btn" onclick="restartVideo('originalVideo')">
                        <span>🔄</span> 重新播放
                    </button>
                </div>
                <div class="comparison-info">
                    <div class="comparison-info-item">
                        <span>檔案:</span>
                        <span title="${original.filename}">${original.filename.length > 20 ? original.filename.substring(0, 20) + '...' : original.filename}</span>
                    </div>
                    <div class="comparison-info-item">
                        <span>尺寸:</span>
                        <span>${original.info.width || '未知'} × ${original.info.height || '未知'}</span>
                    </div>
                    <div class="comparison-info-item">
                        <span>長寬比:</span>
                        <span>${original.info.width && original.info.height ? 
                            (original.info.width / original.info.height).toFixed(2) + ':1' : '未知'}</span>
                    </div>
                    <div class="comparison-info-item">
                        <span>時長:</span>
                        <span>${original.info.duration ? original.info.duration.toFixed(1) : '未知'} 秒</span>
                    </div>
                    <div class="comparison-info-item">
                        <span>幀率:</span>
                        <span>${original.info.fps ? original.info.fps.toFixed(1) : '未知'} fps</span>
                    </div>
                </div>
            </div>
            
            <!-- 轉換後影片 -->
            <div class="comparison-video">
                <h5>✨ 轉換後影片</h5>
                <div class="comparison-video-player">
                    <video 
                        id="convertedVideo"
                        src="${converted.url}"
                        style="width: ${convertedDisplaySize.width}px; height: ${convertedDisplaySize.height}px;"
                        controls
                        muted
                        preload="metadata"
                        onloadedmetadata="this.currentTime = 0.1">
                        您的瀏覽器不支援影片播放
                    </video>
                </div>
                <div class="comparison-controls">
                    <button class="video-control-btn" onclick="toggleVideoPlayback('convertedVideo')">
                        <span>▶</span> 播放/暫停
                    </button>
                    <button class="video-control-btn" onclick="restartVideo('convertedVideo')">
                        <span>🔄</span> 重新播放
                    </button>
                    <button class="video-control-btn" onclick="syncVideos()">
                        <span>🔗</span> 同步播放
                    </button>
                </div>
                <div class="comparison-info">
                    <div class="comparison-info-item">
                        <span>檔案:</span>
                        <span title="${converted.filename}">${converted.filename.length > 20 ? converted.filename.substring(0, 20) + '...' : converted.filename}</span>
                    </div>
                    <div class="comparison-info-item">
                        <span>尺寸:</span>
                        <span>${converted.info.width || '未知'} × ${converted.info.height || '未知'}</span>
                    </div>
                    <div class="comparison-info-item">
                        <span>長寬比:</span>
                        <span>${converted.info.width && converted.info.height ? 
                            (converted.info.width / converted.info.height).toFixed(2) + ':1' : '未知'}</span>
                    </div>
                    <div class="comparison-info-item">
                        <span>時長:</span>
                        <span>${converted.info.duration ? converted.info.duration.toFixed(1) : '未知'} 秒</span>
                    </div>
                    <div class="comparison-info-item">
                        <span>幀率:</span>
                        <span>${converted.info.fps ? converted.info.fps.toFixed(1) : '未知'} fps</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="comparison-notes">
            <p><strong>使用說明：</strong></p>
            <ul>
                <li>點擊播放器或按鈕控制影片播放</li>
                <li>使用「同步播放」讓兩個影片同時播放以便比較</li>
                <li>影片已依比例縮放以便於比較，實際尺寸請參考資訊欄</li>
            </ul>
        </div>
    `;
    
    comparisonContent.innerHTML = comparisonHtml;
    
    // 初始化影片控制函數
    initializeVideoComparison();
    
    // 初始化關閉按鈕
    const closeBtn = document.getElementById('closeCompareBtn');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            document.getElementById('comparisonSection').style.display = 'none';
        });
    }
}

function initializeVideoComparison() {
    // 全局變量來跟蹤同步播放狀態
    window.videoSyncEnabled = false;
}

// 影片控制函數
function toggleVideoPlayback(videoId) {
    const video = document.getElementById(videoId);
    if (!video) return;
    
    if (video.paused) {
        video.play();
    } else {
        video.pause();
    }
}

function restartVideo(videoId) {
    const video = document.getElementById(videoId);
    if (!video) return;
    
    video.currentTime = 0;
    video.play();
}

function syncVideos() {
    const originalVideo = document.getElementById('originalVideo');
    const convertedVideo = document.getElementById('convertedVideo');
    
    if (!originalVideo || !convertedVideo) return;
    
    // 同步到原始影片的時間點
    convertedVideo.currentTime = originalVideo.currentTime;
    
    // 如果原始影片在播放，則同時播放轉換後的影片
    if (!originalVideo.paused) {
        convertedVideo.play();
    } else {
        convertedVideo.pause();
    }
    
    // 顯示同步完成提示
    if (window.AdaptVideo && window.AdaptVideo.showStatus) {
        window.AdaptVideo.showStatus('影片已同步', 'success');
    }
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
    displayVideoComparison,
    initializeVideoComparison,
    loadHistoryPage,
    setupManualTab,
    toggleCustomRequirements
};

// 將影片控制函數添加到全局作用域以便 HTML 調用
window.toggleVideoPlayback = toggleVideoPlayback;
window.restartVideo = restartVideo;
window.syncVideos = syncVideos;