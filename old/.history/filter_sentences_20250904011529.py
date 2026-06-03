#!/usr/bin/env python3
"""
处理 movie_lines.tsv 文件，筛选出 8-15 词的句子
每个 line 可能包含多个句子，需要分别处理
"""

import re
import csv
from typing import List, Tuple

def split_into_sentences(text: str) -> List[str]:
    """
    将文本分割成句子
    处理各种句子结束符：. ! ? 以及引号等
    """
    # 清理文本，移除多余的空白字符
    text = re.sub(r'\s+', ' ', text.strip())
    
    # 分割句子的正则表达式
    # 匹配 . ! ? 后面跟着空格或结束，但要避免缩写词
    sentence_endings = r'[.!?]+(?:\s+|$)'
    
    # 先按句子结束符分割
    sentences = re.split(sentence_endings, text)
    
    # 清理和过滤句子
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and len(sentence) > 0:
            # 移除引号等标点符号
            sentence = re.sub(r'^["\']+|["\']+$', '', sentence)
            sentence = sentence.strip()
            if sentence:
                cleaned_sentences.append(sentence)
    
    return cleaned_sentences

def count_words(text: str) -> int:
    """
    计算文本中的单词数量
    """
    # 按空白字符分割，过滤空字符串
    words = [word for word in re.split(r'\s+', text.strip()) if word]
    return len(words)

def is_valid_sentence(sentence: str) -> bool:
    """
    检查句子是否有效（包含字母，不是纯标点符号等）
    """
    # 必须包含至少一个字母
    if not re.search(r'[a-zA-Z]', sentence):
        return False
    
    # 不能只是标点符号或数字
    if re.match(r'^[^a-zA-Z]*$', sentence):
        return False
    
    return True

def process_movie_lines(input_file: str, output_file: str):
    """
    处理 movie_lines.tsv 文件
    """
    valid_sentences = []
    total_lines = 0
    total_sentences = 0
    
    print(f"开始处理文件: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        # 使用 csv.reader 处理 TSV 格式
        reader = csv.reader(f, delimiter='\t')
        
        for row_num, row in enumerate(reader, 1):
            if len(row) < 5:
                continue  # 跳过格式不正确的行
            
            line_id, user_id, movie_id, character, dialogue = row[:5]
            total_lines += 1
            
            # 分割成多个句子
            sentences = split_into_sentences(dialogue)
            total_sentences += len(sentences)
            
            for sentence in sentences:
                if not is_valid_sentence(sentence):
                    continue
                
                word_count = count_words(sentence)
                
                # 筛选 8-15 词的句子
                if 8 <= word_count <= 15:
                    valid_sentences.append({
                        'line_id': line_id,
                        'character': character,
                        'sentence': sentence,
                        'word_count': word_count,
                        'original_dialogue': dialogue
                    })
            
            # 每处理1000行显示进度
            if row_num % 1000 == 0:
                print(f"已处理 {row_num} 行，找到 {len(valid_sentences)} 个有效句子")
    
    print(f"\n处理完成!")
    print(f"总行数: {total_lines}")
    print(f"总句子数: {total_sentences}")
    print(f"符合条件的句子数: {len(valid_sentences)}")
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['Line_ID', 'Character', 'Word_Count', 'Sentence', 'Original_Dialogue'])
        
        for item in valid_sentences:
            writer.writerow([
                item['line_id'],
                item['character'],
                item['word_count'],
                item['sentence'],
                item['original_dialogue']
            ])
    
    print(f"结果已保存到: {output_file}")
    
    # 显示一些示例
    print(f"\n前10个符合条件的句子示例:")
    for i, item in enumerate(valid_sentences[:10]):
        print(f"{i+1}. [{item['word_count']}词] {item['character']}: {item['sentence']}")

if __name__ == "__main__":
    input_file = "movie_lines.tsv"
    output_file = "filtered_sentences_8_15_words.tsv"
    
    try:
        process_movie_lines(input_file, output_file)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
