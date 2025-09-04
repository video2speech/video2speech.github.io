#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re

def analyze_word_frequency(filename, top_n=1200):
    """
    从2_2_spokenvwritten.txt文件中提取前N个词频最高的词
    """
    print(f"正在分析文件: {filename}")
    print(f"提取前 {top_n} 个词频最高的词...")
    
    # 读取文件
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 解析数据
    words_data = []
    
    for line in lines[1:]:  # 跳过标题行
        line = line.strip()
        if not line:  # 跳过空行
            continue
            
        # 分割列，使用制表符分割
        parts = line.split('\t')
        if len(parts) >= 6:  # 确保有足够的列
            word = parts[1].strip()
            pos = parts[2].strip()
            try:
                fr_spoken = int(parts[3].strip())
                ll = parts[4].strip()
                fr_written = int(parts[5].strip())
                
                words_data.append({
                    'word': word,
                    'pos': pos,
                    'fr_spoken': fr_spoken,
                    'll': ll,
                    'fr_written': fr_written
                })
            except (ValueError, IndexError) as e:
                # 调试信息
                if len(words_data) < 5:  # 只打印前几个错误
                    print(f"解析错误: {line[:50]}... -> {e}")
                continue
    
    # 转换为DataFrame
    df = pd.DataFrame(words_data)
    
    if df.empty:
        print("没有找到有效数据")
        return
    
    print(f"总共找到 {len(df)} 个词")
    
    # 按口语频率排序，获取前N个
    top_words = df.nlargest(top_n, 'fr_spoken')
    
    print(f"\n前 {top_n} 个词频最高的词（按口语频率排序）:")
    print("=" * 80)
    print(f"{'排名':<6} {'单词':<15} {'词性':<8} {'口语频率':<10} {'书面语频率':<12} {'对数似然':<10}")
    print("-" * 80)
    
    for i, (_, row) in enumerate(top_words.iterrows(), 1):
        print(f"{i:<6} {row['word']:<15} {row['pos']:<8} {row['fr_spoken']:<10} {row['fr_written']:<12} {row['ll']:<10}")
    
    # 保存到文件
    output_file = f"top_{top_n}_words.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"前 {top_n} 个词频最高的词（按口语频率排序）\n")
        f.write("=" * 80 + "\n")
        f.write(f"{'排名':<6} {'单词':<15} {'词性':<8} {'口语频率':<10} {'书面语频率':<12} {'对数似然':<10}\n")
        f.write("-" * 80 + "\n")
        
        for i, (_, row) in enumerate(top_words.iterrows(), 1):
            f.write(f"{i:<6} {row['word']:<15} {row['pos']:<8} {row['fr_spoken']:<10} {row['fr_written']:<12} {row['ll']:<10}\n")
    
    print(f"\n结果已保存到: {output_file}")
    
    # 统计信息
    print(f"\n统计信息:")
    print(f"总词数: {len(df)}")
    print(f"最高口语频率: {df['fr_spoken'].max()}")
    print(f"平均口语频率: {df['fr_spoken'].mean():.2f}")
    print(f"前{top_n}个词的口语频率总和: {top_words['fr_spoken'].sum()}")
    print(f"前{top_n}个词占总口语频率的比例: {top_words['fr_spoken'].sum() / df['fr_spoken'].sum() * 100:.2f}%")

if __name__ == "__main__":
    filename = "2_2_spokenvwritten.txt"
    analyze_word_frequency(filename, 1200)
