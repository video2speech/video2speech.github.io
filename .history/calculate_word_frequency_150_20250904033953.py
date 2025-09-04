#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nltk.tokenize import TreebankWordTokenizer
from collections import Counter
import csv

def calculate_word_frequency():
    """计算 filtered_sentences_150_words_clean.txt 中所有词的词频"""
    
    print("=" * 80)
    print("📊 计算 filtered_sentences_150_words_clean.txt 词频统计")
    print("=" * 80)
    
    # 读取句子文件
    try:
        with open('filtered_sentences_150_words_clean.txt', 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"✅ 成功读取 {len(sentences):,} 个句子")
        
    except FileNotFoundError:
        print("❌ 未找到文件 filtered_sentences_150_words_clean.txt")
        return
    
    # 初始化分词器和计数器
    tokenizer = TreebankWordTokenizer()
    word_counts = Counter()
    total_tokens = 0
    total_words = 0
    
    print("🔄 正在分析词频...")
    
    # 处理每个句子
    for sentence in sentences:
        # 分词
        tokens = tokenizer.tokenize(sentence)
        total_tokens += len(tokens)
        
        # 分析每个token
        for token in tokens:
            # 只计算字母词汇，忽略纯标点符号
            if token.isalpha():
                word_counts[token.lower()] += 1
                total_words += 1
    
    print(f"✅ 分析完成！")
    print(f"   总token数: {total_tokens:,}")
    print(f"   总词汇数: {total_words:,} (不包括标点符号)")
    print(f"   唯一词汇数: {len(word_counts):,}")
    
    # 按频率排序
    sorted_words = word_counts.most_common()
    
    # 计算累积频率
    cumulative_freq = 0
    word_stats = []
    
    for rank, (word, count) in enumerate(sorted_words, 1):
        cumulative_freq += count
        percentage = (count / total_words) * 100
        cumulative_percentage = (cumulative_freq / total_words) * 100
        
        word_stats.append({
            'rank': rank,
            'word': word,
            'count': count,
            'percentage': percentage,
            'cumulative_count': cumulative_freq,
            'cumulative_percentage': cumulative_percentage
        })
    
    # 保存详细结果到TXT文件
    output_txt = 'filtered_sentences_150_words_frequency.txt'
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write("filtered_sentences_150_words_clean.txt 词频统计报告\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"数据源: filtered_sentences_150_words_clean.txt\n")
        f.write(f"句子总数: {len(sentences):,}\n")
        f.write(f"总词汇数: {total_words:,} (不包括标点符号)\n")
        f.write(f"唯一词汇数: {len(word_counts):,}\n")
        f.write(f"平均每句词数: {total_words/len(sentences):.2f}\n\n")
        
        f.write("排名  词汇        频次    占比      累积频次  累积占比\n")
        f.write("-" * 70 + "\n")
        
        for stats in word_stats:
            f.write(f"{stats['rank']:3d}. {stats['word']:<12} {stats['count']:4d} {stats['percentage']:6.2f}%  "
                   f"{stats['cumulative_count']:6d}  {stats['cumulative_percentage']:6.2f}%\n")
    
    # 保存CSV格式
    output_csv = 'filtered_sentences_150_words_frequency.csv'
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['排名', '词汇', '频次', '占比(%)', '累积频次', '累积占比(%)'])
        
        for stats in word_stats:
            writer.writerow([
                stats['rank'],
                stats['word'],
                stats['count'],
                f"{stats['percentage']:.2f}",
                stats['cumulative_count'],
                f"{stats['cumulative_percentage']:.2f}"
            ])
    
    print(f"💾 结果已保存:")
    print(f"   📄 {output_txt} - 详细文本报告")
    print(f"   📊 {output_csv} - CSV格式数据")
    
    # 显示统计摘要
    print(f"\n📈 词频统计摘要:")
    print(f"   最高频词汇: '{sorted_words[0][0]}' ({sorted_words[0][1]}次, {sorted_words[0][1]/total_words*100:.2f}%)")
    
    # 显示前20高频词
    print(f"\n🔝 前20高频词汇:")
    for i, (word, count) in enumerate(sorted_words[:20], 1):
        percentage = (count / total_words) * 100
        print(f"   {i:2d}. {word:<12} {count:4d}次 ({percentage:5.2f}%)")
    
    # 频率分布分析
    freq_1 = sum(1 for count in word_counts.values() if count == 1)
    freq_2_5 = sum(1 for count in word_counts.values() if 2 <= count <= 5)
    freq_6_10 = sum(1 for count in word_counts.values() if 6 <= count <= 10)
    freq_11_20 = sum(1 for count in word_counts.values() if 11 <= count <= 20)
    freq_21_plus = sum(1 for count in word_counts.values() if count > 20)
    
    print(f"\n📊 词频分布:")
    print(f"   出现1次: {freq_1}个词 ({freq_1/len(word_counts)*100:.1f}%)")
    print(f"   出现2-5次: {freq_2_5}个词 ({freq_2_5/len(word_counts)*100:.1f}%)")
    print(f"   出现6-10次: {freq_6_10}个词 ({freq_6_10/len(word_counts)*100:.1f}%)")
    print(f"   出现11-20次: {freq_11_20}个词 ({freq_11_20/len(word_counts)*100:.1f}%)")
    print(f"   出现>20次: {freq_21_plus}个词 ({freq_21_plus/len(word_counts)*100:.1f}%)")
    
    # 覆盖率分析
    print(f"\n🎯 覆盖率分析:")
    coverage_points = [10, 20, 30, 50, 80, 100]
    for point in coverage_points:
        if point <= len(sorted_words):
            coverage = sum(count for _, count in sorted_words[:point])
            coverage_pct = (coverage / total_words) * 100
            print(f"   前{point:3d}个高频词覆盖: {coverage:5d}词次 ({coverage_pct:5.1f}%)")
    
    # 与150词汇表对比
    print(f"\n🔍 与150词汇表对比:")
    try:
        with open('materials/150_words_list.txt', 'r', encoding='utf-8') as f:
            vocab_150 = set(word.strip().lower() for word in f.readlines() if word.strip())
        
        found_in_vocab = sum(1 for word in word_counts.keys() if word in vocab_150)
        not_in_vocab = len(word_counts) - found_in_vocab
        
        print(f"   150词汇表中的词: {found_in_vocab}个")
        print(f"   不在150词汇表中: {not_in_vocab}个")
        print(f"   覆盖率: {found_in_vocab/len(word_counts)*100:.1f}%")
        
        # 显示不在词汇表中的词（如果有的话）
        if not_in_vocab > 0:
            missing_words = [word for word in word_counts.keys() if word not in vocab_150]
            print(f"   不在词汇表中的词: {', '.join(missing_words[:10])}{'...' if len(missing_words) > 10 else ''}")
        
    except FileNotFoundError:
        print("   ⚠️  无法读取150词汇表文件进行对比")
    
    return word_stats

def main():
    """主函数"""
    word_stats = calculate_word_frequency()
    
    if word_stats:
        print(f"\n✅ 词频分析完成！")
        print(f"🎯 共分析了 {len(word_stats)} 个不同的词汇")
        print(f"📊 详细结果已保存到文件中")

if __name__ == "__main__":
    main()
