#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
from nltk.tokenize import TreebankWordTokenizer, sent_tokenize
import nltk
from tqdm import tqdm
from collections import Counter

def load_vocabulary(vocab_file):
    """加载词汇表"""
    print(f"正在加载词汇表: {vocab_file}")
    
    try:
        with open(vocab_file, 'r', encoding='utf-8') as f:
            vocab = set(word.strip().lower() for word in f.readlines() if word.strip())
        
        print(f"成功加载 {len(vocab)} 个词汇")
        return vocab
    
    except Exception as e:
        print(f"加载词汇表失败: {e}")
        return set()

def download_nltk_data():
    """下载必要的NLTK数据"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("正在下载NLTK punkt数据...")
        nltk.download('punkt')
    
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("正在下载NLTK punkt_tab数据...")
        nltk.download('punkt_tab')

def clean_text(text):
    """清理文本"""
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    # 移除HTML标签和特殊字符，但保留基本标点
    text = re.sub(r'<[^>]+>', '', text)  # 移除HTML标签
    text = re.sub(r'[^\w\s\'\-\.\,\?\!\:\;\(\)\"]+', ' ', text)  # 保留基本标点
    text = re.sub(r'\s+', ' ', text)  # 合并多个空格
    
    return text.strip()

def check_sentence_vocabulary(sentence, vocab, tokenizer):
    """检查句子中的所有词是否都在词汇表中"""
    if not sentence or len(sentence.strip()) < 3:
        return False, [], []
    
    # 分词
    tokens = tokenizer.tokenize(sentence)
    
    # 分离词汇和标点符号
    word_tokens = []
    punctuation_tokens = []
    invalid_tokens = []
    
    for token in tokens:
        # 检查是否是纯标点符号
        if token in ".,!?;:()\"'-":
            punctuation_tokens.append(token)
        # 检查是否是数字（也算作词汇）
        elif token.isdigit():
            word_tokens.append(token)
        # 检查是否在词汇表中
        elif token.lower() in vocab:
            word_tokens.append(token)
        else:
            invalid_tokens.append(token)
    
    # 检查条件：
    # 1. 所有token都有效（无invalid_tokens）
    # 2. 词汇数量≥4（不包括标点符号）
    is_valid = len(invalid_tokens) == 0 and len(word_tokens) >= 4
    
    all_tokens = word_tokens + punctuation_tokens
    
    return is_valid, all_tokens, invalid_tokens

def analyze_word_frequency_in_filtered_sentences(sentences, tokenizer):
    """分析筛选后句子中的词频"""
    
    print(f"\n开始分析筛选后句子的词频...")
    
    # 统计所有词汇
    all_words = []
    word_counter = Counter()
    
    for sentence_info in sentences:
        sentence = sentence_info['sentence']
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
    
    return all_words, word_counter

def process_movie_lines(movie_file, vocab_file, output_file, max_lines=None):
    """处理电影台词文件"""
    
    print("=" * 80)
    print("电影台词词汇过滤器 - 使用 150_words_list.txt")
    print("=" * 80)
    
    # 下载NLTK数据
    download_nltk_data()
    
    # 加载词汇表
    vocab = load_vocabulary(vocab_file)
    if not vocab:
        return
    
    # 初始化分词器
    tokenizer = TreebankWordTokenizer()
    
    # 读取电影台词
    try:
        print(f"\n正在读取电影台词文件: {movie_file}")
        df = pd.read_csv(movie_file, sep='\t', header=None, 
                        names=['line_id', 'character_id', 'movie_id', 'character_name', 'text'],
                        encoding='utf-8', on_bad_lines='skip')
        
        print(f"成功读取 {len(df)} 行对话")
        
        # 如果指定了最大行数，则截取
        if max_lines and max_lines < len(df):
            df = df.head(max_lines)
            print(f"处理前 {max_lines} 行对话")
        
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    
    # 处理每一行
    valid_sentences = []
    invalid_sentences = []
    
    print(f"\n开始处理对话...")
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="处理进度"):
        text = clean_text(row['text'])
        
        if not text:
            continue
        
        # 将每行文本分割成句子
        sentences = sent_tokenize(text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # 跳过太短的句子
            if len(sentence) < 5:
                continue
            
            # 检查句子词汇（≥4词）
            is_valid, valid_tokens, invalid_tokens = check_sentence_vocabulary(sentence, vocab, tokenizer)
            
            if is_valid:
                # 计算实际词汇数量（不包括标点符号）
                word_count = len([token for token in valid_tokens if token not in ".,!?;:()\"'-"])
                
                valid_sentences.append({
                    'line_id': row['line_id'],
                    'character_name': row['character_name'],
                    'sentence': sentence,
                    'tokens': valid_tokens,
                    'token_count': len(valid_tokens),
                    'word_count': word_count  # 实际词汇数量
                })
            else:
                invalid_sentences.append({
                    'line_id': row['line_id'],
                    'character_name': row['character_name'],
                    'sentence': sentence,
                    'invalid_tokens': invalid_tokens,
                    'all_tokens': valid_tokens + invalid_tokens
                })
    
    # 去重处理
    print(f"\n去重前句子数: {len(valid_sentences)}")
    unique_sentences = []
    seen_sentences = set()
    
    for item in valid_sentences:
        sentence_lower = item['sentence'].lower()
        if sentence_lower not in seen_sentences:
            seen_sentences.add(sentence_lower)
            unique_sentences.append(item)
    
    print(f"去重后句子数: {len(unique_sentences)}")
    print(f"重复句子数: {len(valid_sentences) - len(unique_sentences)}")
    
    # 保存结果
    print(f"\n处理完成！")
    print(f"有效句子: {len(unique_sentences)} (已去重)")
    print(f"无效句子: {len(invalid_sentences)}")
    print(f"有效率: {len(unique_sentences)/(len(unique_sentences)+len(invalid_sentences))*100:.2f}%")
    
    # 按句子长度分析（使用实际词汇数量，不包括标点符号）
    if unique_sentences:
        word_lengths = [item['word_count'] for item in unique_sentences]
        print(f"\n句子长度统计（不包括标点符号）:")
        print(f"  最短: {min(word_lengths)} 词")
        print(f"  最长: {max(word_lengths)} 词")
        print(f"  平均: {sum(word_lengths)/len(word_lengths):.2f} 词")
        
        # 长度分布
        short = sum(1 for l in word_lengths if 4 <= l <= 5)
        medium = sum(1 for l in word_lengths if 6 <= l <= 10)
        long = sum(1 for l in word_lengths if l > 10)
        
        print(f"  短句 (4-5词): {short} ({short/len(word_lengths)*100:.1f}%)")
        print(f"  中句 (6-10词): {medium} ({medium/len(word_lengths)*100:.1f}%)")
        print(f"  长句 (>10词): {long} ({long/len(word_lengths)*100:.1f}%)")
    
    # 分析筛选后句子的词频
    all_words, word_counter = analyze_word_frequency_in_filtered_sentences(unique_sentences, tokenizer)
    
    print(f"\n📊 筛选后句子的词频统计:")
    print(f"  总词汇数: {len(all_words)} 个（包括重复）")
    print(f"  唯一词汇数: {len(word_counter)} 个")
    
    # 按频率排序
    sorted_words = word_counter.most_common()
    
    if sorted_words:
        print(f"  最高频词: '{sorted_words[0][0]}' 出现 {sorted_words[0][1]} 次")
        print(f"  最低频词: '{sorted_words[-1][0]}' 出现 {sorted_words[-1][1]} 次")
        
        # 显示前20个高频词
        print(f"\n🔝 前20个高频词:")
        print("-" * 50)
        print(f"{'排名':<4} {'词汇':<15} {'频率':<6} {'占比'}")
        print("-" * 50)
        
        for i, (word, freq) in enumerate(sorted_words[:20], 1):
            percentage = freq / len(all_words) * 100
            print(f"{i:>3}. {word:<15} {freq:>5} {percentage:>6.2f}%")
    
    # 保存有效句子
    print(f"\n正在保存有效句子到: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 电影台词 - 仅包含 150_words_list.txt 词汇表的句子 (≥4词，已去重)\n")
        f.write(f"# 总共 {len(unique_sentences)} 个有效句子\n")
        f.write(f"# 词汇表: {vocab_file} ({len(vocab)} 个词)\n")
        f.write(f"# 限制条件: 所有词汇都在词汇表中，且词汇数量≥4（不包括标点符号）\n")
        f.write(f"# 生成时间: {pd.Timestamp.now()}\n\n")
        
        for i, item in enumerate(unique_sentences, 1):
            f.write(f"{i}. {item['sentence']}\n")
    
    # 生成纯句子文件（无序号）
    clean_output_file = output_file.replace('.txt', '_clean.txt')
    with open(clean_output_file, 'w', encoding='utf-8') as f:
        for item in unique_sentences:
            f.write(item['sentence'] + '\n')
    
    print(f"正在保存纯句子文件到: {clean_output_file}")
    
    # 保存词频分析结果
    freq_file = output_file.replace('.txt', '_frequency.txt')
    with open(freq_file, 'w', encoding='utf-8') as f:
        f.write(f"筛选后句子词频分析结果\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"句子数: {len(unique_sentences)}\n")
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
    
    print(f"\n✅ 处理完成！生成的文件:")
    print(f"   📄 {output_file} - 有编号的句子")
    print(f"   📄 {clean_output_file} - 纯句子（无编号）")
    print(f"   📊 {freq_file} - 词频分析报告")
    print(f"   📊 {csv_file} - 词频CSV数据")
    
    return len(unique_sentences), len(invalid_sentences), sorted_words

def main():
    """主函数"""
    movie_file = "others/movie_lines.tsv"
    vocab_file = "materials/150_words_list.txt"
    output_file = "filtered_sentences_150_words_v2.txt"  # 使用v2版本避免覆盖
    max_lines = None  # 处理所有行
    
    print("🎯 筛选条件:")
    print("   1. 句子长度 ≥ 4 个词（不包括标点符号）")
    print("   2. 所有词汇都必须在 150_words_list.txt 中")
    print("   3. 自动去重处理")
    print()
    
    # 运行处理
    result = process_movie_lines(movie_file, vocab_file, output_file, max_lines)
    
    if result:
        valid_count, invalid_count, sorted_words = result
        print(f"\n🎯 最终统计:")
        print(f"   有效句子: {valid_count:,} 个")
        print(f"   无效句子: {invalid_count:,} 个")
        print(f"   词频分析: {len(sorted_words)} 个不同词汇")
        print(f"   有效率: {valid_count/(valid_count+invalid_count)*100:.2f}%")

if __name__ == "__main__":
    main()