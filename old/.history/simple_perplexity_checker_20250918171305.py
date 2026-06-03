#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import math
import re
from collections import defaultdict, Counter

class SimplePerplexityChecker:
    def __init__(self):
        """基于n-gram的简单困惑度计算器"""
        self.word_counts = defaultdict(int)
        self.bigram_counts = defaultdict(int)
        self.trigram_counts = defaultdict(int)
        self.total_words = 0
        self.vocab_size = 0
        
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
    
    def clean_text(self, text):
        """清理文本"""
        # 转小写
        text = text.lower()
        # 去除标点符号，保留基本结构
        text = re.sub(r'[^\w\s]', '', text)
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def tokenize(self, text):
        """分词"""
        clean_text = self.clean_text(text)
        tokens = clean_text.split()
        return ['<s>'] + tokens + ['</s>']  # 添加句子开始和结束标记
    
    def build_language_model(self, sentences):
        """构建语言模型"""
        print("🔄 构建语言模型...")
        
        all_tokens = []
        for sentence in sentences:
            tokens = self.tokenize(sentence)
            all_tokens.extend(tokens)
            
            # 统计unigram
            for token in tokens:
                self.word_counts[token] += 1
            
            # 统计bigram
            for i in range(len(tokens) - 1):
                bigram = (tokens[i], tokens[i + 1])
                self.bigram_counts[bigram] += 1
            
            # 统计trigram
            for i in range(len(tokens) - 2):
                trigram = (tokens[i], tokens[i + 1], tokens[i + 2])
                self.trigram_counts[trigram] += 1
        
        self.total_words = len(all_tokens)
        self.vocab_size = len(self.word_counts)
        
        print(f"✅ 语言模型构建完成")
        print(f"   总词数: {self.total_words}")
        print(f"   词汇量: {self.vocab_size}")
        print(f"   Bigram数: {len(self.bigram_counts)}")
        print(f"   Trigram数: {len(self.trigram_counts)}")
    
    def get_word_probability(self, word):
        """获取词的概率（带平滑）"""
        # 拉普拉斯平滑
        count = self.word_counts[word]
        return (count + 1) / (self.total_words + self.vocab_size)
    
    def get_bigram_probability(self, w1, w2):
        """获取bigram概率（带平滑）"""
        bigram_count = self.bigram_counts[(w1, w2)]
        w1_count = self.word_counts[w1]
        
        if w1_count == 0:
            return 1 / self.vocab_size  # 平滑处理
        
        # 拉普拉斯平滑
        return (bigram_count + 1) / (w1_count + self.vocab_size)
    
    def get_trigram_probability(self, w1, w2, w3):
        """获取trigram概率（带平滑）"""
        trigram_count = self.trigram_counts[(w1, w2, w3)]
        bigram_count = self.bigram_counts[(w1, w2)]
        
        if bigram_count == 0:
            return self.get_bigram_probability(w2, w3)  # 回退到bigram
        
        # 拉普拉斯平滑
        return (trigram_count + 1) / (bigram_count + self.vocab_size)
    
    def calculate_sentence_probability(self, sentence, model_type="trigram"):
        """计算句子概率"""
        tokens = self.tokenize(sentence)
        log_prob = 0.0
        
        if model_type == "unigram":
            for token in tokens:
                prob = self.get_word_probability(token)
                log_prob += math.log(prob)
        
        elif model_type == "bigram":
            for i in range(len(tokens) - 1):
                prob = self.get_bigram_probability(tokens[i], tokens[i + 1])
                log_prob += math.log(prob)
        
        elif model_type == "trigram":
            # 前两个词用bigram
            if len(tokens) >= 2:
                prob = self.get_bigram_probability(tokens[0], tokens[1])
                log_prob += math.log(prob)
            
            # 其余用trigram
            for i in range(2, len(tokens)):
                prob = self.get_trigram_probability(tokens[i-2], tokens[i-1], tokens[i])
                log_prob += math.log(prob)
        
        return log_prob
    
    def calculate_perplexity(self, sentence, model_type="trigram"):
        """计算困惑度"""
        tokens = self.tokenize(sentence)
        log_prob = self.calculate_sentence_probability(sentence, model_type)
        
        # 困惑度 = 2^(-log_prob / N)，这里用e为底
        perplexity = math.exp(-log_prob / len(tokens))
        
        return perplexity, log_prob
    
    def analyze_all_sentences(self, sentences, model_type="trigram"):
        """分析所有句子的困惑度"""
        print(f"\n🔄 使用 {model_type} 模型计算困惑度...")
        
        results = []
        total = len(sentences)
        
        for i, sentence in enumerate(sentences, 1):
            print(f"⏳ 处理中 ({i}/{total}): {sentence[:50]}{'...' if len(sentence) > 50 else ''}")
            
            perplexity, log_prob = self.calculate_perplexity(sentence, model_type)
            
            results.append({
                'index': i,
                'sentence': sentence,
                'perplexity': perplexity,
                'log_probability': log_prob,
                'length': len(sentence.split()),
                'model_type': model_type
            })
        
        return results
    
    def analyze_results(self, results):
        """分析困惑度结果"""
        if not results:
            print("❌ 没有结果可分析")
            return
        
        perplexities = [r['perplexity'] for r in results]
        
        print("\n" + "=" * 80)
        print("📊 困惑度分析结果")
        print("=" * 80)
        
        # 统计信息
        print(f"\n📈 统计摘要:")
        print(f"   总句子数: {len(results)}")
        print(f"   模型类型: {results[0]['model_type']}")
        print(f"   平均困惑度: {sum(perplexities)/len(perplexities):.2f}")
        print(f"   中位数困惑度: {sorted(perplexities)[len(perplexities)//2]:.2f}")
        print(f"   最低困惑度: {min(perplexities):.2f}")
        print(f"   最高困惑度: {max(perplexities):.2f}")
        
        # 按困惑度排序
        sorted_results = sorted(results, key=lambda x: x['perplexity'])
        
        # 显示最自然的句子（低困惑度）
        print(f"\n🌟 最自然的句子 (低困惑度):")
        print("-" * 60)
        for i, result in enumerate(sorted_results[:10], 1):
            print(f"{i:2d}. 困惑度: {result['perplexity']:8.2f} | {result['sentence']}")
        
        # 显示最不自然的句子（高困惑度）
        print(f"\n⚠️  最不自然的句子 (高困惑度):")
        print("-" * 60)
        for i, result in enumerate(sorted_results[-10:], 1):
            print(f"{i:2d}. 困惑度: {result['perplexity']:8.2f} | {result['sentence']}")
        
        return sorted_results
    
    def save_results(self, results, filename="simple_perplexity_report.json"):
        """保存结果"""
        try:
            # JSON格式
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 文本格式
            txt_filename = filename.replace('.json', '.txt')
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write("句子困惑度分析报告 (基于N-gram)\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"模型类型: {results[0]['model_type']}\n")
                f.write(f"总句子数: {len(results)}\n\n")
                
                sorted_results = sorted(results, key=lambda x: x['perplexity'])
                
                f.write("所有句子的困惑度 (按困惑度排序):\n")
                f.write("-" * 50 + "\n")
                
                for result in sorted_results:
                    f.write(f"\n困惑度: {result['perplexity']:8.2f} | 词数: {result['length']:2d} | {result['sentence']}\n")
            
            print(f"✅ 结果已保存到:")
            print(f"   📄 {filename}")
            print(f"   📄 {txt_filename}")
            
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")

def main():
    print("🎯 简单困惑度检查器 (基于N-gram)")
    print("=" * 50)
    
    checker = SimplePerplexityChecker()
    
    # 加载句子
    sentences = checker.load_sentences()
    if not sentences:
        return
    
    # 构建语言模型
    checker.build_language_model(sentences)
    
    # 选择模型类型
    print("\n📚 可用模型:")
    print("   1. Unigram (单词概率)")
    print("   2. Bigram (二元语法)")
    print("   3. Trigram (三元语法，推荐)")
    
    choice = input("\n选择模型 (1-3, 默认3): ").strip() or "3"
    model_types = {"1": "unigram", "2": "bigram", "3": "trigram"}
    model_type = model_types.get(choice, "trigram")
    
    try:
        # 计算困惑度
        results = checker.analyze_all_sentences(sentences, model_type)
        
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

if __name__ == "__main__":
    main()

