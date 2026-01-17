#!/usr/bin/env python3
"""
Comprehensive test for sliding window feature.
Tests translation quality with and without overlap.
"""
import requests
import json
import time

API_URL = "http://localhost:8022/api/translate"

# Test cases - various text types that previously had issues
TEST_CASES = [
    {
        "name": "技术文章 (之前出问题的类型)",
        "text": """人工智能的概念可以追溯到古希腊神话中的自动机器人，这些神话描绘了由工匠赫菲斯托斯创造的金属生物。然而，作为一门正式学科，人工智能诞生于1956年的达特茅斯会议。在这次会议上，约翰·麦卡锡首次提出了"人工智能"这一术语。早期的人工智能研究主要集中在符号推理和问题求解上。研究人员相信，通过编写足够复杂的规则，机器可以模拟人类的思维过程。""",
        "keywords": ["人工智能", "古希腊", "赫菲斯托斯", "达特茅斯", "麦卡锡", "符号推理"],
    },
    {
        "name": "长段落连续文本",
        "text": """机器学习是人工智能的一个重要分支，它使计算机能够从数据中学习，而无需明确编程。深度学习是机器学习的一个子集，使用多层神经网络来处理复杂的模式识别任务。近年来，大型语言模型如GPT和BERT的出现，彻底改变了自然语言处理领域。这些模型通过在海量文本数据上进行预训练，学会了理解和生成人类语言。Transformer架构的引入是这一突破的关键，它允许模型并行处理序列数据，大大提高了训练效率。""",
        "keywords": ["机器学习", "深度学习", "神经网络", "GPT", "BERT", "Transformer"],
    },
    {
        "name": "多句子复杂段落",
        "text": """量子计算是一种利用量子力学原理进行计算的新型计算范式。与传统计算机使用比特不同，量子计算机使用量子比特或称为"qubit"。量子比特可以同时处于0和1的叠加态，这使得量子计算机在某些特定问题上具有指数级的计算优势。目前，谷歌、IBM和微软等科技巨头都在积极研发量子计算机。2019年，谷歌宣布实现了"量子霸权"，其量子处理器在200秒内完成了传统超级计算机需要10000年才能完成的计算任务。""",
        "keywords": ["量子计算", "量子力学", "qubit", "叠加态", "谷歌", "量子霸权"],
    },
]

def test_translation(text: str, target_lang: str, chunk_size: int, overlap: int) -> dict:
    """Run a single translation test."""
    payload = {
        "text": text,
        "target_lang": target_lang,
        "chunk_size": chunk_size,
        "overlap": overlap,
    }
    
    start = time.time()
    resp = requests.post(API_URL, json=payload)
    elapsed = time.time() - start
    
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}"}
    
    data = resp.json()
    if data.get("status") != "success":
        return {"error": data.get("error", "Unknown error")}
    
    return {
        "result": data.get("result", ""),
        "chunks": data.get("chunks", 0),
        "elapsed_ms": data.get("elapsed_ms", 0),
        "overlap_used": data.get("overlap_used", 0),
        "input_length": len(text),
        "output_length": len(data.get("result", "")),
    }

def check_keywords(result: str, keywords: list) -> dict:
    """Check how many keywords are preserved in translation context."""
    # For Chinese->English, we check if the translation covers the concepts
    # This is a simplified check - in reality we'd need semantic matching
    found = 0
    missing = []
    
    # Simple heuristic: check if result length is proportional to input
    # A complete translation should have reasonable length
    return {
        "output_length": len(result),
        "has_content": len(result) > 50,
    }

def run_comparison_test(test_case: dict, chunk_size: int = 100):
    """Run comparison test with and without overlap."""
    print(f"\n{'='*60}")
    print(f"测试: {test_case['name']}")
    print(f"输入长度: {len(test_case['text'])} 字符")
    print(f"chunk_size: {chunk_size}")
    print(f"{'='*60}")
    
    results = {}
    
    # Test configurations
    configs = [
        {"overlap": 0, "name": "无滑动窗口 (overlap=0)"},
        {"overlap": 20, "name": "滑动窗口 (overlap=20)"},
        {"overlap": 30, "name": "滑动窗口 (overlap=30)"},
    ]
    
    for config in configs:
        print(f"\n--- {config['name']} ---")
        result = test_translation(
            text=test_case["text"],
            target_lang="en",
            chunk_size=chunk_size,
            overlap=config["overlap"],
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
            results[config["name"]] = {"error": result["error"]}
            continue
        
        print(f"分段数: {result['chunks']}")
        print(f"耗时: {result['elapsed_ms']}ms")
        print(f"输出长度: {result['output_length']} 字符")
        print(f"翻译结果预览: {result['result'][:200]}...")
        
        results[config["name"]] = result
    
    return results

def run_chunk_size_comparison(test_case: dict):
    """Compare different chunk sizes with overlap."""
    print(f"\n{'='*60}")
    print(f"Chunk Size 对比测试: {test_case['name']}")
    print(f"{'='*60}")
    
    configs = [
        {"chunk_size": 80, "overlap": 0},
        {"chunk_size": 80, "overlap": 20},
        {"chunk_size": 100, "overlap": 0},
        {"chunk_size": 100, "overlap": 20},
        {"chunk_size": 120, "overlap": 0},
        {"chunk_size": 120, "overlap": 30},
    ]
    
    results = []
    
    for config in configs:
        print(f"\n--- chunk={config['chunk_size']}, overlap={config['overlap']} ---")
        result = test_translation(
            text=test_case["text"],
            target_lang="en",
            chunk_size=config["chunk_size"],
            overlap=config["overlap"],
        )
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
            results.append({**config, "error": result["error"]})
            continue
        
        # Check for truncation (output too short relative to input)
        ratio = result["output_length"] / result["input_length"]
        status = "✅" if ratio > 0.8 else "⚠️" if ratio > 0.5 else "❌"
        
        print(f"分段: {result['chunks']}, 耗时: {result['elapsed_ms']}ms")
        print(f"输出/输入比: {ratio:.2f} {status}")
        
        results.append({
            **config,
            "chunks": result["chunks"],
            "elapsed_ms": result["elapsed_ms"],
            "output_length": result["output_length"],
            "ratio": ratio,
            "status": status,
        })
    
    return results

def main():
    print("=" * 60)
    print("TranslateGemma 滑动窗口功能测试")
    print("=" * 60)
    
    # Check API health
    try:
        resp = requests.get("http://localhost:8022/health")
        if resp.status_code != 200:
            print("❌ API 不可用")
            return
        print("✅ API 连接正常")
    except Exception as e:
        print(f"❌ 无法连接 API: {e}")
        return
    
    # Run tests
    all_results = {}
    
    for test_case in TEST_CASES:
        # Basic comparison test
        results = run_comparison_test(test_case, chunk_size=100)
        all_results[test_case["name"]] = results
    
    # Detailed chunk size comparison on first test case
    print("\n" + "=" * 60)
    print("详细 Chunk Size 对比")
    print("=" * 60)
    chunk_results = run_chunk_size_comparison(TEST_CASES[0])
    
    # Summary
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    print("\n| 配置 | 分段 | 耗时 | 输出比 | 状态 |")
    print("|------|------|------|--------|------|")
    for r in chunk_results:
        if "error" in r:
            print(f"| chunk={r['chunk_size']}, overlap={r['overlap']} | - | - | - | ❌ |")
        else:
            print(f"| chunk={r['chunk_size']}, overlap={r['overlap']} | {r['chunks']} | {r['elapsed_ms']}ms | {r['ratio']:.2f} | {r['status']} |")
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()
