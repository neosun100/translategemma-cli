# Integration Tests for TranslateGemma Chunking & Sliding Window

This directory contains integration tests for validating the chunking and sliding window features.

## Test Scripts

| Script | Purpose |
|--------|---------|
| `test_sliding_window.py` | Basic sliding window functionality test |
| `test_critical.py` | Critical truncation issue validation |
| `test_quality.py` | Translation quality comparison |
| `test_context_consistency.py` | Context consistency across chunks |
| `test_cross_chunk.py` | Cross-chunk terminology consistency |

## Running Tests

```bash
# Ensure the API is running
docker compose up -d

# Run individual tests
python tests/integration/test_critical.py
python tests/integration/test_cross_chunk.py

# Run all tests
for f in tests/integration/test_*.py; do python "$f"; done
```

## Test Results

See [docs/CHUNKING_RESEARCH_REPORT.md](../../docs/CHUNKING_RESEARCH_REPORT.md) for detailed test results and analysis.

## Key Findings

1. **chunk_size=100 is the safe boundary** - ensures 100% translation completeness
2. **Sliding window (overlap) causes repetition** - overlap content gets translated twice
3. **Model maintains consistency without overlap** - TranslateGemma handles pronouns and terminology well
