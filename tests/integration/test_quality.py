#!/usr/bin/env python3
"""
Quality comparison test - with vs without sliding window at chunk_size=100
Focus on translation coherence and context preservation.
"""
import requests
import json

API_URL = "http://localhost:8022/api/translate"

# Test text with context-dependent content
TEST_TEXT = """人工智能的概念可以追溯到古希腊神话中的自动机器人，这些神话描绘了由工匠赫菲斯托斯创造的金属生物。然而，作为一门正式学科，人工智能诞生于1956年的达特茅斯会议。在这次会议上，约翰·麦卡锡首次提出了"人工智能"这一术语。早期的人工智能研究主要集中在符号推理和问题求解上。研究人员相信，通过编写足够复杂的规则，机器可以模拟人类的思维过程。这一时期被称为"符号主义"或"GOFAI"（Good Old-Fashioned AI）时代。

1980年代，专家系统的兴起标志着人工智能的第一次商业化浪潮。这些系统通过编码领域专家的知识来解决特定问题。然而，专家系统的局限性很快显现：它们难以处理不确定性，且知识获取成本高昂。这导致了1980年代末的"人工智能寒冬"。

进入21世纪，随着计算能力的提升和大数据的出现，机器学习特别是深度学习取得了突破性进展。2012年，AlexNet在ImageNet竞赛中的胜利标志着深度学习时代的到来。此后，人工智能在图像识别、语音识别、自然语言处理等领域取得了令人瞩目的成就。"""

def translate(overlap: int) -> dict:
    payload = {
        "text": TEST_TEXT,
        "target_lang": "en",
        "chunk_size": 100,
        "overlap": overlap,
    }
    resp = requests.post(API_URL, json=payload)
    return resp.json()

def main():
    print("=" * 70)
    print("翻译质量对比: 有无滑动窗口 (chunk_size=100)")
    print("=" * 70)
    
    # Test without overlap
    print("\n" + "=" * 70)
    print("【无滑动窗口】overlap=0")
    print("=" * 70)
    result_no_overlap = translate(0)
    if result_no_overlap.get("status") == "success":
        print(f"分段数: {result_no_overlap.get('chunks')}")
        print(f"耗时: {result_no_overlap.get('elapsed_ms')}ms")
        print(f"\n完整翻译结果:\n")
        print(result_no_overlap.get("result"))
    
    # Test with overlap
    print("\n" + "=" * 70)
    print("【有滑动窗口】overlap=20")
    print("=" * 70)
    result_with_overlap = translate(20)
    if result_with_overlap.get("status") == "success":
        print(f"分段数: {result_with_overlap.get('chunks')}")
        print(f"耗时: {result_with_overlap.get('elapsed_ms')}ms")
        print(f"\n完整翻译结果:\n")
        print(result_with_overlap.get("result"))
    
    # Compare
    print("\n" + "=" * 70)
    print("对比分析")
    print("=" * 70)
    
    if result_no_overlap.get("status") == "success" and result_with_overlap.get("status") == "success":
        len_no = len(result_no_overlap.get("result", ""))
        len_with = len(result_with_overlap.get("result", ""))
        
        print(f"无滑动窗口输出长度: {len_no} 字符")
        print(f"有滑动窗口输出长度: {len_with} 字符")
        print(f"差异: {len_with - len_no} 字符 ({(len_with/len_no - 1)*100:.1f}%)")
        
        # Check for potential repetition in overlap version
        result_text = result_with_overlap.get("result", "")
        words = result_text.split()
        
        # Simple repetition check - look for repeated phrases
        repeated = []
        for i in range(len(words) - 3):
            phrase = " ".join(words[i:i+4])
            rest = " ".join(words[i+4:])
            if phrase in rest:
                repeated.append(phrase)
        
        if repeated:
            print(f"\n⚠️ 检测到可能的重复内容:")
            for r in set(repeated)[:5]:
                print(f"  - '{r}'")
        else:
            print(f"\n✅ 未检测到明显重复内容")

if __name__ == "__main__":
    main()
