// TranslateGemma UI Application
const API_BASE = '';

// i18n translations
const i18n = {
    'en': {
        subtitle: 'Local AI Translation - 55 Languages Supported',
        source_text: 'Source Text',
        auto_detect: 'Auto Detect',
        enter_text: 'Enter text to translate...',
        clear: 'Clear',
        upload_file: '📁 Upload',
        translation: 'Translation',
        copy: 'Copy',
        download: 'Download',
        translate: 'Translate',
        stream_mode: 'Stream Mode',
        advanced_settings: '⚙️ Advanced Settings',
        model: 'Model',
        chunk_size: 'Chunk Size',
        auto_split: 'Auto Split Long Text',
        release_gpu: 'Release GPU',
        translating: 'Translating...',
        copied: 'Copied!',
        error: 'Error',
    },
    'zh-CN': {
        subtitle: '本地 AI 翻译 - 支持 55 种语言',
        source_text: '源文本',
        auto_detect: '自动检测',
        enter_text: '输入要翻译的文本...',
        clear: '清空',
        upload_file: '📁 上传',
        translation: '翻译结果',
        copy: '复制',
        download: '下载',
        translate: '翻译',
        stream_mode: '流式输出',
        advanced_settings: '⚙️ 高级设置',
        model: '模型',
        chunk_size: '分块大小',
        auto_split: '自动分割长文本',
        release_gpu: '释放显存',
        translating: '翻译中...',
        copied: '已复制！',
        error: '错误',
    },
    'zh-TW': {
        subtitle: '本地 AI 翻譯 - 支援 55 種語言',
        source_text: '原文',
        auto_detect: '自動偵測',
        enter_text: '輸入要翻譯的文字...',
        clear: '清除',
        upload_file: '📁 上傳',
        translation: '翻譯結果',
        copy: '複製',
        download: '下載',
        translate: '翻譯',
        stream_mode: '串流模式',
        advanced_settings: '⚙️ 進階設定',
        model: '模型',
        chunk_size: '分塊大小',
        auto_split: '自動分割長文',
        release_gpu: '釋放顯存',
        translating: '翻譯中...',
        copied: '已複製！',
        error: '錯誤',
    },
    'ja': {
        subtitle: 'ローカルAI翻訳 - 55言語対応',
        source_text: '原文',
        auto_detect: '自動検出',
        enter_text: '翻訳するテキストを入力...',
        clear: 'クリア',
        upload_file: '📁 アップロード',
        translation: '翻訳結果',
        copy: 'コピー',
        download: 'ダウンロード',
        translate: '翻訳',
        stream_mode: 'ストリーミング',
        advanced_settings: '⚙️ 詳細設定',
        model: 'モデル',
        chunk_size: 'チャンクサイズ',
        auto_split: '長文自動分割',
        release_gpu: 'GPU解放',
        translating: '翻訳中...',
        copied: 'コピーしました！',
        error: 'エラー',
    },
};

let currentLang = 'en';
let languages = {};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadLanguages();
    initTheme();
    initUI();
    updateGPUStatus();
    setInterval(updateGPUStatus, 10000);
});

// Load supported languages
async function loadLanguages() {
    try {
        const res = await fetch(`${API_BASE}/api/languages`);
        languages = await res.json();
        populateLanguageSelects();
    } catch (e) {
        console.error('Failed to load languages:', e);
    }
}

// Populate language dropdowns
function populateLanguageSelects() {
    const sourceSelect = document.getElementById('source-lang');
    const targetSelect = document.getElementById('target-lang');
    
    // Keep auto-detect option for source
    const autoOption = sourceSelect.querySelector('option[value="auto"]');
    sourceSelect.innerHTML = '';
    sourceSelect.appendChild(autoOption);
    
    targetSelect.innerHTML = '';
    
    // Sort languages by name
    const sorted = Object.entries(languages).sort((a, b) => a[1].localeCompare(b[1]));
    
    for (const [code, name] of sorted) {
        const opt1 = new Option(`${name} (${code})`, code);
        const opt2 = new Option(`${name} (${code})`, code);
        sourceSelect.appendChild(opt1);
        targetSelect.appendChild(opt2);
    }
    
    // Set defaults
    targetSelect.value = 'en';
}

// Theme handling
function initTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.getElementById('theme-toggle').textContent = '☀️';
    }
    
    document.getElementById('theme-toggle').addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
        document.getElementById('theme-toggle').textContent = isDark ? '🌙' : '☀️';
        localStorage.setItem('theme', isDark ? 'light' : 'dark');
    });
}

// UI initialization
function initUI() {
    const sourceText = document.getElementById('source-text');
    const translateBtn = document.getElementById('translate-btn');
    const clearBtn = document.getElementById('clear-btn');
    const copyBtn = document.getElementById('copy-btn');
    const downloadBtn = document.getElementById('download-btn');
    const offloadBtn = document.getElementById('offload-btn');
    const fileInput = document.getElementById('file-input');
    const uiLang = document.getElementById('ui-lang');
    
    // Character count
    sourceText.addEventListener('input', () => {
        document.getElementById('char-count').textContent = `${sourceText.value.length} chars`;
    });
    
    // Translate button
    translateBtn.addEventListener('click', doTranslate);
    
    // Clear button
    clearBtn.addEventListener('click', () => {
        sourceText.value = '';
        document.getElementById('output-text').textContent = '';
        document.getElementById('char-count').textContent = '0 chars';
        document.getElementById('output-info').textContent = '';
    });
    
    // Copy button
    copyBtn.addEventListener('click', () => {
        const text = document.getElementById('output-text').textContent;
        navigator.clipboard.writeText(text).then(() => {
            copyBtn.textContent = i18n[currentLang].copied || 'Copied!';
            setTimeout(() => copyBtn.textContent = i18n[currentLang].copy || 'Copy', 2000);
        });
    });
    
    // Download button
    downloadBtn.addEventListener('click', () => {
        const text = document.getElementById('output-text').textContent;
        const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'translation.txt';
        a.click();
        URL.revokeObjectURL(url);
    });
    
    // File upload
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (ev) => {
                sourceText.value = ev.target.result;
                document.getElementById('char-count').textContent = `${sourceText.value.length} chars`;
            };
            reader.readAsText(file);
        }
    });
    
    // GPU offload
    offloadBtn.addEventListener('click', async () => {
        try {
            await fetch(`${API_BASE}/api/gpu/offload`, { method: 'POST' });
            updateGPUStatus();
        } catch (e) {
            console.error('Failed to offload GPU:', e);
        }
    });
    
    // UI language
    uiLang.addEventListener('change', () => {
        currentLang = uiLang.value;
        updateUILanguage();
    });
    
    // Keyboard shortcut
    sourceText.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            doTranslate();
        }
    });
}

// Update UI language
function updateUILanguage() {
    const trans = i18n[currentLang] || i18n['en'];
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (trans[key]) el.textContent = trans[key];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (trans[key]) el.placeholder = trans[key];
    });
}

// Translate
async function doTranslate() {
    const text = document.getElementById('source-text').value.trim();
    if (!text) return;
    
    const targetLang = document.getElementById('target-lang').value;
    const sourceLang = document.getElementById('source-lang').value;
    const streamMode = document.getElementById('stream-mode').checked;
    const model = document.getElementById('model-select').value;
    const chunkSize = parseInt(document.getElementById('chunk-size').value) || 80;
    const autoSplit = document.getElementById('auto-split').checked;
    
    const translateBtn = document.getElementById('translate-btn');
    const outputText = document.getElementById('output-text');
    const outputInfo = document.getElementById('output-info');
    const progressContainer = document.getElementById('progress-container');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    translateBtn.disabled = true;
    translateBtn.innerHTML = `<span class="loading"></span> ${i18n[currentLang].translating || 'Translating...'}`;
    outputText.textContent = '';
    outputInfo.textContent = '';
    
    // Parse model
    const [modelSize, quantStr] = model.split('-Q');
    const quantization = parseInt(quantStr);
    
    try {
        if (streamMode) {
            // Stream mode
            progressContainer.classList.remove('hidden');
            progressFill.style.width = '0%';
            
            const res = await fetch(`${API_BASE}/api/translate/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    target_lang: targetLang,
                    source_lang: sourceLang === 'auto' ? null : sourceLang,
                    model: modelSize,
                    quantization,
                    chunk_size: chunkSize,
                }),
            });
            
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let result = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            
                            if (data.event === 'start') {
                                progressText.textContent = `0/${data.total_chunks} chunks`;
                            } else if (data.event === 'progress') {
                                const pct = (data.chunk / data.total) * 100;
                                progressFill.style.width = `${pct}%`;
                                progressText.textContent = `${data.chunk}/${data.total} chunks`;
                            } else if (data.event === 'chunk') {
                                result += (result ? ' ' : '') + data.result;
                                outputText.textContent = result;
                            } else if (data.event === 'done') {
                                progressFill.style.width = '100%';
                                outputInfo.textContent = `${data.elapsed_ms}ms | ${text.length} → ${data.output_length} chars`;
                            }
                        } catch (e) {}
                    }
                }
            }
            
            setTimeout(() => progressContainer.classList.add('hidden'), 1000);
            
        } else {
            // Non-stream mode
            const res = await fetch(`${API_BASE}/api/translate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text,
                    target_lang: targetLang,
                    source_lang: sourceLang === 'auto' ? null : sourceLang,
                    model: modelSize,
                    quantization,
                    chunk_size: chunkSize,
                    auto_split: autoSplit,
                    stream: false,
                }),
            });
            
            const data = await res.json();
            
            if (data.status === 'success') {
                outputText.textContent = data.result;
                outputInfo.textContent = `${data.elapsed_ms}ms | ${data.chars_per_sec} chars/s | ${data.chunks} chunks`;
            } else {
                outputText.textContent = `Error: ${data.error}`;
            }
        }
    } catch (e) {
        outputText.textContent = `Error: ${e.message}`;
    } finally {
        translateBtn.disabled = false;
        translateBtn.textContent = i18n[currentLang].translate || 'Translate';
        updateGPUStatus();
    }
}

// Update GPU status
async function updateGPUStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/gpu/status`);
        const data = await res.json();
        
        const gpuStatus = document.getElementById('gpu-status');
        const modelStatus = document.getElementById('model-status');
        
        if (data.gpu?.available) {
            const usedMB = data.gpu.total_mb - data.gpu.free_mb;
            gpuStatus.textContent = `GPU: ${data.gpu.device} (${usedMB}/${data.gpu.total_mb} MB)`;
        } else {
            gpuStatus.textContent = 'GPU: Not available';
        }
        
        if (data.loaded) {
            modelStatus.textContent = `Model: ${data.current_model} | Idle: ${data.idle_seconds}s`;
        } else if (data.loading) {
            modelStatus.textContent = 'Loading model...';
        } else {
            modelStatus.textContent = `Model: Not loaded (default: ${data.default_model})`;
        }
    } catch (e) {
        document.getElementById('gpu-status').textContent = 'GPU: Connection error';
    }
}
