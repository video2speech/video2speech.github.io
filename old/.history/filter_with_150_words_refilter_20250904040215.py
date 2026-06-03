#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
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
    
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("正在下载NLTK punkt_tab数据...")
        nltk.download('punkt_tab')

def load_vocabulary(vocab_file):
    """加载词汇表"""
    try:
        with open(vocab_file, 'r', encoding='utf-8') as f:
            vocab = set()
            for line in f:
                word = line.strip()
                if word:
                    vocab.add(word.lower())
        return vocab
    except FileNotFoundError:
        print(f"❌ 找不到词汇表文件: {vocab_file}")
        return set()

def check_sentence_vocabulary(sentence, vocab, tokenizer):
    """检查句子中的所有词汇是否都在词汇表中"""
    # 分词
    tokens = tokenizer.tokenize(sentence)
    
    word_tokens = []
    punctuation_tokens = []
    invalid_tokens = []
    
    for token in tokens:
        if token in ".,!?;:()\"'-":
            punctuation_tokens.append(token)
        elif token.isdigit():
            # 数字也算作有效词汇
            word_tokens.append(token)
        elif token.lower() in vocab:
            word_tokens.append(token)
        else:
            invalid_tokens.append(token)
    
    # 检查条件：1. 所有词汇都有效（无invalid_tokens）2. 词汇数≥4（不包括标点符号）
    is_valid = len(invalid_tokens) == 0 and len(word_tokens) >= 4
    all_tokens = word_tokens + punctuation_tokens
    
    return is_valid, all_tokens, invalid_tokens

def process_movie_lines(movie_file, vocab, tokenizer):
    """处理电影台词文件"""
    try:
        # 读取TSV文件
        df = pd.read_csv(movie_file, sep='\t', encoding='utf-8', 
                        names=['line_id', 'character_id', 'movie_id', 'character_name', 'text'])
        
        print(f"总行数: {len(df)}")
        
        valid_sentences = []
        invalid_sentences = []
        
        for index, row in df.iterrows():
            if pd.isna(row['text']):
                continue
            
            sentence = str(row['text']).strip()
            if not sentence:
                continue
            
            # 检查句子词汇
            is_valid, valid_tokens, invalid_tokens = check_sentence_vocabulary(sentence, vocab, tokenizer)
            
            if is_valid:
                # 计算实际词汇数（不包括标点符号）
                word_count = len([token for token in valid_tokens if token not in ".,!?;:()\"'-"])
                valid_sentences.append({
                    'line_id': row['line_id'],
                    'character_name': row['character_name'],
                    'sentence': sentence,
                    'tokens': valid_tokens,
                    'token_count': len(valid_tokens),
                    'word_count': word_count  # 实际词汇数
                })
            else:
                invalid_sentences.append({
                    'line_id': row['line_id'],
                    'character_name': row['character_name'],
                    'sentence': sentence,
                    'invalid_tokens': invalid_tokens,
                    'word_count': len([token for token in tokenizer.tokenize(sentence) if token not in ".,!?;:()\"'-"])
                })
        
        return valid_sentences, invalid_sentences
        
    except FileNotFoundError:
        print(f"❌ 找不到电影台词文件: {movie_file}")
        return [], []
    except Exception as e:
        print(f"❌ 处理电影台词文件时出错: {e}")
        return [], []

def save_results(valid_sentences, invalid_sentences, vocab_size):
    """保存筛选结果"""
    
    # 保存有效句子（带编号）
    output_file = 'filtered_sentences_150_words_refilter.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"使用150词表重新筛选的句子 (词汇表大小: {vocab_size})\n")
        f.write(f"筛选条件: 句子长度≥4个词，所有词汇都在150词表中\n")
        f.write("=" * 70 + "\n\n")
        
        for i, item in enumerate(valid_sentences, 1):
            f.write(f"{i:>4}. {item['sentence']}\n")
            f.write(f"      词汇数: {item['word_count']} | 总token数: {item['token_count']}\n")
            f.write(f"      角色: {item['character_name']} | ID: {item['line_id']}\n\n")
    
    # 保存干净的句子列表（无编号）
    clean_output_file = 'filtered_sentences_150_words_refilter_clean.txt'
    with open(clean_output_file, 'w', encoding='utf-8') as f:
        for item in valid_sentences:
            f.write(f"{item['sentence']}\n")
    
    # 去重处理
    unique_sentences = []
    seen_sentences = set()
    for item in valid_sentences:
        sentence_lower = item['sentence'].lower().strip()
        if sentence_lower not in seen_sentences:
            unique_sentences.append(item)
            seen_sentences.add(sentence_lower)
    
    # 保存去重后的句子
    unique_output_file = 'filtered_sentences_150_words_refilter_unique.txt'
    with open(unique_output_file, 'w', encoding='utf-8') as f:
        for item in unique_sentences:
            f.write(f"{item['sentence']}\n")
    
    # 保存统计报告
    stats_file = 'filtered_sentences_150_words_refilter_stats.txt'
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("150词表重新筛选统计报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"词汇表大小: {vocab_size} 个词汇\n")
        f.write(f"筛选条件: 句子长度≥4个词，所有词汇都在150词表中\n\n")
        
        f.write(f"筛选结果:\n")
        f.write(f"  有效句子数: {len(valid_sentences)} 个\n")
        f.write(f"  去重后句子数: {len(unique_sentences)} 个\n")
        f.write(f"  无效句子数: {len(invalid_sentences)} 个\n")
        f.write(f"  重复句子数: {len(valid_sentences) - len(unique_sentences)} 个\n\n")
        
        # 长度分布统计
        length_counter = Counter(item['word_count'] for item in valid_sentences)
        f.write("句子长度分布:\n")
        for length in sorted(length_counter.keys()):
            count = length_counter[length]
            percentage = count / len(valid_sentences) * 100
            f.write(f"  {length:>2}词: {count:>4} 个 ({percentage:>5.1f}%)\n")
        
        f.write(f"\n平均句子长度: {sum(item['word_count'] for item in valid_sentences) / len(valid_sentences):.1f} 个词\n")
    
    # 保存无效句子样本
    if invalid_sentences:
        invalid_samples_file = 'filtered_sentences_150_words_refilter_invalid_samples.txt'
        with open(invalid_samples_file, 'w', encoding='utf-8') as f:
            f.write("无效句子样本 (前100个)\n")
            f.write("=" * 50 + "\n\n")
            
            for i, item in enumerate(invalid_sentences[:100], 1):
                f.write(f"{i:>3}. {item['sentence']}\n")
                f.write(f"     词汇数: {item['word_count']} | 无效词汇: {item['invalid_tokens']}\n")
                f.write(f"     角色: {item['character_name']}\n\n")
    
    return len(unique_sentences)

def calculate_word_frequency(valid_sentences, vocab_size):
    """计算筛选后句子的词频"""
    print("\n📊 计算筛选后句子的词频...")
    
    tokenizer = TreebankWordTokenizer()
    word_counter = Counter()
    all_words = []
    
    for item in valid_sentences:
        sentence = item['sentence']
        tokens = tokenizer.tokenize(sentence)
        
        for token in tokens:
            # 跳过标点符号
            if token in ".,!?;:()\"'-":
                continue
            
            word_lower = token.lower()
            all_words.append(word_lower)
            word_counter[word_lower] += 1
    
    # 保存词频统计
    frequency_file = 'filtered_sentences_150_words_refilter_frequency.txt'
    with open(frequency_file, 'w', encoding='utf-8') as f:
        f.write(f"150词表重新筛选句子词频统计\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"总句子数: {len(valid_sentences)}\n")
        f.write(f"总词汇数: {len(all_words)} 个（包括重复）\n")
        f.write(f"唯一词汇数: {len(word_counter)} 个\n")
        f.write(f"词汇表大小: {vocab_size} 个\n\n")
        
        sorted_words = word_counter.most_common()
        f.write("完整词频列表（按频率降序排列）:\n")
        f.write("-" * 60 + "\n")
        f.write(f"{'排名':<6} {'词汇':<20} {'频率':<8} {'占比':<8} {'累积占比'}\n")
        f.write("-" * 60 + "\n")
        
        cumulative_freq = 0
        for i, (word, freq) in enumerate(sorted_words, 1):
            percentage = freq / len(all_words) * 100
            cumulative_freq += freq
            cumulative_percentage = cumulative_freq / len(all_words) * 100
            f.write(f"{i:>5}. {word:<20} {freq:>7} {percentage:>7.2f}% {cumulative_percentage:>8.2f}%\n")
    
    # 保存CSV格式
    csv_file = 'filtered_sentences_150_words_refilter_frequency.csv'
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("排名,词汇,频率,占比,累积占比\n")
        cumulative_freq = 0
        sorted_words = word_counter.most_common()
        for i, (word, freq) in enumerate(sorted_words, 1):
            percentage = freq / len(all_words) * 100
            cumulative_freq += freq
            cumulative_percentage = cumulative_freq / len(all_words) * 100
            f.write(f"{i},{word},{freq},{percentage:.2f}%,{cumulative_percentage:.2f}%\n")
    
    return word_counter

def main():
    """主函数"""
    print("🎯 使用150词表重新筛选句子")
    print("=" * 60)
    
    # 下载NLTK数据
    download_nltk_data()
    
    # 加载150词汇表
    vocab_file = 'materials/150_words_list.txt'
    vocab = load_vocabulary(vocab_file)
    
    if not vocab:
        print("❌ 词汇表加载失败，程序退出")
        return
    
    print(f"📚 加载词汇表: {len(vocab)} 个唯一词汇")
    
    # 初始化分词器
    tokenizer = TreebankWordTokenizer()
    
    # 处理电影台词
    movie_file = 'others/movie_lines.tsv'
    print(f"📖 处理电影台词文件: {movie_file}")
    
    valid_sentences, invalid_sentences = process_movie_lines(movie_file, vocab, tokenizer)
    
    if not valid_sentences:
        print("❌ 没有找到有效句子")
        return
    
    print(f"\n📊 筛选结果:")
    print(f"   有效句子: {len(valid_sentences)} 个")
    print(f"   无效句子: {len(invalid_sentences)} 个")
    print(f"   有效率: {len(valid_sentences) / (len(valid_sentences) + len(invalid_sentences)) * 100:.1f}%")
    
    # 保存结果
    unique_count = save_results(valid_sentences, invalid_sentences, len(vocab))
    print(f"   去重后句子: {unique_count} 个")
    
    # 计算词频
    word_counter = calculate_word_frequency(valid_sentences, len(vocab))
    
    print(f"\n💾 文件已生成:")
    print(f"   📄 filtered_sentences_150_words_refilter.txt - 详细句子列表")
    print(f"   📝 filtered_sentences_150_words_refilter_clean.txt - 干净句子列表")
    print(f"   🎯 filtered_sentences_150_words_refilter_unique.txt - 去重句子列表")
    print(f"   📊 filtered_sentences_150_words_refilter_stats.txt - 统计报告")
    print(f"   📈 filtered_sentences_150_words_refilter_frequency.txt - 词频统计")
    print(f"   📊 filtered_sentences_150_words_refilter_frequency.csv - 词频CSV")
    
    if invalid_sentences:
        print(f"   ⚠️  filtered_sentences_150_words_refilter_invalid_samples.txt - 无效句子样本")
    
    print(f"\n✅ 150词表重新筛选完成！")
    print(f"🎯 共筛选出 {len(valid_sentences)} 个有效句子（去重后 {unique_count} 个）")
    print(f"📊 词频统计显示 {len(word_counter)} 个不同词汇")

if __name__ == "__main__":
    main()
