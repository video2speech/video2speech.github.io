#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import nltk
from nltk.tokenize import word_tokenize

# 下载必要的NLTK数据（首次运行需要）
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("正在下载NLTK数据...")
    nltk.download('punkt')

def tokenize_with_nltk(text):
    """
    使用NLTK的word_tokenize进行分词
    这种方法可以正确处理缩略形式
    """
    return word_tokenize(text)

def tokenize_with_regex(text):
    """
    使用正则表达式进行分词
    自定义处理缩略形式
    """
    # 定义缩略形式模式
    contractions = {
        r"n't": " not",
        r"'re": " are", 
        r"'m": " am",
        r"'ll": " will",
        r"'ve": " have",
        r"'d": " would",
        r"'s": " is",
        r"can't": "cannot",
        r"won't": "will not",
        r"shan't": "shall not"
    }
    
    # 替换缩略形式
    for contraction, expansion in contractions.items():
        text = re.sub(contraction, expansion, text)
    
    # 分词：匹配单词、数字、标点符号
    tokens = re.findall(r"\b\w+\b|[^\w\s]", text)
    return tokens

def tokenize_simple(text):
    """
    简单的空格分词
    """
    return text.split()

def demo_tokenization():
    """
    演示不同的分词方法
    """
    # 测试句子
    test_sentences = [
        "I can't believe you're not coming.",
        "We're going to the store, aren't we?",
        "I'm happy that you'll be there.",
        "She's been working hard, hasn't she?",
        "They'd better hurry up!",
        "It's a beautiful day, isn't it?"
    ]
    
    print("=== 分词方法对比 ===\n")
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"句子 {i}: {sentence}")
        print("-" * 50)
        
        # NLTK分词
        nltk_tokens = tokenize_with_nltk(sentence)
        print(f"NLTK分词:     {nltk_tokens}")
        
        # 正则表达式分词
        regex_tokens = tokenize_with_regex(sentence)
        print(f"正则分词:     {regex_tokens}")
        
        # 简单分词
        simple_tokens = tokenize_simple(sentence)
        print(f"简单分词:     {simple_tokens}")
        
        print()

def create_advanced_tokenizer():
    """
    创建高级分词器，结合我们的词频数据
    """
    from top_1200_words_list import top_1200_words
    
    def advanced_tokenize(text):
        """
        高级分词器：
        1. 使用NLTK进行基础分词
        2. 处理特殊缩略形式
        3. 保留在词频列表中的词
        """
        # 基础分词
        tokens = word_tokenize(text.lower())
        
        # 处理特殊缩略形式
        processed_tokens = []
        for token in tokens:
            if token in ["n't", "'re", "'m", "'ll", "'ve", "'d", "'s"]:
                processed_tokens.append(token)
            elif token in top_1200_words:
                processed_tokens.append(token)
            else:
                # 如果不在高频词列表中，尝试分解
                if "'" in token:
                    # 处理缩略形式
                    parts = re.split(r"(')", token)
                    for part in parts:
                        if part and part in top_1200_words:
                            processed_tokens.append(part)
                else:
                    processed_tokens.append(token)
        
        return processed_tokens
    
    return advanced_tokenize

def test_with_movie_data():
    """
    使用电影数据测试分词效果
    """
    print("=== 使用电影数据测试分词 ===\n")
    
    # 读取电影数据的一小部分
    try:
        with open('movie_lines.tsv', 'r', encoding='utf-8') as f:
            lines = f.readlines()[:5]  # 只读前5行
        
        advanced_tokenizer = create_advanced_tokenizer()
        
        for i, line in enumerate(lines, 1):
            if '\t' in line:
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    text = parts[4]  # 对话内容
                    print(f"原始文本 {i}: {text}")
                    
                    # 使用高级分词器
                    tokens = advanced_tokenizer(text)
                    print(f"分词结果: {tokens}")
                    
                    # 统计高频词
                    from top_1200_words_list import top_1200_words
                    high_freq_words = [token for token in tokens if token in top_1200_words]
                    print(f"高频词: {high_freq_words}")
                    print("-" * 60)
                    
    except FileNotFoundError:
        print("未找到movie_lines.tsv文件")

if __name__ == "__main__":
    # 演示基本分词方法
    demo_tokenization()
    
    # 测试电影数据
    test_with_movie_data()
