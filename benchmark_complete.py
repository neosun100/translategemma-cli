#!/usr/bin/env python3
"""
Complete Model Benchmark Script
Tests GGUF (Q4/Q8) and PyTorch (bfloat16) models for comparison.
"""

import time
import json
import gc
import os
from pathlib import Path
from datetime import datetime

# Test texts
SHORT_TEXT = "Hello, how are you today?"
MEDIUM_TEXT = """
Artificial intelligence has transformed the way we live and work. 
From voice assistants to self-driving cars, AI is everywhere.
Machine learning algorithms can now recognize faces, translate languages, 
and even write code. The future of AI is both exciting and challenging.
""".strip()

LONG_TEXT = """
The history of artificial intelligence began in antiquity, with myths, stories and rumors of artificial beings endowed with intelligence or consciousness by master craftsmen. The seeds of modern AI were planted by philosophers who attempted to describe the process of human thinking as the mechanical manipulation of symbols. This work culminated in the invention of the programmable digital computer in the 1940s, a machine based on the abstract essence of mathematical reasoning.

This device and the ideas behind it inspired a handful of scientists to begin seriously discussing the possibility of building an electronic brain. The field of AI research was founded at a workshop held on the campus of Dartmouth College during the summer of 1956. Those who attended would become the leaders of AI research for decades. Many of them predicted that a machine as intelligent as a human being would exist in no more than a generation, and they were given millions of dollars to make this vision come true.

Eventually, it became obvious that commercial developers and researchers had grossly underestimated the difficulty of the project. In 1974, in response to the criticism from James Lighthill and ongoing pressure from congress, the U.S. and British Governments stopped funding undirected research into artificial intelligence, and the difficult years that followed would later be known as an "AI winter". Seven years later, a visionary initiative by the Japanese Government inspired governments and industry to provide AI with billions of dollars, but by the late 1980s the investors became disillusioned and withdrew funding again.

Investment and interest in AI boomed in the first decades of the 21st century when machine learning was successfully applied to many problems in academia and industry due to new methods, the application of powerful computer hardware, and the collection of immense data sets. The field of deep learning began to dominate AI benchmarks around 2012 and generative AI became widely popular in 2022 with the release of ChatGPT.
""".strip()

QUALITY_TESTS = [
    ("Hello world", "zh", "Basic greeting"),
    ("The weather is beautiful today.", "ja", "Simple sentence"),
    ("I love programming and artificial intelligence.", "zh", "Technical terms"),
    ("今天天气真好，我们去公园散步吧。", "en", "Chinese to English"),
    ("人工智能正在改变我们的生活方式。", "en", "Technical Chinese"),
]

def detect_language(text: str) -> str:
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return "zh"
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in text):
        return "ja"
    return "en"

def format_gguf_prompt(text: str, source_lang: str, target_lang: str) -> str:
    lang_names = {
        "en": "English", "zh": "Chinese", "ja": "Japanese",
        "ko": "Korean", "fr": "French", "de": "German",
    }
    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)
    
    return (
        f"<start_of_turn>user\n"
        f"You are a professional {source_name} ({source_lang}) to {target_name} ({target_lang}) translator. "
        f"Your goal is to accurately convey the meaning and nuances of the original {source_name} text "
        f"while adhering to {target_name} grammar, vocabulary, and cultural sensitivities.\n"
        f"Produce only the {target_name} translation, without any additional explanations or commentary. "
        f"Please translate the following {source_name} text into {target_name}:\n\n\n"
        f"{text.strip()}<end_of_turn>\n"
        f"<start_of_turn>model\n"
    )

def clean_response(text: str) -> str:
    for token in ["<end_of_turn>", "<eos>", "<bos>", "<pad>"]:
        text = text.replace(token, "").strip()
    return text

class GGUFModel:
    def __init__(self, size: str, quant: int):
        from llama_cpp import Llama
        from translategemma_cli.config import get_model_path, get_config
        
        config = get_config()
        path = get_model_path(size, quant, "gguf")
        self.name = f"{size}-Q{quant}"
        self.path = path
        self.size_gb = path.stat().st_size / (1024**3)
        
        load_start = time.time()
        self.model = Llama(
            model_path=str(path),
            n_gpu_layers=config.gguf_n_gpu_layers,
            n_ctx=config.gguf_n_ctx,
            verbose=False,
        )
        self.load_time = time.time() - load_start
        self.backend = "gguf"
    
    def translate(self, text: str, source: str, target: str, max_tokens: int = 512) -> tuple[str, float]:
        prompt = format_gguf_prompt(text, source, target)
        start = time.time()
        output = self.model(prompt, max_tokens=max_tokens, echo=False, temperature=0.0)
        elapsed = time.time() - start
        result = clean_response(output["choices"][0]["text"])
        return result, elapsed
    
    def cleanup(self):
        del self.model
        gc.collect()

class PyTorchModel:
    def __init__(self, size: str):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        self.name = f"{size}-bf16"
        self.size = size
        hf_model_id = f"google/translategemma-{size}-it"
        
        load_start = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(hf_model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            hf_model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        self.load_time = time.time() - load_start
        self.backend = "pytorch"
        
        # Get model size from GPU memory
        self.size_gb = sum(p.numel() * p.element_size() for p in self.model.parameters()) / (1024**3)
        
        # Warmup
        inputs = self.tokenizer("Hello", return_tensors="pt").to("cuda:0")
        with torch.no_grad():
            _ = self.model.generate(**inputs, max_new_tokens=1, do_sample=False)
    
    def translate(self, text: str, source: str, target: str, max_tokens: int = 512) -> tuple[str, float]:
        import torch
        from translategemma_cli.translator import LANG_CODE_MAP
        
        source_code = LANG_CODE_MAP.get(source, source)
        target_code = LANG_CODE_MAP.get(target, target)
        
        messages = [{
            "role": "user",
            "content": [{
                "type": "text",
                "source_lang_code": source_code,
                "target_lang_code": target_code,
                "text": text,
            }],
        }]
        
        inputs = self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
            return_dict=True, return_tensors="pt"
        ).to(self.model.device)
        
        input_len = inputs["input_ids"].shape[1]
        
        start = time.time()
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        elapsed = time.time() - start
        
        result = self.tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
        return clean_response(result), elapsed
    
    def cleanup(self):
        import torch
        del self.model
        del self.tokenizer
        gc.collect()
        torch.cuda.empty_cache()

def run_model_test(model, test_name: str) -> dict:
    """Run all tests on a model."""
    print(f"\n{'='*60}")
    print(f"Testing {model.name}...")
    print(f"{'='*60}")
    print(f"Size: {model.size_gb:.2f} GB, Load time: {model.load_time:.2f}s")
    
    results = {
        "name": model.name,
        "backend": model.backend,
        "size_gb": round(model.size_gb, 2),
        "load_time_s": round(model.load_time, 2),
        "tests": {},
        "quality_tests": []
    }
    
    # Speed tests
    print("\n--- Speed Tests ---")
    
    for name, text, max_tok in [("short", SHORT_TEXT, 512), ("medium", MEDIUM_TEXT, 1024), ("long", LONG_TEXT, 2048)]:
        result, elapsed = model.translate(text, "en", "zh", max_tok)
        chars_per_sec = len(text) / elapsed
        results["tests"][name] = {
            "input_chars": len(text),
            "time_s": round(elapsed, 2),
            "chars_per_sec": round(chars_per_sec, 1),
            "result": result[:200]
        }
        print(f"{name.capitalize()} ({len(text)} chars): {elapsed:.2f}s ({chars_per_sec:.1f} chars/s)")
    
    # Quality tests
    print("\n--- Quality Tests ---")
    for text, target, desc in QUALITY_TESTS:
        source = detect_language(text)
        result, elapsed = model.translate(text, source, target)
        results["quality_tests"].append({
            "description": desc,
            "input": text,
            "output": result,
            "time_s": round(elapsed, 2)
        })
        print(f"{desc}: \"{text}\" → \"{result}\"")
    
    return results

def run_benchmark():
    """Run complete benchmark."""
    # Use GPU 1 and 2 for multi-GPU models
    os.environ["CUDA_VISIBLE_DEVICES"] = "1,2"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "gpu": "NVIDIA L40S × 2 (CUDA_VISIBLE_DEVICES=1,2)",
        "models": {}
    }
    
    # Test GGUF models (single GPU is enough)
    gguf_models = [
        ("4b", 4), ("4b", 8),
        ("12b", 4), ("12b", 8),
        ("27b", 4), ("27b", 8),
    ]
    
    for size, quant in gguf_models:
        try:
            model = GGUFModel(size, quant)
            result = run_model_test(model, f"{size}-Q{quant}")
            results["models"][model.name] = result
            model.cleanup()
        except Exception as e:
            print(f"Error testing {size}-Q{quant}: {e}")
    
    # Test PyTorch bfloat16 models
    pytorch_sizes = ["4b", "12b", "27b"]
    
    for size in pytorch_sizes:
        try:
            print(f"\n*** Loading PyTorch {size} (bfloat16, multi-GPU) ***")
            model = PyTorchModel(size)
            result = run_model_test(model, f"{size}-bf16")
            results["models"][model.name] = result
            model.cleanup()
        except Exception as e:
            print(f"Error testing {size}-bf16: {e}")
            import traceback
            traceback.print_exc()
    
    return results

def generate_comparison_report(results: dict) -> str:
    """Generate comparison report."""
    report = f"""# TranslateGemma 完整模型对比测试报告

**测试时间**: {results['timestamp'][:10]}  
**测试环境**: {results['gpu']}  
**测试框架**: llama-cpp-python (GGUF) + transformers (PyTorch)

---

## 📋 测试模型

| 类型 | 模型 | 量化方式 | 文件/内存大小 |
|------|------|----------|---------------|
"""
    
    for name, data in results["models"].items():
        model_type = "GGUF" if "Q" in name else "PyTorch"
        quant = name.split("-")[1] if "-" in name else "N/A"
        report += f"| {model_type} | {name} | {quant} | {data['size_gb']:.2f} GB |\n"
    
    report += """
---

## ⚡ 速度对比

### 长文本测试 (~2000 字符)

| 模型 | 耗时 | 速度 (字符/秒) | 相对性能 |
|------|------|----------------|----------|
"""
    
    # Sort by speed
    speed_data = [(name, data["tests"]["long"]["chars_per_sec"]) 
                  for name, data in results["models"].items() 
                  if "long" in data["tests"]]
    speed_data.sort(key=lambda x: x[1], reverse=True)
    max_speed = speed_data[0][1] if speed_data else 1
    
    for name, speed in speed_data:
        data = results["models"][name]
        time_s = data["tests"]["long"]["time_s"]
        pct = int(speed / max_speed * 100)
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        report += f"| **{name}** | {time_s:.2f}s | {speed:.1f} | {bar} {pct}% |\n"
    
    report += """
### 速度总结

| 模型 | 短文本 | 中文本 | 长文本 | 平均速度 |
|------|--------|--------|--------|----------|
"""
    
    for name, data in results["models"].items():
        tests = data["tests"]
        short = tests.get("short", {}).get("chars_per_sec", 0)
        medium = tests.get("medium", {}).get("chars_per_sec", 0)
        long = tests.get("long", {}).get("chars_per_sec", 0)
        avg = (short + medium + long) / 3
        report += f"| {name} | {short:.0f} | {medium:.0f} | {long:.0f} | **{avg:.0f}** |\n"
    
    report += """
---

## 🎯 翻译质量对比

### 测试 1: 基础问候 (English → Chinese)
**原文**: "Hello world"

| 模型 | 翻译结果 |
|------|----------|
"""
    
    for name, data in results["models"].items():
        if data["quality_tests"]:
            result = data["quality_tests"][0]["output"]
            report += f"| {name} | {result} |\n"
    
    report += """
### 测试 4: 中文到英文
**原文**: "今天天气真好，我们去公园散步吧。"

| 模型 | 翻译结果 |
|------|----------|
"""
    
    for name, data in results["models"].items():
        if len(data["quality_tests"]) > 3:
            result = data["quality_tests"][3]["output"]
            report += f"| {name} | {result} |\n"
    
    report += """
---

## 📊 GGUF vs PyTorch 对比

### 27b 模型对比

| 指标 | 27b-Q4 | 27b-Q8 | 27b-bf16 |
|------|--------|--------|----------|
"""
    
    models_27b = {k: v for k, v in results["models"].items() if k.startswith("27b")}
    if models_27b:
        metrics = ["size_gb", "load_time_s"]
        metric_names = {"size_gb": "大小 (GB)", "load_time_s": "加载时间 (s)"}
        
        for metric in metrics:
            row = f"| {metric_names[metric]} |"
            for name in ["27b-Q4", "27b-Q8", "27b-bf16"]:
                if name in models_27b:
                    val = models_27b[name].get(metric, "N/A")
                    row += f" {val:.2f} |" if isinstance(val, float) else f" {val} |"
                else:
                    row += " N/A |"
            report += row + "\n"
        
        # Speed comparison
        row = "| 长文本速度 |"
        for name in ["27b-Q4", "27b-Q8", "27b-bf16"]:
            if name in models_27b and "long" in models_27b[name]["tests"]:
                speed = models_27b[name]["tests"]["long"]["chars_per_sec"]
                row += f" {speed:.1f} |"
            else:
                row += " N/A |"
        report += row + "\n"
    
    report += """
---

## 🏆 结论与推荐

### 速度排名
"""
    
    # Speed ranking
    for i, (name, speed) in enumerate(speed_data[:5], 1):
        report += f"{i}. **{name}**: {speed:.1f} 字符/秒\n"
    
    report += """
### 推荐配置

| 场景 | 推荐模型 | 原因 |
|------|----------|------|
| 最高质量 | 27b-bf16 | 原始精度，无量化损失 |
| 高质量 + 单GPU | 27b-Q4 | 质量接近原始，单GPU可运行 |
| 平衡选择 | 12b-Q4 | 速度与质量最佳平衡 |
| 快速翻译 | 4b-Q4 | 速度最快 |

### VRAM 需求

| 模型 | 单GPU | 多GPU |
|------|-------|-------|
| 4b-Q4 | ~4 GB | - |
| 12b-Q4 | ~8 GB | - |
| 27b-Q4 | ~18 GB | - |
| 27b-bf16 | ❌ | ~54 GB (2×GPU) |

---

*报告生成时间: {timestamp}*
""".format(timestamp=results['timestamp'])
    
    return report

if __name__ == "__main__":
    print("="*60)
    print("TranslateGemma Complete Model Benchmark")
    print("Testing GGUF (Q4/Q8) and PyTorch (bfloat16) models")
    print("="*60)
    
    results = run_benchmark()
    
    # Save results
    with open("complete_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nResults saved to complete_benchmark_results.json")
    
    # Generate report
    report = generate_comparison_report(results)
    with open("COMPLETE_BENCHMARK_REPORT.md", "w") as f:
        f.write(report)
    print("Report saved to COMPLETE_BENCHMARK_REPORT.md")
