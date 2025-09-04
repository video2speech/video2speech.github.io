#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

def extract_top_words_to_list(filename, top_n=1200):
    """
    从2_2_spokenvwritten.txt文件中提取前N个词频最高的词，存储到Python列表中
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
        if len(parts) >= 5:  # 确保有足够的列
            word = parts[0].strip()
            pos = parts[1].strip()
            try:
                fr_spoken = int(parts[2].strip())
                ll = parts[3].strip()  # 对数似然值，包含符号
                fr_written = float(parts[4].strip())  # 书面语频率可能是小数
                
                words_data.append({
                    'word': word,
                    'pos': pos,
                    'fr_spoken': fr_spoken,
                    'll': ll,
                    'fr_written': fr_written
                })
            except (ValueError, IndexError) as e:
                continue
    
    # 转换为DataFrame
    df = pd.DataFrame(words_data)
    
    if df.empty:
        print("没有找到有效数据")
        return []
    
    print(f"总共找到 {len(df)} 个词")
    
    # 按口语频率排序，获取前N个
    top_words = df.nlargest(top_n, 'fr_spoken')
    
    # 提取单词列表
    word_list = top_words['word'].tolist()
    
    print(f"成功提取前 {len(word_list)} 个词频最高的词")
    print(f"前10个词: {word_list[:10]}")
    
    return word_list

def save_word_list_to_file(word_list, output_file="top_words_list.py"):
    """
    将单词列表保存到Python文件中
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 前1200个词频最高的词列表\n")
        f.write("# 从2_2_spokenvwritten.txt文件中提取，按口语频率排序\n\n")
        f.write("top_1200_words = [\n")
        
        # 每行写10个词，便于阅读
        for i in range(0, len(word_list), 10):
            batch = word_list[i:i+10]
            f.write("    " + ", ".join([f'"{word}"' for word in batch]))
            if i + 10 < len(word_list):
                f.write(",")
            f.write("\n")
        
        f.write("]\n\n")
        f.write(f"# 总共 {len(word_list)} 个词\n")
        f.write(f"# 使用方式: from {output_file.replace('.py', '')} import top_1200_words\n")
    
    print(f"单词列表已保存到: {output_file}")

if __name__ == "__main__":
    # 提取前1200个词频最高的词
    word_list = extract_top_words_to_list("2_2_spokenvwritten.txt", 1200)
    
    if word_list:
        # 保存到Python文件
        save_word_list_to_file(word_list, "top_1200_words_list.py")
        
        # 也可以直接使用列表
        print(f"\n可以直接使用的Python列表:")
        print(f"word_list = {word_list[:20]}...")  # 只显示前20个
        print(f"列表长度: {len(word_list)}")
        
        # 保存为简单的文本文件
        with open("top_1200_words_simple.txt", 'w', encoding='utf-8') as f:
            for word in word_list:
                f.write(word + "\n")
        print("单词列表也已保存到: top_1200_words_simple.txt (每行一个词)")
