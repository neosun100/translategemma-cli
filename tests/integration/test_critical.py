#!/usr/bin/env python3
"""
Critical test - reproduce the truncation issue with chunk_size >= 120
"""
import requests
import json

API_URL = "http://localhost:8022/api/translate"

# The problematic long text that caused 32% content loss before
LONG_TEXT = """人工智能的概念可以追溯到古希腊神话中的自动机器人，这些神话描绘了由工匠赫菲斯托斯创造的金属生物。然而，作为一门正式学科，人工智能诞生于1956年的达特茅斯会议。在这次会议上，约翰·麦卡锡首次提出了"人工智能"这一术语。早期的人工智能研究主要集中在符号推理和问题求解上。研究人员相信，通过编写足够复杂的规则，机器可以模拟人类的思维过程。这一时期被称为"符号主义"或"GOFAI"（Good Old-Fashioned AI）时代。

1980年代，专家系统的兴起标志着人工智能的第一次商业化浪潮。这些系统通过编码领域专家的知识来解决特定问题。然而，专家系统的局限性很快显现：它们难以处理不确定性，且知识获取成本高昂。这导致了1980年代末的"人工智能寒冬"。

进入21世纪，随着计算能力的提升和大数据的出现，机器学习特别是深度学习取得了突破性进展。2012年，AlexNet在ImageNet竞赛中的胜利标志着深度学习时代的到来。此后，人工智能在图像识别、语音识别、自然语言处理等领域取得了令人瞩目的成就。"""

KEYWORDS = [
    "古希腊", "赫菲斯托斯", "达特茅斯", "麦卡锡", "符号推理", "GOFAI",
    "专家系统", "人工智能寒冬", "深度学习", "AlexNet", "ImageNet"
]

def test_config(chunk_size: int, overlap: int) -> dict:
    """Test a specific configuration."""
    payload = {
        "text": LONG_TEXT,
        "target_lang": "en",
        "chunk_size": chunk_size,
        "overlap": overlap,
    }
    
    resp = requests.post(API_URL, json=payload)
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}"}
    
    data = resp.json()
    if data.get("status") != "success":
        return {"error": data.get("error")}
    
    result = data.get("result", "")
    
    # Check for key concepts in translation
    # These English terms should appear if translation is complete
    key_terms = [
        "Greek", "Hephaestus", "Dartmouth", "McCarthy", 
        "expert system", "AI winter", "deep learning", "AlexNet", "ImageNet"
    ]
    
    found_terms = []
    missing_terms = []
    for term in key_terms:
        if term.lower() in result.lower():
            found_terms.append(term)
        else:
            missing_terms.append(term)
    
    return {
        "chunks": data.get("chunks"),
        "elapsed_ms": data.get("elapsed_ms"),
        "input_length": len(LONG_TEXT),
        "output_length": len(result),
        "ratio": len(result) / len(LONG_TEXT),
        "found_terms": found_terms,
        "missing_terms": missing_terms,
        "completeness": len(found_terms) / len(key_terms) * 100,
        "result_preview": result[:300] + "..." if len(result) > 300 else result,
        "result_end": "..." + result[-200:] if len(result) > 200 else result,
    }

def main():
    print("=" * 70)
    print("关键测试: 验证 chunk_size >= 120 的截断问题")
    print(f"测试文本长度: {len(LONG_TEXT)} 字符")
    print("=" * 70)
    
    # Test configurations - focus on the problematic sizes
    configs = [
        # Safe configurations
        {"chunk_size": 80, "overlap": 0, "desc": "安全配置 (无overlap)"},
        {"chunk_size": 80, "overlap": 20, "desc": "安全配置 (有overlap)"},
        {"chunk_size": 100, "overlap": 0, "desc": "推荐配置 (无overlap)"},
        {"chunk_size": 100, "overlap": 20, "desc": "推荐配置 (有overlap)"},
        # Previously problematic configurations
        {"chunk_size": 120, "overlap": 0, "desc": "⚠️ 之前有问题 (无overlap)"},
        {"chunk_size": 120, "overlap": 30, "desc": "⚠️ 之前有问题 (有overlap)"},
        {"chunk_size": 150, "overlap": 0, "desc": "❌ 之前严重截断 (无overlap)"},
        {"chunk_size": 150, "overlap": 40, "desc": "❌ 之前严重截断 (有overlap)"},
    ]
    
    results = []
    
    for config in configs:
        print(f"\n{'='*70}")
        print(f"测试: {config['desc']}")
        print(f"chunk_size={config['chunk_size']}, overlap={config['overlap']}")
        print("-" * 70)
        
        result = test_config(config["chunk_size"], config["overlap"])
        
        if "error" in result:
            print(f"❌ 错误: {result['error']}")
            results.append({**config, "status": "ERROR", "completeness": 0})
            continue
        
        status = "✅" if result["completeness"] >= 80 else "⚠️" if result["completeness"] >= 50 else "❌"
        
        print(f"分段数: {result['chunks']}")
        print(f"耗时: {result['elapsed_ms']}ms")
        print(f"输出长度: {result['output_length']} (比例: {result['ratio']:.2f})")
        print(f"关键词完整度: {result['completeness']:.0f}% {status}")
        print(f"找到的关键词: {', '.join(result['found_terms'])}")
        if result['missing_terms']:
            print(f"缺失的关键词: {', '.join(result['missing_terms'])}")
        print(f"\n翻译开头: {result['result_preview'][:150]}...")
        print(f"翻译结尾: ...{result['result_end'][-150:]}")
        
        results.append({
            **config,
            "status": status,
            "chunks": result["chunks"],
            "completeness": result["completeness"],
            "output_length": result["output_length"],
        })
    
    # Summary table
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    print("\n| chunk | overlap | 分段 | 完整度 | 状态 | 说明 |")
    print("|-------|---------|------|--------|------|------|")
    for r in results:
        print(f"| {r['chunk_size']} | {r['overlap']} | {r.get('chunks', '-')} | {r['completeness']:.0f}% | {r['status']} | {r['desc']} |")
    
    print("\n" + "=" * 70)
    print("结论")
    print("=" * 70)
    
    # Analyze results
    safe_results = [r for r in results if r["chunk_size"] <= 100]
    risky_results = [r for r in results if r["chunk_size"] > 100]
    
    safe_complete = all(r["completeness"] >= 80 for r in safe_results)
    risky_complete = all(r["completeness"] >= 80 for r in risky_results)
    
    if safe_complete:
        print("✅ chunk_size <= 100 的配置全部通过测试")
    else:
        print("⚠️ chunk_size <= 100 的配置有问题")
    
    if risky_complete:
        print("✅ chunk_size > 100 的配置也通过测试 (滑动窗口可能有帮助)")
    else:
        print("⚠️ chunk_size > 100 的配置仍有截断风险")
    
    # Check if overlap helps
    for cs in [120, 150]:
        no_overlap = next((r for r in results if r["chunk_size"] == cs and r["overlap"] == 0), None)
        with_overlap = next((r for r in results if r["chunk_size"] == cs and r["overlap"] > 0), None)
        if no_overlap and with_overlap:
            if with_overlap["completeness"] > no_overlap["completeness"]:
                print(f"✅ chunk_size={cs}: 滑动窗口提升了完整度 ({no_overlap['completeness']:.0f}% → {with_overlap['completeness']:.0f}%)")
            elif with_overlap["completeness"] == no_overlap["completeness"]:
                print(f"➡️ chunk_size={cs}: 滑动窗口无明显影响")
            else:
                print(f"⚠️ chunk_size={cs}: 滑动窗口反而降低了完整度")

if __name__ == "__main__":
    main()
