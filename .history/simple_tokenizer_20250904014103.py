#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def tokenize_text(text):
    """
    智能分词器，可以正确处理缩略形式
    包括 n't, 're, 'm, 'll, 've, 'd, 's 等
    """
    # 定义缩略形式映射
    contractions = {
        r"can't": "can not",
        r"won't": "will not", 
        r"shan't": "shall not",
        r"n't": " not",
        r"'re": " are",
        r"'m": " am", 
        r"'ll": " will",
        r"'ve": " have",
        r"'d": " would",
        r"'s": " is"
    }
    
    # 预处理：替换缩略形式
    processed_text = text
    for contraction, expansion in contractions.items():
        processed_text = re.sub(contraction, expansion, processed_text, flags=re.IGNORECASE)
    
    # 分词：匹配单词、数字、标点符号
    # \b\w+\b 匹配完整单词
    # [^\w\s] 匹配标点符号
    tokens = re.findall(r"\b\w+\b|[^\w\s]", processed_text)
    
    return tokens

def tokenize_preserve_contractions(text):
    """
    分词但保留缩略形式
    """
    # 先标记缩略形式
    contractions = ["n't", "'re", "'m", "'ll", "'ve", "'d", "'s", "can't", "won't", "shan't"]
    
    # 在缩略形式前后添加特殊标记
    processed_text = text
    for contraction in contractions:
        pattern = re.escape(contraction)
        processed_text = re.sub(pattern, f" {contraction} ", processed_text, flags=re.IGNORECASE)
    
    # 分词
    tokens = re.findall(r"\b\w+\b|[^\w\s]|'[a-z]+", processed_text)
    
    # 清理空字符串
    tokens = [token for token in tokens if token.strip()]
    
    return tokens

def tokenize_with_frequency_list(text, frequency_list):
    """
    使用词频列表进行智能分词
    """
    # 先进行基础分词
    tokens = tokenize_preserve_contractions(text)
    
    # 处理不在词频列表中的词
    processed_tokens = []
    for token in tokens:
        if token.lower() in frequency_list:
            processed_tokens.append(token.lower())
        else:
            # 尝试分解复合词
            if "'" in token:
                # 处理缩略形式
                parts = re.split(r"(')", token)
                for part in parts:
                    if part and part.lower() in frequency_list:
                        processed_tokens.append(part.lower())
            else:
                processed_tokens.append(token.lower())
    
    return processed_tokens

def demo_tokenization():
    """
    演示分词效果
    """
    test_sentences = [
        "I can't believe you're not coming.",
        "We're going to the store, aren't we?", 
        "I'm happy that you'll be there.",
        "She's been working hard, hasn't she?",
        "They'd better hurry up!",
        "It's a beautiful day, isn't it?",
        "Don't you think it's wonderful?",
        "I've never seen anything like it."
    ]
    
    print("=== 分词方法演示 ===\n")
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"句子 {i}: {sentence}")
        print("-" * 50)
        
        # 方法1：展开缩略形式
        tokens1 = tokenize_text(sentence)
        print(f"展开缩略: {tokens1}")
        
        # 方法2：保留缩略形式
        tokens2 = tokenize_preserve_contractions(sentence)
        print(f"保留缩略: {tokens2}")
        
        print()

def test_with_frequency_list():
    """
    使用词频列表测试分词
    """
    try:
        from top_1200_words_list import top_1200_words
        
        test_sentences = [
            "I can't believe you're not coming.",
            "We're going to the store, aren't we?",
            "I'm happy that you'll be there."
        ]
        
        print("=== 使用词频列表分词 ===\n")
        
        for sentence in test_sentences:
            print(f"原句: {sentence}")
            
            tokens = tokenize_with_frequency_list(sentence, top_1200_words)
            print(f"分词: {tokens}")
            
            # 统计高频词
            high_freq_words = [token for token in tokens if token in top_1200_words]
            print(f"高频词: {high_freq_words}")
            print(f"高频词比例: {len(high_freq_words)}/{len(tokens)} = {len(high_freq_words)/len(tokens)*100:.1f}%")
            print("-" * 60)
            
    except ImportError:
        print("未找到词频列表文件")

def create_tokenizer_function():
    """
    创建一个可重用的分词函数
    """
    def tokenize(sentence, preserve_contractions=True, use_frequency_list=False):
        """
        通用分词函数
        
        参数:
        - sentence: 要分词的句子
        - preserve_contractions: 是否保留缩略形式
        - use_frequency_list: 是否使用词频列表优化
        """
        if preserve_contractions:
            tokens = tokenize_preserve_contractions(sentence)
        else:
            tokens = tokenize_text(sentence)
        
        if use_frequency_list:
            try:
                from top_1200_words_list import top_1200_words
                tokens = tokenize_with_frequency_list(sentence, top_1200_words)
            except ImportError:
                pass
        
        return tokens
    
    return tokenize

if __name__ == "__main__":
    # 演示基本分词
    demo_tokenization()
    
    # 测试词频列表分词
    test_with_frequency_list()
    
    # 创建可重用的分词器
    tokenizer = create_tokenizer_function()
    
    print("=== 可重用分词器测试 ===\n")
    test_sentence = "I can't believe you're not coming to the party!"
    
    print(f"原句: {test_sentence}")
    print(f"保留缩略: {tokenizer(test_sentence, preserve_contractions=True)}")
    print(f"展开缩略: {tokenizer(test_sentence, preserve_contractions=False)}")
    print(f"使用词频列表: {tokenizer(test_sentence, use_frequency_list=True)}")
