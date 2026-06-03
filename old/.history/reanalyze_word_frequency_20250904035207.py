#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nltk.tokenize import TreebankWordTokenizer
import nltk
from collections import Counter

def download_nltk_data():
    """下载必要的NLTK数据"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("正在下载NLTK punkt数据...")
        nltk.download('punkt')

def analyze_word_frequency_in_file(filename):
    """重新分析文件中的词频"""
    
    print("=" * 80)
    print(f"重新分析 {filename} 中的词频")
    print("=" * 80)
    
    # 下载NLTK数据
    download_nltk_data()
    
    try:
        # 读取句子文件
        with open(filename, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"总句子数: {len(sentences)}")
        
        # 初始化分词器
        tokenizer = TreebankWordTokenizer()
        
        # 统计所有词汇
        all_words = []
        word_counter = Counter()
        
        for sentence in sentences:
            # 分词
            tokens = tokenizer.tokenize(sentence)
            
            # 处理每个词汇
            for token in tokens:
                # 跳过标点符号
                if token in ".,!?;:()\"'-":
                    continue
                
                # 转换为小写进行统计
                word_lower = token.lower()
                all_words.append(word_lower)
                word_counter[word_lower] += 1
        
        print(f"总词汇数: {len(all_words)} 个（包括重复）")
        print(f"唯一词汇数: {len(word_counter)} 个")
        
        # 按频率排序
        sorted_words = word_counter.most_common()
        
        print(f"\n📊 词频统计结果:")
        print(f"   最高频词: '{sorted_words[0][0]}' 出现 {sorted_words[0][1]} 次")
        print(f"   最低频词: '{sorted_words[-1][0]}' 出现 {sorted_words[-1][1]} 次")
        
        # 频率分布统计
        freq_distribution = Counter(word_counter.values())
        print(f"\n📈 频率分布:")
        for freq in sorted(freq_distribution.keys(), reverse=True)[:10]:
            count = freq_distribution[freq]
            print(f"   出现 {freq:>3} 次的词汇: {count:>3} 个")
        
        # 显示前30个高频词
        print(f"\n🔝 前30个高频词:")
        print("-" * 60)
        print(f"{'排名':<4} {'词汇':<15} {'频率':<6} {'占比':<8} {'累积占比'}")
        print("-" * 60)
        
        cumulative_freq = 0
        for i, (word, freq) in enumerate(sorted_words[:30], 1):
            percentage = freq / len(all_words) * 100
            cumulative_freq += freq
            cumulative_percentage = cumulative_freq / len(all_words) * 100
            print(f"{i:>3}. {word:<15} {freq:>5} {percentage:>7.2f}% {cumulative_percentage:>8.2f}%")
        
        # 显示后20个低频词
        print(f"\n🔻 后20个低频词:")
        print("-" * 50)
        print(f"{'排名':<4} {'词汇':<15} {'频率':<6}")
        print("-" * 50)
        
        for i, (word, freq) in enumerate(sorted_words[-20:], len(sorted_words) - 19):
            print(f"{i:>3}. {word:<15} {freq:>5}")
        
        # 保存详细结果到文件
        output_file = filename.replace('.txt', '_word_frequency_new.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"重新词频分析结果 - {filename}\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"总句子数: {len(sentences)}\n")
            f.write(f"总词汇数: {len(all_words)} 个（包括重复）\n")
            f.write(f"唯一词汇数: {len(word_counter)} 个\n\n")
            
            f.write("完整词频列表（按频率降序排列）:\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'排名':<6} {'词汇':<20} {'频率':<8} {'占比':<8} {'累积占比'}\n")
            f.write("-" * 70 + "\n")
            
            cumulative_freq = 0
            for i, (word, freq) in enumerate(sorted_words, 1):
                percentage = freq / len(all_words) * 100
                cumulative_freq += freq
                cumulative_percentage = cumulative_freq / len(all_words) * 100
                f.write(f"{i:>5}. {word:<20} {freq:>7} {percentage:>7.2f}% {cumulative_percentage:>8.2f}%\n")
        
        # 保存CSV格式
        csv_file = filename.replace('.txt', '_word_frequency_new.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("排名,词汇,频率,占比,累积占比\n")
            cumulative_freq = 0
            for i, (word, freq) in enumerate(sorted_words, 1):
                percentage = freq / len(all_words) * 100
                cumulative_freq += freq
                cumulative_percentage = cumulative_freq / len(all_words) * 100
                f.write(f"{i},{word},{freq},{percentage:.2f}%,{cumulative_percentage:.2f}%\n")
        
        print(f"\n💾 结果已保存:")
        print(f"   📄 {output_file} - 详细文本报告")
        print(f"   📊 {csv_file} - CSV格式数据")
        
        # 分析一些有趣的统计
        print(f"\n🔍 有趣的统计:")
        
        # 计算前10个词汇的累积占比
        top_10_freq = sum(freq for _, freq in sorted_words[:10])
        top_10_percentage = top_10_freq / len(all_words) * 100
        print(f"   前10个高频词占总词汇的 {top_10_percentage:.1f}%")
        
        # 计算前20个词汇的累积占比
        top_20_freq = sum(freq for _, freq in sorted_words[:20])
        top_20_percentage = top_20_freq / len(all_words) * 100
        print(f"   前20个高频词占总词汇的 {top_20_percentage:.1f}%")
        
        # 计算前50个词汇的累积占比
        if len(sorted_words) >= 50:
            top_50_freq = sum(freq for _, freq in sorted_words[:50])
            top_50_percentage = top_50_freq / len(all_words) * 100
            print(f"   前50个高频词占总词汇的 {top_50_percentage:.1f}%")
        
        # 只出现一次的词汇数量
        once_words = sum(1 for freq in word_counter.values() if freq == 1)
        once_percentage = once_words / len(word_counter) * 100
        print(f"   只出现1次的词汇: {once_words} 个 ({once_percentage:.1f}%)")
        
        # 出现次数≤5的词汇数量
        low_freq_words = sum(1 for freq in word_counter.values() if freq <= 5)
        low_freq_percentage = low_freq_words / len(word_counter) * 100
        print(f"   出现≤5次的词汇: {low_freq_words} 个 ({low_freq_percentage:.1f}%)")
        
        # 出现次数≥100的词汇数量
        high_freq_words = sum(1 for freq in word_counter.values() if freq >= 100)
        print(f"   出现≥100次的词汇: {high_freq_words} 个")
        
        return sorted_words, word_counter, all_words
        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {filename}")
        return None, None, None
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        return None, None, None

def main():
    """主函数"""
    filename = 'filtered_sentences_150_words_clean.txt'
    sorted_words, word_counter, all_words = analyze_word_frequency_in_file(filename)
    
    if sorted_words:
        print(f"\n✅ 词频分析完成！")
        print(f"🎯 共发现 {len(word_counter)} 个不同的词汇")
        print(f"📊 总计 {len(all_words)} 个词汇使用实例")

if __name__ == "__main__":
    main()
