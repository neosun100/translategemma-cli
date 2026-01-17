[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# TranslateGemma

> 🌍 本地 AI 翻譯服務，支援 Web UI、REST API 和 MCP 整合  
> 55 種語言，智慧分塊，串流輸出。基於 Google TranslateGemma。

[![Docker](https://img.shields.io/badge/Docker-v1.0.0-blue?logo=docker)](https://hub.docker.com/r/neosun/translategemma)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CUDA 12.4](https://img.shields.io/badge/CUDA-12.4-green?logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)

---

## ✨ 功能亮點

- 🌐 **Web UI** - 美觀響應式翻譯介面
- 🔌 **REST API** - 完整 API，支援串流輸出
- 🤖 **MCP 整合** - 支援 Claude Desktop 等 AI 助手
- 🌍 **55 種語言** - 完整 TranslateGemma 語言支援
- 📚 **智慧分塊** - 處理無限長度文字 (chunk_size=100)
- ⚡ **串流輸出** - 即時翻譯進度
- 🐳 **All-in-One Docker** - 82GB 映像檔，內建全部 6 個模型
- 🎯 **多模型支援** - 4B/12B/27B，Q4/Q8 量化

---

## 🎬 快速開始

### 方式一：Docker All-in-One（推薦）

```bash
# 拉取 all-in-one 映像檔（82GB，包含所有模型）
docker pull neosun/translategemma:v1.0.0-allinone

# 使用 GPU 執行
docker run -d --gpus '"device=0"' \
  -p 8022:8022 \
  -e MODEL_NAME=27b \
  -e QUANTIZATION=8 \
  --name translategemma \
  neosun/translategemma:v1.0.0-allinone

# 存取 Web UI
open http://localhost:8022
```

### 方式二：Docker 按需下載模型

```bash
# 拉取輕量映像檔（10GB）
docker pull neosun/translategemma:latest

# 執行（首次使用時下載模型）
docker run -d --gpus '"device=0"' \
  -p 8022:8022 \
  -v ~/.cache/translate/models:/root/.cache/translate/models \
  --name translategemma \
  neosun/translategemma:latest
```

### 方式三：Docker Compose

```yaml
# docker-compose.yml
services:
  translategemma:
    image: neosun/translategemma:v1.0.0-allinone
    container_name: translategemma
    ports:
      - "8022:8022"
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
      - MODEL_NAME=27b
      - QUANTIZATION=8
      - BACKEND=gguf
      - GPU_IDLE_TIMEOUT=0
      - MAX_CHUNK_LENGTH=100
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              device_ids: ["0"]
              capabilities: [gpu]
```

```bash
docker-compose up -d
```

### 方式四：本地執行

**環境需求：**
- Python 3.11+
- NVIDIA GPU + CUDA 12.4+
- 16GB+ 顯存（27B 模型）

```bash
# 複製儲存庫
git clone https://github.com/neosun100/translategemma.git
cd translategemma

# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate

# 安裝相依套件
pip install -e ".[cuda]"

# 啟動服務
uvicorn app_fastapi:app --host 0.0.0.0 --port 8022

# 驗證
curl http://localhost:8022/health
```

---

## 🖥️ Web UI

存取 `http://localhost:8022` 使用 Web 介面：

![TranslateGemma Web UI](docs/screenshot.png)

**功能特性：**
- 🎨 深色/淺色主題切換
- 🔄 語言交換按鈕
- 📊 即時翻譯統計
- ⚙️ 進階參數控制
- 📁 檔案上傳支援
- 🔥 GPU 狀態監控

---

## 🔌 REST API

### 翻譯文字

```bash
# 簡單翻譯
curl -X POST http://localhost:8022/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "target_lang": "zh-TW"}'

# 回應
{
  "translation": "你好，世界",
  "source_lang": "en",
  "target_lang": "zh-TW",
  "model": "27b-Q8",
  "time_ms": 1234
}
```

### 串流翻譯

```bash
curl -X POST http://localhost:8022/translate/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "長文字...", "target_lang": "zh-TW"}'
```

### API 端點

| 端點 | 方法 | 描述 |
|------|------|------|
| `/translate` | POST | 翻譯文字 |
| `/translate/stream` | POST | 串流翻譯 |
| `/config` | GET | 取得目前設定 |
| `/models` | GET | 列出可用模型 |
| `/languages` | GET | 列出支援的語言 |
| `/gpu/status` | GET | GPU 記憶體狀態 |
| `/health` | GET | 健康檢查 |

---

## ⚙️ 設定說明

### 環境變數

| 變數 | 預設值 | 描述 |
|------|--------|------|
| `MODEL_NAME` | `27b` | 模型大小：4b, 12b, 27b |
| `QUANTIZATION` | `8` | 量化：4 或 8 |
| `BACKEND` | `gguf` | 後端：gguf, pytorch |
| `GPU_IDLE_TIMEOUT` | `0` | 自動卸載逾時（0=立即） |
| `MAX_CHUNK_LENGTH` | `100` | 安全分塊大小 |
| `DEFAULT_OVERLAP` | `0` | 滑動視窗重疊（0=停用） |
| `NVIDIA_VISIBLE_DEVICES` | `0` | GPU 裝置 ID |

### 模型選擇指南

| 模型 | 顯存 | 品質 | 速度 | 使用場景 |
|------|------|------|------|----------|
| 4B-Q4 | ~3GB | 良好 | 快 | 快速翻譯 |
| 4B-Q8 | ~5GB | 較好 | 快 | 日常使用 |
| 12B-Q4 | ~7GB | 高 | 中 | 平衡選擇 |
| 12B-Q8 | ~12GB | 更高 | 中 | 推薦使用 |
| 27B-Q4 | ~15GB | 最佳 | 慢 | 高品質翻譯 |
| **27B-Q8** | ~28GB | **最佳+** | 慢 | **專業翻譯** ⭐ |

---

## 🌍 支援的語言（55 種）

| 代碼 | 語言 | 代碼 | 語言 | 代碼 | 語言 |
|------|------|------|------|------|------|
| `en` | 英語 | `zh` | 簡體中文 | `zh-TW` | 繁體中文 |
| `ja` | 日語 | `ko` | 韓語 | `yue` | 粵語 |
| `fr` | 法語 | `de` | 德語 | `es` | 西班牙語 |
| `pt` | 葡萄牙語 | `ru` | 俄語 | `ar` | 阿拉伯語 |
| `hi` | 印地語 | `th` | 泰語 | `vi` | 越南語 |

...以及 40 多種其他語言。查看 `/languages` 端點取得完整列表。

---

## 🐳 Docker 映像檔

| 映像檔 | 大小 | 描述 |
|--------|------|------|
| `neosun/translategemma:v1.0.0-allinone` | 82GB | 內建全部 6 個模型 |
| `neosun/translategemma:latest-allinone` | 82GB | 最新 all-in-one |
| `neosun/translategemma:v1.0.0` | 10GB | 輕量版，按需下載模型 |
| `neosun/translategemma:latest` | 10GB | 最新輕量版 |

---

## 📊 技術細節

### 智慧分塊

TranslateGemma 會截斷長文字。我們的智慧分塊確保完整翻譯：

```
chunk_size=100  →  100% 翻譯完整度
chunk_size=120  →  44% 完整度（截斷）
chunk_size=150  →  44% 完整度（截斷）
```

**關鍵發現**：`chunk_size=100` 是確保完整翻譯的安全邊界。

### 上下文一致性

TranslateGemma 自動維護跨分塊的一致性：
- ✅ 代名詞（他/她/他們）
- ✅ 術語（NLP、AI）
- ✅ 專有名詞（Google、Microsoft）
- ✅ 性別一致性

無需重疊即可保持上下文。

---

## 🤖 MCP 整合

與 Claude Desktop 或其他 MCP 相容的 AI 助手配合使用：

```json
{
  "mcpServers": {
    "translategemma": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "TRANSLATEGEMMA_URL": "http://localhost:8022"
      }
    }
  }
}
```

---

## 📁 專案結構

```
translategemma/
├── app_fastapi.py          # FastAPI 伺服器
├── mcp_server.py           # MCP 伺服器
├── templates/
│   └── index.html          # Web UI
├── static/
│   ├── app.js              # 前端 JS
│   └── style.css           # 樣式
├── translategemma_cli/     # 核心函式庫
│   ├── translator.py       # 翻譯邏輯
│   ├── chunker.py          # 文字分塊
│   ├── model.py            # 模型載入
│   └── config.py           # 設定
├── Dockerfile              # 標準映像檔
├── Dockerfile.allinone     # All-in-one 映像檔
├── docker-compose.yml      # Compose 設定
└── tests/                  # 測試套件
```

---

## 🔬 研究發現

我們的廣泛測試揭示：

| 參數 | 最佳值 | 原因 |
|------|--------|------|
| chunk_size | 100 | 100% 翻譯完整度 |
| overlap | 0 | TranslateGemma 自動維護上下文 |
| quantization | Q8 | 最佳品質/速度平衡 |

詳見 [CHUNKING_RESEARCH_REPORT.md](docs/CHUNKING_RESEARCH_REPORT.md)。

---

## 🤝 貢獻指南

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳情。

1. Fork 本儲存庫
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 建立 Pull Request

---

## 📄 授權條款

MIT License - 詳見 [LICENSE](LICENSE) 檔案。

**注意**：TranslateGemma 模型受 [Google 模型授權條款](https://ai.google.dev/gemma/terms) 約束。

---

## 🙏 致謝

- [Google TranslateGemma](https://huggingface.co/collections/google/translategemma) - 基礎翻譯模型
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) - GGUF 推論
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/translategemma&type=Date)](https://star-history.com/#neosun100/translategemma)

## 📱 關注公眾號

![公眾號](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
