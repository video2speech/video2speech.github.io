#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nltk.tokenize import TreebankWordTokenizer
import pandas as pd
import re
from collections import Counter

def load_sample_movie_lines(filename, num_samples=50):
    """加载电影台词样本"""
    try:
        df = pd.read_csv(filename, sep='\t', header=None, 
                        names=['line_id', 'character_id', 'movie_id', 'character_name', 'text'],
                        encoding='utf-8', on_bad_lines='skip')
        
        # 清理和过滤
        df['text'] = df['text'].astype(str)
        df = df[df['text'].str.len().between(20, 150)]  # 选择中等长度的句子
        
        # 选择包含常见缩写的句子
        contractions = ["'m", "'re", "'ve", "'ll", "'d", "n't", "'s"]
        mask = df['text'].str.contains('|'.join(contractions), case=False, na=False)
        contraction_sentences = df[mask].head(num_samples//2)
        
        # 选择包含标点的句子  
        punctuation_mask = df['text'].str.contains('[,;:!?]', na=False)
        punctuation_sentences = df[punctuation_mask].head(num_samples//2)
        
        # 合并样本
        samples = pd.concat([contraction_sentences, punctuation_sentences]).drop_duplicates()
        
        return samples['text'].tolist()[:num_samples]
        
    except Exception as e:
        print(f"加载文件出错: {e}")
        return []

def demonstrate_advanced_tokenization():
    """高级分词演示"""
    
    print("=" * 80)
    print("🎬 电影台词 TreebankWordTokenizer 高级分词演示")
    print("=" * 80)
    
    tokenizer = TreebankWordTokenizer()
    
    # 加载电影台词
    movie_lines = load_sample_movie_lines("movie_lines.tsv", 20)
    
    if not movie_lines:
        # 如果加载失败，使用预设的示例
        movie_lines = [
            "I'm telling you, we're gonna be rich!",
            "Don't you dare leave me here alone.",
            "What's the matter? You look upset.",
            "I can't believe you'd do this to me.",
            "She's the most beautiful woman I've ever seen.",
            "You're absolutely right about that.",
            "I won't let them hurt you, I promise.",
            "That's not what I meant, and you know it.",
            "We've been through this before, haven't we?",
            "I'd rather die than give up now."
        ]
    
    print(f"\n📝 分词详细分析 (共{len(movie_lines)}个句子):")
    print("-" * 80)
    
    total_words_treebank = 0
    total_words_simple = 0
    
    for i, sentence in enumerate(movie_lines, 1):
        # 清理句子
        clean_sentence = re.sub(r'[^\w\s\'\-\.\,\?\!\:\;]', '', sentence).strip()
        
        if len(clean_sentence) < 10:
            continue
            
        # TreebankWordTokenizer分词
        treebank_tokens = tokenizer.tokenize(clean_sentence)
        
        # 简单split分词
        simple_tokens = clean_sentence.split()
        
        total_words_treebank += len(treebank_tokens)
        total_words_simple += len(simple_tokens)
        
        print(f"\n{i:2d}. 原句: {clean_sentence}")
        print(f"    TreeBank: {treebank_tokens}")
        print(f"    简单split: {simple_tokens}")
        print(f"    词数对比: TreeBank({len(treebank_tokens)}) vs Split({len(simple_tokens)})")
        
        # 分析差异
        if len(treebank_tokens) != len(simple_tokens):
            print(f"    💡 差异分析:")
            # 找出TreeBank多分出的词
            treebank_set = set(treebank_tokens)
            simple_set = set(simple_tokens)
            
            if len(treebank_tokens) > len(simple_tokens):
                print(f"       TreeBank更细致地处理了缩写和标点")
                # 显示缩写拆分
                contractions_found = [token for token in treebank_tokens if token in ["'m", "'re", "'ve", "'ll", "'d", "n't", "'s"]]
                if contractions_found:
                    print(f"       发现缩写: {contractions_found}")
                
                # 显示标点分离
                punctuation_found = [token for token in treebank_tokens if token in ".,!?;:"]
                if punctuation_found:
                    print(f"       分离标点: {punctuation_found}")

def analyze_tokenization_benefits():
    """分析分词的好处"""
    
    print(f"\n🔍 TreebankWordTokenizer 的优势分析:")
    print("-" * 50)
    
    tokenizer = TreebankWordTokenizer()
    
    test_cases = [
        {
            "text": "I'm not gonna lie, you're absolutely right!",
            "focus": "缩写处理"
        },
        {
            "text": "The price is $19.99, isn't it?",
            "focus": "价格和标点"
        },
        {
            "text": "Visit our website: www.example.com today!",
            "focus": "网址和标点"
        },
        {
            "text": "Call us at (555) 123-4567 for help.",
            "focus": "电话号码"
        },
        {
            "text": "It's a state-of-the-art system, don't you think?",
            "focus": "连字符和缩写"
        }
    ]
    
    for case in test_cases:
        text = case["text"]
        focus = case["focus"]
        
        treebank_tokens = tokenizer.tokenize(text)
        simple_tokens = text.split()
        
        print(f"\n📌 重点: {focus}")
        print(f"原文: {text}")
        print(f"TreeBank ({len(treebank_tokens)}词): {treebank_tokens}")
        print(f"简单split ({len(simple_tokens)}词): {simple_tokens}")

def word_frequency_analysis():
    """词频分析"""
    
    print(f"\n📊 基于分词的词频分析:")
    print("-" * 40)
    
    tokenizer = TreebankWordTokenizer()
    movie_lines = load_sample_movie_lines("movie_lines.tsv", 100)
    
    if not movie_lines:
        return
    
    # 收集所有词汇
    all_tokens = []
    for line in movie_lines:
        clean_line = re.sub(r'[^\w\s\'\-\.\,\?\!\:\;]', '', line).strip()
        if len(clean_line) > 5:
            tokens = tokenizer.tokenize(clean_line.lower())
            all_tokens.extend(tokens)
    
    # 词频统计
    word_freq = Counter(all_tokens)
    
    print(f"总词数: {len(all_tokens)}")
    print(f"不重复词数: {len(word_freq)}")
    
    print(f"\n前20个最常见的词:")
    for i, (word, freq) in enumerate(word_freq.most_common(20), 1):
        print(f"{i:2d}. '{word}': {freq} 次")
    
    # 分析缩写词频
    contractions = [word for word in word_freq.keys() if word in ["'m", "'re", "'ve", "'ll", "'d", "n't", "'s"]]
    if contractions:
        print(f"\n缩写词频统计:")
        for contraction in contractions:
            print(f"   '{contraction}': {word_freq[contraction]} 次")

def practical_applications():
    """实际应用示例"""
    
    print(f"\n🚀 实际应用场景:")
    print("-" * 30)
    
    tokenizer = TreebankWordTokenizer()
    
    print("1. 文本预处理 (用于机器学习)")
    print("2. 搜索引擎查询处理")
    print("3. 自然语言处理管道")
    print("4. 文本统计和分析")
    
    # 示例：文本清理管道
    sample_text = "I'm really excited about this project! Don't you think it's amazing?"
    
    print(f"\n💡 文本处理管道示例:")
    print(f"原文: {sample_text}")
    
    # 步骤1: 分词
    tokens = tokenizer.tokenize(sample_text)
    print(f"1. 分词: {tokens}")
    
    # 步骤2: 转小写
    lower_tokens = [token.lower() for token in tokens]
    print(f"2. 转小写: {lower_tokens}")
    
    # 步骤3: 过滤标点
    word_tokens = [token for token in lower_tokens if token.isalnum() or token in ["'m", "'re", "'ve", "'ll", "'d", "n't", "'s"]]
    print(f"3. 过滤标点: {word_tokens}")
    
    # 步骤4: 词频统计
    freq = Counter(word_tokens)
    print(f"4. 词频: {dict(freq)}")

if __name__ == "__main__":
    demonstrate_advanced_tokenization()
    analyze_tokenization_benefits()
    word_frequency_analysis()
    practical_applications()
    
    print(f"\n" + "="*80)
    print("✅ 总结: TreebankWordTokenizer vs 简单split()")
    print("="*80)
    print("TreebankWordTokenizer 优势:")
    print("✓ 正确拆分缩写 (I'm → ['I', \"'m\"])")
    print("✓ 分离标点符号 (Hello! → ['Hello', '!'])")
    print("✓ 保持特殊格式 (URLs, 电话号码等)")
    print("✓ 更准确的词数统计")
    print("✓ 适合NLP下游任务")
    print("\n简单split()的局限:")
    print("✗ 无法处理缩写")
    print("✗ 标点粘连在词上")
    print("✗ 词数统计不准确")
    print("✗ 不适合精确的文本分析")
