#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nltk.tokenize import TreebankWordTokenizer

def filter_sentences_4plus_words():
    """筛选≥4词的句子，去重，生成简单列表"""
    
    print("筛选≥4词句子并去重...")
    
    # 读取句子文件
    with open('sentences_expanded_vocab.txt', 'r', encoding='utf-8') as f:
        sentences = [line.strip() for line in f.readlines() if line.strip()]
    
    tokenizer = TreebankWordTokenizer()
    filtered_sentences = []
    seen_sentences = set()  # 用于去重
    
    for sentence in sentences:
        # 分词并只计算非标点符号的词汇
        tokens = tokenizer.tokenize(sentence)
        words = [token for token in tokens if token not in ".,!?;:()\"'-"]
        
        # 只保留≥4词的句子
        if len(words) >= 4:
            # 去重（转换为小写进行比较，但保留原始格式）
            sentence_lower = sentence.lower()
            if sentence_lower not in seen_sentences:
                seen_sentences.add(sentence_lower)
                filtered_sentences.append(sentence)
    
    print(f'筛选前: {len(sentences)} 个句子')
    print(f'≥4词句子: {len(filtered_sentences)} 个')
    
    # 保存为简单列表（无序号）
    with open('sentences_4plus_words.txt', 'w', encoding='utf-8') as f:
        for sentence in filtered_sentences:
            f.write(sentence + '\n')
    
    print(f'✅ 已生成 sentences_4plus_words.txt')
    
    # 显示前10个句子作为样本
    print(f'\n📝 前10个句子样本:')
    for i, sentence in enumerate(filtered_sentences[:10], 1):
        print(f'   {sentence}')
    
    return filtered_sentences

if __name__ == "__main__":
    filtered_sentences = filter_sentences_4plus_words()
