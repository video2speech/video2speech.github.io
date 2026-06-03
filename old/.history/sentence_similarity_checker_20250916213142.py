#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from difflib import SequenceMatcher
from itertools import combinations
import re

class SentenceSimilarityChecker:
    def __init__(self):
        self.sentences = []
        self.load_sentences()
    
    def load_sentences(self):
        """加载句子数据"""
        sentences_file = "selected_sentences_analyzer.json"
        if os.path.exists(sentences_file):
            try:
                with open(sentences_file, 'r', encoding='utf-8') as f:
                    self.sentences = json.load(f)
                print(f"📁 加载了 {len(self.sentences)} 个句子")
            except:
                print("❌ 加载句子文件失败")
                self.sentences = []
        else:
            print("❌ 未找到 selected_sentences_analyzer.json 文件")
            self.sentences = []
    
    def clean_for_comparison(self, sentence):
        """清理句子用于比较（去除标点，统一大小写）"""
        # 转小写
        sentence = sentence.lower()
        # 去除标点符号
        sentence = re.sub(r'[^\w\s]', '', sentence)
        # 去除多余空格
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        return sentence
    
    def calculate_similarity(self, sent1, sent2):
        """计算两个句子的相似度"""
        # 清理句子
        clean1 = self.clean_for_comparison(sent1)
        clean2 = self.clean_for_comparison(sent2)
        
        # 使用 SequenceMatcher 计算相似度
        similarity = SequenceMatcher(None, clean1, clean2).ratio()
        return similarity
    
    def word_overlap_similarity(self, sent1, sent2):
        """计算词汇重叠相似度"""
        words1 = set(self.clean_for_comparison(sent1).split())
        words2 = set(self.clean_for_comparison(sent2).split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def analyze_similarity(self):
        """分析所有句子对的相似度"""
        if len(self.sentences) < 2:
            print("❌ 需要至少2个句子才能进行相似度分析")
            return
        
        print(f"\n🔍 分析 {len(self.sentences)} 个句子的相似度...")
        print(f"总共需要比较 {len(self.sentences) * (len(self.sentences) - 1) // 2} 对句子")
        
        similarities = []
        
        # 计算所有句子对的相似度
        for i, j in combinations(range(len(self.sentences)), 2):
            sent1 = self.sentences[i]
            sent2 = self.sentences[j]
            
            # 字符序列相似度
            char_sim = self.calculate_similarity(sent1, sent2)
            # 词汇重叠相似度
            word_sim = self.word_overlap_similarity(sent1, sent2)
            # 综合相似度（字符相似度和词汇相似度的平均值）
            combined_sim = (char_sim + word_sim) / 2
            
            similarities.append({
                'index1': i + 1,
                'index2': j + 1,
                'sentence1': sent1,
                'sentence2': sent2,
                'char_similarity': char_sim,
                'word_similarity': word_sim,
                'combined_similarity': combined_sim
            })
        
        # 按综合相似度排序（从高到低）
        similarities.sort(key=lambda x: x['combined_similarity'], reverse=True)
        
        return similarities
    
    def display_results(self, similarities, top_n=20):
        """显示相似度分析结果"""
        print("\n" + "=" * 100)
        print("📊 句子相似度分析结果 (按相似度排序)")
        print("=" * 100)
        
        print(f"\n🔝 显示前 {min(top_n, len(similarities))} 个最相似的句子对:")
        print("-" * 100)
        
        for i, sim in enumerate(similarities[:top_n], 1):
            print(f"\n#{i:2d} 相似度: {sim['combined_similarity']:.3f} (字符: {sim['char_similarity']:.3f}, 词汇: {sim['word_similarity']:.3f})")
            print(f"    句子 {sim['index1']:2d}: {sim['sentence1']}")
            print(f"    句子 {sim['index2']:2d}: {sim['sentence2']}")
        
        # 统计信息
        print(f"\n📈 统计摘要:")
        print(f"   总句子对数: {len(similarities)}")
        high_sim = sum(1 for s in similarities if s['combined_similarity'] > 0.8)
        medium_sim = sum(1 for s in similarities if 0.5 < s['combined_similarity'] <= 0.8)
        low_sim = sum(1 for s in similarities if s['combined_similarity'] <= 0.5)
        
        print(f"   高相似度 (>0.8): {high_sim} 对 ({high_sim/len(similarities)*100:.1f}%)")
        print(f"   中相似度 (0.5-0.8): {medium_sim} 对 ({medium_sim/len(similarities)*100:.1f}%)")
        print(f"   低相似度 (≤0.5): {low_sim} 对 ({low_sim/len(similarities)*100:.1f}%)")
        
        avg_sim = sum(s['combined_similarity'] for s in similarities) / len(similarities)
        print(f"   平均相似度: {avg_sim:.3f}")
    
    def find_duplicates(self, threshold=0.9):
        """查找可能的重复句子"""
        similarities = self.analyze_similarity()
        if not similarities:
            return
        
        duplicates = [s for s in similarities if s['combined_similarity'] >= threshold]
        
        print(f"\n🔍 可能的重复句子 (相似度 ≥ {threshold}):")
        print("-" * 80)
        
        if duplicates:
            for i, dup in enumerate(duplicates, 1):
                print(f"\n#{i} 相似度: {dup['combined_similarity']:.3f}")
                print(f"   句子 {dup['index1']}: {dup['sentence1']}")
                print(f"   句子 {dup['index2']}: {dup['sentence2']}")
        else:
            print("   未发现高度相似的句子")
        
        return duplicates
    
    def save_results(self, similarities, filename="sentence_similarity_report.txt"):
        """保存相似度分析结果到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("句子相似度分析报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"总句子数: {len(self.sentences)}\n")
            f.write(f"总句子对数: {len(similarities)}\n\n")
            
            f.write("所有句子对的相似度 (按相似度排序):\n")
            f.write("-" * 50 + "\n")
            
            for i, sim in enumerate(similarities, 1):
                f.write(f"\n#{i:3d} 相似度: {sim['combined_similarity']:.3f} ")
                f.write(f"(字符: {sim['char_similarity']:.3f}, 词汇: {sim['word_similarity']:.3f})\n")
                f.write(f"      句子 {sim['index1']:2d}: {sim['sentence1']}\n")
                f.write(f"      句子 {sim['index2']:2d}: {sim['sentence2']}\n")
        
        print(f"✅ 结果已保存到 {filename}")

def main():
    checker = SentenceSimilarityChecker()
    
    if not checker.sentences:
        return
    
    print("\n🎯 句子相似度检查工具")
    print("=" * 50)
    print("💡 功能选项:")
    print("   1. 显示最相似的句子对")
    print("   2. 查找可能的重复句子")
    print("   3. 保存完整分析报告")
    print("   4. 退出")
    
    while True:
        choice = input("\n请选择功能 (1-4): ").strip()
        
        if choice == '1':
            similarities = checker.analyze_similarity()
            if similarities:
                try:
                    top_n = int(input("显示前几个最相似的句子对 (默认20): ") or "20")
                    checker.display_results(similarities, top_n)
                except ValueError:
                    checker.display_results(similarities)
        
        elif choice == '2':
            try:
                threshold = float(input("相似度阈值 (默认0.9): ") or "0.9")
                checker.find_duplicates(threshold)
            except ValueError:
                checker.find_duplicates()
        
        elif choice == '3':
            similarities = checker.analyze_similarity()
            if similarities:
                filename = input("保存文件名 (默认sentence_similarity_report.txt): ").strip()
                if not filename:
                    filename = "sentence_similarity_report.txt"
                checker.save_results(similarities, filename)
        
        elif choice == '4':
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请输入 1-4")

if __name__ == "__main__":
    main()
