[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# TranslateGemma CLI

> 🚀 由 Google TranslateGemma 驅動的生產級本地翻譯工具  
> 支援 55 種語言，具備智慧分塊、串流輸出和批次處理功能

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Model: TranslateGemma](https://img.shields.io/badge/Model-TranslateGemma-green.svg)](https://huggingface.co/collections/google/translategemma)

---

## ✨ 亮點功能

- **🌍 55 種語言** - 完整支援 TranslateGemma 語言
- **📚 無限長度** - 智慧分塊與滑動視窗處理任意長度文本
- **⚡ 串流輸出** - 即時翻譯進度顯示
- **📦 批次處理** - 一次翻譯整個目錄
- **🎯 多種後端** - 本地 (MLX/PyTorch)、vLLM 或 Ollama
- **💻 跨平台** - macOS (Apple Silicon)、Linux、Windows
- **🔧 高度可配置** - 靈活參數適應不同使用場景

---

## 🎬 快速開始

### 安裝

```bash
# 使用 uv（推薦）
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[mlx]"  # macOS Apple Silicon
# 或
uv pip install -e ".[cuda]"  # Linux/Windows with NVIDIA GPU

# 使用 pip
pip install -e ".[mlx]"  # macOS Apple Silicon
pip install -e ".[cuda]"  # Linux/Windows with NVIDIA GPU
pip install -e ".[cpu]"  # 僅 CPU
```

### 首次運行

```bash
# 初始化配置
translate init

# 下載模型（僅首次）
translate model download 27b

# 開始翻譯！
translate --text "Hello world"
# 輸出: 你好，世界。
```

---

## 🚀 功能特色

### 1. 智慧長文本翻譯

**問題**：TranslateGemma 會截斷長文本（>500 字符）

**解決方案**：智慧分塊與滑動視窗

```bash
# 長文本自動分塊
translate --file long_article.txt

# 自定義分塊參數
translate --file book.txt --chunk-size 80 --overlap 10

# 短文本禁用分塊
translate --file short.txt --no-chunk
```

**工作原理**：
```
原文: [AAAAA][BBBBB][CCCCC][DDDDD]

滑動視窗:
分塊 1: [AAAAA]
分塊 2:    [AA|BBBBB]    ← 重疊提供上下文
分塊 3:         [BB|CCCCC]
分塊 4:              [CC|DDDDD]

結果: 完整翻譯並保持上下文
```

### 2. 串流輸出

即時翻譯進度，提升用戶體驗：

```bash
# 逐詞串流輸出
translate --file article.txt --stream

# 結合分塊使用
translate --file book.txt --chunk-size 80 --stream
```

### 3. 批次翻譯

高效翻譯整個目錄：

```bash
# 翻譯所有 .txt 和 .md 檔案
translate --dir ./documents

# 輸出到 ./documents/translated/
```

### 4. 互動式 REPL

```bash
translate
```

```
TranslateGemma Interactive (yue ↔ en)
Model: 27b | Mode: direct | Type /help for commands

> 今日天氣好好
[yue→en] The weather is really nice today

> /to ja
Target language set to: ja

> Hello
[en→ja] こんにちは。

> /quit
再見！Goodbye!
```

---

## 📖 使用方法

### 基本翻譯

```bash
# 單一文本
translate --text "Hello world"

# 從檔案
translate --file input.txt --output output.txt

# 從標準輸入
echo "Bonjour" | translate

# 強制目標語言
translate --text "Hello" --to ja
```

### 長文本翻譯

```bash
# 自動分塊（文本 > 300 字符）
translate --file article.txt

# 自定義分塊
translate --file book.txt --chunk-size 80 --overlap 10

# 即時回饋串流
translate --file long.txt --stream

# 禁用分塊
translate --file short.txt --no-chunk
```

### 批次處理

```bash
# 翻譯目錄
translate --dir ./documents

# 使用自定義參數
translate --dir ./docs --chunk-size 100
```

### 模型管理

```bash
# 列出模型
translate model list

# 下載模型
translate model download 4b

# 檢查狀態
translate model status

# 列出支援語言
translate model langs
```

---

## ⚙️ 配置

配置檔案：`~/.config/translate/config.yaml`

### 預設配置（已優化）

```yaml
model:
  name: 27b              # 模型大小: 4b, 12b, 27b
  quantization: 4        # 4-bit 或 8-bit

backend:
  type: auto             # auto, mlx, pytorch, vllm, ollama
  vllm_url: http://localhost:8000
  ollama_url: http://localhost:11434

translation:
  languages: [yue, en]   # 語言對
  mode: direct           # direct 或 explain
  max_tokens: 512        # 基礎最大詞元（自動調整分塊）
  
  chunking:
    enabled: true        # 啟用智慧分塊
    chunk_size: 80       # 完整性最佳
    overlap: 10          # 最小重複
    split_by: sentence   # sentence, paragraph, 或 char
    auto_threshold: 300  # 文本 > 300 字符自動啟用

ui:
  show_detected_language: true
  colored_output: true
  show_progress: true
```

### 自定義設定

```bash
# 使用預設值初始化
translate init

# 強制覆寫
translate init --force

# 手動編輯
vim ~/.config/translate/config.yaml
```

---

## 🎯 最佳實踐

### 分塊大小選擇

| 文本類型 | chunk_size | overlap | 原因 |
|-----------|------------|---------|--------|
| 日常對話 | 60-80 | 10-15 | 短句 |
| 技術文件 | 80-100 | 15-20 | 術語一致性 |
| 文學作品 | 80-100 | 20-30 | 上下文保持 |
| 長篇文章 | 80-100 | 10-20 | 平衡品質與速度 |

### 何時使用分塊

| 文本長度 | 建議 |
|-------------|----------------|
| < 300 字符 | 使用 `--no-chunk` 提升速度 |
| 300-1000 字符 | 自動分塊（預設） |
| 1000-5000 字符 | `--chunk-size 80 --overlap 10` |
| 5000+ 字符（書籍） | `--chunk-size 80 --stream` |

### 效能提示

1. **互動模式** - 模型載入一次，多次翻譯更快
2. **批次處理** - 使用 `--dir` 而非逐一翻譯檔案
3. **串流** - 長文本使用 `--stream` 查看進度
4. **最佳分塊** - chunk_size=80, overlap=10 是最佳平衡點

---

## 📊 效能表現

**測試環境**：MacBook Pro M2 Max, 96GB, MLX 後端

| 文本長度 | 分塊數 | 時間 | 吞吐量 |
|-------------|--------|------|------------|
| 100 字符 | 1 | 1.2s | 83 字符/秒 |
| 400 字符 | 4 | 8.5s | 48 字符/秒 |
| 1000 字符 | 12 | ~22s | ~45 字符/秒 |
| 5000 字符 | 60 | ~110s | ~45 字符/秒 |

**記憶體使用量**：14.15 GB（所有文本長度穩定）

---

## 🛠️ 系統需求

### macOS (Apple Silicon)
- M1/M2/M3/M4 Mac
- 8GB+ 統一記憶體 (4b)，16GB+ (12b)，32GB+ (27b)
- macOS 14.0+

### Linux / Windows
- NVIDIA GPU 8GB+ VRAM（或 CPU 16GB+ RAM）
- CUDA 11.8+（GPU 版本）

### 所有平台
- Python 3.11+

---

## 📦 安裝選項

### 選項 1：uv（最快，推薦）

```bash
# 安裝 uv（如果尚未安裝）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 複製並安裝
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
uv venv .venv
source .venv/bin/activate

# macOS Apple Silicon
uv pip install -e ".[mlx]"

# Linux/Windows with NVIDIA GPU
uv pip install -e ".[cuda]"

# 僅 CPU
uv pip install -e ".[cpu]"
```

### 選項 2：pipx（隔離安裝）

```bash
# 從本地目錄安裝
pipx install /path/to/translategemma-cli[mlx]

# 或從 git（發布後）
pipx install git+https://github.com/jhkchan/translategemma-cli.git[mlx]
```

### 選項 3：pip（傳統方式）

```bash
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
python3 -m venv venv
source venv/bin/activate
pip install -e ".[mlx]"  # 或 [cuda] 或 [cpu]
```

---

## 🌍 支援語言（55 種）

| 代碼 | 語言 | 代碼 | 語言 |
|------|----------|------|----------|
| `en` | 英語 | `yue` | 粵語 |
| `zh` | 中文（簡體） | `zh-TW` | 中文（繁體） |
| `ja` | 日語 | `ko` | 韓語 |
| `fr` | 法語 | `de` | 德語 |
| `es` | 西班牙語 | `pt` | 葡萄牙語 |
| `ru` | 俄語 | `ar` | 阿拉伯語 |

...還有 45 種語言。執行 `translate model langs` 查看完整列表。

---

## 🎓 進階用法

### 自定義語言對

編輯 `~/.config/translate/config.yaml`：

```yaml
translation:
  languages: [ja, en]  # 日語 ↔ 英語
  # 或
  languages: [zh, fr]  # 中文 ↔ 法語
```

### 後端選項

```bash
# 本地（預設）
translate --backend mlx  # macOS
translate --backend pytorch  # Linux/Windows

# vLLM（高吞吐量）
vllm serve google/translategemma-27b-it --quantization awq
translate --backend vllm --server http://localhost:8000

# Ollama（簡易設定）
ollama pull translategemma:27b
translate --backend ollama
```

### 互動式指令

| 指令 | 功能 |
|---------|----------|
| `/to <lang>` | 強制目標語言 |
| `/auto` | 啟用自動偵測 |
| `/mode direct` | 直接翻譯 |
| `/mode explain` | 附帶解釋 |
| `/model <size>` | 切換模型 |
| `/backend <type>` | 切換後端 |
| `/langs` | 列出語言 |
| `/config` | 顯示配置 |
| `/quit` | 退出 |

---

## 🔬 技術細節

### 智慧分塊演算法

```python
# 基於句子的滑動視窗分割
TextChunker(
    chunk_size=80,      # 目標分塊大小
    overlap=10,         # 上下文重疊
    split_by="sentence" # 在句子邊界分割
)

# 處理流程:
1. 在句子邊界分割文本
2. 將句子組合成分塊（~80 字符）
3. 從前一分塊添加重疊
4. 翻譯每個帶上下文的分塊
5. 合併結果（跳過重疊）
```

### 自適應 max_tokens

```python
# 根據輸入長度動態調整
adaptive_max_tokens = min(
    2048,                      # 上限
    max(512, len(chunk) * 3)   # 3倍輸入（安全緩衝）
)

# 為什麼是 3 倍？
# - 中文 → 英文通常擴展 1.5-2 倍
# - 3 倍提供安全緩衝
# - 防止截斷
```

### 合併策略

```python
# 簡單串接（重疊僅提供上下文）
def merge(chunks, translations):
    result = [translations[0]]  # 保留第一個完整
    for trans in translations[1:]:
        result.append(" " + trans)  # 分塊間添加空格
    return "".join(result)

# 注意：最小重疊（10）減少重複
```

---

## 📚 文件

| 文件 | 描述 |
|----------|-------------|
| [README.md](README.md) | 主要文件（此檔案） |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 快速參考卡 |
| [BEST_PRACTICES.md](BEST_PRACTICES.md) | 使用最佳實踐 |
| [LONG_TEXT_FEATURE_REPORT.md](LONG_TEXT_FEATURE_REPORT.md) | 功能詳細報告 |
| [FINAL_TEST_REPORT.md](FINAL_TEST_REPORT.md) | 綜合測試報告 |
| [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) | 開發總結 |
| [TRANSLATION_TEST_REPORT.md](TRANSLATION_TEST_REPORT.md) | 多語言品質評估 |

---

## 🎯 使用案例

### 案例 1：翻譯書籍

```bash
# 使用串流顯示進度回饋
translate --file novel.txt --chunk-size 80 --overlap 10 --stream --output novel_en.txt
```

### 案例 2：批次翻譯文件

```bash
# 翻譯目錄中所有文件
translate --dir ./docs

# 輸出到 ./docs/translated/
```

### 案例 3：快速翻譯

```bash
# 短文本，無分塊
translate --text "Hello world" --no-chunk

# 或使用互動模式
translate
> Hello world
[en→yue] 你好，世界。
```

### 案例 4：多語言工作流程

```bash
# 英語到多種語言
translate --text "Welcome" --to ja  # 日語
translate --text "Welcome" --to ko  # 韓語
translate --text "Welcome" --to zh  # 中文
translate --text "Welcome" --to fr  # 法語
```

---

## 🔧 開發洞察

### 關鍵學習

1. **TranslateGemma 模型特性**：
   - 截斷長文本（>500 字符）
   - 在段落分隔符（空行）處停止
   - 需要小分塊（80-100 字符）以確保完整性

2. **最佳分塊策略**：
   - chunk_size=80：最佳完整性（98%）
   - overlap=10：最小重複（<5%）
   - split_by=sentence：自然邊界

3. **自適應 max_tokens**：
   - 固定 512 詞元對長分塊不足
   - 3 倍輸入長度確保完整性
   - 上限 2048 防止過度生成

4. **合併策略**：
   - 簡單串接效果最佳
   - 重疊提供上下文，非去重用
   - 智慧去重複雜（未來工作）

### 架構

```
用戶輸入
    ↓
TextChunker (chunker.py)
    ↓
[分塊 1] [分塊 2] [分塊 3] ...
    ↓         ↓         ↓
Translator.translate_long()
    ↓
自適應 max_tokens（3 倍輸入）
    ↓
MLX/PyTorch/vLLM/Ollama 後端
    ↓
合併結果
    ↓
輸出（完整翻譯）
```

---

## 🧪 測試

### 執行測試

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 執行所有測試
pytest

# 執行覆蓋率測試
pytest --cov=translategemma_cli

# 執行特定測試
pytest tests/test_chunker.py
```

### 手動測試

```bash
# 綜合測試套件
./tests/comprehensive_test.sh

# 或測試個別功能
translate --file test.txt --chunk-size 80
translate --dir ./test_docs
translate --text "Test" --stream
```

---

## 📊 基準測試

### 翻譯完整性

| 方法 | 完整性 | 速度 | 建議 |
|--------|--------------|-------|----------------|
| 無分塊 | 13% | 快 | ❌ 長文本失敗 |
| chunk=150 | 70% | 中等 | ⚠️ 不推薦 |
| chunk=100 | 95% | 中等 | ✅ 良好 |
| chunk=80 | 98% | 中等 | ✅ **最佳** |
| chunk=60 | 100% | 慢 | ⚠️ 過度分塊 |

### 重疊影響

| 重疊 | 重複率 | 品質 | 建議 |
|---------|------------|---------|----------------|
| 0 | 0% | 中等 | ⚠️ 無上下文 |
| 10 | <5% | 高 | ✅ **最佳** |
| 20 | 5-10% | 高 | ✅ 良好 |
| 30 | 10-15% | 中等 | ⚠️ 過多 |
| 50 | 20-30% | 低 | ❌ 不推薦 |

---

## 🎨 模型選擇

| 模型 | 參數量 | 磁碟大小 | 記憶體 | 使用場景 |
|-------|------------|-----------|--------|----------|
| **4b** | 5B | ~3.2 GB | 8GB+ | 快速翻譯，資源有限 |
| **12b** | 13B | ~7.0 GB | 16GB+ | 平衡效能與品質 |
| **27b** | 29B | ~14.8 GB | 32GB+ | **最佳品質**（推薦） |

---

## 🌟 v0.2.0 新功能

### 主要功能

- ✅ **智慧文本分塊** - 處理無限長度文本
- ✅ **滑動視窗** - 重疊保持上下文
- ✅ **串流輸出** - 即時翻譯進度
- ✅ **批次翻譯** - 處理整個目錄
- ✅ **自適應 max_tokens** - 防止截斷
- ✅ **進度顯示** - rich 視覺回饋

### 新 CLI 參數

```bash
--chunk-size <int>    # 分塊大小（預設：80）
--overlap <int>       # 重疊大小（預設：10）
--no-chunk            # 禁用分塊
--stream              # 啟用串流
--dir <path>          # 批次翻譯目錄
```

### 效能改進

- **翻譯完整性**：13% → 98%（長文本）
- **吞吐量**：穩定 45-50 字符/秒
- **記憶體**：不變（14.15 GB）

---

## 🐛 已知限制

### 1. 模型行為

- **段落分隔**：模型在空行處停止
  - **解決方案**：使用小分塊（80 字符）
- **長分塊**：分塊 > 150 字符時截斷
  - **解決方案**：自適應 max_tokens（3 倍輸入）

### 2. 重疊重複

- **問題**：重疊 > 10 造成輕微重複
- **原因**：重疊區域翻譯兩次
- **建議**：使用 overlap=10-20

### 3. 尚未實現

- 智慧去重（計劃 v0.3.0）
- 翻譯快取（計劃 v0.3.0）
- 恢復功能（計劃 v0.4.0）
- 術語支援（評估中）

---

## 🤝 貢獻

歡迎貢獻！請：

1. Fork 儲存庫
2. 建立功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交變更（`git commit -m 'Add AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 開啟 Pull Request

---

## 📄 授權

此專案採用 MIT 授權 - 請參閱 [LICENSE](LICENSE) 檔案。

**注意**：TranslateGemma 模型受 Google 模型授權條款約束。請查閱並遵守[模型授權](https://ai.google.dev/gemma/terms)。

---

## 🙏 致謝

- [Google TranslateGemma](https://huggingface.co/collections/google/translategemma) - 基礎翻譯模型
- [MLX](https://github.com/ml-explore/mlx) - Apple Silicon 優化
- [Cursor](https://cursor.com/) + [Claude](https://www.anthropic.com/claude) - 開發工具
- [hy-mt](https://github.com/neosun100/hy-mt) - 分塊策略靈感

---

## 🔗 連結

- **GitHub**：https://github.com/jhkchan/translategemma-cli
- **HuggingFace**：https://huggingface.co/collections/google/translategemma
- **問題回報**：https://github.com/jhkchan/translategemma-cli/issues
- **文件**：請參閱 [docs](docs/) 目錄

---

## 📞 支援

- **問題**：[GitHub Issues](https://github.com/jhkchan/translategemma-cli/issues)
- **討論**：[GitHub Discussions](https://github.com/jhkchan/translategemma-cli/discussions)
- **電子郵件**：[Your Email]

---

## 🗺️ 路線圖

### v0.3.0（下一版）
- [ ] 智慧去重演算法
- [ ] 翻譯快取系統
- [ ] 改進語言偵測
- [ ] 術語支援

### v0.4.0（未來）
- [ ] 恢復功能
- [ ] 並行翻譯（多 GPU）
- [ ] Web UI
- [ ] REST API 伺服器

---

**版本**：0.2.0  
**最後更新**：2026-01-17  
**狀態**：生產就緒 ✅