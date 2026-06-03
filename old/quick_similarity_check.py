#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
from difflib import SequenceMatcher
from itertools import combinations
import re

def load_sentences():
    """加载句子数据"""
    sentences_file = "selected_sentences_analyzer.json"
    if os.path.exists(sentences_file):
        try:
            with open(sentences_file, 'r', encoding='utf-8') as f:
                sentences = json.load(f)
            print(f"📁 加载了 {len(sentences)} 个句子")
            return sentences
        except:
            print("❌ 加载句子文件失败")
            return []
    else:
        print("❌ 未找到 selected_sentences_analyzer.json 文件")
        return []

def clean_for_comparison(sentence):
    """清理句子用于比较"""
    sentence = sentence.lower()
    sentence = re.sub(r'[^\w\s]', '', sentence)
    sentence = re.sub(r'\s+', ' ', sentence).strip()
    return sentence

def calculate_similarity(sent1, sent2):
    """计算两个句子的相似度"""
    clean1 = clean_for_comparison(sent1)
    clean2 = clean_for_comparison(sent2)
    
    # 字符序列相似度
    char_sim = SequenceMatcher(None, clean1, clean2).ratio()
    
    # 词汇重叠相似度
    words1 = set(clean1.split())
    words2 = set(clean2.split())
    
    if not words1 and not words2:
        word_sim = 1.0
    elif not words1 or not words2:
        word_sim = 0.0
    else:
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        word_sim = intersection / union if union > 0 else 0.0
    
    # 综合相似度
    combined_sim = (char_sim + word_sim) / 2
    return char_sim, word_sim, combined_sim

def main():
    sentences = load_sentences()
    
    if len(sentences) < 2:
        print("❌ 需要至少2个句子才能进行相似度分析")
        return
    
    print(f"\n🔍 分析 {len(sentences)} 个句子的相似度...")
    total_pairs = len(sentences) * (len(sentences) - 1) // 2
    print(f"总共需要比较 {total_pairs} 对句子")
    
    similarities = []
    
    # 计算所有句子对的相似度
    for i, j in combinations(range(len(sentences)), 2):
        sent1 = sentences[i]
        sent2 = sentences[j]
        
        char_sim, word_sim, combined_sim = calculate_similarity(sent1, sent2)
        
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
    
    # 显示结果
    print("\n" + "=" * 100)
    print("📊 句子相似度分析结果 (按相似度排序)")
    print("=" * 100)
    
    # 显示前20个最相似的句子对
    print(f"\n🔝 前 20 个最相似的句子对:")
    print("-" * 100)
    
    for i, sim in enumerate(similarities[:20], 1):
        print(f"\n#{i:2d} 相似度: {sim['combined_similarity']:.3f} (字符: {sim['char_similarity']:.3f}, 词汇: {sim['word_similarity']:.3f})")
        print(f"    句子 {sim['index1']:2d}: {sim['sentence1']}")
        print(f"    句子 {sim['index2']:2d}: {sim['sentence2']}")
    
    # 查找高度相似的句子（可能是重复）
    print(f"\n🔍 高度相似的句子 (相似度 ≥ 0.8):")
    print("-" * 80)
    
    high_similarity = [s for s in similarities if s['combined_similarity'] >= 0.8]
    if high_similarity:
        for i, sim in enumerate(high_similarity, 1):
            print(f"\n#{i} 相似度: {sim['combined_similarity']:.3f}")
            print(f"   句子 {sim['index1']}: {sim['sentence1']}")
            print(f"   句子 {sim['index2']}: {sim['sentence2']}")
    else:
        print("   未发现高度相似的句子")
    
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
    
    # 保存结果
    print(f"\n💾 保存详细结果到文件...")
    with open("sentence_similarity_report.txt", 'w', encoding='utf-8') as f:
        f.write("句子相似度分析报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"总句子数: {len(sentences)}\n")
        f.write(f"总句子对数: {len(similarities)}\n\n")
        
        f.write("所有句子对的相似度 (按相似度排序):\n")
        f.write("-" * 50 + "\n")
        
        for i, sim in enumerate(similarities, 1):
            f.write(f"\n#{i:3d} 相似度: {sim['combined_similarity']:.3f} ")
            f.write(f"(字符: {sim['char_similarity']:.3f}, 词汇: {sim['word_similarity']:.3f})\n")
            f.write(f"      句子 {sim['index1']:2d}: {sim['sentence1']}\n")
            f.write(f"      句子 {sim['index2']:2d}: {sim['sentence2']}\n")
    
    print("✅ 详细结果已保存到 sentence_similarity_report.txt")

if __name__ == "__main__":
    main()


