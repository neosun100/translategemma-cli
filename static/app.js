// TranslateGemma UI - Matching HY-MT Style
const API = '';

// Model configurations
const MODELS = [
    { id: '4b-Q4', name: 'TranslateGemma 4B', size: '4B', quant: 'Q4', vram: '~3GB', desc: '快速翻译，资源占用低' },
    { id: '4b-Q8', name: 'TranslateGemma 4B', size: '4B', quant: 'Q8', vram: '~5GB', desc: 'Q8 量化，更高质量' },
    { id: '12b-Q4', name: 'TranslateGemma 12B', size: '12B', quant: 'Q4', vram: '~7GB', desc: '平衡速度与质量' },
    { id: '12b-Q8', name: 'TranslateGemma 12B', size: '12B', quant: 'Q8', vram: '~12GB', desc: '12B Q8 量化版本' },
    { id: '27b-Q4', name: 'TranslateGemma 27B', size: '27B', quant: 'Q4', vram: '~15GB', desc: '大模型，高质量翻译' },
    { id: '27b-Q8', name: 'TranslateGemma 27B', size: '27B', quant: 'Q8', vram: '~28GB', desc: '最高翻译质量 ⭐', selected: true },
];

let selectedModel = '27b-Q8';
let languages = {};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    renderModels();
    await loadLanguages();
    setupSliders();
    setupFileDrop();
    updateGPUStatus();
    setInterval(updateGPUStatus, 5000);
});

// Render model cards
function renderModels() {
    const grid = document.getElementById('model-grid');
    grid.innerHTML = MODELS.map(m => `
        <div class="model-card ${m.id === selectedModel ? 'selected' : ''}" onclick="selectModel('${m.id}')">
            <div class="model-name">${m.name}</div>
            <div class="model-tags">
                <span class="tag tag-size">${m.size}</span>
                <span class="tag tag-quant">${m.quant}</span>
                <span class="tag tag-vram">显存: ${m.vram}</span>
            </div>
            <div class="model-desc">${m.desc}</div>
        </div>
    `).join('');
}

function selectModel(id) {
    selectedModel = id;
    document.querySelectorAll('.model-card').forEach(c => c.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
}

// Load languages
async function loadLanguages() {
    try {
        const res = await fetch(`${API}/api/languages`);
        languages = await res.json();
        populateLanguages();
    } catch (e) {
        console.error('Failed to load languages:', e);
    }
}

function populateLanguages() {
    const source = document.getElementById('source-lang');
    const target = document.getElementById('target-lang');
    
    const sorted = Object.entries(languages).sort((a, b) => a[1].localeCompare(b[1]));
    
    sorted.forEach(([code, name]) => {
        source.add(new Option(`${name} (${code})`, code));
        target.add(new Option(`${name} (${code})`, code));
    });
    
    target.value = 'zh';
}

function swapLangs() {
    const source = document.getElementById('source-lang');
    const target = document.getElementById('target-lang');
    if (source.value !== 'auto') {
        [source.value, target.value] = [target.value, source.value];
    }
}

// Sliders
function setupSliders() {
    const sliders = [
        { id: 'temperature', display: 'temp-val' },
        { id: 'top-p', display: 'topp-val' },
        { id: 'top-k', display: 'topk-val' },
        { id: 'repetition', display: 'rep-val' },
    ];
    
    sliders.forEach(({ id, display }) => {
        const slider = document.getElementById(id);
        const val = document.getElementById(display);
        slider.addEventListener('input', () => val.textContent = slider.value);
    });
}

// File drop
function setupFileDrop() {
    const drop = document.getElementById('file-drop');
    const input = document.getElementById('file-input');
    
    drop.addEventListener('click', () => input.click());
    drop.addEventListener('dragover', e => { e.preventDefault(); drop.classList.add('dragover'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('dragover'));
    drop.addEventListener('drop', e => {
        e.preventDefault();
        drop.classList.remove('dragover');
        handleFile(e.dataTransfer.files[0]);
    });
    input.addEventListener('change', e => handleFile(e.target.files[0]));
}

function handleFile(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => document.getElementById('source-text').value = e.target.result;
    reader.readAsText(file);
}

// Translation
async function translate() {
    const text = document.getElementById('source-text').value.trim();
    if (!text) return;
    
    const btn = event.currentTarget;
    btn.disabled = true;
    btn.classList.add('loading');
    
    const [size, quantStr] = selectedModel.split('-Q');
    
    try {
        const res = await fetch(`${API}/api/translate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                target_lang: document.getElementById('target-lang').value,
                source_lang: document.getElementById('source-lang').value === 'auto' ? null : document.getElementById('source-lang').value,
                model: size,
                quantization: parseInt(quantStr),
                stream: false,
            }),
        });
        
        const data = await res.json();
        const result = document.getElementById('result-text');
        
        if (data.status === 'success') {
            result.textContent = data.result;
            result.classList.add('has-content');
        } else {
            result.textContent = `错误: ${data.error}`;
        }
    } catch (e) {
        document.getElementById('result-text').textContent = `错误: ${e.message}`;
    } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
        updateGPUStatus();
    }
}

async function translateStream() {
    const text = document.getElementById('source-text').value.trim();
    if (!text) return;
    
    const btn = event.currentTarget;
    btn.disabled = true;
    btn.classList.add('loading');
    
    const progress = document.getElementById('progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const result = document.getElementById('result-text');
    
    progress.classList.remove('hidden');
    progressFill.style.width = '0%';
    result.textContent = '';
    result.classList.add('has-content');
    
    const [size, quantStr] = selectedModel.split('-Q');
    
    try {
        const res = await fetch(`${API}/api/translate/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text,
                target_lang: document.getElementById('target-lang').value,
                source_lang: document.getElementById('source-lang').value === 'auto' ? null : document.getElementById('source-lang').value,
                model: size,
                quantization: parseInt(quantStr),
            }),
        });
        
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let output = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            for (const line of chunk.split('\n')) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.event === 'start') {
                            progressText.textContent = `0/${data.total_chunks} 块`;
                        } else if (data.event === 'progress') {
                            progressFill.style.width = `${(data.chunk / data.total) * 100}%`;
                            progressText.textContent = `${data.chunk}/${data.total} 块`;
                        } else if (data.event === 'chunk') {
                            output += (output ? ' ' : '') + data.result;
                            result.textContent = output;
                        } else if (data.event === 'done') {
                            progressFill.style.width = '100%';
                            progressText.textContent = `完成 - ${data.elapsed_ms}ms`;
                        }
                    } catch (e) {}
                }
            }
        }
    } catch (e) {
        result.textContent = `错误: ${e.message}`;
    } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
        setTimeout(() => progress.classList.add('hidden'), 2000);
        updateGPUStatus();
    }
}

function clearAll() {
    document.getElementById('source-text').value = '';
    document.getElementById('result-text').textContent = '翻译结果将显示在这里...';
    document.getElementById('result-text').classList.remove('has-content');
}

function copySource() {
    navigator.clipboard.writeText(document.getElementById('source-text').value);
}

function copyResult() {
    navigator.clipboard.writeText(document.getElementById('result-text').textContent);
}

// GPU Status
async function updateGPUStatus() {
    try {
        const res = await fetch(`${API}/api/gpu/status`);
        const data = await res.json();
        
        const loaded = document.getElementById('gpu-loaded');
        loaded.textContent = data.loaded ? '● 已加载' : '● 未加载';
        loaded.classList.toggle('loaded', data.loaded);
        
        if (data.gpu?.available) {
            const used = data.gpu.total_mb - data.gpu.free_mb;
            document.getElementById('gpu-mem').textContent = `📊 显存: ${used} / ${data.gpu.total_mb} MB`;
        }
        
        document.getElementById('gpu-idle').textContent = `⏱️ 空闲: ${data.idle_seconds}秒`;
        document.getElementById('gpu-model').textContent = `🤖 当前模型: ${data.current_model || '-'}`;
    } catch (e) {}
}

async function releaseGPU() {
    await fetch(`${API}/api/gpu/offload`, { method: 'POST' });
    updateGPUStatus();
}
