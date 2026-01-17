# TranslateGemma CLI 最佳实践指南

## 📖 目录

1. [快速开始](#快速开始)
2. [使用模式](#使用模式)
3. [语言配置](#语言配置)
4. [模型管理](#模型管理)
5. [后端选择](#后端选择)
6. [配置文件](#配置文件)
7. [实用技巧](#实用技巧)
8. [常见场景](#常见场景)

---

## 快速开始

### 激活环境

```bash
cd /path/to/translategemma-cli
source .venv/bin/activate
```

### 最简单的翻译

```bash
# 自动检测语言，翻译到配置的另一种语言
translate --text "Hello world"
# 输出: 你好，世界。
```

---

## 使用模式

### 1. 单次翻译模式

最常用的方式，适合快速翻译单句：

```bash
# 基本用法
translate --text "今日天氣好好"

# 指定目标语言
translate --text "Hello" --to ja
# 输出: こんにちは。

translate --text "Hello" --to fr
# 输出: Bonjour.

translate --text "Hello" --to de
# 输出: Hallo.
```

### 2. 交互模式 (REPL)

适合连续翻译多句，模型只加载一次：

```bash
translate
```

进入交互界面后：
```
TranslateGemma Interactive (yue ↔ en)
Model: 27b | Mode: direct | Type /help for commands

> 你好
[yue→en] Hello

> Good morning
[en→yue] 早晨

> /to ja          # 切换目标语言为日语
Target language set to: ja

> Hello
[en→ja] こんにちは。

> /auto           # 恢复自动检测
Auto-detection enabled

> /quit           # 退出
```

**交互模式命令速查：**

| 命令 | 功能 | 示例 |
|------|------|------|
| `/to <lang>` | 强制输出到指定语言 | `/to ja` |
| `/auto` | 恢复自动语言检测 | `/auto` |
| `/mode direct` | 直接翻译模式 | `/mode direct` |
| `/mode explain` | 解释模式（含上下文） | `/mode explain` |
| `/model <size>` | 切换模型大小 | `/model 4b` |
| `/backend <type>` | 切换后端 | `/backend ollama` |
| `/langs` | 显示支持的语言 | `/langs` |
| `/config` | 显示当前配置 | `/config` |
| `/clear` | 清屏 | `/clear` |
| `/help` | 显示帮助 | `/help` |
| `/quit` | 退出 | `/quit` |

### 3. 文件翻译模式

适合翻译长文本或批量处理：

```bash
# 翻译文件内容
translate --file input.txt --output output.txt

# 只翻译，输出到终端
translate --file document.txt
```

### 4. 管道模式

适合与其他命令组合：

```bash
# 从管道读取
echo "Bonjour le monde" | translate

# 组合使用
cat article.txt | translate > translated.txt

# 从剪贴板翻译 (macOS)
pbpaste | translate

# 翻译并复制到剪贴板 (macOS)
translate --text "Hello" | pbcopy
```

---

## 语言配置

### 支持的 55 种语言

运行 `translate model langs` 查看完整列表。

**常用语言代码：**

| 代码 | 语言 | 代码 | 语言 |
|------|------|------|------|
| `en` | English | `yue` | 粤语 |
| `zh` | 简体中文 | `zh-TW` | 繁体中文 |
| `ja` | 日语 | `ko` | 韩语 |
| `fr` | 法语 | `de` | 德语 |
| `es` | 西班牙语 | `pt` | 葡萄牙语 |
| `ru` | 俄语 | `ar` | 阿拉伯语 |

### 指定目标语言

```bash
# 命令行指定
translate --text "Hello" --to ja

# 交互模式中切换
> /to fr
> Hello
[en→fr] Bonjour.
```

### 修改默认语言对

编辑配置文件 `~/.config/translate/config.yaml`：

```yaml
translation:
  languages:
    - ja    # 第一语言
    - en    # 第二语言
```

**常见语言对配置示例：**

```yaml
# 日语 ↔ 英语
languages: [ja, en]

# 简体中文 ↔ 英语
languages: [zh, en]

# 韩语 ↔ 英语
languages: [ko, en]

# 法语 ↔ 德语
languages: [fr, de]
```

---

## 模型管理

### 查看模型状态

```bash
# 列出所有模型
translate model list

# 查看当前模型详情
translate model status
```

### 模型选择指南

| 模型 | 参数量 | 磁盘占用 | 推荐内存 | 适用场景 |
|------|--------|----------|----------|----------|
| **4b** | 5B | ~3.2 GB | 8GB+ | 快速翻译、资源有限 |
| **12b** | 13B | ~7.0 GB | 16GB+ | 平衡性能与质量 |
| **27b** | 29B | ~14.8 GB | 32GB+ | 最高质量、复杂文本 |

### 下载/切换模型

```bash
# 下载模型
translate model download 4b
translate model download 12b
translate model download 27b

# 使用指定模型翻译
translate --model 4b --text "Hello"

# 交互模式中切换
> /model 4b
```

### 删除模型

```bash
translate model remove 4b
```

---

## 后端选择

### 可用后端

| 后端 | 平台 | 特点 |
|------|------|------|
| **mlx** | macOS (Apple Silicon) | 原生 Metal 优化，内存效率最高 |
| **pytorch** | Linux/Windows | CUDA 加速或 CPU 回退 |
| **vllm** | 服务器 | 高吞吐量，适合批量处理 |
| **ollama** | 全平台 | 简单易用，一键部署 |

### 查看后端状态

```bash
translate backend status
```

输出示例：
```
Backend Status:
  Configured: auto

  Local: mlx
  vLLM: Not connected (http://localhost:8000)
  Ollama: ✓ Running at http://localhost:11434
```

### 使用 Ollama 后端

```bash
# 1. 安装 Ollama (https://ollama.ai)
# 2. 拉取模型
ollama pull translategemma:27b

# 3. 使用 Ollama 后端
translate --backend ollama --text "Hello"

# 或在交互模式中
> /backend ollama
```

### 使用 vLLM 后端

```bash
# 1. 启动 vLLM 服务器
vllm serve google/translategemma-27b-it --quantization awq

# 2. 使用 vLLM 后端
translate --backend vllm --server http://localhost:8000 --text "Hello"
```

---

## 配置文件

### 配置文件位置

```
~/.config/translate/config.yaml
```

### 初始化配置

```bash
# 创建默认配置
translate init

# 强制覆盖现有配置
translate init --force
```

### 完整配置示例

```yaml
# 模型设置
model:
  name: 27b              # 模型大小: 4b, 12b, 27b
  quantization: 4        # 量化位数: 4 或 8

# 后端设置
backend:
  type: auto             # auto, mlx, pytorch, vllm, ollama
  vllm_url: http://localhost:8000
  ollama_url: http://localhost:11434

# 翻译设置
translation:
  languages:             # 语言对
    - yue
    - en
  mode: direct           # direct (直接翻译) 或 explain (含解释)
  max_tokens: 512        # 最大输出长度

# 界面设置
ui:
  show_detected_language: true   # 显示检测到的语言
  colored_output: true           # 彩色输出
```

---

## 实用技巧

### 1. 解释模式

获取翻译的文化背景和上下文解释：

```bash
translate --explain --text "你食咗飯未"
```

输出会包含翻译和解释说明。

### 2. Shell 别名

在 `~/.zshrc` 或 `~/.bashrc` 中添加：

```bash
# 快速翻译别名
alias t='cd ~/Code/GenAI/translategemma-cli && source .venv/bin/activate && translate'
alias te='t --explain'
alias tj='t --to ja'
alias tz='t --to zh'

# 使用示例
t --text "Hello"
te --text "你好"
tj --text "Good morning"
```

### 3. 批量翻译脚本

```bash
#!/bin/bash
# batch_translate.sh

INPUT_DIR="./input"
OUTPUT_DIR="./output"

cd ~/Code/GenAI/translategemma-cli
source .venv/bin/activate

for file in "$INPUT_DIR"/*.txt; do
    filename=$(basename "$file")
    translate --file "$file" --output "$OUTPUT_DIR/$filename"
    echo "Translated: $filename"
done
```

### 4. 与 Alfred/Raycast 集成

创建快捷工作流，选中文本后一键翻译。

---

## 常见场景

### 场景 1: 日常粤语英语互译

```bash
# 配置 (默认)
languages: [yue, en]

# 使用
translate --text "早晨"
# 输出: Good morning

translate --text "How are you?"
# 输出: 你好嗎？
```

### 场景 2: 多语言翻译工作流

```bash
# 英语 → 多语言
translate --text "Welcome" --to ja   # 日语
translate --text "Welcome" --to ko   # 韩语
translate --text "Welcome" --to zh   # 中文
translate --text "Welcome" --to fr   # 法语
translate --text "Welcome" --to de   # 德语
```

### 场景 3: 文档翻译

```bash
# 翻译 Markdown 文档
translate --file README_EN.md --output README_ZH.md

# 翻译代码注释 (提取注释后翻译)
grep -E "^#|^//" code.py | translate
```

### 场景 4: 实时翻译聊天

```bash
# 进入交互模式
translate

# 持续翻译对话
> Hello, how can I help you?
[en→yue] 你好，有咩可以幫到你？

> 我想問下呢個產品幾錢
[yue→en] I'd like to ask how much this product costs.
```

### 场景 5: 学习外语

```bash
# 使用解释模式学习
translate --explain --text "お疲れ様でした"

# 输出会包含:
# - 翻译: Good job today / Thank you for your hard work
# - 解释: 这是日语中常用的问候语，用于...
```

---

## 性能优化建议

### 1. 选择合适的模型

- **快速响应**: 使用 4b 模型
- **日常使用**: 使用 12b 模型
- **高质量翻译**: 使用 27b 模型

### 2. 使用交互模式

模型只加载一次，后续翻译更快：

```bash
translate  # 进入交互模式，避免重复加载模型
```

### 3. 批量处理使用文件模式

```bash
# 比逐行翻译更高效
translate --file large_document.txt --output translated.txt
```

### 4. 服务器部署使用 vLLM

对于高并发场景，使用 vLLM 后端可获得更高吞吐量。

---

## 故障排除

### 模型加载慢

首次加载需要时间，后续会更快。使用交互模式避免重复加载。

### 内存不足

切换到更小的模型：
```bash
translate --model 4b --text "Hello"
```

### 翻译质量不佳

1. 尝试使用更大的模型 (27b)
2. 使用解释模式获取更多上下文
3. 检查语言代码是否正确

---

*文档版本: 1.0*  
*更新日期: 2026-01-17*
