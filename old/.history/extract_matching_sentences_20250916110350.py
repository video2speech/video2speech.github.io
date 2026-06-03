#!/usr/bin/env python3
"""
从 movie_lines.tsv 中提取符合条件的句子
条件：句子长度 >= 4个词汇，且每个词汇都在 PICK.txt 中
"""

import re
import string

def load_pick_words():
    """加载 PICK.txt 中的词汇集"""
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/PICK.txt', 'r', encoding='utf-8') as f:
        words = set(word.strip().lower() for word in f if word.strip())
    return words

def clean_word(word):
    """清理词汇，移除标点符号"""
    # 移除标点符号，但保留撇号（用于缩写）
    word = word.strip()
    # 移除开头和结尾的标点符号，但保留中间的撇号
    word = re.sub(r'^[^\w\']+|[^\w\']+$', '', word)
    return word.lower()

def split_into_sentences(text):
    """将文本分割成句子"""
    # 使用句号、问号、感叹号分割句子
    sentences = re.split(r'[.!?]+', text)
    # 清理空白句子
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def check_sentence(sentence, pick_words):
    """检查句子是否符合条件"""
    # 分割成词汇
    words = sentence.split()
    
    # 清理词汇并检查
    cleaned_words = []
    for word in words:
        cleaned = clean_word(word)
        if cleaned:  # 只保留非空词汇
            cleaned_words.append(cleaned)
    
    # 检查长度
    if len(cleaned_words) < 4:
        return False
    
    # 检查每个词汇是否都在 PICK.txt 中
    for word in cleaned_words:
        if word not in pick_words:
            return False
    
    return True

def extract_matching_sentences():
    """提取符合条件的句子"""
    print("加载词汇集...")
    pick_words = load_pick_words()
    print(f"词汇集大小: {len(pick_words)}")
    
    matching_sentences = []
    total_lines = 0
    total_sentences = 0
    
    print("处理 movie_lines.tsv...")
    
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/materials/movie_lines.tsv', 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            
            if line_num % 10000 == 0:
                print(f"处理进度: {line_num} 行, 找到 {len(matching_sentences)} 个匹配句子")
            
            # 解析 TSV 格式，提取对话内容（最后一列）
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
            
            dialogue = parts[-1]  # 最后一列是对话内容
            
            # 分割成句子
            sentences = split_into_sentences(dialogue)
            total_sentences += len(sentences)
            
            # 检查每个句子
            for sentence in sentences:
                if check_sentence(sentence, pick_words):
                    matching_sentences.append(sentence.strip())
    
    print(f"\n处理完成!")
    print(f"总行数: {total_lines}")
    print(f"总句子数: {total_sentences}")
    print(f"符合条件的句子: {len(matching_sentences)}")
    
    # 保存到文件
    output_file = '/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/matching_sentences.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence in matching_sentences:
            f.write(sentence + '\n')
    
    print(f"✅ 结果已保存到: matching_sentences.txt")
    
    # 显示前几个示例
    if matching_sentences:
        print(f"\n📝 前10个匹配的句子示例:")
        print("-" * 50)
        for i, sentence in enumerate(matching_sentences[:10], 1):
            print(f"{i:2d}. {sentence}")
    
    return matching_sentences

def test_sentence_checking():
    """测试句子检查功能"""
    pick_words = load_pick_words()
    
    test_sentences = [
        "I think you are right",  # 应该匹配
        "They have what we need",  # 应该匹配
        "This is very complicated",  # 可能不匹配（complicated不在PICK中）
        "Yes we can do it",  # 应该匹配
        "No way",  # 长度不够
    ]
    
    print("测试句子检查功能:")
    print("-" * 40)
    for sentence in test_sentences:
        result = check_sentence(sentence, pick_words)
        print(f"'{sentence}' -> {result}")

if __name__ == "__main__":
    # 先测试功能
    print("🧪 测试句子检查功能...")
    test_sentence_checking()
    
    print("\n" + "="*60)
    print("🎬 开始处理电影对话...")
    sentences = extract_matching_sentences()
