[English](README.md) | [简体中文](README_CN.md) | [繁體中文](README_TW.md) | [日本語](README_JP.md)

# TranslateGemma

> 🌍 ローカル AI 翻訳サービス - Web UI、REST API、MCP 統合対応  
> 55言語、スマートチャンキング、ストリーミング出力。Google TranslateGemma 搭載。

[![Docker](https://img.shields.io/badge/Docker-v1.0.0-blue?logo=docker)](https://hub.docker.com/r/neosun/translategemma)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CUDA 12.4](https://img.shields.io/badge/CUDA-12.4-green?logo=nvidia)](https://developer.nvidia.com/cuda-toolkit)

---

## ✨ 主な機能

- 🌐 **Web UI** - 美しいレスポンシブ翻訳インターフェース
- 🔌 **REST API** - ストリーミング対応の完全な API
- 🤖 **MCP 統合** - Claude Desktop などの AI アシスタントと連携
- 🌍 **55言語** - TranslateGemma の全言語サポート
- 📚 **スマートチャンキング** - 無制限の長さのテキストを処理 (chunk_size=100)
- ⚡ **ストリーミング出力** - リアルタイム翻訳進捗
- 🐳 **All-in-One Docker** - 82GB イメージ、全6モデル内蔵
- 🎯 **マルチモデル** - 4B/12B/27B、Q4/Q8 量子化

---

## 🎬 クイックスタート

### 方法1：Docker All-in-One（推奨）

```bash
# all-in-one イメージをプル（82GB、全モデル含む）
docker pull neosun/translategemma:v1.0.0-allinone

# GPU で実行
docker run -d --gpus '"device=0"' \
  -p 8022:8022 \
  -e MODEL_NAME=27b \
  -e QUANTIZATION=8 \
  --name translategemma \
  neosun/translategemma:v1.0.0-allinone

# Web UI にアクセス
open http://localhost:8022
```

### 方法2：Docker でモデルをオンデマンドダウンロード

```bash
# 軽量イメージをプル（10GB）
docker pull neosun/translategemma:latest

# 実行（初回使用時にモデルをダウンロード）
docker run -d --gpus '"device=0"' \
  -p 8022:8022 \
  -v ~/.cache/translate/models:/root/.cache/translate/models \
  --name translategemma \
  neosun/translategemma:latest
```

### 方法3：Docker Compose

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

### 方法4：ローカル実行

**必要環境：**
- Python 3.11+
- NVIDIA GPU + CUDA 12.4+
- 16GB+ VRAM（27B モデル用）

```bash
# リポジトリをクローン
git clone https://github.com/neosun100/translategemma.git
cd translategemma

# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate

# 依存関係をインストール
pip install -e ".[cuda]"

# サーバーを起動
uvicorn app_fastapi:app --host 0.0.0.0 --port 8022

# 確認
curl http://localhost:8022/health
```

---

## 🖥️ Web UI

`http://localhost:8022` で Web インターフェースにアクセス：

**機能：**
- 🎨 ダーク/ライトテーマ切り替え
- 🔄 言語スワップボタン
- 📊 リアルタイム翻訳統計
- ⚙️ 詳細パラメータ制御
- 📁 ファイルアップロード対応
- 🔥 GPU ステータス監視

---

## 🔌 REST API

### テキスト翻訳

```bash
# シンプルな翻訳
curl -X POST http://localhost:8022/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "target_lang": "ja"}'

# レスポンス
{
  "translation": "こんにちは、世界",
  "source_lang": "en",
  "target_lang": "ja",
  "model": "27b-Q8",
  "time_ms": 1234
}
```

### ストリーミング翻訳

```bash
curl -X POST http://localhost:8022/translate/stream \
  -H "Content-Type: application/json" \
  -d '{"text": "長いテキスト...", "target_lang": "ja"}'
```

### API エンドポイント

| エンドポイント | メソッド | 説明 |
|----------------|----------|------|
| `/translate` | POST | テキスト翻訳 |
| `/translate/stream` | POST | ストリーミング翻訳 |
| `/config` | GET | 現在の設定を取得 |
| `/models` | GET | 利用可能なモデル一覧 |
| `/languages` | GET | サポート言語一覧 |
| `/gpu/status` | GET | GPU メモリ状態 |
| `/health` | GET | ヘルスチェック |

---

## ⚙️ 設定

### 環境変数

| 変数 | デフォルト | 説明 |
|------|------------|------|
| `MODEL_NAME` | `27b` | モデルサイズ：4b, 12b, 27b |
| `QUANTIZATION` | `8` | 量子化：4 または 8 |
| `BACKEND` | `gguf` | バックエンド：gguf, pytorch |
| `GPU_IDLE_TIMEOUT` | `0` | 自動アンロードタイムアウト（0=即時） |
| `MAX_CHUNK_LENGTH` | `100` | 安全なチャンクサイズ |
| `DEFAULT_OVERLAP` | `0` | スライディングウィンドウオーバーラップ（0=無効） |
| `NVIDIA_VISIBLE_DEVICES` | `0` | GPU デバイス ID |

### モデル選択ガイド

| モデル | VRAM | 品質 | 速度 | 用途 |
|--------|------|------|------|------|
| 4B-Q4 | ~3GB | 良好 | 高速 | クイック翻訳 |
| 4B-Q8 | ~5GB | より良い | 高速 | 日常使用 |
| 12B-Q4 | ~7GB | 高 | 中速 | バランス |
| 12B-Q8 | ~12GB | より高い | 中速 | 推奨 |
| 27B-Q4 | ~15GB | 最高 | 低速 | 高品質翻訳 |
| **27B-Q8** | ~28GB | **最高+** | 低速 | **プロ翻訳** ⭐ |

---

## 🌍 サポート言語（55言語）

| コード | 言語 | コード | 言語 | コード | 言語 |
|--------|------|--------|------|--------|------|
| `en` | 英語 | `zh` | 簡体字中国語 | `zh-TW` | 繁体字中国語 |
| `ja` | 日本語 | `ko` | 韓国語 | `yue` | 広東語 |
| `fr` | フランス語 | `de` | ドイツ語 | `es` | スペイン語 |
| `pt` | ポルトガル語 | `ru` | ロシア語 | `ar` | アラビア語 |
| `hi` | ヒンディー語 | `th` | タイ語 | `vi` | ベトナム語 |

...他40言語以上。完全なリストは `/languages` エンドポイントを参照。

---

## 🐳 Docker イメージ

| イメージ | サイズ | 説明 |
|----------|--------|------|
| `neosun/translategemma:v1.0.0-allinone` | 82GB | 全6モデル内蔵 |
| `neosun/translategemma:latest-allinone` | 82GB | 最新 all-in-one |
| `neosun/translategemma:v1.0.0` | 10GB | 軽量版、オンデマンドダウンロード |
| `neosun/translategemma:latest` | 10GB | 最新軽量版 |

---

## 📊 技術詳細

### スマートチャンキング

TranslateGemma は長いテキストを切り捨てます。スマートチャンキングで完全な翻訳を保証：

```
chunk_size=100  →  100% 翻訳完全性
chunk_size=120  →  44% 完全性（切り捨て）
chunk_size=150  →  44% 完全性（切り捨て）
```

**重要な発見**：`chunk_size=100` が完全な翻訳を保証する安全な境界。

### コンテキスト一貫性

TranslateGemma はチャンク間の一貫性を自動的に維持：
- ✅ 代名詞（彼/彼女/彼ら）
- ✅ 用語（NLP、AI）
- ✅ 固有名詞（Google、Microsoft）
- ✅ 性別の一貫性

コンテキスト保持にオーバーラップは不要。

---

## 🤖 MCP 統合

Claude Desktop や他の MCP 互換 AI アシスタントと使用：

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

## 📁 プロジェクト構造

```
translategemma/
├── app_fastapi.py          # FastAPI サーバー
├── mcp_server.py           # MCP サーバー
├── templates/
│   └── index.html          # Web UI
├── static/
│   ├── app.js              # フロントエンド JS
│   └── style.css           # スタイル
├── translategemma_cli/     # コアライブラリ
│   ├── translator.py       # 翻訳ロジック
│   ├── chunker.py          # テキストチャンキング
│   ├── model.py            # モデル読み込み
│   └── config.py           # 設定
├── Dockerfile              # 標準イメージ
├── Dockerfile.allinone     # All-in-one イメージ
├── docker-compose.yml      # Compose 設定
└── tests/                  # テストスイート
```

---

## 🔬 研究結果

広範なテストで判明：

| パラメータ | 最適値 | 理由 |
|------------|--------|------|
| chunk_size | 100 | 100% 翻訳完全性 |
| overlap | 0 | TranslateGemma が自動でコンテキスト維持 |
| quantization | Q8 | 最適な品質/速度バランス |

詳細は [CHUNKING_RESEARCH_REPORT.md](docs/CHUNKING_RESEARCH_REPORT.md) を参照。

---

## 🤝 コントリビューション

コントリビューション歓迎！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照。

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. Pull Request を作成

---

## 📄 ライセンス

MIT License - [LICENSE](LICENSE) ファイルを参照。

**注意**：TranslateGemma モデルは [Google モデルライセンス](https://ai.google.dev/gemma/terms) に従います。

---

## 🙏 謝辞

- [Google TranslateGemma](https://huggingface.co/collections/google/translategemma) - ベース翻訳モデル
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python) - GGUF 推論
- [FastAPI](https://fastapi.tiangolo.com/) - Web フレームワーク

---

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=neosun100/translategemma&type=Date)](https://star-history.com/#neosun100/translategemma)

## 📱 公式アカウント

![公式アカウント](https://img.aws.xin/uPic/扫码_搜索联合传播样式-标准色版.png)
