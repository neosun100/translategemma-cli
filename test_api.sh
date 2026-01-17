#!/bin/bash
# TranslateGemma API Test Script

API_BASE="${API_BASE:-http://localhost:8022}"

echo "=========================================="
echo "TranslateGemma API Test"
echo "API: $API_BASE"
echo "=========================================="

# Health check
echo -e "\n[1] Health Check"
curl -s "$API_BASE/health" | python3 -m json.tool

# Languages
echo -e "\n[2] Languages (first 5)"
curl -s "$API_BASE/api/languages" | python3 -c "import sys,json; d=json.load(sys.stdin); print(dict(list(d.items())[:5]))"

# Models
echo -e "\n[3] Available Models"
curl -s "$API_BASE/api/models" | python3 -m json.tool

# Translation: English to Chinese
echo -e "\n[4] Translate: English → Chinese"
curl -s -X POST "$API_BASE/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you today?", "target_lang": "zh"}' | python3 -m json.tool

# Translation: Chinese to English
echo -e "\n[5] Translate: Chinese → English"
curl -s -X POST "$API_BASE/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "今天天气真好", "target_lang": "en"}' | python3 -m json.tool

# Translation: English to Japanese
echo -e "\n[6] Translate: English → Japanese"
curl -s -X POST "$API_BASE/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Good morning", "target_lang": "ja"}' | python3 -m json.tool

# Batch translation
echo -e "\n[7] Batch Translation"
curl -s -X POST "$API_BASE/api/translate/batch" \
  -H "Content-Type: application/json" \
  -d '{"texts": ["Hello", "World", "Thank you"], "target_lang": "zh"}' | python3 -m json.tool

# GPU status
echo -e "\n[8] GPU Status"
curl -s "$API_BASE/api/gpu/status" | python3 -m json.tool

echo -e "\n=========================================="
echo "Test Complete!"
echo "=========================================="
