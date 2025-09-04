#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
比较两个词汇列表：
1. 150词基础列表 (materials/150_words_list.txt)
2. 频率统计中出现的词汇 (filtered_sentences_150_words_frequency.txt)

找出在列表1中但不在列表2中的词汇
"""

import re

def read_150_words_list(file_path):
    """读取150词基础列表"""
    words = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    words.append(word)
        return words
    except Exception as e:
        print(f"读取150词列表时出错: {e}")
        return []

def extract_words_from_frequency_file(file_path):
    """从频率统计文件中提取词汇"""
    words = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 匹配形如 "    1. you                     1710    8.03%" 的行
                match = re.match(r'\s*\d+\.\s+([^\s]+)', line)
                if match:
                    word = match.group(1)
                    words.add(word)
        return words
    except Exception as e:
        print(f"读取频率文件时出错: {e}")
        return set()

def find_missing_words(list1, list2):
    """找出在list1中但不在list2中的词汇"""
    set1 = set(list1)
    set2 = set(list2)
    missing = set1 - set2
    return sorted(missing)

def main():
    # 文件路径
    words_150_file = "materials/150_words_list.txt"
    frequency_file = "filtered_sentences_150_words_frequency.txt"
    
    print("=" * 60)
    print("词汇列表比较分析")
    print("=" * 60)
    
    # 读取150词列表
    print(f"\n1. 读取150词基础列表: {words_150_file}")
    words_150 = read_150_words_list(words_150_file)
    print(f"   共找到 {len(words_150)} 个词汇")
    
    # 读取频率统计中的词汇
    print(f"\n2. 读取频率统计文件: {frequency_file}")
    frequency_words = extract_words_from_frequency_file(frequency_file)
    print(f"   共找到 {len(frequency_words)} 个词汇")
    
    # 找出缺失的词汇
    print(f"\n3. 查找在150词列表中但不在频率统计中的词汇...")
    missing_words = find_missing_words(words_150, frequency_words)
    
    print(f"\n" + "=" * 60)
    print("结果分析")
    print("=" * 60)
    print(f"150词列表总数: {len(words_150)}")
    print(f"频率统计词汇数: {len(frequency_words)}")
    print(f"缺失词汇数: {len(missing_words)}")
    
    if missing_words:
        print(f"\n在150词列表中但不在频率统计中的词汇 ({len(missing_words)}个):")
        print("-" * 40)
        for i, word in enumerate(missing_words, 1):
            print(f"{i:3d}. {word}")
    else:
        print("\n✓ 所有150词都在频率统计中出现了！")
    
    # 显示一些统计信息
    print(f"\n" + "=" * 60)
    print("详细对比")
    print("=" * 60)
    
    # 显示150词列表的前10个词汇
    print("\n150词列表前10个词汇:")
    for i, word in enumerate(words_150[:10], 1):
        status = "✓" if word in frequency_words else "✗"
        print(f"{i:2d}. {word:15s} {status}")
    
    # 显示频率统计的前10个词汇
    print(f"\n频率统计前10个词汇:")
    frequency_list = sorted(frequency_words)
    for i, word in enumerate(frequency_list[:10], 1):
        status = "✓" if word in words_150 else "✗"
        print(f"{i:2d}. {word:15s} {status}")

if __name__ == "__main__":
    main()
