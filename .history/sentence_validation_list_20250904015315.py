#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import re
from nltk.tokenize import TreebankWordTokenizer, sent_tokenize
import nltk
import json
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
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 移除多余的空白
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def is_valid_word(word, vocab):
    """检查词是否有效"""
    # 转换为小写
    word_lower = word.lower()
    
    # 如果直接在词汇表中，返回True
    if word_lower in vocab:
        return True
    
    # 检查是否为纯标点符号（允许）
    if re.match(r'^[^\w\s]+$', word):
        return True
    
    # 检查是否为数字（允许）
    if word.isdigit():
        return True
    
    # 其他情况返回False
    return False

def validate_sentence(sentence, tokenizer, vocab):
    """验证句子是否满足词汇要求"""
    if not sentence.strip():
        return False, []
    
    # TreeBank分词
    tokens = tokenizer.tokenize(sentence)
    
    # 检查每个词
    invalid_words = []
    for token in tokens:
        if not is_valid_word(token, vocab):
            invalid_words.append(token)
    
    is_valid = len(invalid_words) == 0
    return is_valid, invalid_words

def process_movie_lines(movie_file, vocab_file, max_lines=10000):
    """处理电影台词文件"""
    print(f"开始处理电影台词文件: {movie_file}")
    
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
        df = pd.read_csv(movie_file, sep='\t', header=None, 
                        names=['line_id', 'character_id', 'movie_id', 'character_name', 'text'],
                        encoding='utf-8', on_bad_lines='skip')
        
        print(f"成功加载 {len(df)} 行电影台词")
        
        # 限制处理行数（用于测试）
        if max_lines and len(df) > max_lines:
            df = df.head(max_lines)
            print(f"限制处理前 {max_lines} 行")
        
    except Exception as e:
        print(f"读取电影台词文件失败: {e}")
        return
    
    # 结果列表
    validation_results = []
    
    print("开始验证句子...")
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="处理进度"):
        line_id = row['line_id']
        original_text = clean_text(row['text'])
        
        if not original_text:
            validation_results.append({
                'line_id': line_id,
                'original_text': '',
                'is_valid': False,
                'reason': 'empty_text',
                'invalid_words': [],
                'sentence_count': 0,
                'sentences': []
            })
            continue
        
        # 分割成句子
        try:
            sentences = sent_tokenize(original_text)
        except:
            sentences = [original_text]  # 如果分句失败，就当作一个句子
        
        # 验证每个句子
        sentence_results = []
        all_sentences_valid = True
        all_invalid_words = []
        
        for sentence in sentences:
            is_valid, invalid_words = validate_sentence(sentence, tokenizer, vocab)
            sentence_results.append({
                'sentence': sentence,
                'is_valid': is_valid,
                'invalid_words': invalid_words
            })
            
            if not is_valid:
                all_sentences_valid = False
                all_invalid_words.extend(invalid_words)
        
        # 整体结果
        validation_results.append({
            'line_id': line_id,
            'original_text': original_text,
            'is_valid': all_sentences_valid,
            'reason': 'valid' if all_sentences_valid else 'contains_invalid_words',
            'invalid_words': list(set(all_invalid_words)),
            'sentence_count': len(sentences),
            'sentences': sentence_results
        })
    
    return validation_results

def save_results(results, output_file):
    """保存结果"""
    print(f"保存结果到: {output_file}")
    
    # 统计信息
    total_lines = len(results)
    valid_lines = sum(1 for r in results if r['is_valid'])
    invalid_lines = total_lines - valid_lines
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 电影台词验证结果\n")
        f.write(f"# 总行数: {total_lines}\n")
        f.write(f"# 有效行数: {valid_lines} ({valid_lines/total_lines*100:.2f}%)\n")
        f.write(f"# 无效行数: {invalid_lines} ({invalid_lines/total_lines*100:.2f}%)\n")
        f.write("#" + "="*80 + "\n\n")
        
        for i, result in enumerate(results):
            f.write(f"{i+1}. 行ID: {result['line_id']}\n")
            f.write(f"   原文: {result['original_text'][:100]}{'...' if len(result['original_text']) > 100 else ''}\n")
            f.write(f"   是否有效: {'✅ 是' if result['is_valid'] else '❌ 否'}\n")
            
            if not result['is_valid'] and result['invalid_words']:
                f.write(f"   无效词汇: {result['invalid_words'][:10]}{'...' if len(result['invalid_words']) > 10 else ''}\n")
            
            f.write(f"   句子数量: {result['sentence_count']}\n")
            f.write("\n")
    
    # 同时保存JSON格式（便于程序读取）
    json_file = output_file.replace('.txt', '.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"结果已保存到:")
    print(f"  - 文本格式: {output_file}")
    print(f"  - JSON格式: {json_file}")
    
    # 打印统计信息
    print(f"\n📊 统计信息:")
    print(f"  总行数: {total_lines}")
    print(f"  有效行数: {valid_lines} ({valid_lines/total_lines*100:.2f}%)")
    print(f"  无效行数: {invalid_lines} ({invalid_lines/total_lines*100:.2f}%)")

def main():
    """主函数"""
    movie_file = 'movie_lines.tsv'
    vocab_file = 'top_1200_words_simple.txt'
    output_file = 'sentence_validation_results.txt'
    
    # 处理电影台词（限制处理行数以提高速度）
    results = process_movie_lines(movie_file, vocab_file, max_lines=5000)
    
    if results:
        # 保存结果
        save_results(results, output_file)
        
        # 显示一些样本
        print(f"\n📝 前5个结果样本:")
        for i, result in enumerate(results[:5]):
            status = "✅ 有效" if result['is_valid'] else "❌ 无效"
            print(f"{i+1}. {status} - {result['original_text'][:50]}...")
            if not result['is_valid'] and result['invalid_words']:
                print(f"   无效词: {result['invalid_words'][:5]}")

if __name__ == "__main__":
    main()
