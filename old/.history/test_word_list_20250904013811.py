#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 导入生成的单词列表
from top_1200_words_list import top_1200_words

def test_word_list():
    """测试单词列表的功能"""
    
    print("=== 前1200个词频最高的词列表测试 ===")
    print(f"列表长度: {len(top_1200_words)}")
    print(f"前10个词: {top_1200_words[:10]}")
    print(f"最后10个词: {top_1200_words[-10:]}")
    
    # 测试搜索功能
    test_words = ['the', 'hello', 'computer', 'beautiful']
    print(f"\n=== 搜索测试 ===")
    for word in test_words:
        if word in top_1200_words:
            index = top_1200_words.index(word)
            print(f"'{word}' 在列表中，排名: {index + 1}")
        else:
            print(f"'{word}' 不在前1200个词中")
    
    # 统计词性
    print(f"\n=== 词性统计 ===")
    # 这里我们无法直接统计词性，因为列表只包含单词
    # 但可以统计一些基本特征
    punctuation_chars = "'*~/"
    words_with_punctuation = [word for word in top_1200_words if any(c in word for c in punctuation_chars)]
    print(f"包含标点符号的词: {words_with_punctuation}")
    
    # 按长度分组
    length_groups = {}
    for word in top_1200_words:
        length = len(word)
        if length not in length_groups:
            length_groups[length] = 0
        length_groups[length] += 1
    
    print(f"\n=== 单词长度分布 ===")
    for length in sorted(length_groups.keys()):
        print(f"长度 {length}: {length_groups[length]} 个词")
    
    # 导出为其他格式
    print(f"\n=== 导出功能 ===")
    
    # 导出为JSON
    import json
    with open('top_1200_words.json', 'w', encoding='utf-8') as f:
        json.dump(top_1200_words, f, ensure_ascii=False, indent=2)
    print("已导出为JSON格式: top_1200_words.json")
    
    # 导出为CSV
    import csv
    with open('top_1200_words.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['rank', 'word'])
        for i, word in enumerate(top_1200_words, 1):
            writer.writerow([i, word])
    print("已导出为CSV格式: top_1200_words.csv")

if __name__ == "__main__":
    test_word_list()
