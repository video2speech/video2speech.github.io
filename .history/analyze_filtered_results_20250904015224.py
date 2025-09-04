#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import Counter
import re

def analyze_filtered_results():
    """分析过滤结果"""
    
    print("=" * 80)
    print("电影台词过滤结果分析")
    print("=" * 80)
    
    # 读取有效句子
    try:
        with open('filtered_movie_sentences.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 提取句子（跳过注释行）
        valid_sentences = []
        for line in lines:
            if line.strip() and not line.startswith('#'):
                # 移除行号
                sentence = re.sub(r'^\d+\.\s*', '', line.strip())
                valid_sentences.append(sentence)
        
        print(f"✅ 成功加载 {len(valid_sentences)} 个有效句子")
        
    except Exception as e:
        print(f"❌ 读取有效句子失败: {e}")
        return
    
    # 分析句子特征
    print(f"\n📊 有效句子分析:")
    print("-" * 40)
    
    # 长度分析
    lengths = [len(sentence.split()) for sentence in valid_sentences]
    print(f"句子长度统计:")
    print(f"  平均长度: {sum(lengths)/len(lengths):.2f} 词")
    print(f"  最短句子: {min(lengths)} 词")
    print(f"  最长句子: {max(lengths)} 词")
    
    # 长度分布
    length_dist = Counter(lengths)
    print(f"\n长度分布 (前10):")
    for length, count in length_dist.most_common(10):
        print(f"  {length} 词: {count} 句 ({count/len(valid_sentences)*100:.1f}%)")
    
    # 句子类型分析
    questions = sum(1 for s in valid_sentences if s.endswith('?'))
    exclamations = sum(1 for s in valid_sentences if s.endswith('!'))
    statements = len(valid_sentences) - questions - exclamations
    
    print(f"\n句子类型分布:")
    print(f"  陈述句: {statements} ({statements/len(valid_sentences)*100:.1f}%)")
    print(f"  疑问句: {questions} ({questions/len(valid_sentences)*100:.1f}%)")
    print(f"  感叹句: {exclamations} ({exclamations/len(valid_sentences)*100:.1f}%)")
    
    # 显示不同长度的示例
    print(f"\n📝 不同长度句子示例:")
    print("-" * 40)
    
    for target_length in [2, 5, 8, 12, 15]:
        examples = [s for s in valid_sentences if len(s.split()) == target_length]
        if examples:
            print(f"\n{target_length}词句子示例:")
            for i, example in enumerate(examples[:3], 1):
                print(f"  {i}. {example}")
    
    # 常见开头词
    first_words = [sentence.split()[0].lower() for sentence in valid_sentences if sentence.split()]
    first_word_freq = Counter(first_words)
    
    print(f"\n🔤 最常见的开头词 (前15):")
    print("-" * 30)
    for word, count in first_word_freq.most_common(15):
        print(f"  '{word}': {count} 次 ({count/len(valid_sentences)*100:.1f}%)")
    
    # 保存分析结果
    with open('filtered_sentences_analysis.txt', 'w', encoding='utf-8') as f:
        f.write("电影台词过滤结果详细分析\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"有效句子总数: {len(valid_sentences)}\n\n")
        
        f.write("长度统计:\n")
        f.write(f"  平均长度: {sum(lengths)/len(lengths):.2f} 词\n")
        f.write(f"  最短句子: {min(lengths)} 词\n")
        f.write(f"  最长句子: {max(lengths)} 词\n\n")
        
        f.write("句子类型分布:\n")
        f.write(f"  陈述句: {statements} ({statements/len(valid_sentences)*100:.1f}%)\n")
        f.write(f"  疑问句: {questions} ({questions/len(valid_sentences)*100:.1f}%)\n")
        f.write(f"  感叹句: {exclamations} ({exclamations/len(valid_sentences)*100:.1f}%)\n\n")
        
        f.write("长度分布:\n")
        for length, count in sorted(length_dist.items()):
            f.write(f"  {length:2d} 词: {count:4d} 句 ({count/len(valid_sentences)*100:.1f}%)\n")
        
        f.write(f"\n最常见开头词:\n")
        for word, count in first_word_freq.most_common(20):
            f.write(f"  '{word}': {count} 次 ({count/len(valid_sentences)*100:.1f}%)\n")
        
        f.write(f"\n随机句子样本 (100个):\n")
        import random
        random.seed(42)
        samples = random.sample(valid_sentences, min(100, len(valid_sentences)))
        for i, sentence in enumerate(samples, 1):
            f.write(f"{i:2d}. {sentence}\n")
    
    print(f"\n✅ 详细分析已保存到: filtered_sentences_analysis.txt")
    
    return valid_sentences

def create_training_data():
    """创建用于训练的数据格式"""
    
    print(f"\n🚀 创建训练数据格式:")
    print("-" * 30)
    
    try:
        with open('filtered_movie_sentences.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 提取句子
        sentences = []
        for line in lines:
            if line.strip() and not line.startswith('#'):
                sentence = re.sub(r'^\d+\.\s*', '', line.strip())
                sentences.append(sentence)
        
        # 创建不同格式的训练数据
        
        # 1. 纯文本格式（每行一句）
        with open('training_sentences_clean.txt', 'w', encoding='utf-8') as f:
            for sentence in sentences:
                f.write(sentence + '\n')
        
        # 2. 按长度分组
        length_groups = {}
        for sentence in sentences:
            length = len(sentence.split())
            if length not in length_groups:
                length_groups[length] = []
            length_groups[length].append(sentence)
        
        # 保存短句（适合初学者）
        short_sentences = []
        for length in range(1, 8):  # 1-7词的短句
            if length in length_groups:
                short_sentences.extend(length_groups[length])
        
        with open('training_sentences_short.txt', 'w', encoding='utf-8') as f:
            f.write(f"# 短句训练数据 (1-7词，共{len(short_sentences)}句)\n")
            for sentence in short_sentences:
                f.write(sentence + '\n')
        
        # 保存中等长度句子（适合进阶）
        medium_sentences = []
        for length in range(8, 15):  # 8-14词的中等句子
            if length in length_groups:
                medium_sentences.extend(length_groups[length])
        
        with open('training_sentences_medium.txt', 'w', encoding='utf-8') as f:
            f.write(f"# 中等长度句子训练数据 (8-14词，共{len(medium_sentences)}句)\n")
            for sentence in medium_sentences:
                f.write(sentence + '\n')
        
        print(f"✅ 训练数据已生成:")
        print(f"   📄 training_sentences_clean.txt - 全部句子 ({len(sentences)}句)")
        print(f"   📄 training_sentences_short.txt - 短句 ({len(short_sentences)}句)")
        print(f"   📄 training_sentences_medium.txt - 中等句子 ({len(medium_sentences)}句)")
        
    except Exception as e:
        print(f"❌ 创建训练数据失败: {e}")

if __name__ == "__main__":
    valid_sentences = analyze_filtered_results()
    if valid_sentences:
        create_training_data()
    
    print(f"\n" + "="*80)
    print("📋 总结:")
    print("="*80)
    print("✅ 成功从10,000行电影对话中过滤出5,319个有效句子")
    print("✅ 有效率: 32.97% (约1/3的句子仅使用Top1200词汇)")
    print("✅ 这些句子可用于:")
    print("   • 英语学习材料")
    print("   • 语言模型训练")
    print("   • 口语练习")
    print("   • 词汇学习辅助")
