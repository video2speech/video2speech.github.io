#!/usr/bin/env python3
"""
从 movie_lines.tsv 中提取符合条件的句子
条件：句子长度>=3个词汇，且每个词汇都在PICK.txt中
"""

import re
import string

def load_pick_words():
    """加载PICK.txt中的词汇"""
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/PICK.txt', 'r', encoding='utf-8') as f:
        words = set()
        for line in f:
            word = line.strip()
            if word:
                words.add(word.lower())  # 转换为小写进行匹配
        return words

def clean_and_split_text(text):
    """清理文本并分割成句子"""
    # 移除引号和其他标点符号，但保留句子分隔符
    text = text.replace('"', '').replace("'", "'")
    
    # 按句子分隔符分割
    sentences = re.split(r'[.!?]+', text)
    
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            cleaned_sentences.append(sentence)
    
    return cleaned_sentences

def extract_words_from_sentence(sentence):
    """从句子中提取单词"""
    # 移除标点符号，保留单词和空格
    # 处理缩写形式
    sentence = sentence.replace("'t", " not")  # don't -> do not
    sentence = sentence.replace("'re", " are")  # you're -> you are  
    sentence = sentence.replace("'ll", " will")  # I'll -> I will
    sentence = sentence.replace("'ve", " have")  # I've -> I have
    sentence = sentence.replace("'d", " would")  # I'd -> I would
    sentence = sentence.replace("'m", " am")  # I'm -> I am
    sentence = sentence.replace("'s", " is")  # it's -> it is
    
    # 移除标点符号
    translator = str.maketrans('', '', string.punctuation)
    sentence = sentence.translate(translator)
    
    # 分割单词并转换为小写
    words = sentence.lower().split()
    
    return words

def check_sentence_matches(sentence, pick_words):
    """检查句子是否符合条件"""
    words = extract_words_from_sentence(sentence)
    
    # 检查长度是否>=3
    if len(words) < 3:
        return False
    
    # 检查每个词汇是否都在PICK.txt中
    for word in words:
        if word not in pick_words:
            return False
    
    return True

def process_movie_lines():
    """处理movie_lines.tsv文件"""
    print("🎬 开始处理 movie_lines.tsv...")
    
    # 加载PICK词汇
    pick_words = load_pick_words()
    print(f"📝 加载了 {len(pick_words)} 个PICK词汇")
    
    matching_sentences = []
    seen_sentences = set()  # 用于去重
    total_lines = 0
    total_sentences = 0
    
    # 处理movie_lines.tsv
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/materials/movie_lines.tsv', 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            
            if line_num % 10000 == 0:
                print(f"📊 处理进度: {line_num} 行, 找到 {len(matching_sentences)} 个匹配句子")
            
            # 解析TSV格式：L1045	u0	m0	BIANCA	They do not!
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                dialogue = parts[4]  # 对话内容
                
                # 分割成句子
                sentences = clean_and_split_text(dialogue)
                total_sentences += len(sentences)
                
                for sentence in sentences:
                    # 检查是否符合条件
                    if check_sentence_matches(sentence, pick_words):
                        # 去重检查
                        sentence_lower = sentence.lower().strip()
                        if sentence_lower not in seen_sentences:
                            seen_sentences.add(sentence_lower)
                            matching_sentences.append(sentence.strip())
    
    print(f"\n📈 处理完成:")
    print(f"   总行数: {total_lines:,}")
    print(f"   总句子数: {total_sentences:,}")
    print(f"   匹配句子数: {len(matching_sentences):,}")
    
    # 保存结果
    output_file = '/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/matching_sentences.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence in matching_sentences:
            f.write(sentence + '\n')
    
    print(f"💾 已保存到: matching_sentences.txt")
    
    # 显示前10个匹配的句子作为示例
    print(f"\n📋 前10个匹配句子示例:")
    print("-" * 50)
    for i, sentence in enumerate(matching_sentences[:10], 1):
        print(f"{i:2d}. {sentence}")
    
    return matching_sentences

if __name__ == "__main__":
    sentences = process_movie_lines()
