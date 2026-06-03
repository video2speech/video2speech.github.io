#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import torch
import numpy as np
from transformers import GPT2LMHeadModel, GPT2Tokenizer, AutoTokenizer, AutoModelForCausalLM
import warnings
warnings.filterwarnings("ignore")

class PerplexityChecker:
    def __init__(self, model_name="gpt2"):
        """
        初始化困惑度检查器
        可选模型:
        - "gpt2" (小模型，快速)
        - "gpt2-medium" (中等模型)
        - "gpt2-large" (大模型，更准确但慢)
        - "microsoft/DialoGPT-medium" (对话模型)
        """
        print(f"🔄 加载语言模型: {model_name}")
        self.model_name = model_name
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"📱 使用设备: {self.device}")
        
        try:
            # 加载tokenizer和模型
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # 设置pad token（如果没有的话）
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.model.to(self.device)
            self.model.eval()
            
            print(f"✅ 模型加载成功")
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            print("💡 请确保安装了transformers和torch:")
            print("   pip install transformers torch")
            raise
    
    def load_sentences(self, filename="selected_sentences_analyzer.json"):
        """加载句子数据"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    sentences = json.load(f)
                print(f"📁 加载了 {len(sentences)} 个句子")
                return sentences
            except Exception as e:
                print(f"❌ 加载句子文件失败: {e}")
                return []
        else:
            print(f"❌ 未找到文件: {filename}")
            return []
    
    def calculate_perplexity(self, text):
        """计算单个句子的困惑度"""
        try:
            # 编码文本
            encodings = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
            input_ids = encodings.input_ids.to(self.device)
            
            # 计算困惑度
            with torch.no_grad():
                outputs = self.model(input_ids, labels=input_ids)
                loss = outputs.loss
                perplexity = torch.exp(loss).item()
            
            return perplexity, loss.item()
            
        except Exception as e:
            print(f"❌ 计算困惑度失败: {text[:50]}... - {e}")
            return float('inf'), float('inf')
    
    def batch_calculate_perplexity(self, sentences, batch_size=8):
        """批量计算困惑度"""
        results = []
        total = len(sentences)
        
        print(f"\n🔄 开始计算 {total} 个句子的困惑度...")
        print(f"📊 批处理大小: {batch_size}")
        
        for i in range(0, total, batch_size):
            batch = sentences[i:i+batch_size]
            batch_results = []
            
            for j, sentence in enumerate(batch):
                current_idx = i + j + 1
                print(f"⏳ 处理中 ({current_idx}/{total}): {sentence[:50]}{'...' if len(sentence) > 50 else ''}")
                
                perplexity, loss = self.calculate_perplexity(sentence)
                
                batch_results.append({
                    'index': current_idx,
                    'sentence': sentence,
                    'perplexity': perplexity,
                    'loss': loss,
                    'length': len(sentence.split())  # 词数
                })
            
            results.extend(batch_results)
            
            # 显示进度
            progress = (i + len(batch)) / total * 100
            print(f"📈 进度: {progress:.1f}% ({i + len(batch)}/{total})")
        
        return results
    
    def analyze_results(self, results):
        """分析困惑度结果"""
        if not results:
            print("❌ 没有结果可分析")
            return
        
        # 过滤掉无效结果
        valid_results = [r for r in results if r['perplexity'] != float('inf')]
        
        if not valid_results:
            print("❌ 没有有效的困惑度计算结果")
            return
        
        perplexities = [r['perplexity'] for r in valid_results]
        
        print("\n" + "=" * 80)
        print("📊 困惑度分析结果")
        print("=" * 80)
        
        # 统计信息
        print(f"\n📈 统计摘要:")
        print(f"   总句子数: {len(results)}")
        print(f"   有效计算: {len(valid_results)}")
        print(f"   平均困惑度: {np.mean(perplexities):.2f}")
        print(f"   中位数困惑度: {np.median(perplexities):.2f}")
        print(f"   最低困惑度: {np.min(perplexities):.2f}")
        print(f"   最高困惑度: {np.max(perplexities):.2f}")
        print(f"   标准差: {np.std(perplexities):.2f}")
        
        # 按困惑度排序（从低到高，低困惑度表示更自然）
        sorted_results = sorted(valid_results, key=lambda x: x['perplexity'])
        
        # 显示最自然的句子（低困惑度）
        print(f"\n🌟 最自然的句子 (低困惑度):")
        print("-" * 60)
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"{i:2d}. 困惑度: {result['perplexity']:6.2f} | {result['sentence']}")
        
        # 显示最不自然的句子（高困惑度）
        print(f"\n⚠️  最不自然的句子 (高困惑度):")
        print("-" * 60)
        for i, result in enumerate(sorted_results[-10:], 1):
            print(f"{i:2d}. 困惑度: {result['perplexity']:6.2f} | {result['sentence']}")
        
        return sorted_results
    
    def save_results(self, results, filename="perplexity_report.json"):
        """保存结果到文件"""
        try:
            # 保存JSON格式
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 保存可读文本格式
            txt_filename = filename.replace('.json', '.txt')
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write("句子困惑度分析报告\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"模型: {self.model_name}\n")
                f.write(f"总句子数: {len(results)}\n\n")
                
                # 按困惑度排序
                sorted_results = sorted([r for r in results if r['perplexity'] != float('inf')], 
                                      key=lambda x: x['perplexity'])
                
                f.write("所有句子的困惑度 (按困惑度排序):\n")
                f.write("-" * 50 + "\n")
                
                for result in sorted_results:
                    f.write(f"\n困惑度: {result['perplexity']:6.2f} | 词数: {result['length']:2d} | {result['sentence']}\n")
            
            print(f"✅ 结果已保存到:")
            print(f"   📄 {filename} (JSON格式)")
            print(f"   📄 {txt_filename} (文本格式)")
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")

def main():
    print("🎯 句子困惑度检查器")
    print("=" * 50)
    
    # 选择模型
    models = {
        "1": "gpt2",
        "2": "gpt2-medium", 
        "3": "microsoft/DialoGPT-medium"
    }
    
    print("📚 可用模型:")
    print("   1. GPT-2 (小模型，快速)")
    print("   2. GPT-2 Medium (中等模型)")
    print("   3. DialoGPT Medium (对话模型)")
    
    choice = input("\n选择模型 (1-3, 默认1): ").strip() or "1"
    model_name = models.get(choice, "gpt2")
    
    try:
        # 初始化检查器
        checker = PerplexityChecker(model_name)
        
        # 加载句子
        sentences = checker.load_sentences()
        if not sentences:
            return
        
        # 批量计算困惑度
        batch_size = int(input(f"\n批处理大小 (默认4): ").strip() or "4")
        results = checker.batch_calculate_perplexity(sentences, batch_size)
        
        # 分析结果
        sorted_results = checker.analyze_results(results)
        
        # 保存结果
        if sorted_results:
            save_choice = input("\n💾 是否保存结果? (y/N): ").strip().lower()
            if save_choice in ['y', 'yes']:
                checker.save_results(results)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("💡 如果是模型加载问题，请尝试:")
        print("   pip install transformers torch")
        print("   或选择更小的模型")

if __name__ == "__main__":
    main()

