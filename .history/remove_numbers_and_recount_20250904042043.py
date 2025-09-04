#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nltk.tokenize import TreebankWordTokenizer
import nltk
from collections import Counter
import re

def download_nltk_data():
    """下载必要的NLTK数据"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("正在下载NLTK punkt数据...")
        nltk.download('punkt')

def remove_sentences_with_numbers_and_recount(input_file):
    """移除包含数字的句子并重新统计词频"""
    
    print("=" * 80)
    print(f"移除包含数字的句子并重新统计词频")
    print("=" * 80)
    
    # 下载NLTK数据
    download_nltk_data()
    
    try:
        # 读取原始句子
        with open(input_file, 'r', encoding='utf-8') as f:
            original_sentences = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"原始句子数: {len(original_sentences)}")
        
        # 初始化分词器
        tokenizer = TreebankWordTokenizer()
        
        # 过滤包含数字的句子
        clean_sentences = []
        removed_sentences = []
        
        for sentence in original_sentences:
            # 分词检查是否包含数字
            tokens = tokenizer.tokenize(sentence)
            contains_number = False
            
            for token in tokens:
                # 检查是否是数字（包括纯数字和包含数字的词）
                if re.search(r'\d', token):
                    contains_number = True
                    break
            
            if contains_number:
                removed_sentences.append(sentence)
            else:
                clean_sentences.append(sentence)
        
        print(f"移除句子数: {len(removed_sentences)}")
        print(f"保留句子数: {len(clean_sentences)}")
        print(f"保留率: {len(clean_sentences)/len(original_sentences)*100:.1f}%")
        
        # 保存清理后的句子
        output_file = input_file.replace('.txt', '_no_numbers.txt')
        with open(output_file, 'w', encoding='utf-8') as f:
            for sentence in clean_sentences:
                f.write(sentence + '\n')
        
        print(f"\n✅ 清理后的句子已保存: {output_file}")
        
        # 显示一些被移除的句子样本
        if removed_sentences:
            print(f"\n🗑️ 被移除的句子样本 (前10个):")
            for i, sentence in enumerate(removed_sentences[:10], 1):
                print(f"{i:2d}. {sentence}")
            
            if len(removed_sentences) > 10:
                print(f"... 还有 {len(removed_sentences) - 10} 个句子被移除")
        
        # 重新统计词频
        print(f"\n开始重新统计词频...")
        
        all_words = []
        word_counter = Counter()
        
        for sentence in clean_sentences:
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
        
        print(f"\n📊 新的词频统计结果:")
        print(f"   最高频词: '{sorted_words[0][0]}' 出现 {sorted_words[0][1]} 次")
        if len(sorted_words) > 1:
            print(f"   最低频词: '{sorted_words[-1][0]}' 出现 {sorted_words[-1][1]} 次")
        
        # 显示前20个高频词
        print(f"\n🔝 前20个高频词:")
        print("-" * 50)
        print(f"{'排名':<4} {'词汇':<15} {'频率':<6} {'占比'}")
        print("-" * 50)
        
        for i, (word, freq) in enumerate(sorted_words[:20], 1):
            percentage = freq / len(all_words) * 100
            print(f"{i:>3}. {word:<15} {freq:>5} {percentage:>6.2f}%")
        
        # 保存词频分析结果
        freq_output_file = output_file.replace('.txt', '_frequency.txt')
        with open(freq_output_file, 'w', encoding='utf-8') as f:
            f.write(f"清理后句子词频分析结果（移除含数字句子）\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"原始句子数: {len(original_sentences)}\n")
            f.write(f"移除句子数: {len(removed_sentences)}\n")
            f.write(f"保留句子数: {len(clean_sentences)}\n")
            f.write(f"保留率: {len(clean_sentences)/len(original_sentences)*100:.1f}%\n\n")
            f.write(f"总词汇数: {len(all_words)} 个（包括重复）\n")
            f.write(f"唯一词汇数: {len(word_counter)} 个\n\n")
            
            f.write("完整词频列表（按频率降序排列）:\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'排名':<6} {'词汇':<20} {'频率':<8} {'占比'}\n")
            f.write("-" * 60 + "\n")
            
            for i, (word, freq) in enumerate(sorted_words, 1):
                percentage = freq / len(all_words) * 100
                f.write(f"{i:>5}. {word:<20} {freq:>7} {percentage:>7.2f}%\n")
        
        # 保存CSV格式
        csv_file = output_file.replace('.txt', '_frequency.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("排名,词汇,频率,占比\n")
            for i, (word, freq) in enumerate(sorted_words, 1):
                percentage = freq / len(all_words) * 100
                f.write(f"{i},{word},{freq},{percentage:.2f}%\n")
        
        # 创建移除报告
        report_file = output_file.replace('.txt', '_removal_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("数字句子移除报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"处理文件: {input_file}\n")
            f.write(f"处理时间: {pd.Timestamp.now() if 'pd' in globals() else 'N/A'}\n\n")
            
            f.write(f"统计信息:\n")
            f.write("-" * 30 + "\n")
            f.write(f"原始句子数: {len(original_sentences)}\n")
            f.write(f"移除句子数: {len(removed_sentences)}\n")
            f.write(f"保留句子数: {len(clean_sentences)}\n")
            f.write(f"保留率: {len(clean_sentences)/len(original_sentences)*100:.1f}%\n\n")
            
            f.write("被移除的句子列表:\n")
            f.write("-" * 30 + "\n")
            for i, sentence in enumerate(removed_sentences, 1):
                f.write(f"{i:3d}. {sentence}\n")
        
        print(f"\n💾 结果已保存:")
        print(f"   📄 {output_file} - 清理后的句子")
        print(f"   📊 {freq_output_file} - 词频分析报告")
        print(f"   📊 {csv_file} - 词频CSV数据")
        print(f"   📋 {report_file} - 移除报告")
        
        # 分析一些有趣的统计
        print(f"\n🔍 有趣的统计:")
        
        # 计算前10个词汇的累积占比
        if len(sorted_words) >= 10:
            top_10_freq = sum(freq for _, freq in sorted_words[:10])
            top_10_percentage = top_10_freq / len(all_words) * 100
            print(f"   前10个高频词占总词汇的 {top_10_percentage:.1f}%")
        
        # 计算前50个词汇的累积占比
        if len(sorted_words) >= 50:
            top_50_freq = sum(freq for _, freq in sorted_words[:50])
            top_50_percentage = top_50_freq / len(all_words) * 100
            print(f"   前50个高频词占总词汇的 {top_50_percentage:.1f}%")
        
        # 只出现一次的词汇数量
        once_words = sum(1 for freq in word_counter.values() if freq == 1)
        if len(word_counter) > 0:
            once_percentage = once_words / len(word_counter) * 100
            print(f"   只出现1次的词汇: {once_words} 个 ({once_percentage:.1f}%)")
        
        return clean_sentences, sorted_words, word_counter
        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {input_file}")
        return None, None, None
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        return None, None, None

def main():
    """主函数"""
    try:
        import pandas as pd
        globals()['pd'] = pd
    except ImportError:
        pass
    
    input_file = 'filtered_sentences_150_words_v2_clean.txt'
    clean_sentences, sorted_words, word_counter = remove_sentences_with_numbers_and_recount(input_file)
    
    if clean_sentences and sorted_words:
        print(f"\n✅ 处理完成！")
        print(f"🎯 清理后句子数: {len(clean_sentences):,}")
        print(f"📊 唯一词汇数: {len(word_counter)}")

if __name__ == "__main__":
    main()
