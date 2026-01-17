# TranslateGemma CLI - 安装指南

## 🚀 快速安装（推荐）

### 方式1: 从 PyPI 安装（最简单）

```bash
# macOS (Apple Silicon)
pip install translategemma-cli[mlx]

# Linux/Windows with NVIDIA GPU
pip install translategemma-cli[cuda]

# CPU-only
pip install translategemma-cli[cpu]
```

### 方式2: 使用 pipx（隔离安装）

```bash
# macOS (Apple Silicon)
pipx install translategemma-cli[mlx]

# Linux/Windows with NVIDIA GPU
pipx install translategemma-cli[cuda]
```

### 方式3: 使用 uv（最快）

```bash
# macOS (Apple Silicon)
uv tool install translategemma-cli[mlx]

# 或创建虚拟环境
uv venv .venv
source .venv/bin/activate
uv pip install translategemma-cli[mlx]
```

---

## 📦 首次使用

```bash
# 1. 初始化配置
translate init

# 2. 下载模型（首次运行）
translate model download 27b

# 3. 开始翻译！
translate --text "Hello world"
# 输出: 你好，世界。
```

---

## 🎯 验证安装

```bash
# 检查版本
translate --help

# 查看模型状态
translate model status

# 查看支持的语言
translate model langs

# 测试翻译
translate --text "Hello"
```

---

## 🔧 开发安装（从源码）

```bash
# 克隆仓库
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli

# 使用 uv（推荐）
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[mlx]"  # macOS
# 或
uv pip install -e ".[cuda]"  # Linux/Windows GPU

# 使用 pip
python3 -m venv venv
source venv/bin/activate
pip install -e ".[mlx]"  # macOS
```

---

## 📊 模型选择

| 模型 | 参数量 | 磁盘占用 | 推荐内存 | 下载命令 |
|------|--------|----------|----------|----------|
| 4b | 5B | ~3.2 GB | 8GB+ | `translate model download 4b` |
| 12b | 13B | ~7.0 GB | 16GB+ | `translate model download 12b` |
| 27b | 29B | ~14.8 GB | 32GB+ | `translate model download 27b` |

---

## 🌍 支持的平台

| 平台 | 后端 | 安装命令 |
|------|------|----------|
| macOS (M1/M2/M3/M4) | MLX | `pip install translategemma-cli[mlx]` |
| Linux (NVIDIA GPU) | PyTorch + CUDA | `pip install translategemma-cli[cuda]` |
| Windows (NVIDIA GPU) | PyTorch + CUDA | `pip install translategemma-cli[cuda]` |
| 任意平台 (CPU) | PyTorch | `pip install translategemma-cli[cpu]` |

---

## 💡 常见问题

**Q: 安装后找不到 translate 命令？**  
A: 确保虚拟环境已激活，或使用 pipx 安装

**Q: 模型下载慢？**  
A: 首次下载需要时间，模型会缓存到 `~/.cache/translate/models/`

**Q: 内存不足？**  
A: 使用更小的模型：`translate --model 4b`

**Q: 如何卸载？**  
A: `pip uninstall translategemma-cli` 或 `pipx uninstall translategemma-cli`

---

## 🔗 相关链接

- **PyPI**: https://pypi.org/project/translategemma-cli/
- **GitHub**: https://github.com/jhkchan/translategemma-cli
- **文档**: [README.md](README.md)

---

*更新时间: 2026-01-17*  
*当前版本: v0.2.0*
