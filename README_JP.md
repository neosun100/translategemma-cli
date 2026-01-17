[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# TranslateGemma CLI

> 🚀 GoogleのTranslateGemmaを活用したプロダクション対応のローカル翻訳  
> スマートチャンキング、ストリーミング出力、バッチ処理で55言語をサポート

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Model: TranslateGemma](https://img.shields.io/badge/Model-TranslateGemma-green.svg)](https://huggingface.co/collections/google/translategemma)

---

## ✨ ハイライト

- **🌍 55言語** - TranslateGemmaの完全な言語サポート
- **📚 無制限の長さ** - あらゆる長さのテキストに対応するスライディングウィンドウ付きスマートチャンキング
- **⚡ ストリーミング出力** - リアルタイム翻訳進捗
- **📦 バッチ処理** - ディレクトリ全体を一度に翻訳
- **🎯 複数のバックエンド** - ローカル（MLX/PyTorch）、vLLM、またはOllama
- **💻 マルチプラットフォーム** - macOS（Apple Silicon）、Linux、Windows
- **🔧 高度な設定可能性** - 様々な用途に対応する柔軟なパラメータ

---

## 🎬 クイックスタート

### インストール

```bash
# uv使用（推奨）
uv venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[mlx]"  # macOS Apple Silicon
# または
uv pip install -e ".[cuda]"  # Linux/Windows with NVIDIA GPU

# pip使用
pip install -e ".[mlx]"  # macOS Apple Silicon
pip install -e ".[cuda]"  # Linux/Windows with NVIDIA GPU
pip install -e ".[cpu]"  # CPU専用
```

### 初回実行

```bash
# 設定を初期化
translate init

# モデルをダウンロード（初回のみ）
translate model download 27b

# 翻訳開始！
translate --text "Hello world"
# 出力: 你好，世界。
```

---

## 🚀 機能

### 1. スマート長文翻訳

**問題**: TranslateGemmaは長いテキスト（>500文字）を切り詰める

**解決策**: スライディングウィンドウ付きスマートチャンキング

```bash
# 長文の自動チャンキング
translate --file long_article.txt

# カスタムチャンクパラメータ
translate --file book.txt --chunk-size 80 --overlap 10

# 短文のチャンキング無効化
translate --file short.txt --no-chunk
```

**動作原理**:
```
元のテキスト: [AAAAA][BBBBB][CCCCC][DDDDD]

スライディングウィンドウ:
チャンク1: [AAAAA]
チャンク2:    [AA|BBBBB]    ← オーバーラップがコンテキストを提供
チャンク3:         [BB|CCCCC]
チャンク4:              [CC|DDDDD]

結果: コンテキストを保持した完全な翻訳
```

### 2. ストリーミング出力

より良いUXのためのリアルタイム翻訳進捗:

```bash
# トークンごとの出力ストリーミング
translate --file article.txt --stream

# チャンキングと組み合わせ
translate --file book.txt --chunk-size 80 --stream
```

### 3. バッチ翻訳

ディレクトリ全体を効率的に翻訳:

```bash
# すべての.txtと.mdファイルを翻訳
translate --dir ./documents

# ./documents/translated/に出力
```

### 4. インタラクティブREPL

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

### 基本的な翻訳

```bash
# 単一テキスト
translate --text "Hello world"

# ファイルから
translate --file input.txt --output output.txt

# 標準入力から
echo "Bonjour" | translate

# ターゲット言語を強制指定
translate --text "Hello" --to ja
```

### 長文翻訳

```bash
# 自動チャンキング（テキスト > 300文字）
translate --file article.txt

# カスタムチャンキング
translate --file book.txt --chunk-size 80 --overlap 10

# リアルタイムフィードバック用ストリーミング
translate --file long.txt --stream

# チャンキング無効化
translate --file short.txt --no-chunk
```

### バッチ処理

```bash
# ディレクトリを翻訳
translate --dir ./documents

# カスタムパラメータ付き
translate --dir ./docs --chunk-size 100
```

### モデル管理

```bash
# モデル一覧
translate model list

# モデルダウンロード
translate model download 4b

# ステータス確認
translate model status

# サポート言語一覧
translate model langs
```

---

## ⚙️ 設定

設定ファイル: `~/.config/translate/config.yaml`

### デフォルト設定（最適化済み）

```yaml
model:
  name: 27b              # モデルサイズ: 4b, 12b, 27b
  quantization: 4        # 4ビットまたは8ビット

backend:
  type: auto             # auto, mlx, pytorch, vllm, ollama
  vllm_url: http://localhost:8000
  ollama_url: http://localhost:11434

translation:
  languages: [yue, en]   # 言語ペア
  mode: direct           # direct または explain
  max_tokens: 512        # ベースmax_tokens（チャンク用に自動調整）
  
  chunking:
    enabled: true        # スマートチャンキングを有効化
    chunk_size: 80       # 完全性に最適
    overlap: 10          # 最小限の重複
    split_by: sentence   # sentence, paragraph, または char
    auto_threshold: 300  # テキスト > 300文字で自動有効化

ui:
  show_detected_language: true
  colored_output: true
  show_progress: true
```

### カスタマイズ

```bash
# デフォルトで初期化
translate init

# 強制上書き
translate init --force

# 手動編集
vim ~/.config/translate/config.yaml
```

---

## 🎯 ベストプラクティス

### チャンクサイズの選択

| テキストタイプ | chunk_size | overlap | 理由 |
|-----------|------------|---------|--------|
| 日常会話 | 60-80 | 10-15 | 短い文 |
| 技術文書 | 80-100 | 15-20 | 用語の一貫性 |
| 文学作品 | 80-100 | 20-30 | コンテキストの保持 |
| 長い記事 | 80-100 | 10-20 | 品質と速度のバランス |

### チャンキングを使用するタイミング

| テキスト長 | 推奨事項 |
|-------------|----------------|
| < 300文字 | 速度のため`--no-chunk`を使用 |
| 300-1000文字 | 自動チャンキング（デフォルト） |
| 1000-5000文字 | `--chunk-size 80 --overlap 10` |
| 5000+文字（書籍） | `--chunk-size 80 --stream` |

### パフォーマンスのヒント

1. **インタラクティブモード** - モデルを一度読み込み、複数翻訳で高速化
2. **バッチ処理** - ファイルを一つずつではなく`--dir`を使用
3. **ストリーミング** - 長文では`--stream`で進捗確認
4. **最適チャンク** - chunk_size=80, overlap=10が最適解

---

## 📊 パフォーマンス

**テスト環境**: MacBook Pro M2 Max、96GB、MLXバックエンド

| テキスト長 | チャンク数 | 時間 | スループット |
|-------------|--------|------|------------|
| 100文字 | 1 | 1.2秒 | 83文字/秒 |
| 400文字 | 4 | 8.5秒 | 48文字/秒 |
| 1000文字 | 12 | ~22秒 | ~45文字/秒 |
| 5000文字 | 60 | ~110秒 | ~45文字/秒 |

**メモリ使用量**: 14.15 GB（すべてのテキスト長で安定）

---

## 🛠️ 要件

### macOS（Apple Silicon）
- M1/M2/M3/M4 Mac
- 8GB+統合メモリ（4b）、16GB+（12b）、32GB+（27b）
- macOS 14.0+

### Linux / Windows
- 8GB+ VRAMのNVIDIA GPU（またはCPUで16GB+ RAM）
- CUDA 11.8+（GPU用）

### 全プラットフォーム
- Python 3.11+

---

## 📦 インストールオプション

### オプション1: uv（最速、推奨）

```bash
# uvがインストールされていない場合
curl -LsSf https://astral.sh/uv/install.sh | sh

# クローンとインストール
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
uv venv .venv
source .venv/bin/activate

# macOS Apple Silicon
uv pip install -e ".[mlx]"

# Linux/Windows with NVIDIA GPU
uv pip install -e ".[cuda]"

# CPU専用
uv pip install -e ".[cpu]"
```

### オプション2: pipx（分離インストール）

```bash
# ローカルディレクトリからインストール
pipx install /path/to/translategemma-cli[mlx]

# またはgitから（公開時）
pipx install git+https://github.com/jhkchan/translategemma-cli.git[mlx]
```

### オプション3: pip（従来型）

```bash
git clone https://github.com/jhkchan/translategemma-cli.git
cd translategemma-cli
python3 -m venv venv
source venv/bin/activate
pip install -e ".[mlx]"  # または [cuda] または [cpu]
```

---

## 🌍 サポート言語（55言語）

| コード | 言語 | コード | 言語 |
|------|----------|------|----------|
| `en` | 英語 | `yue` | 広東語 |
| `zh` | 中国語（簡体字） | `zh-TW` | 中国語（繁体字） |
| `ja` | 日本語 | `ko` | 韓国語 |
| `fr` | フランス語 | `de` | ドイツ語 |
| `es` | スペイン語 | `pt` | ポルトガル語 |
| `ru` | ロシア語 | `ar` | アラビア語 |

...他45言語。完全なリストは`translate model langs`で確認。

---

## 🎓 高度な使用方法

### カスタム言語ペア

`~/.config/translate/config.yaml`を編集:

```yaml
translation:
  languages: [ja, en]  # 日本語 ↔ 英語
  # または
  languages: [zh, fr]  # 中国語 ↔ フランス語
```

### バックエンドオプション

```bash
# ローカル（デフォルト）
translate --backend mlx  # macOS
translate --backend pytorch  # Linux/Windows

# vLLM（高スループット）
vllm serve google/translategemma-27b-it --quantization awq
translate --backend vllm --server http://localhost:8000

# Ollama（簡単セットアップ）
ollama pull translategemma:27b
translate --backend ollama
```

### インタラクティブコマンド

| コマンド | 機能 |
|---------|----------|
| `/to <lang>` | ターゲット言語を強制指定 |
| `/auto` | 自動検出を有効化 |
| `/mode direct` | 直接翻訳 |
| `/mode explain` | 説明付き |
| `/model <size>` | モデル切り替え |
| `/backend <type>` | バックエンド切り替え |
| `/langs` | 言語一覧 |
| `/config` | 設定表示 |
| `/quit` | 終了 |

---

## 🔬 技術詳細

### スマートチャンキングアルゴリズム

```python
# スライディングウィンドウ付き文ベース分割
TextChunker(
    chunk_size=80,      # ターゲットチャンクサイズ
    overlap=10,         # コンテキスト用オーバーラップ
    split_by="sentence" # 文境界で分割
)

# プロセス:
1. 文境界でテキストを分割
2. 文を約80文字のチャンクにグループ化
3. 前のチャンクからオーバーラップを追加
4. コンテキスト付きで各チャンクを翻訳
5. 結果をマージ（オーバーラップをスキップ）
```

### 適応的max_tokens

```python
# 入力長に基づいて動的調整
adaptive_max_tokens = min(
    2048,                      # 上限
    max(512, len(chunk) * 3)   # 3倍入力（安全バッファ）
)

# なぜ3倍？
# - 中国語 → 英語は通常1.5-2倍に拡張
# - 3倍は安全バッファを提供
# - 切り詰めを防止
```

### マージ戦略

```python
# シンプルな連結（オーバーラップはコンテキストのみ提供）
def merge(chunks, translations):
    result = [translations[0]]  # 最初を完全に保持
    for trans in translations[1:]:
        result.append(" " + trans)  # チャンク間にスペース追加
    return "".join(result)

# 注意: 最小オーバーラップ（10）で重複を削減
```

---

## 📚 ドキュメント

| ドキュメント | 説明 |
|----------|-------------|
| [README.md](README.md) | メインドキュメント（このファイル） |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | クイックリファレンスカード |
| [BEST_PRACTICES.md](BEST_PRACTICES.md) | 使用ベストプラクティス |
| [LONG_TEXT_FEATURE_REPORT.md](LONG_TEXT_FEATURE_REPORT.md) | 機能詳細レポート |
| [FINAL_TEST_REPORT.md](FINAL_TEST_REPORT.md) | 包括的テストレポート |
| [DEVELOPMENT_SUMMARY.md](DEVELOPMENT_SUMMARY.md) | 開発サマリー |
| [TRANSLATION_TEST_REPORT.md](TRANSLATION_TEST_REPORT.md) | 多言語品質評価 |

---

## 🎯 使用例

### 使用例1: 書籍の翻訳

```bash
# 進捗フィードバック付きストリーミング
translate --file novel.txt --chunk-size 80 --overlap 10 --stream --output novel_en.txt
```

### 使用例2: ドキュメントのバッチ翻訳

```bash
# ディレクトリ内のすべてのドキュメントを翻訳
translate --dir ./docs

# ./docs/translated/に出力
```

### 使用例3: クイック翻訳

```bash
# 短文、チャンキングなし
translate --text "Hello world" --no-chunk

# またはインタラクティブモードを使用
translate
> Hello world
[en→yue] 你好，世界。
```

### 使用例4: 多言語ワークフロー

```bash
# 英語から複数言語へ
translate --text "Welcome" --to ja  # 日本語
translate --text "Welcome" --to ko  # 韓国語
translate --text "Welcome" --to zh  # 中国語
translate --text "Welcome" --to fr  # フランス語
```

---

## 🔧 開発インサイト

### 主要な学び

1. **TranslateGemmaモデルの特性**:
   - 長いテキスト（>500文字）を切り詰める
   - 段落区切り（空行）で停止
   - 完全性のため小さなチャンク（80-100文字）が必要

2. **最適チャンキング戦略**:
   - chunk_size=80: 最高の完全性（98%）
   - overlap=10: 最小限の重複（<5%）
   - split_by=sentence: 自然な境界

3. **適応的max_tokens**:
   - 固定512トークンは長いチャンクに不十分
   - 入力長の3倍で完全性を保証
   - 2048でキャップして過剰生成を防止

4. **マージ戦略**:
   - シンプルな連結が最適
   - オーバーラップはコンテキスト提供、重複除去用ではない
   - スマート重複除去は複雑（将来の作業）

### アーキテクチャ

```
ユーザー入力
    ↓
TextChunker (chunker.py)
    ↓
[チャンク1] [チャンク2] [チャンク3] ...
    ↓         ↓         ↓
Translator.translate_long()
    ↓
適応的max_tokens（3倍入力）
    ↓
MLX/PyTorch/vLLM/Ollamaバックエンド
    ↓
結果をマージ
    ↓
出力（完全な翻訳）
```

---

## 🧪 テスト

### テスト実行

```bash
# 開発依存関係をインストール
pip install -e ".[dev]"

# すべてのテストを実行
pytest

# カバレッジ付きで実行
pytest --cov=translategemma_cli

# 特定のテストを実行
pytest tests/test_chunker.py
```

### 手動テスト

```bash
# 包括的テストスイート
./tests/comprehensive_test.sh

# または個別機能をテスト
translate --file test.txt --chunk-size 80
translate --dir ./test_docs
translate --text "Test" --stream
```

---

## 📊 ベンチマーク

### 翻訳完全性

| 方法 | 完全性 | 速度 | 推奨 |
|--------|--------------|-------|----------------|
| チャンキングなし | 13% | 高速 | ❌ 長文で失敗 |
| chunk=150 | 70% | 中程度 | ⚠️ 非推奨 |
| chunk=100 | 95% | 中程度 | ✅ 良好 |
| chunk=80 | 98% | 中程度 | ✅ **最適** |
| chunk=60 | 100% | 低速 | ⚠️ 過剰チャンキング |

### オーバーラップの影響

| オーバーラップ | 重複 | 品質 | 推奨 |
|---------|------------|---------|----------------|
| 0 | 0% | 中程度 | ⚠️ コンテキストなし |
| 10 | <5% | 高 | ✅ **最適** |
| 20 | 5-10% | 高 | ✅ 良好 |
| 30 | 10-15% | 中程度 | ⚠️ 過多 |
| 50 | 20-30% | 低 | ❌ 非推奨 |

---

## 🎨 モデル選択

| モデル | パラメータ | ディスクサイズ | メモリ | 用途 |
|-------|------------|-----------|--------|----------|
| **4b** | 5B | ~3.2 GB | 8GB+ | 高速翻訳、限られたリソース |
| **12b** | 13B | ~7.0 GB | 16GB+ | パフォーマンスと品質のバランス |
| **27b** | 29B | ~14.8 GB | 32GB+ | **最高品質**（推奨） |

---

## 🌟 v0.2.0の新機能

### 主要機能

- ✅ **スマートテキストチャンキング** - 無制限のテキスト長に対応
- ✅ **スライディングウィンドウ** - オーバーラップでコンテキストを保持
- ✅ **ストリーミング出力** - リアルタイム翻訳進捗
- ✅ **バッチ翻訳** - ディレクトリ全体を処理
- ✅ **適応的max_tokens** - 切り詰めを防止
- ✅ **進捗表示** - richによる視覚的フィードバック

### 新しいCLIパラメータ

```bash
--chunk-size <int>    # チャンクサイズ（デフォルト: 80）
--overlap <int>       # オーバーラップサイズ（デフォルト: 10）
--no-chunk            # チャンキング無効化
--stream              # ストリーミング有効化
--dir <path>          # ディレクトリのバッチ翻訳
```

### パフォーマンス改善

- **翻訳完全性**: 13% → 98%（長文用）
- **スループット**: 安定した45-50文字/秒
- **メモリ**: 変更なし（14.15 GB）

---

## 🐛 既知の制限

### 1. モデルの動作

- **段落区切り**: モデルは空行で停止
  - **解決策**: 小さなチャンク（80文字）を使用
- **長いチャンク**: チャンク > 150文字で切り詰め
  - **解決策**: 適応的max_tokens（3倍入力）

### 2. オーバーラップの重複

- **問題**: overlap > 10で軽微な重複が発生
- **理由**: オーバーラップ領域が2回翻訳される
- **推奨**: overlap=10-20を使用

### 3. 未実装機能

- スマート重複除去（v0.3.0で予定）
- 翻訳キャッシュ（v0.3.0で予定）
- 再開機能（v0.4.0で予定）
- 用語サポート（評価中）

---

## 🤝 貢献

貢献を歓迎します！以下の手順でお願いします：

1. リポジトリをフォーク
2. 機能ブランチを作成（`git checkout -b feature/AmazingFeature`）
3. 変更をコミット（`git commit -m 'Add AmazingFeature'`）
4. ブランチにプッシュ（`git push origin feature/AmazingFeature`）
5. プルリクエストを開く

---

## 📄 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています - [LICENSE](LICENSE)ファイルを参照してください。

**注意**: TranslateGemmaモデルはGoogleのモデルライセンス条項の対象です。[モデルライセンス](https://ai.google.dev/gemma/terms)を確認し、遵守してください。

---

## 🙏 謝辞

- [Google TranslateGemma](https://huggingface.co/collections/google/translategemma) - ベース翻訳モデル
- [MLX](https://github.com/ml-explore/mlx) - Apple Silicon最適化
- [Cursor](https://cursor.com/) + [Claude](https://www.anthropic.com/claude) - 開発ツール
- [hy-mt](https://github.com/neosun100/hy-mt) - チャンキング戦略のインスピレーション

---

## 🔗 リンク

- **GitHub**: https://github.com/jhkchan/translategemma-cli
- **HuggingFace**: https://huggingface.co/collections/google/translategemma
- **Issues**: https://github.com/jhkchan/translategemma-cli/issues
- **ドキュメント**: [docs](docs/)ディレクトリを参照

---

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/jhkchan/translategemma-cli/issues)
- **ディスカッション**: [GitHub Discussions](https://github.com/jhkchan/translategemma-cli/discussions)
- **メール**: [Your Email]

---

## 🗺️ ロードマップ

### v0.3.0（次期）
- [ ] スマート重複除去アルゴリズム
- [ ] 翻訳キャッシュシステム
- [ ] 改善された言語検出
- [ ] 用語サポート

### v0.4.0（将来）
- [ ] 再開機能
- [ ] 並列翻訳（マルチGPU）
- [ ] Web UI
- [ ] REST APIサーバー

---

**バージョン**: 0.2.0  
**最終更新**: 2026-01-17  
**ステータス**: プロダクション対応 ✅