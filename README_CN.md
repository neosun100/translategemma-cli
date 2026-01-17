[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# TranslateGemma CLI

> 🚀 基于 Google TranslateGemma 的生产级本地翻译工具  
> 支持 55 种语言，具备智能分块、流式输出和批量处理功能

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Model: TranslateGemma](https://img.shields.io/badge/Model-TranslateGemma-green.svg)](https://huggingface.co/collections/google/translategemma)

---

## ✨ 亮点功能

- **🌍 55 种语言** - 完整支持 TranslateGemma 语言
- **📚 无限长度** - 智能分块滑动窗口处理任意长度文本
- **⚡ 流式输出** - 实时翻译进度显示
- **📦 批量处理** - 一次翻译整个目录
- **🎯 多种后端** - 本地 (MLX/PyTorch)、vLLM 或 Ollama
- **💻 跨平台** - macOS (Apple Silicon)、Linux、Windows
- **🔧 高度可配置** - 灵活参数适应不同使用场景

---

## 🎬 快速开始

### 安装

```bash
# 使用 uv（推荐）
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[mlx]"  # macOS Apple Silicon
# 或者
uv pip install -e ".[cuda]"  # Linux/Windows with NVIDIA GPU

# 使用 pip
pip install -e ".[mlx]"  # macOS Apple Silicon
pip install -e ".[cuda]"  # Linux/Windows with NVIDIA GPU
pip install -e ".[cpu]"  # 仅 CPU
```

### 首次运行

```bash
# 初始化配置
translate init

# 下载模型（仅首次）
translate model download 27b

# 开始翻译！
translate --text "Hello world"
# 输出: 你好，世界。
```

---

## 🚀 功能特性

### 1. 智能长文本翻译

**问题**: TranslateGemma 会截断长文本（>500 字符）

**解决方案**: 智能分块滑动窗口

```bash
# 长文本自动分块
translate --file long_article.txt

# 自定义分块参数
translate --file book.txt --chunk-size 80 --overlap 10

# 短文本禁用分块
translate --file short.txt --no-chunk
```

**工作原理**:
```
原文: [AAAAA][BBBBB][CCCCC][DDDDD]

滑动窗口:
分块 1: [AAAAA]
分块 2:    [AA|BBBBB]    ← 重叠提供上下文
分块 3:         [BB|CCCCC]
分块 4:              [CC|DDDDD]

结果: 保持上下文的完整翻译
```

### 2. 流式输出

实时翻译进度提升用户体验:

```bash
# 逐词流式输出
translate --file article.txt --stream

# 结合分块使用
translate --file book.txt --chunk-size 80 --stream
```

### 3. 批量翻译

高效翻译整个目录:

```bash
# 翻译所有 .txt 和 .md 文件
translate --dir ./documents

# 输出到 ./documents/translated/
```

### 4. 交互式 REPL

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

### 基础翻译

```bash
# 单个文本
translate --text "Hello world"

# 从文件
translate --file input.txt --output output.txt

# 从标准输入
echo "Bonjour" | translate

# 强制目标语言
translate --text "Hello" --to ja
```

### 长文本翻译

```bash
# 自动分块（文本 > 300 字符）
translate --file article.txt

# 自定义分块
translate --file book.txt --chunk-size 80 --overlap 10

# 实时反馈流式输出
translate --file long.txt --stream

# 禁用分块
translate --file short.txt --no-chunk
```

### 批量处理

```bash
# 翻译目录
translate --dir ./documents

# 使用自定义参数
translate --dir ./docs --chunk-size 100
```

### 模型管理

```bash
# 列出模型
translate model list

# 下载模型
translate model download 4b

# 检查状态
translate model status

# 列出支持的语言
translate model langs
```

---

## ⚙️ 配置

配置文件: `~/.config/translate/config.yaml`

### 默认配置（已优化）

```yaml
model:
  name: 27b              # 模型大小: 4b, 12b, 27b
  quantization: 4        # 4位或8位量化

backend:
  type: auto             # auto, mlx, pytorch, vllm, ollama
  vllm_url: http://localhost:8000
  ollama_url: http://localhost:11434

translation:
  languages: [yue, en]   # 语言对
  mode: direct           # direct 或 explain
  max_tokens: 512        # 基础最大令牌数（分块时自动调整）
  
  chunking:
    enabled: true        # 启用智能分块
    chunk_size: 80       # 完整性最优
    overlap: 10          # 最小重复
    split_by: sentence   # sentence, paragraph, 或 char
    auto_threshold: 300  # 文本 > 300 字符时自动启用

ui:
  show_detected_language: true
  colored_output: true
  show_progress: true
```

### 自定义配置

```bash
# 使用默认值初始化
translate init

# 强制覆盖
translate init --force

# 手动编辑
vim ~/.config/translate/config.yaml
```

---

## 🎯 最佳实践

### 分块大小选择

| 文本类型 | chunk_size | overlap | 原因 |
|-----------|------------|---------|--------|
| 日常对话 | 60-80 | 10-15 | 短句 |
| 技术文档 | 80-100 | 15-20 | 术语一致性 |
| 文学作品 | 80-100 | 20-30 | 上下文保持 |
| 长篇文章 | 80-100 | 10-20 | 平衡质量与速度 |

### 何时使用分块

| 文本长度 | 建议 |
|-------------|----------------|
| < 300 字符 | 使用 `--no-chunk` 提升速度 |
| 300-1000 字符 | 自动分块（默认） |
| 1000-5000 字符 | `--chunk-size 80 --overlap 10` |
| 5000+ 字符（书籍） | `--chunk-size 80 --stream` |

### 性能提示

1. **交互模式** - 模型加载一次，多次翻译更快
2. **批量处理** - 使用 `--dir` 而非逐个翻译文件
3. **流式输出** - 长文本使用 `--stream` 查看进度
4. **最优分块** - chunk_size=80, overlap=10 是最佳选择

---

## 📊 性能表现

**测试环境**: MacBook Pro M2 Max, 96GB, MLX 后端

| 文本长度 | 分块数 | 时间 | 吞吐量 |
|-------------|--------|------|------------|
| 100 字符 | 1 | 1.2s | 83 字符/秒 |
| 400 字符 | 4 | 8.5s | 48 字符/秒 |
| 1000 字符 | 12 | ~22s | ~45 字符/秒 |
| 5000 字符 | 60 | ~110s | ~45 字符/秒 |

**内存使用**: 14.15 GB（所有文本长度稳定）

---

## 🛠️ 系统要求

### macOS (Apple Silicon)
- M1/M2/M3/M4 Mac
- 8GB+ 统一内存 (4b), 16GB+ (12b), 32GB+ (27b)
- macOS 14.0+

### Linux (NVIDIA GPU) ⚠️ 重要

> **注意**: TranslateGemma-27b 在 Linux 上需要**多个 GPU**，因为 bitsandbytes 量化存在兼容性问题。详见 [LINUX_DEPLOYMENT.md](LINUX_DEPLOYMENT.md)。

- **27b 模型**: 2x GPU，每卡 ≥32GB 显存（如 A100、L40S、RTX 4090×3）
- **12b 模型**: 1x GPU，≥24GB 显存
- **4b 模型**: 1x GPU，≥16GB 显存
- CUDA 11.8+
- Python 3.11+

```bash
# Linux 多 GPU 使用方式（27b 模型必需）
CUDA_VISIBLE_DEVICES=1,2 translate --text "Hello world"
```

### Windows
- NVIDIA GPU 16GB+ 显存
- CUDA 11.8+（GPU 版本）

### 所有平台
- Python 3.11+

---

## 📦 安装选项

### 选项 1: uv（最快，推荐）

```bash
# 如未安装 uv，先安装
curl -LsSf https://astral.sh/uv/install.sh | sh

# 克隆并安装
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
uv venv .venv
source .venv/bin/activate

# macOS Apple Silicon
uv pip install -e ".[mlx]"

# Linux/Windows with NVIDIA GPU
uv pip install -e ".[cuda]"

# 仅 CPU
uv pip install -e ".[cpu]"
```

### 选项 2: pipx（隔离安装）

```bash
# 从本地目录安装
pipx install /path/to/translategemma-cli[mlx]

# 或从 git（发布后）
pipx install git+https://github.com/jhkchan/translategemma-cli.git[mlx]
```

### 选项 3: pip（传统方式）

```bash
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
python3 -m venv venv
source venv/bin/activate
pip install -e ".[mlx]"  # 或 [cuda] 或 [cpu]
```

---

## 🌍 支持的语言（55种）

| 代码 | 语言 | 代码 | 语言 |
|------|----------|------|----------|
| `en` | 英语 | `yue` | 粤语 |
| `zh` | 中文（简体） | `zh-TW` | 中文（繁体） |
| `ja` | 日语 | `ko` | 韩语 |
| `fr` | 法语 | `de` | 德语 |
| `es` | 西班牙语 | `pt` | 葡萄牙语 |
| `ru` | 俄语 | `ar` | 阿拉伯语 |

...还有 45 种语言。运行 `translate model langs` 查看完整列表。

---

## 🎓 高级用法

### 自定义语言对

编辑 `~/.config/translate/config.yaml`:

```yaml
translation:
  languages: [ja, en]  # 日语 ↔ 英语
  # 或
  languages: [zh, fr]  # 中文 ↔ 法语
```

### 后端选项

```bash
# 本地（默认）
translate --backend mlx  # macOS
translate --backend pytorch  # Linux/Windows

# vLLM（高吞吐量）
vllm serve google/translategemma-27b-it --quantization awq
translate --backend vllm --server http://localhost:8000

# Ollama（简易设置）
ollama pull translategemma:27b
translate --backend ollama
```

### 交互式命令

| 命令 | 功能 |
|---------|----------|
| `/to <lang>` | 强制目标语言 |
| `/auto` | 启用自动检测 |
| `/mode direct` | 直接翻译 |
| `/mode explain` | 带解释翻译 |
| `/model <size>` | 切换模型 |
| `/backend <type>` | 切换后端 |
| `/langs` | 列出语言 |
| `/config` | 显示配置 |
| `/quit` | 退出 |

---

## 🔬 技术细节

### 智能分块算法

```python
# 基于句子的滑动窗口分割
TextChunker(
    chunk_size=80,      # 目标分块大小
    overlap=10,         # 上下文重叠
    split_by="sentence" # 在句子边界分割
)

# 处理流程:
1. 在句子边界分割文本
2. 将句子分组为分块（~80字符）
3. 添加前一分块的重叠
4. 带上下文翻译每个分块
5. 合并结果（跳过重叠）
```

### 自适应 max_tokens

```python
# 基于输入长度动态调整
adaptive_max_tokens = min(
    2048,                      # 上限
    max(512, len(chunk) * 3)   # 3倍输入（安全缓冲）
)

# 为什么是 3倍？
# - 中文 → 英文通常扩展 1.5-2倍
# - 3倍提供安全缓冲
# - 防止截断
```

### 合并策略

```python
# 简单连接（重叠仅提供上下文）
def merge(chunks, translations):
    result = [translations[0]]  # 保留第一个完整
    for trans in translations[1:]:
        result.append(" " + trans)  # 分块间添加空格
    return "".join(result)

# 注意: 最小重叠（10）减少重复
```

---

## 📚 文档

| 文档 | 描述 |
|----------|-------------|
| [README.md](README.md) | 主要文档（本文件） |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 快速参考卡 |
| [BEST_PRACTICES.md](BEST_PRACTICES.md) | 使用最佳实践 |
| [LONG_TEXT_FEATURE_REPORT.md](LONG_TEXT_FEATURE_REPORT.md) | 功能详细报告 |
| [FINAL_TEST_REPORT.md](FINAL_TEST_REPORT.md) | 综合测试报告 |
| [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) | 开发总结 |
| [TRANSLATION_TEST_REPORT.md](TRANSLATION_TEST_REPORT.md) | 多语言质量评估 |

---

## 🎯 使用场景

### 场景 1: 翻译书籍

```bash
# 带进度反馈的流式输出
translate --file novel.txt --chunk-size 80 --overlap 10 --stream --output novel_en.txt
```

### 场景 2: 批量翻译文档

```bash
# 翻译目录中所有文档
translate --dir ./docs

# 输出到 ./docs/translated/
```

### 场景 3: 快速翻译

```bash
# 短文本，无分块
translate --text "Hello world" --no-chunk

# 或使用交互模式
translate
> Hello world
[en→yue] 你好，世界。
```

### 场景 4: 多语言工作流

```bash
# 英语到多种语言
translate --text "Welcome" --to ja  # 日语
translate --text "Welcome" --to ko  # 韩语
translate --text "Welcome" --to zh  # 中文
translate --text "Welcome" --to fr  # 法语
```

---

## 🔧 开发洞察

### 关键学习

1. **TranslateGemma 模型特性**:
   - 截断长文本（>500 字符）
   - 在段落分隔符（空行）处停止
   - 需要小分块（80-100 字符）确保完整性

2. **最优分块策略**:
   - chunk_size=80: 最佳完整性（98%）
   - overlap=10: 最小重复（<5%）
   - split_by=sentence: 自然边界

3. **自适应 max_tokens**:
   - 固定 512 令牌对长分块不足
   - 3倍输入长度确保完整性
   - 上限 2048 防止过度生成

4. **合并策略**:
   - 简单连接效果最佳
   - 重叠提供上下文，非去重用
   - 智能去重复杂（未来工作）

### 架构

```
用户输入
    ↓
TextChunker (chunker.py)
    ↓
[分块 1] [分块 2] [分块 3] ...
    ↓         ↓         ↓
Translator.translate_long()
    ↓
自适应 max_tokens（3倍输入）
    ↓
MLX/PyTorch/vLLM/Ollama 后端
    ↓
合并结果
    ↓
输出（完整翻译）
```

---

## 🧪 测试

### 运行测试

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行所有测试
pytest

# 带覆盖率运行
pytest --cov=translategemma_cli

# 运行特定测试
pytest tests/test_chunker.py
```

### 手动测试

```bash
# 综合测试套件
./tests/comprehensive_test.sh

# 或测试单个功能
translate --file test.txt --chunk-size 80
translate --dir ./test_docs
translate --text "Test" --stream
```

---

## 📊 基准测试

### 翻译完整性

| 方法 | 完整性 | 速度 | 建议 |
|--------|--------------|-------|----------------|
| 无分块 | 13% | 快 | ❌ 长文本失败 |
| chunk=150 | 70% | 中等 | ⚠️ 不推荐 |
| chunk=100 | 95% | 中等 | ✅ 良好 |
| chunk=80 | 98% | 中等 | ✅ **最佳** |
| chunk=60 | 100% | 慢 | ⚠️ 过度分块 |

### 重叠影响

| 重叠 | 重复率 | 质量 | 建议 |
|---------|------------|---------|----------------|
| 0 | 0% | 中等 | ⚠️ 无上下文 |
| 10 | <5% | 高 | ✅ **最佳** |
| 20 | 5-10% | 高 | ✅ 良好 |
| 30 | 10-15% | 中等 | ⚠️ 过多 |
| 50 | 20-30% | 低 | ❌ 不推荐 |

---

## 🎨 模型选择

| 模型 | 参数量 | 磁盘大小 | 内存 | 使用场景 |
|-------|------------|-----------|--------|----------|
| **4b** | 5B | ~3.2 GB | 8GB+ | 快速翻译，资源有限 |
| **12b** | 13B | ~7.0 GB | 16GB+ | 平衡性能与质量 |
| **27b** | 29B | ~14.8 GB | 32GB+ | **最佳质量**（推荐） |

---

## 🌟 v0.2.0 新功能

### 主要功能

- ✅ **智能文本分块** - 处理无限长度文本
- ✅ **滑动窗口** - 重叠保持上下文
- ✅ **流式输出** - 实时翻译进度
- ✅ **批量翻译** - 处理整个目录
- ✅ **自适应 max_tokens** - 防止截断
- ✅ **进度显示** - rich 库视觉反馈

### 新 CLI 参数

```bash
--chunk-size <int>    # 分块大小（默认: 80）
--overlap <int>       # 重叠大小（默认: 10）
--no-chunk            # 禁用分块
--stream              # 启用流式输出
--dir <path>          # 批量翻译目录
```

### 性能改进

- **翻译完整性**: 13% → 98%（长文本）
- **吞吐量**: 稳定 45-50 字符/秒
- **内存**: 不变（14.15 GB）

---

## 🐛 已知限制

### 1. 模型行为

- **段落分隔**: 模型在空行处停止
  - **解决方案**: 使用小分块（80 字符）
- **长分块**: 分块 > 150 字符时截断
  - **解决方案**: 自适应 max_tokens（3倍输入）

### 2. 重叠重复

- **问题**: 重叠 > 10 导致轻微重复
- **原因**: 重叠区域被翻译两次
- **建议**: 使用 overlap=10-20

### 3. 尚未实现

- 智能去重（计划 v0.3.0）
- 翻译缓存（计划 v0.3.0）
- 恢复功能（计划 v0.4.0）
- 术语支持（评估中）

---

## 🤝 贡献

欢迎贡献！请：

1. Fork 仓库
2. 创建功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 打开 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件。

**注意**: TranslateGemma 模型受 Google 模型许可条款约束。请查看并遵守[模型许可证](https://ai.google.dev/gemma/terms)。

---

## 🙏 致谢

- [Google TranslateGemma](https://huggingface.co/collections/google/translategemma) - 基础翻译模型
- [MLX](https://github.com/ml-explore/mlx) - Apple Silicon 优化
- [Cursor](https://cursor.com/) + [Claude](https://www.anthropic.com/claude) - 开发工具
- [hy-mt](https://github.com/neosun100/hy-mt) - 分块策略灵感

---

## 🔗 链接

- **GitHub**: https://github.com/jhkchan/translategemma-cli
- **HuggingFace**: https://huggingface.co/collections/google/translategemma
- **Issues**: https://github.com/jhkchan/translategemma-cli/issues
- **文档**: 查看 [docs](docs/) 目录

---

## 📞 支持

- **Issues**: [GitHub Issues](https://github.com/jhkchan/translategemma-cli/issues)
- **讨论**: [GitHub Discussions](https://github.com/jhkchan/translategemma-cli/discussions)
- **邮箱**: [Your Email]

---

## 🗺️ 路线图

### v0.3.0（下一版本）
- [ ] 智能去重算法
- [ ] 翻译缓存系统
- [ ] 改进语言检测
- [ ] 术语支持

### v0.4.0（未来）
- [ ] 恢复功能
- [ ] 并行翻译（多GPU）
- [ ] Web UI
- [ ] REST API 服务器

---

**版本**: 0.2.0  
**最后更新**: 2026-01-17  
**状态**: 生产就绪 ✅