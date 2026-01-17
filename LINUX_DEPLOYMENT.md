# TranslateGemma CLI - Linux 多 GPU 部署指南

> ⚠️ **重要提示**: TranslateGemma-27b 模型在 Linux 上使用 bitsandbytes 4-bit/8-bit 量化时存在数值稳定性问题，会产生 NaN 或乱码输出。本指南提供经过验证的多 GPU 部署方案。

## 🔍 问题背景

在 Linux + NVIDIA GPU 环境下测试发现：

| 量化方式 | 内存占用 | 输出质量 | 状态 |
|----------|----------|----------|------|
| 4-bit (bitsandbytes) | ~15GB | NaN/无输出 | ❌ 不可用 |
| 8-bit (bitsandbytes) | ~28GB | 乱码 | ❌ 不可用 |
| float16 | ~54GB | 正常 | ⚠️ 单卡放不下 |
| **bfloat16 + 多GPU** | ~27GB/卡 | **正常** | ✅ **推荐** |

## 🚀 推荐部署方案

### 硬件要求

- **GPU**: 2x NVIDIA GPU，每卡 ≥32GB VRAM
  - 推荐: A100 40GB, L40S 48GB, RTX 4090 24GB×3
- **系统内存**: ≥64GB RAM
- **存储**: ≥100GB 可用空间

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli

# 2. 使用 uv 创建环境（推荐）
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[cuda,dev]"

# 3. 初始化配置
translate init
```

### 多 GPU 启动

```bash
# 查看 GPU 状态，选择空闲的 GPU
nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv

# 使用 GPU 1 和 GPU 2 运行（根据实际情况调整）
CUDA_VISIBLE_DEVICES=1,2 translate --text "Hello world"

# 或者设置环境变量后运行
export CUDA_VISIBLE_DEVICES=1,2
translate --text "Hello world"
```

### 验证安装

```bash
# 测试英文到粤语
CUDA_VISIBLE_DEVICES=1,2 translate --text "Hello world, how are you today?"
# 预期输出: 哈囉，世界，你今天過得怎麼樣？

# 测试中文到英文
CUDA_VISIBLE_DEVICES=1,2 translate --text "今天天气真好" --to en
# 预期输出: The weather is really nice today.

# 测试日语
CUDA_VISIBLE_DEVICES=1,2 translate --text "Hello" --to ja
# 预期输出: こんにちは。
```

## 📊 性能数据

**测试环境**: 4x NVIDIA L40S (48GB), Ubuntu Linux

| 指标 | 数值 |
|------|------|
| 模型加载时间 | ~8 秒 |
| 翻译延迟 | ~2-3 秒/句 |
| GPU 内存使用 | ~27GB/卡 |
| 支持的最大文本 | 无限制（自动分块） |

## 🔧 故障排除

### 问题 1: CUDA out of memory

```
torch.OutOfMemoryError: CUDA out of memory
```

**解决方案**: 增加 GPU 数量
```bash
# 使用 3 个 GPU
CUDA_VISIBLE_DEVICES=0,1,2 translate --text "Hello"
```

### 问题 2: 输出全是 pad token 或 NaN

**原因**: 使用了 bitsandbytes 量化的本地缓存模型

**解决方案**: 删除本地缓存，让程序直接从 HuggingFace 加载
```bash
rm -rf ~/.cache/translate/models/translategemma-*
```

### 问题 3: 模型加载缓慢

**解决方案**: 确保 HuggingFace 模型已缓存
```bash
# 预下载模型
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('google/translategemma-27b-it')"
```

### 问题 4: 找不到 CUDA

```bash
# 检查 CUDA 是否可用
python -c "import torch; print(torch.cuda.is_available())"

# 检查 PyTorch CUDA 版本
python -c "import torch; print(torch.version.cuda)"
```

## 🐳 Docker 部署（可选）

```dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y python3.11 python3-pip git
RUN pip install uv

WORKDIR /app
COPY . .
RUN uv venv .venv && . .venv/bin/activate && uv pip install -e ".[cuda]"

ENV CUDA_VISIBLE_DEVICES=0,1
CMD [".venv/bin/translate"]
```

```bash
# 构建并运行
docker build -t translategemma-cli .
docker run --gpus '"device=1,2"' -it translategemma-cli --text "Hello"
```

## 📝 Shell 别名（推荐）

添加到 `~/.bashrc` 或 `~/.zshrc`:

```bash
# TranslateGemma 快捷命令
alias tg='CUDA_VISIBLE_DEVICES=1,2 /path/to/translategemma-cli/.venv/bin/translate'
alias tg-en='tg --to en'
alias tg-zh='tg --to zh'
alias tg-ja='tg --to ja'

# 使用示例
# tg "Hello world"
# tg-zh "Good morning"
# echo "Bonjour" | tg-en
```

## 🔗 相关文档

- [README.md](README.md) - 主文档
- [INSTALLATION.md](INSTALLATION.md) - 安装指南
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - 最佳实践

---

**测试日期**: 2026-01-17  
**测试环境**: Ubuntu Linux, 4x NVIDIA L40S, Python 3.12  
**版本**: v0.2.1
