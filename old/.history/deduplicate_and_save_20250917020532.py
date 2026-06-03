#!/usr/bin/env python3
"""
去重词汇列表并保存到 PICK.txt
"""

def extract_and_deduplicate_words():
    """从终端选择的词汇列表中提取并去重"""
    
    # 从您提供的列表中提取词汇
    word_list = [
        "the", "I", "you", "and", "it", "a", "is", "to", "of", "that",
        "in", "we", "do", "they", "yes", "have", "what", "but", "for", "on",
        "this", "know", "so", "are", "if", "with", "no", "there", "think", "can",
        "get", "did", "or", "would", "them", "now", "your", "about", "when", "will",
        "client", "appeal", "confirm", "judge", "signature", "litigation", "exposure", 
        "point", "case", "trial"
    ]
    
    print(f"原始词汇数量: {len(word_list)}")
    
    # 去重 - 使用 set 去重，然后转回 list 保持顺序
    seen = set()
    unique_words = []
    for word in word_list:
        if word.lower() not in seen:
            seen.add(word.lower())
            unique_words.append(word)
    
    print(f"去重后词汇数量: {len(unique_words)}")
    
    # 显示重复的词汇（如果有）
    duplicates = len(word_list) - len(unique_words)
    if duplicates > 0:
        print(f"发现 {duplicates} 个重复词汇")
    else:
        print("没有发现重复词汇")
    
    # 保存到 PICK.txt
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/PICK.txt', 'w', encoding='utf-8') as f:
        for word in unique_words:
            f.write(word + '\n')
    
    print(f"\n✅ 已保存到 PICK.txt")
    print(f"📝 去重后的词汇列表:")
    print("-" * 40)
    
    # 显示去重后的词汇列表
    for i, word in enumerate(unique_words, 1):
        print(f"{i:2d}. {word}")
    
    return unique_words

if __name__ == "__main__":
    words = extract_and_deduplicate_words()
