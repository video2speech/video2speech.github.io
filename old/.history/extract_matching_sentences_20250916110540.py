#!/usr/bin/env python3
"""
从 movie_lines.tsv 中提取符合条件的句子
条件：
1. 句子长度 >= 4个词汇
2. 每个词汇都在 PICK.txt 中
3. 去重并保存到文件
"""

import re
import string

def load_pick_words():
    """加载 PICK.txt 中的词汇"""
    try:
        with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/PICK.txt', 'r', encoding='utf-8') as f:
            words = set(word.strip().lower() for word in f if word.strip())
        print(f"✅ 加载了 {len(words)} 个目标词汇")
        return words
    except FileNotFoundError:
        print("❌ 找不到 PICK.txt 文件")
        return set()

def clean_word(word):
    """清理词汇，移除标点符号并转为小写"""
    # 移除标点符号
    word = word.translate(str.maketrans('', '', string.punctuation))
    return word.lower().strip()

def split_into_sentences(text):
    """将文本分割成句子"""
    # 使用正则表达式按句号、问号、感叹号分割
    sentences = re.split(r'[.!?]+', text)
    # 过滤空句子并去除首尾空格
    return [s.strip() for s in sentences if s.strip()]

def extract_words_from_sentence(sentence):
    """从句子中提取词汇"""
    # 使用正则表达式提取单词（只保留字母）
    words = re.findall(r'\b[a-zA-Z]+\b', sentence)
    return [clean_word(word) for word in words if clean_word(word)]

def is_sentence_valid(sentence, pick_words):
    """检查句子是否符合条件"""
    words = extract_words_from_sentence(sentence)
    
    # 检查长度是否 >= 4
    if len(words) < 4:
        return False
    
    # 检查每个词汇是否都在 PICK.txt 中
    for word in words:
        if word not in pick_words:
            return False
    
    return True

def process_movie_lines():
    """处理 movie_lines.tsv 文件"""
    pick_words = load_pick_words()
    if not pick_words:
        return
    
    print("🎬 开始处理 movie_lines.tsv...")
    
    valid_sentences = set()  # 使用 set 自动去重
    total_lines = 0
    processed_sentences = 0
    
    try:
        with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/materials/movie_lines.tsv', 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                total_lines += 1
                
                # 每处理1000行显示一次进度
                if line_num % 1000 == 0:
                    print(f"📊 已处理 {line_num} 行，找到 {len(valid_sentences)} 个有效句子...")
                
                # 解析 TSV 格式，提取对话内容（最后一列）
                parts = line.strip().split('\t')
                if len(parts) < 5:
                    continue
                
                dialogue = parts[4]  # 对话内容在第5列（索引4）
                
                # 将对话分割成句子
                sentences = split_into_sentences(dialogue)
                
                for sentence in sentences:
                    processed_sentences += 1
                    
                    # 检查句子是否符合条件
                    if is_sentence_valid(sentence, pick_words):
                        valid_sentences.add(sentence.strip())
    
    except FileNotFoundError:
        print("❌ 找不到 materials/movie_lines.tsv 文件")
        return
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        return
    
    print(f"\n📈 处理完成!")
    print(f"   总行数: {total_lines}")
    print(f"   总句子数: {processed_sentences}")
    print(f"   符合条件的句子: {len(valid_sentences)} (去重后)")
    
    # 保存结果到文件
    output_file = '/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/matching_sentences.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence in sorted(valid_sentences):  # 排序以便查看
            f.write(sentence + '\n')
    
    print(f"✅ 结果已保存到: matching_sentences.txt")
    
    # 显示前10个句子作为示例
    if valid_sentences:
        print(f"\n📝 示例句子 (前10个):")
        print("-" * 50)
        for i, sentence in enumerate(sorted(valid_sentences)[:10], 1):
            print(f"{i:2d}. {sentence}")
    
    return list(valid_sentences)

if __name__ == "__main__":
    sentences = process_movie_lines()
