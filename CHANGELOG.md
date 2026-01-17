# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-18

### Added
- 🌐 **Web UI** - Beautiful, responsive translation interface with dark/light theme
- 🔌 **REST API** - Full-featured API with streaming support
- 🤖 **MCP Integration** - Works with Claude Desktop & AI assistants
- 🌍 **55 Languages** - Full TranslateGemma language support
- 📚 **Smart Chunking** - Handle unlimited text length with chunk_size=100
- ⚡ **Streaming Output** - Real-time translation progress
- 🐳 **Docker Images** - Both lightweight (10GB) and all-in-one (82GB) versions
- 🎯 **Multi-Model Support** - 4B/12B/27B with Q4/Q8 quantization
- 📊 **GPU Status Monitoring** - Real-time VRAM usage display
- 📁 **File Upload** - Support for text file translation

### Technical
- FastAPI backend with async support
- GGUF backend via llama-cpp-python for optimal performance
- Automatic context consistency across chunks
- Configurable via environment variables

### Research Findings
- `chunk_size=100` is the safe boundary for 100% translation completeness
- `overlap=0` recommended - TranslateGemma maintains context automatically
- Q8 quantization provides best quality/speed balance

## [0.2.1] - 2026-01-17

### Added
- Initial CLI version
- Basic translation functionality
- PyPI package release

---

[1.0.0]: https://github.com/neosun100/translategemma/releases/tag/v1.0.0
[0.2.1]: https://github.com/neosun100/translategemma-cli/releases/tag/v0.2.1
