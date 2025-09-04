#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

def generate_word_lists(filename, word_counts=[1200, 2000]):
    """
    从2_2_spokenvwritten.txt文件中生成不同数量的词频列表
    """
    print(f"正在分析文件: {filename}")
    
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
        return {}
    
    print(f"总共找到 {len(df)} 个词")
    
    # 按口语频率排序
    df_sorted = df.sort_values('fr_spoken', ascending=False)
    total_frequency = df_sorted['fr_spoken'].sum()
    
    print(f"总口语频率: {total_frequency:,}")
    
    results = {}
    
    for word_count in word_counts:
        print(f"\n=== 前 {word_count} 个词 ===")
        
        # 获取前N个词
        top_words = df_sorted.head(word_count)
        word_list = top_words['word'].tolist()
        
        # 计算频率覆盖
        top_frequency = top_words['fr_spoken'].sum()
        coverage_percentage = (top_frequency / total_frequency) * 100
        
        print(f"前 {word_count} 个词的频率总和: {top_frequency:,}")
        print(f"覆盖百分比: {coverage_percentage:.2f}%")
        
        # 保存到Python文件
        py_filename = f"top_{word_count}_words.py"
        with open(py_filename, 'w', encoding='utf-8') as f:
            f.write(f"# 前{word_count}个词频最高的词列表\n")
            f.write("# 从2_2_spokenvwritten.txt文件中提取，按口语频率排序\n\n")
            f.write(f"top_{word_count}_words = [\n")
            
            # 每行写10个词，便于阅读
            for i in range(0, len(word_list), 10):
                batch = word_list[i:i+10]
                f.write("    " + ", ".join([f'"{word}"' for word in batch]))
                if i + 10 < len(word_list):
                    f.write(",")
                f.write("\n")
            
            f.write("]\n\n")
            f.write(f"# 总共 {len(word_list)} 个词\n")
            f.write(f"# 覆盖口语频率: {coverage_percentage:.2f}%\n")
            f.write(f"# 使用方式: from {py_filename.replace('.py', '')} import top_{word_count}_words\n")
        
        print(f"已保存到: {py_filename}")
        
        # 保存到简单文本文件
        txt_filename = f"top_{word_count}_words_simple.txt"
        with open(txt_filename, 'w', encoding='utf-8') as f:
            for word in word_list:
                f.write(word + "\n")
        
        print(f"已保存到: {txt_filename}")
        
        # 保存详细统计信息
        stats_filename = f"top_{word_count}_words_stats.txt"
        with open(stats_filename, 'w', encoding='utf-8') as f:
            f.write(f"前 {word_count} 个词频最高的词统计信息\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"词汇数量: {len(word_list)}\n")
            f.write(f"频率总和: {top_frequency:,}\n")
            f.write(f"覆盖百分比: {coverage_percentage:.2f}%\n")
            f.write(f"平均频率: {top_frequency / len(word_list):.2f}\n")
            f.write(f"最高频率: {top_words['fr_spoken'].max():,} (词: {top_words.iloc[0]['word']})\n")
            f.write(f"最低频率: {top_words['fr_spoken'].min():,} (词: {top_words.iloc[-1]['word']})\n\n")
            
            # 前20个词的详细信息
            f.write("前20个词详细信息:\n")
            f.write("-" * 30 + "\n")
            for i, (_, row) in enumerate(top_words.head(20).iterrows(), 1):
                f.write(f"{i:2d}. {row['word']:<15} ({row['pos']:<8}) 频率: {row['fr_spoken']:>6,}\n")
        
        print(f"统计信息已保存到: {stats_filename}")
        
        results[word_count] = {
            'word_list': word_list,
            'frequency': top_frequency,
            'coverage': coverage_percentage
        }
    
    # 生成对比报告
    print(f"\n=== 对比报告 ===")
    comparison_filename = "word_lists_comparison.txt"
    with open(comparison_filename, 'w', encoding='utf-8') as f:
        f.write("词频列表对比报告\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"数据源: {filename}\n")
        f.write(f"总词汇数: {len(df):,}\n")
        f.write(f"总频率: {total_frequency:,}\n\n")
        
        for word_count in word_counts:
            result = results[word_count]
            f.write(f"前 {word_count} 个词:\n")
            f.write(f"  - 频率覆盖: {result['coverage']:.2f}%\n")
            f.write(f"  - 频率总和: {result['frequency']:,}\n")
            f.write(f"  - 平均频率: {result['frequency'] / word_count:.2f}\n\n")
        
        # 增量分析
        if len(word_counts) == 2:
            diff_count = word_counts[1] - word_counts[0]
            diff_freq = results[word_counts[1]]['frequency'] - results[word_counts[0]]['frequency']
            diff_coverage = results[word_counts[1]]['coverage'] - results[word_counts[0]]['coverage']
            
            f.write(f"从 {word_counts[0]} 到 {word_counts[1]} 词的增量分析:\n")
            f.write(f"  - 增加词数: {diff_count}\n")
            f.write(f"  - 增加频率: {diff_freq:,}\n")
            f.write(f"  - 增加覆盖率: {diff_coverage:.2f}%\n")
            f.write(f"  - 新增词的平均频率: {diff_freq / diff_count:.2f}\n")
    
    print(f"对比报告已保存到: {comparison_filename}")
    
    return results

if __name__ == "__main__":
    results = generate_word_lists("2_2_spokenvwritten.txt", [1200, 2000])
    
    print(f"\n=== 最终总结 ===")
    for word_count, result in results.items():
        print(f"前 {word_count} 个词覆盖 {result['coverage']:.2f}% 的口语频率")
