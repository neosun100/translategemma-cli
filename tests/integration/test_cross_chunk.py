#!/usr/bin/env python3
"""
测试：跨 chunk 边界的上下文一致性
使用足够长的文本确保触发多 chunk 分割
"""
import requests

API_URL = "http://localhost:8022/api/translate"

# 长文本测试用例 - 确保跨越多个 chunk
TEST_CASES = [
    {
        "name": "代词指代跨chunk",
        "text": """李明是一位杰出的计算机科学家，他在北京大学获得了博士学位。毕业后，他加入了一家知名的科技公司担任首席技术官。在他的领导下，公司开发出了多款创新产品。他的管理风格深受员工喜爱。他经常说，创新是公司发展的核心动力。他的愿景是让技术改变人们的生活方式。他相信，只有不断学习才能保持竞争力。他的团队在他的带领下取得了许多突破性成果。""",
        "focus": "检查'他'在不同chunk中是否一致翻译为He/His",
    },
    {
        "name": "术语一致性跨chunk",
        "text": """自然语言处理是人工智能的重要分支。自然语言处理技术可以让计算机理解人类语言。近年来，自然语言处理取得了巨大进步。大型语言模型推动了自然语言处理的发展。自然语言处理被广泛应用于机器翻译领域。自然语言处理还用于情感分析和文本摘要。未来，自然语言处理将变得更加智能。自然语言处理的研究者们正在探索新的方向。""",
        "focus": "检查'自然语言处理'是否始终翻译为'natural language processing'或'NLP'",
    },
    {
        "name": "公司名称跨chunk",
        "text": """谷歌是全球最大的搜索引擎公司。谷歌的总部位于加利福尼亚州山景城。谷歌开发了安卓操作系统。谷歌还拥有YouTube视频平台。谷歌的人工智能研究处于世界领先地位。谷歌推出了许多创新产品和服务。谷歌的使命是整合全球信息。谷歌的员工来自世界各地。谷歌的企业文化鼓励创新和冒险。""",
        "focus": "检查'谷歌'是否始终翻译为'Google'",
    },
    {
        "name": "复杂上下文依赖",
        "text": """张伟博士是清华大学的教授。他专注于深度学习研究。他的实验室有二十名研究生。他们正在研究新型神经网络架构。他的学生小李最近发表了一篇重要论文。这篇论文引起了学术界的广泛关注。他对小李的工作非常满意。他计划推荐小李去国外深造。他相信小李将来会成为优秀的研究者。""",
        "focus": "检查'他'指代张伟，'小李'保持一致，代词不混淆",
    },
]

def translate(text: str, overlap: int) -> tuple:
    payload = {
        "text": text,
        "target_lang": "en",
        "chunk_size": 100,
        "overlap": overlap,
    }
    resp = requests.post(API_URL, json=payload)
    data = resp.json()
    return data.get("result", ""), data.get("chunks", 0)

def count_term(text: str, terms: list) -> dict:
    """统计术语出现次数"""
    result = {}
    for term in terms:
        result[term] = text.lower().count(term.lower())
    return result

def main():
    print("=" * 70)
    print("跨 Chunk 上下文一致性测试")
    print("chunk_size=100, 对比 overlap=0 vs overlap=20")
    print("=" * 70)
    
    for case in TEST_CASES:
        print(f"\n{'='*70}")
        print(f"测试: {case['name']}")
        print(f"关注点: {case['focus']}")
        print(f"原文长度: {len(case['text'])} 字符")
        print("-" * 70)
        
        # 无滑动窗口
        result_no, chunks_no = translate(case["text"], 0)
        print(f"\n【无滑动窗口】({chunks_no} chunks)")
        print(f"翻译结果:\n{result_no}")
        
        # 有滑动窗口
        result_with, chunks_with = translate(case["text"], 20)
        print(f"\n【有滑动窗口】({chunks_with} chunks)")
        print(f"翻译结果:\n{result_with}")
        
        # 分析
        print(f"\n📊 分析:")
        print(f"  无overlap: {len(result_no)} 字符")
        print(f"  有overlap: {len(result_with)} 字符 ({len(result_with)-len(result_no):+d})")
        
        # 检查特定术语
        if "代词" in case["name"]:
            terms = ["he", "his", "him"]
            no_counts = count_term(result_no, terms)
            with_counts = count_term(result_with, terms)
            print(f"  代词统计(无overlap): {no_counts}")
            print(f"  代词统计(有overlap): {with_counts}")
        
        if "术语" in case["name"] or "自然语言" in case["text"]:
            terms = ["natural language processing", "nlp"]
            no_counts = count_term(result_no, terms)
            with_counts = count_term(result_with, terms)
            print(f"  术语统计(无overlap): {no_counts}")
            print(f"  术语统计(有overlap): {with_counts}")
        
        if "谷歌" in case["text"]:
            terms = ["google"]
            no_counts = count_term(result_no, terms)
            with_counts = count_term(result_with, terms)
            print(f"  Google出现次数(无overlap): {no_counts}")
            print(f"  Google出现次数(有overlap): {with_counts}")
    
    print("\n" + "=" * 70)
    print("结论分析")
    print("=" * 70)

if __name__ == "__main__":
    main()
