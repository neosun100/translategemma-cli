# TranslateGemma CLI - 项目总览

## 🎯 项目简介

TranslateGemma CLI 是一个生产级的本地翻译命令行工具，基于 Google 的 TranslateGemma 模型，支持 55 种语言的高质量翻译。

**核心特性**: 智能分块 + 滑动窗口 + 流式输出 + 批量处理

---

## 📦 快速开始

```bash
# 安装
pip install translategemma-cli[mlx]  # macOS
pip install translategemma-cli[cuda] # Linux/Windows GPU

# 初始化
translate init
translate model download 27b

# 使用
translate --text "Hello world"
translate --file article.txt --stream
translate --dir ./documents
```

---

## 📚 文档导航

| 文档 | 用途 | 适合人群 |
|------|------|----------|
| [README.md](README.md) | 完整功能说明 | 所有用户 |
| [INSTALLATION.md](INSTALLATION.md) | 安装指南 | 新用户 |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 快速参考 | 日常使用 |
| [BEST_PRACTICES.md](BEST_PRACTICES.md) | 最佳实践 | 进阶用户 |
| [LONG_TEXT_FEATURE_REPORT.md](LONG_TEXT_FEATURE_REPORT.md) | 长文本功能详解 | 开发者 |
| [TRANSLATION_TEST_REPORT.md](TRANSLATION_TEST_REPORT.md) | 多语言质量评估 | 质量关注者 |
| [FINAL_TEST_REPORT.md](FINAL_TEST_REPORT.md) | 综合测试报告 | 开发者 |
| [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) | 开发总结 | 开发者 |
| [COMPLETION_REPORT.md](COMPLETION_REPORT.md) | 项目完成报告 | 项目管理 |

---

## 🚀 核心功能

### 1. 智能分块翻译

```bash
translate --file long_article.txt
# 自动分块，完整翻译
```

### 2. 滑动窗口

```
[块1] → 翻译1
  [重叠 + 块2] → 翻译2
    [重叠 + 块3] → 翻译3
```

### 3. 流式输出

```bash
translate --file book.txt --stream
# 实时看到翻译进度
```

### 4. 批量处理

```bash
translate --dir ./documents
# 一次翻译整个目录
```

---

## 📊 性能数据

| 文本长度 | 耗时 | 吞吐量 |
|----------|------|--------|
| 100字符 | 1.2秒 | 83字符/秒 |
| 400字符 | 8.5秒 | 48字符/秒 |
| 1000字符 | 22秒 | 45字符/秒 |

**内存**: 14.15 GB (稳定)

---

## 🎯 最佳配置

```yaml
# 已设为默认
chunk_size: 80      # 98% 完整度
overlap: 10         # < 5% 重复
auto_threshold: 300 # 智能触发
```

---

## 🔗 链接

- **PyPI**: https://pypi.org/project/translategemma-cli/
- **GitHub**: https://github.com/jhkchan/translategemma-cli
- **HuggingFace**: https://huggingface.co/collections/google/translategemma

---

## 📞 支持

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: [Your Email]

---

**版本**: v0.2.0  
**状态**: Production Ready ✅  
**发布日期**: 2026-01-17
