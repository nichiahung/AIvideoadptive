/**
 * AdaptVideo 主應用程式邏輯
 */

// 全域變數
let selectedFile = null;
let selectedTemplate = null;
let fileId = null;
let selectedLLMSubjects = [];
let originalThumbnail = '';
let videoInfo = {};
let allTemplates = [];
let allSubjects = [];
let originalFilename = '';
let currentCustomPrompt = '';
let conversationHistory = [];

// 圖標定義
const ICONS = {
    check: `<svg class="icon-svg" viewBox="64 64 896 896" focusable="false" data-icon="check-circle" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"></path><path d="M699.1 316.2c-4.9-4.9-12.8-4.9-17.7 0L469 528.4 342.9 402.3c-4.9-4.9-12.8-4.9-17.7 0s-4.9 12.8 0 17.7l138.4 138.4c4.9 4.9 12.8 4.9 17.7 0l224.5-224.5c4.8-4.9 4.8-12.8-.1-17.7z"></path></svg>`,
    warning: `<svg class="icon-svg" viewBox="64 64 896 896" focusable="false" data-icon="exclamation-circle" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"></path><path d="M496 632h32c4.4 0 8-3.6 8-8V448c0-4.4-3.6-8-8-8h-32c-4.4 0-8 3.6-8 8v176c0 4.4 3.6 8 8 8zm0-240h32c4.4 0 8-3.6 8-8v-32c0-4.4-3.6-8-8-8h-32c-4.4 0-8 3.6-8 8v32c0 4.4 3.6 8 8 8z"></path></svg>`,
    download: `<svg class="icon-svg" viewBox="64 64 896 896" focusable="false" data-icon="download" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M505.7 661a8 8 0 0012.6 0l112-141.7c4.1-5.2.4-12.9-6.3-12.9h-74.1V168c0-4.4-3.6-8-8-8h-60c-4.4 0-8 3.6-8 8v338.3H400c-6.7 0-10.4 7.7-6.3 12.9l112 141.8zM878 626h-138c-4.4 0-8 3.6-8 8v60c0 4.4 3.6 8 8 8h138c35.3 0 64-28.7 64-64V465c0-35.3-28.7-64-64-64h-138c-4.4 0-8 3.6-8 8v60c0 4.4 3.6 8 8 8h138v154zM146 626h138c4.4 0 8 3.6 8 8v60c0 4.4-3.6 8-8 8H146c-35.3 0-64-28.7-64-64V465c0-35.3 28.7-64 64-64h138c4.4 0 8 3.6 8 8v60c0 4.4-3.6-8-8 8H146v154z"></path></svg>`,
    adjust: `<svg class="icon-svg" viewBox="64 64 896 896" focusable="false" data-icon="setting" width="1em" height="1em" fill="currentColor" aria-hidden="true"><path d="M924.8 625.7l-65.5-56c3.1-19 4.7-38.4 4.7-57.8s-1.6-38.8-4.7-57.8l65.5-56a32.03 32.03 0 009.3-35.2l-.9-2.6a443.74 443.74 0 00-79.7-137.9l-1.8-2.1a32.12 32.12 0 00-35.1-9.5l-81.3 28.9c-30-24.6-63.5-44-99.7-57.6l-15.7-85a32.05 32.05 0 00-25.8-25.7l-2.7-.5c-52.1-9.4-106.9-9.4-159 0l-2.7.5a32.05 32.05 0 00-25.8 25.7l-15.8 85.4a351.86 351.86 0 00-99 57.4l-81.9-29.1a32 32 0 00-35.1 9.5l-1.8 2.1a446.02 446.02 0 00-79.7 137.9l-.9 2.6c-4.5 12.5-.8 26.5 9.3 35.2l66.3 56.6c-3.1 18.8-4.6 38-4.6 57.1 0 19.2 1.5 38.4 4.6 57.1L99 625.5a32.03 32.03 0 00-9.3 35.2l.9 2.6c18.1 50.4 44.9 96.9 79.7 137.9l1.8 2.1a32.12 32.12 0 0035.1 9.5l81.9-29.1c29.8 24.5 63.1 43.9 99 57.4l15.8 85.4a32.05 32.05 0 0025.8 25.7l2.7.5a449.4 449.4 0 00159 0l2.7-.5a32.05 32.05 0 0025.8-25.7l15.7-85a350 350 0 0099.7-57.6l81.3 28.9a32 32 0 0035.1-9.5l1.8-2.1c34.8-41.1 61.6-87.5 79.7-137.9l.9-2.6c4.5-12.3.8-26.3-9.3-35.2zM788.3 465.9c2.5 15.1 3.8 30.6 3.8 46.1s-1.3 31-3.8 46.1l-6.6 40.1 74.7 63.9a370.03 370.03 0 01-42.6 73.6L721 702.8l-31.4 25.8c-23.9 19.6-50.5 35-79.3 45.8l-38.1 14.3-17.9 97a377.5 377.5 0 01-85 0l-17.9-97.2-37.8-14.5c-28.5-10.8-55-26.2-78.7-45.7l-31.4-25.9-93.4 33.2c-17-22.9-31.2-47.6-42.6-73.6l75.5-64.5-6.5-40c-2.4-14.9-3.7-30.3-3.7-45.5 0-15.3 1.2-30.6 3.7-45.5l6.5-40-75.5-64.5c11.3-26.1 25.6-50.7 42.6-73.6l93.4 33.2 31.4-25.9c23.7-19.5 50.2-34.9 78.7-45.7l37.9-14.3 17.9-97.2c28.1-3.2 56.8-3.2 85 0l17.9 97 38.1 14.3c28.7 10.8 55.4 26.2 79.3 45.8l31.4 25.8 92.8-32.9c17 22.9 31.2 47.6 42.6 73.6L781.8 426l6.5 39.9zM512 326c-97.2 0-176 78.8-176 176s78.8 176 176 176 176-78.8 176-176-78.8-176-176-176zm79.2 255.2A111.6 111.6 0 01512 614c-29.9 0-58-11.7-79.2-32.8A111.6 111.6 0 01400 502c0-29.9 11.7-58 32.8-79.2C454 401.6 482.1 390 512 390c29.9 0 58 11.6 79.2 32.8A111.6 111.6 0 01624 502c0 29.9-11.7 58-32.8 79.2z"></path></svg>`
};

// 初始化應用程式
document.addEventListener('DOMContentLoaded', () => {
    initializeNavigation();
    initializeTabs();
    initializeModal();
    initializeFileUpload();
    initializeEventListeners();
    loadAllTemplates();
});

// 工具函數
function showStatus(message, type) {
    const statusEl = document.getElementById('statusMessage');
    statusEl.textContent = message;
    statusEl.className = `status-message ${type}`;
    statusEl.style.display = 'block';
    setTimeout(() => { statusEl.style.display = 'none'; }, type === 'info' ? 6000 : 3000);
}

function resetUIForNewVideo() {
    selectedFile = null;
    selectedTemplate = null;
    fileId = null;
    selectedLLMSubjects = [];
    originalThumbnail = '';
    videoInfo = {};
    allSubjects = [];
    originalFilename = '';
    conversationHistory = [];
    
    document.getElementById('videoPreview').style.display = 'none';
    document.getElementById('templatesSection').style.display = 'none';
    document.getElementById('statusMessage').style.display = 'none';
    
    const videoThumbnail = document.getElementById('videoThumbnail');
    if (videoThumbnail) videoThumbnail.style.display = 'none';
}

function getOriginalFileName(fId) {
    return `${fId}_original.mp4`;
}

// 導出到全域作用域以供 HTML 中的事件處理器使用
window.AdaptVideo = {
    ICONS,
    showStatus,
    resetUIForNewVideo,
    getOriginalFileName
};