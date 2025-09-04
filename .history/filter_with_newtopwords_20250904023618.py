#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
from nltk.tokenize import TreebankWordTokenizer, sent_tokenize
import nltk
from tqdm import tqdm

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

def is_valid_token(token, vocab):
    """检查token是否有效（在词汇表中或是标点符号）"""
    token_lower = token.lower()
    
    # 标点符号总是有效的
    if token in ".,!?;:()\"'-":
        return True
    
    # 检查是否在词汇表中
    if token_lower in vocab:
        return True
    
    # 检查是否是数字（数字也认为是有效的）
    if token.isdigit():
        return True
    
    return False

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
    # 2. 词汇数量大于或等于3（不包括标点符号）
    is_valid = len(invalid_tokens) == 0 and len(word_tokens) >= 3
    
    all_tokens = word_tokens + punctuation_tokens
    
    return is_valid, all_tokens, invalid_tokens

def process_movie_lines(movie_file, vocab_file, output_file, max_lines=None):
    """处理电影台词文件"""
    
    print("=" * 80)
    print("电影台词词汇过滤器 - 使用新词汇表")
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
            
            # 检查句子词汇（无长度限制，但必须>3词）
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
    
    # 保存结果
    print(f"\n处理完成！")
    print(f"有效句子: {len(valid_sentences)}")
    print(f"无效句子: {len(invalid_sentences)}")
    print(f"有效率: {len(valid_sentences)/(len(valid_sentences)+len(invalid_sentences))*100:.2f}%")
    
    # 按句子长度分析（使用实际词汇数量，不包括标点符号）
    if valid_sentences:
        word_lengths = [item['word_count'] for item in valid_sentences]
        print(f"\n句子长度统计（不包括标点符号）:")
        print(f"  最短: {min(word_lengths)} 词")
        print(f"  最长: {max(word_lengths)} 词")
        print(f"  平均: {sum(word_lengths)/len(word_lengths):.2f} 词")
        
        # 长度分布
        short = sum(1 for l in word_lengths if l <= 5)
        medium = sum(1 for l in word_lengths if 6 <= l <= 10)
        long = sum(1 for l in word_lengths if l > 10)
        
        print(f"  短句 (3-5词): {short} ({short/len(word_lengths)*100:.1f}%)")
        print(f"  中句 (6-10词): {medium} ({medium/len(word_lengths)*100:.1f}%)")
        print(f"  长句 (>10词): {long} ({long/len(word_lengths)*100:.1f}%)")
    
    # 保存有效句子
    print(f"\n正在保存有效句子到: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 电影台词 - 仅包含扩展词汇表的句子 (≥3词，不含标点)\n")
        f.write(f"# 总共 {len(valid_sentences)} 个有效句子\n")
        f.write(f"# 词汇表: {vocab_file} ({len(vocab)} 个词)\n")
        f.write(f"# 限制条件: 所有词汇都在词汇表中，且词汇数量≥3（不包括标点符号）\n")
        f.write(f"# 生成时间: {pd.Timestamp.now()}\n\n")
        
        for i, item in enumerate(valid_sentences, 1):
            f.write(f"{i}. {item['sentence']}\n")
    
    # 保存统计信息
    stats_file = output_file.replace('.txt', '_stats.txt')
    print(f"正在保存统计信息到: {stats_file}")
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("电影台词词汇过滤统计报告 - 新词汇表\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"源文件: {movie_file}\n")
        f.write(f"词汇表: {vocab_file}\n")
        f.write(f"词汇表大小: {len(vocab)} 个词\n")
        f.write(f"长度限制: 必须≥3词（不包括标点符号）\n\n")
        f.write(f"处理行数: {len(df)}\n")
        f.write(f"有效句子: {len(valid_sentences)}\n")
        f.write(f"无效句子: {len(invalid_sentences)}\n")
        f.write(f"有效率: {len(valid_sentences)/(len(valid_sentences)+len(invalid_sentences))*100:.2f}%\n\n")
        
        # 句子长度统计（使用实际词汇数量）
        if valid_sentences:
            word_lengths = [item['word_count'] for item in valid_sentences]
            f.write("有效句子长度统计（不包括标点符号）:\n")
            f.write(f"  平均长度: {sum(word_lengths)/len(word_lengths):.2f} 词\n")
            f.write(f"  最短句子: {min(word_lengths)} 词\n")
            f.write(f"  最长句子: {max(word_lengths)} 词\n\n")
            
            # 长度分布
            short = sum(1 for l in word_lengths if l <= 5)
            medium = sum(1 for l in word_lengths if 6 <= l <= 10)
            long = sum(1 for l in word_lengths if l > 10)
            
            f.write("长度分布:\n")
            f.write(f"  短句 (3-5词): {short} ({short/len(word_lengths)*100:.1f}%)\n")
            f.write(f"  中句 (6-10词): {medium} ({medium/len(word_lengths)*100:.1f}%)\n")
            f.write(f"  长句 (>10词): {long} ({long/len(word_lengths)*100:.1f}%)\n\n")
            
            # 显示几个示例
            f.write("有效句子示例:\n")
            for i, item in enumerate(valid_sentences[:15], 1):
                f.write(f"{i:2d}. ({item['word_count']:2d}词) {item['sentence'][:80]}{'...' if len(item['sentence']) > 80 else ''}\n")
        
        f.write("\n无效句子示例 (包含词汇表外的词):\n")
        for i, item in enumerate(invalid_sentences[:10], 1):
            f.write(f"{i:2d}. {item['sentence'][:60]}{'...' if len(item['sentence']) > 60 else ''}\n")
            f.write(f"    无效词: {item['invalid_tokens'][:5]}\n")
    
    # 保存无效句子样本
    invalid_sample_file = output_file.replace('.txt', '_invalid_samples.txt')
    print(f"正在保存无效句子样本到: {invalid_sample_file}")
    
    with open(invalid_sample_file, 'w', encoding='utf-8') as f:
        f.write(f"无效句子样本 (前300个)\n")
        f.write("=" * 50 + "\n\n")
        
        for i, item in enumerate(invalid_sentences[:300], 1):
            f.write(f"{i}. {item['sentence']}\n")
            f.write(f"   无效词: {', '.join(item['invalid_tokens'][:10])}\n")
            f.write(f"   所有词: {', '.join(item['all_tokens'][:15])}\n\n")
    
    print(f"\n✅ 处理完成！生成的文件:")
    print(f"   📄 {output_file} - 有效句子")
    print(f"   📊 {stats_file} - 统计报告") 
    print(f"   🔍 {invalid_sample_file} - 无效句子样本")
    
    return len(valid_sentences), len(invalid_sentences)

def main():
    """主函数"""
    movie_file = "others/movie_lines.tsv"
    vocab_file = "others/newtopwords.txt"
    output_file = "filtered_sentences_newtopwords.txt"
    max_lines = 20000  # 处理更多行以获得更多有效句子
    
    # 运行处理
    process_movie_lines(movie_file, vocab_file, output_file, max_lines)

if __name__ == "__main__":
    main()
