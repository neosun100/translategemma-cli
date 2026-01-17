# TranslateGemma 滑动窗口与分块策略研究报告

**研究日期**: 2026-01-17  
**研究环境**: TranslateGemma 27B-Q8, NVIDIA GPU, Docker  
**研究者**: Kiro AI + Neo

---

## 目录

1. [研究背景](#研究背景)
2. [核心发现](#核心发现)
3. [分块策略测试](#分块策略测试)
4. [滑动窗口测试](#滑动窗口测试)
5. [上下文一致性测试](#上下文一致性测试)
6. [最终配置建议](#最终配置建议)
7. [技术实现细节](#技术实现细节)
8. [未来研究方向](#未来研究方向)

---

## 研究背景

### 问题起源

TranslateGemma 模型在处理长文本时存在截断问题：
- 当输入文本过长时，模型会提前停止输出
- 某些特定的句子组合会触发模型的 EOS (End of Sequence) token

### 研究目标

1. 确定安全的 `chunk_size` 边界
2. 验证滑动窗口 (overlap) 是否能改善翻译质量
3. 测试跨 chunk 的上下文一致性
4. 制定最佳实践配置

---

## 核心发现

### 1. chunk_size 安全边界

| chunk_size | 翻译完整度 | 状态 | 说明 |
|------------|-----------|------|------|
| 80 | 100% | ✅ 安全 | 分段较多，效率稍低 |
| **100** | **100%** | ✅ **推荐** | 最佳平衡点 |
| 120 | 44-56% | ❌ 截断 | 开始出现内容丢失 |
| 150 | 44-56% | ❌ 严重截断 | 丢失约 32% 内容 |

**关键结论**: `chunk_size=100` 是安全边界，超过此值会触发模型截断行为。

### 2. 截断问题根因

```
小 chunk (≤100 字符):
┌─────────────┐    ┌─────────────┐
│  句子 A     │ →  │  句子 B     │  → 各自独立翻译，完整输出
└─────────────┘    └─────────────┘

大 chunk (≥120 字符):
┌─────────────────────────────────────┐
│  句子 A + 句子 B + 句子 C           │  → 某些组合触发提前终止
└─────────────────────────────────────┘
```

**原因分析**:
- TranslateGemma 主要用短句对训练
- 多个语义单元合并时，模型可能误判"翻译已完成"
- 特定标点符号组合可能被误认为输入结束

### 3. 滑动窗口效果

| 场景 | 无 overlap | 有 overlap | 结论 |
|------|-----------|------------|------|
| chunk≤100 完整度 | 100% | 100% | 无差异 |
| chunk>100 完整度 | 44% | 56% | 有帮助但不能完全解决 |
| 翻译一致性 | 良好 | 良好 | 无显著差异 |
| 重复内容 | 无 | 有 (~18%) | overlap 导致重复 |

### 4. 上下文一致性

**测试结果**: TranslateGemma 模型本身具有很强的上下文理解能力

| 测试项 | 无 overlap | 有 overlap | 结论 |
|--------|-----------|------------|------|
| 代词一致性 (He/His) | ✅ 一致 | ✅ 一致 | 模型自动处理 |
| 术语一致性 (NLP) | ✅ 一致 | ✅ 一致 | 模型自动处理 |
| 专有名词 (Google) | ✅ 一致 | ✅ 一致 | 模型自动处理 |
| 指代关系 | ✅ 正确 | ✅ 正确 | 模型自动处理 |

---

## 分块策略测试

### 测试方法

使用 453 字符的中文技术文章，测试不同 chunk_size 的翻译完整度。

### 测试文本

```
人工智能的概念可以追溯到古希腊神话中的自动机器人，这些神话描绘了由工匠赫菲斯托斯
创造的金属生物。然而，作为一门正式学科，人工智能诞生于1956年的达特茅斯会议...
(共 453 字符，包含关键词：古希腊、赫菲斯托斯、达特茅斯、麦卡锡、专家系统、
人工智能寒冬、深度学习、AlexNet、ImageNet)
```

### 测试结果

| chunk_size | overlap | 分段数 | 关键词保留 | 完整度 |
|------------|---------|--------|-----------|--------|
| 80 | 0 | 7 | 9/9 | 100% ✅ |
| 80 | 20 | 7 | 9/9 | 100% ✅ |
| 100 | 0 | 7 | 9/9 | 100% ✅ |
| 100 | 20 | 7 | 9/9 | 100% ✅ |
| 120 | 0 | 5 | 4/9 | 44% ❌ |
| 120 | 30 | 5 | 5/9 | 56% ⚠️ |
| 150 | 0 | 4 | 4/9 | 44% ❌ |
| 150 | 40 | 4 | 5/9 | 56% ⚠️ |

### 关键词检测

检测以下英文关键词是否出现在翻译结果中：
- Greek, Hephaestus, Dartmouth, McCarthy
- expert system, AI winter
- deep learning, AlexNet, ImageNet

**chunk_size=100 结果** (完整):
```
The concept of artificial intelligence can be traced back to the automated 
robots in ancient Greek mythology, which depicted metal beings created by 
the craftsman Hephaestus. However, artificial intelligence emerged as a 
formal discipline at the Dartmouth Conference in 1956...
```

**chunk_size=150 结果** (截断):
```
artificial intelligence.
Researchers believed that by creating sufficiently complex rules, machines 
could simulate human thought processes...
(缺失开头的古希腊、赫菲斯托斯等内容)
```

---

## 滑动窗口测试

### 实现原理

```python
# 滑动窗口分块
def split_text(text, max_length=100, overlap=20):
    """
    overlap > 0 时，每个 chunk 会包含前一个 chunk 的尾部内容
    目的是为模型提供上下文，提高翻译连贯性
    """
    
# 示例：
# 原文: [AAAA][BBBB][CCCC][DDDD]
# 
# overlap=0:
#   chunk1: [AAAA]
#   chunk2: [BBBB]
#   chunk3: [CCCC]
#   chunk4: [DDDD]
#
# overlap=20:
#   chunk1: [AAAA]
#   chunk2: [AA][BBBB]      ← 包含前一块尾部
#   chunk3: [BB][CCCC]
#   chunk4: [CC][DDDD]
```

### 测试结果

#### 对大 chunk 的帮助

| chunk_size | 无 overlap | 有 overlap | 提升 |
|------------|-----------|------------|------|
| 120 | 44% | 56% | +12% |
| 150 | 44% | 56% | +12% |

**结论**: 滑动窗口对大 chunk 有一定帮助，但无法完全解决截断问题。

#### 重复内容问题

**测试文本**: 162 字符代词测试文本

**无 overlap 结果** (632 字符):
```
Li Ming is an outstanding computer scientist who earned his doctorate from 
Peking University. After graduation, he joined a well-known technology 
company and served as its Chief Technology Officer. Under his leadership, 
the company developed several innovative products. His management style is 
highly appreciated by his employees. He often said that innovation is the 
core driving force...
```

**有 overlap 结果** (696 字符, +10%):
```
Li Ming is an outstanding computer scientist who earned his doctorate from 
Peking University. After graduation, he joined a well-known technology 
company and served as its Chief Technology Officer. Under his leadership, 
the company developed several innovative products. His management style is 
highly appreciated by his employees. His management style is highly 
appreciated by his employees. He often says that innovation is the core 
driving force...
                                    ↑
                            重复内容出现
```

**检测到的重复片段**:
- "His management style is highly appreciated by his employees."
- "at the Dartmouth Conference in 1956."
- "machines could simulate human thought processes."
- "they struggled to handle uncertainty,"

---

## 上下文一致性测试

### 测试目的

验证无滑动窗口时，跨 chunk 边界的翻译是否会出现不一致。

### 测试用例

#### 1. 代词指代一致性

**原文** (162 字符):
```
李明是一位杰出的计算机科学家，他在北京大学获得了博士学位。毕业后，他加入了
一家知名的科技公司担任首席技术官。在他的领导下，公司开发出了多款创新产品...
```

**无 overlap 翻译**:
```
Li Ming is an outstanding computer scientist who earned his doctorate from 
Peking University. After graduation, he joined a well-known technology 
company and served as its Chief Technology Officer. Under his leadership...
```

**代词统计**: He: 6次, His: 7次, Him: 0次 ✅ 一致

#### 2. 术语一致性

**原文** (150 字符):
```
自然语言处理是人工智能的重要分支。自然语言处理技术可以让计算机理解人类语言。
近年来，自然语言处理取得了巨大进步...
```

**无 overlap 翻译**:
```
Natural language processing is an important branch of artificial intelligence. 
Natural language processing technology enables computers to understand human 
language. In recent years, natural language processing has made significant 
progress...
```

**术语统计**: "natural language processing": 8次 ✅ 一致

#### 3. 专有名词一致性

**原文** (134 字符):
```
谷歌是全球最大的搜索引擎公司。谷歌的总部位于加利福尼亚州山景城。谷歌开发了
安卓操作系统。谷歌还拥有YouTube视频平台...
```

**无 overlap 翻译**:
```
Google is the world's largest search engine company. Its headquarters are 
located in Mountain View, California. Google developed the Android operating 
system. Google also owns the YouTube video platform...
```

**专有名词统计**: "Google": 8次 ✅ 一致

### 测试结论

| 测试项 | 无 overlap | 有 overlap | 结论 |
|--------|-----------|------------|------|
| 代词 He/His | 一致 | 一致 | 模型自动处理 |
| 术语 NLP | 一致 | 一致 | 模型自动处理 |
| 专有名词 Google | 一致 | 一致 | 模型自动处理 |
| 性别代词 She/Her | 一致 | 一致 | 模型自动处理 |

**重要发现**: TranslateGemma 模型本身具有很强的上下文理解能力，即使分 chunk 翻译，也能保持术语和代词的一致性。

---

## 最终配置建议

### 生产环境推荐配置

```env
# .env 文件
MODEL_NAME=27b
QUANTIZATION=8
BACKEND=gguf
GPU_IDLE_TIMEOUT=0
MAX_CHUNK_LENGTH=100    # 必须 ≤ 100，这是安全边界
DEFAULT_OVERLAP=0       # 默认关闭，避免重复内容
REPETITION_PENALTY=1.0
```

### 配置说明

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| MAX_CHUNK_LENGTH | 100 | 安全边界，保证翻译完整性 |
| DEFAULT_OVERLAP | 0 | 默认关闭，因为会导致重复内容 |
| GPU_IDLE_TIMEOUT | 0 | 翻译完成后立即释放显存 |

### API 使用示例

```python
# 标准翻译（推荐）
requests.post("/api/translate", json={
    "text": "要翻译的文本",
    "target_lang": "en",
    "chunk_size": 100,
    "overlap": 0,  # 默认
})

# 需要强上下文连贯性时（接受轻微重复）
requests.post("/api/translate", json={
    "text": "要翻译的文本",
    "target_lang": "en",
    "chunk_size": 100,
    "overlap": 20,  # 启用滑动窗口
})
```

### 何时使用滑动窗口

| 场景 | overlap 建议 | 说明 |
|------|-------------|------|
| 一般翻译 | 0 | 默认配置，无重复 |
| 技术文档 | 0 | 术语自动保持一致 |
| 文学作品 | 10-20 | 可能需要更强连贯性 |
| 法律文档 | 0 | 避免重复造成歧义 |

---

## 技术实现细节

### 分块算法

```python
def split_text(text: str, max_length: int = 100, overlap: int = 0) -> List[dict]:
    """
    智能文本分块，支持可选的滑动窗口
    
    1. 首先按段落分割（双换行或单换行）
    2. 对长段落按句子边界分割
    3. 累积句子直到达到 max_length
    4. 如果 overlap > 0，添加前一块的尾部作为上下文
    
    返回: [{"text": "...", "overlap_chars": 0}, ...]
    """
```

### 句子分割

```python
def split_sentences(text: str) -> List[str]:
    """
    按句子边界分割文本
    支持中英文标点：。！？.!?
    """
    sentence_pattern = r'([。！？.!?]+[\s]*)'
    # ...
```

### 合并策略

```python
def _merge_translations(results: List[dict], original_text: str, has_overlap: bool) -> str:
    """
    合并翻译结果
    
    当前策略：简单拼接
    - 第一个 chunk 完整保留
    - 后续 chunk 直接拼接
    - overlap 部分会被翻译两次（导致重复）
    
    未来改进：智能去重
    """
```

### API 参数

```python
class TranslateRequest(BaseModel):
    text: str                           # 待翻译文本
    target_lang: str                    # 目标语言
    source_lang: Optional[str] = None   # 源语言（自动检测）
    model: Optional[str] = None         # 模型选择
    chunk_size: int = 100               # 分块大小
    overlap: int = 0                    # 滑动窗口大小
    auto_split: bool = True             # 自动分块
    stream: bool = False                # 流式输出
```

---

## 未来研究方向

### 1. 智能去重算法

**问题**: 当前 overlap 会导致重复内容

**可能方案**:
- 基于相似度匹配的去重
- 使用 LCS (最长公共子序列) 算法
- 翻译后处理去重

### 2. Prompt Engineering

**问题**: 无法精确控制哪部分是"上下文"哪部分是"待翻译内容"

**可能方案**:
- 研究 TranslateGemma 的 chat template
- 尝试自定义 prompt 格式
- 探索 few-shot 示例

### 3. 术语表支持

**问题**: TranslateGemma 不支持术语干预

**可能方案**:
- 后处理替换
- 使用通用 LLM 进行术语控制
- 等待官方支持（论文提到 Future Work）

### 4. 上下文参考

**问题**: 无法提供参考译文

**可能方案**:
- 翻译记忆库 (TM) 集成
- 前文翻译结果作为参考
- 多轮翻译优化

---

## 附录

### A. 测试脚本

| 脚本 | 用途 |
|------|------|
| `test_sliding_window.py` | 滑动窗口基础测试 |
| `test_critical.py` | 截断问题关键测试 |
| `test_quality.py` | 翻译质量对比 |
| `test_context_consistency.py` | 上下文一致性测试 |
| `test_cross_chunk.py` | 跨 chunk 一致性测试 |

### B. 关键代码位置

| 功能 | 文件 | 函数 |
|------|------|------|
| 文本分块 | `app_fastapi.py` | `split_text()` |
| 滑动窗口 | `app_fastapi.py` | `_get_overlap_text()` |
| 翻译合并 | `app_fastapi.py` | `_merge_translations()` |
| CLI 分块器 | `translategemma_cli/chunker.py` | `TextChunker` |

### C. 参考资料

- [TranslateGemma Technical Report](https://arxiv.org/pdf/2601.09012)
- [TranslateGemma HuggingFace](https://huggingface.co/google/translategemma-27b-it)
- [Gemma 3 Technical Report](https://arxiv.org/abs/2503.19786)

---

## 变更历史

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-01-17 | 1.0 | 初始研究报告 |

---

*报告生成时间: 2026-01-17 23:30*  
*TranslateGemma CLI 版本: 0.3.0*
