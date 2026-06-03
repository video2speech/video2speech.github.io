#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nltk
from nltk.tokenize import TreebankWordTokenizer
import pandas as pd
import random
import re

def download_nltk_data():
    """下载必要的NLTK数据"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("正在下载NLTK数据...")
        nltk.download('punkt')

def load_movie_lines(filename, num_samples=20):
    """从movie_lines.tsv文件中加载句子"""
    print(f"正在加载文件: {filename}")
    
    try:
        # 读取TSV文件
        df = pd.read_csv(filename, sep='\t', header=None, 
                        names=['line_id', 'character_id', 'movie_id', 'character_name', 'text'],
                        encoding='utf-8', on_bad_lines='skip')
        
        print(f"总共加载了 {len(df)} 行对话")
        
        # 清理文本数据
        df['text'] = df['text'].astype(str)
        df = df[df['text'].str.len() > 10]  # 过滤太短的句子
        df = df[df['text'].str.len() < 200]  # 过滤太长的句子
        
        print(f"过滤后剩余 {len(df)} 行有效对话")
        
        # 随机选择样本
        if len(df) > num_samples:
            sample_df = df.sample(n=num_samples, random_state=42)
        else:
            sample_df = df
        
        return sample_df['text'].tolist()
        
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []

def demonstrate_tokenization():
    """演示TreebankWordTokenizer的使用"""
    
    print("=" * 80)
    print("TreebankWordTokenizer 分词演示")
    print("=" * 80)
    
    # 初始化分词器
    tokenizer = TreebankWordTokenizer()
    
    # 演示基本用法
    print("\n🎯 基本演示:")
    print("-" * 40)
    text = "I'm sure you're not going, don't you?"
    tokens = tokenizer.tokenize(text)
    print(f"原文: {text}")
    print(f"分词结果: {tokens}")
    print(f"词数: {len(tokens)}")
    
    # 从movie_lines.tsv加载句子进行演示
    print(f"\n🎬 电影台词分词演示:")
    print("-" * 40)
    
    movie_sentences = load_movie_lines("movie_lines.tsv", num_samples=10)
    
    if not movie_sentences:
        print("无法加载电影台词，使用示例句子...")
        movie_sentences = [
            "What are you talking about?",
            "I don't know what you mean.",
            "That's absolutely incredible!",
            "You've got to be kidding me.",
            "I can't believe this is happening."
        ]
    
    for i, sentence in enumerate(movie_sentences[:10], 1):
        # 清理句子（移除特殊字符）
        clean_sentence = re.sub(r'[^\w\s\'\-\.\,\?\!\:]', '', sentence)
        clean_sentence = clean_sentence.strip()
        
        if len(clean_sentence) > 5:  # 确保句子不为空
            tokens = tokenizer.tokenize(clean_sentence)
            
            print(f"\n{i:2d}. 原文: {clean_sentence}")
            print(f"    分词: {tokens}")
            print(f"    词数: {len(tokens)}")

def analyze_tokenization_patterns():
    """分析分词模式"""
    
    print(f"\n🔍 分词模式分析:")
    print("-" * 40)
    
    tokenizer = TreebankWordTokenizer()
    
    # 测试不同类型的文本
    test_cases = [
        "I'm going to the store.",
        "Don't you think it's wonderful?",
        "She said, 'Hello, world!'",
        "The cost is $19.99.",
        "Visit www.example.com for more info.",
        "Call me at 555-123-4567.",
        "It's a state-of-the-art system.",
        "U.S.A. is a country in North America."
    ]
    
    for i, text in enumerate(test_cases, 1):
        tokens = tokenizer.tokenize(text)
        print(f"{i}. {text}")
        print(f"   → {tokens}")
        print()

def compare_with_simple_split():
    """与简单的split()方法比较"""
    
    print(f"\n⚖️  TreebankWordTokenizer vs 简单split()比较:")
    print("-" * 50)
    
    tokenizer = TreebankWordTokenizer()
    
    test_sentences = [
        "I'm not sure if you're right.",
        "The price is $29.99, isn't it?",
        "She said, 'I don't know.'"
    ]
    
    for sentence in test_sentences:
        nltk_tokens = tokenizer.tokenize(sentence)
        simple_tokens = sentence.split()
        
        print(f"原文: {sentence}")
        print(f"TreebankWordTokenizer: {nltk_tokens} ({len(nltk_tokens)} 词)")
        print(f"简单split():           {simple_tokens} ({len(simple_tokens)} 词)")
        print("-" * 50)

def tokenize_and_analyze_movie_corpus():
    """分词并分析电影语料库"""
    
    print(f"\n📊 电影语料库分词统计:")
    print("-" * 40)
    
    tokenizer = TreebankWordTokenizer()
    movie_sentences = load_movie_lines("movie_lines.tsv", num_samples=1000)
    
    if not movie_sentences:
        print("无法加载电影语料库")
        return
    
    all_tokens = []
    sentence_lengths = []
    
    for sentence in movie_sentences[:100]:  # 分析前100句
        clean_sentence = re.sub(r'[^\w\s\'\-\.\,\?\!\:]', '', sentence)
        clean_sentence = clean_sentence.strip()
        
        if len(clean_sentence) > 5:
            tokens = tokenizer.tokenize(clean_sentence)
            all_tokens.extend(tokens)
            sentence_lengths.append(len(tokens))
    
    if all_tokens:
        print(f"分析句子数: {len(sentence_lengths)}")
        print(f"总词数: {len(all_tokens)}")
        print(f"平均句长: {sum(sentence_lengths)/len(sentence_lengths):.2f} 词")
        print(f"最短句子: {min(sentence_lengths)} 词")
        print(f"最长句子: {max(sentence_lengths)} 词")
        
        # 词频统计
        from collections import Counter
        word_freq = Counter(token.lower() for token in all_tokens)
        print(f"\n前10个最常见的词:")
        for word, freq in word_freq.most_common(10):
            print(f"  {word}: {freq}")

if __name__ == "__main__":
    # 下载必要的NLTK数据
    download_nltk_data()
    
    # 运行演示
    demonstrate_tokenization()
    analyze_tokenization_patterns()
    compare_with_simple_split()
    tokenize_and_analyze_movie_corpus()
    
    print(f"\n✅ 演示完成！")
    print("TreebankWordTokenizer 的主要特点:")
    print("- 正确处理缩写 (I'm → I, 'm)")
    print("- 分离标点符号")
    print("- 处理特殊格式 (价格、网址等)")
    print("- 比简单的split()更智能")
