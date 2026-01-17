[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# TranslateGemma

> 🌍 本地 AI 翻译服务，支持 Web UI、REST API 和 MCP 集成  
> 55 种语言，智能分块，流式输出。基于 Google TranslateGemma。

[![Docker](https://img.shields.io/badge/Docker-v1.0.0-blue?logo=docker)](https://hub.docker.com/r/neosun/translategemma)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CUDA 12.4](https://img.shields.io/badge/CUDA-12.4-green?logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)

---

## ✨ 功能亮点

- 🌐 **Web UI** - 美观响应式翻译界面
- 🔌 **REST API** - 完整 API，支持流式输出
- 🤖 **MCP 集成** - 支持 Claude Desktop 等 AI 助手
- 🌍 **55 种语言** - 完整 TranslateGemma 语言支持
- 📚 **智能分块** - 处理无限长度文本 (chunk_size=100)
- ⚡ **流式输出** - 实时翻译进度
- 🐳 **All-in-One Docker** - 82GB 镜像，内置全部 6 个模型
- 🎯 **多模型支持** - 4B/12B/27B，Q4/Q8 量化

---

## 🎬 快速开始

### 方式一：Docker All-in-One（推荐）

```bash
# 拉取 all-in-one 镜像（82GB，包含所有模型）
docker pull neosun/translategemma:v1.0.0-allinone

# 使用 GPU 运行
docker run -d --gpus '"device=0"' \
  -p 8022:8022 \
  -e MODEL_NAME=27b \
  -e QUANTIZATION=8 \
  --name translategemma \
  neosun/translategemma:v1.0.0-allinone

# 访问 Web UI
open http://localhost:8022
```

### 方式二：Docker 按需下载模型

```bash
# 拉取轻量镜像（10GB）
docker pull neosun/translategemma:latest

# 运行（首次使用时下载模型）
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

### 方式四：本地运行

**环境要求：**
- Python 3.11+
- NVIDIA GPU + CUDA 12.4+
- 16GB+ 显存（27B 模型）

```bash
# 克隆仓库
git clone https://github.com/neosun100/translategemma.git
cd translategemma

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -e ".[cuda]"

# 启动服务
uvicorn app_fastapi:app --host 0.0.0.0 --port 8022

# 验证
curl http://localhost:8022/health
```

---

## 🖥️ Web UI

访问 `http://localhost:8022` 使用 Web 界面：

**功能特性：**
- 🎨 深色/浅色主题切换
- 🔄 语言交换按钮
- 📊 实时翻译统计
- ⚙️ 高级参数控制
- 📁 文件上传支持
- 🔥 GPU 状态监控

---

## 🔌 REST API

### 翻译文本

```bash
# 简单翻译
curl -X POST http://localhost:8022/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "target_lang": "zh"}'

# 响应
{
  "translation": "你好，世界",
  "source_lang": "en",
  "target_lang": "zh",
  "model": "27b-Q8",
  "time_ms": 1234
}
```

### 流式翻译

```bash
curl -X POST http://localhost:8022/translate/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "长文本...", "target_lang": "zh"}'
```

### API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/translate` | POST | 翻译文本 |
| `/translate/stream` | POST | 流式翻译 |
| `/config` | GET | 获取当前配置 |
| `/models` | GET | 列出可用模型 |
| `/languages` | GET | 列出支持的语言 |
| `/gpu/status` | GET | GPU 内存状态 |
| `/health` | GET | 健康检查 |

---

## ⚙️ 配置说明

### 环境变量

| 变量 | 默认值 | 描述 |
|------|--------|------|
| `MODEL_NAME` | `27b` | 模型大小：4b, 12b, 27b |
| `QUANTIZATION` | `8` | 量化：4 或 8 |
| `BACKEND` | `gguf` | 后端：gguf, pytorch |
| `GPU_IDLE_TIMEOUT` | `0` | 自动卸载超时（0=立即） |
| `MAX_CHUNK_LENGTH` | `100` | 安全分块大小 |
| `DEFAULT_OVERLAP` | `0` | 滑动窗口重叠（0=禁用） |
| `NVIDIA_VISIBLE_DEVICES` | `0` | GPU 设备 ID |

### 模型选择指南

| 模型 | 显存 | 质量 | 速度 | 使用场景 |
|------|------|------|------|----------|
| 4B-Q4 | ~3GB | 良好 | 快 | 快速翻译 |
| 4B-Q8 | ~5GB | 较好 | 快 | 日常使用 |
| 12B-Q4 | ~7GB | 高 | 中 | 平衡选择 |
| 12B-Q8 | ~12GB | 更高 | 中 | 推荐使用 |
| 27B-Q4 | ~15GB | 最佳 | 慢 | 高质量翻译 |
| **27B-Q8** | ~28GB | **最佳+** | 慢 | **专业翻译** ⭐ |

---

## 🌍 支持的语言（55 种）

| 代码 | 语言 | 代码 | 语言 | 代码 | 语言 |
|------|------|------|------|------|------|
| `en` | 英语 | `zh` | 简体中文 | `zh-TW` | 繁体中文 |
| `ja` | 日语 | `ko` | 韩语 | `yue` | 粤语 |
| `fr` | 法语 | `de` | 德语 | `es` | 西班牙语 |
| `pt` | 葡萄牙语 | `ru` | 俄语 | `ar` | 阿拉伯语 |
| `hi` | 印地语 | `th` | 泰语 | `vi` | 越南语 |

...以及 40 多种其他语言。查看 `/languages` 端点获取完整列表。

---

## 🐳 Docker 镜像

| 镜像 | 大小 | 描述 |
|------|------|------|
| `neosun/translategemma:v1.0.0-allinone` | 82GB | 内置全部 6 个模型 |
| `neosun/translategemma:latest-allinone` | 82GB | 最新 all-in-one |
| `neosun/translategemma:v1.0.0` | 10GB | 轻量版，按需下载模型 |
| `neosun/translategemma:latest` | 10GB | 最新轻量版 |

---

## 📊 技术细节

### 智能分块

TranslateGemma 会截断长文本。我们的智能分块确保完整翻译：

```
chunk_size=100  →  100% 翻译完整度
chunk_size=120  →  44% 完整度（截断）
chunk_size=150  →  44% 完整度（截断）
```

**关键发现**：`chunk_size=100` 是确保完整翻译的安全边界。

### 上下文一致性

TranslateGemma 自动维护跨分块的一致性：
- ✅ 代词（他/她/他们）
- ✅ 术语（NLP、AI）
- ✅ 专有名词（Google、Microsoft）
- ✅ 性别一致性

无需重叠即可保持上下文。

---

## 🤖 MCP 集成

与 Claude Desktop 或其他 MCP 兼容的 AI 助手配合使用：

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

## 📁 项目结构

```
translategemma/
├── app_fastapi.py          # FastAPI 服务器
├── mcp_server.py           # MCP 服务器
├── templates/
│   └── index.html          # Web UI
├── static/
│   ├── app.js              # 前端 JS
│   └── style.css           # 样式
├── translategemma_cli/     # 核心库
│   ├── translator.py       # 翻译逻辑
│   ├── chunker.py          # 文本分块
│   ├── model.py            # 模型加载
│   └── config.py           # 配置
├── Dockerfile              # 标准镜像
├── Dockerfile.allinone     # All-in-one 镜像
├── docker-compose.yml      # Compose 配置
└── tests/                  # 测试套件
```

---

## 🔬 研究发现

我们的广泛测试揭示：

| 参数 | 最优值 | 原因 |
|------|--------|------|
| chunk_size | 100 | 100% 翻译完整度 |
| overlap | 0 | TranslateGemma 自动维护上下文 |
| quantization | Q8 | 最佳质量/速度平衡 |

详见 [CHUNKING_RESEARCH_REPORT.md](docs/CHUNKING_RESEARCH_REPORT.md)。

---

## 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

**注意**：TranslateGemma 模型受 [Google 模型许可证](https://ai.google.dev/gemma/terms) 约束。

---

## 🙏 致谢

- [Google TranslateGemma](https://huggingface.co/collections/google/translategemma) - 基础翻译模型
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) - GGUF 推理
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/translategemma&type=Date)](https://star-history.com/#neosun100/translategemma)

## 📱 关注公众号

![公众号](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
