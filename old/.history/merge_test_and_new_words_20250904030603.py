#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def merge_vocabularies():
    """合并 test.txt 和新增词汇，去重并保持原来的顺序"""
    
    print("=" * 80)
    print("合并词汇表 - test.txt + 新增50词")
    print("=" * 80)
    
    # 读取 test.txt 中的词汇
    try:
        with open('test.txt', 'r', encoding='utf-8') as f:
            test_words = [word.strip().lower() for word in f.readlines() if word.strip()]
        
        print(f"test.txt 词汇数: {len(test_words)} 个")
        
    except FileNotFoundError:
        print("❌ 找不到 test.txt")
        return
    
    # 新增的词汇（转换为小写）
    new_words_raw = [
        "Am", "Are", "Bad", "Bring", "Clean", "Closer", "Comfortable", "Coming", "Computer", "Do",
        "Faith", "Family", "Feel", "Glasses", "Going", "Good", "Goodbye", "Have", "Hello", "Help",
        "Here", "Hope", "How", "Hungry", "I", "Is", "It", "Like", "Music", "My",
        "Need", "No", "Not", "Nurse", "Okay", "Outside", "Please", "Right", "Success", "Tell",
        "That", "They", "Thirsty", "Tired", "Up", "Very", "What", "Where", "Yes", "You"
    ]
    
    new_words = [word.lower() for word in new_words_raw]
    
    print(f"新增词汇: {len(new_words)} 个")
    
    # 合并词汇表，保持原来的顺序，去重
    merged_words = []
    seen = set()
    
    # 首先添加 test.txt 的词汇
    for word in test_words:
        if word not in seen:
            merged_words.append(word)
            seen.add(word)
    
    # 然后添加新词汇（如果不重复的话）
    new_added = []
    for word in new_words:
        if word not in seen:
            merged_words.append(word)
            seen.add(word)
            new_added.append(word)
    
    print(f"实际新增: {len(new_added)} 个词")
    print(f"重复词汇: {len(new_words) - len(new_added)} 个")
    print(f"合并后总数: {len(merged_words)} 个词")
    
    # 显示新增的词汇
    if new_added:
        print(f"\n🆕 新增的词汇:")
        for i, word in enumerate(new_added, 1):
            print(f"{i:2d}. {word}")
    
    # 显示重复的词汇
    duplicates = [word for word in new_words if word in test_words]
    if duplicates:
        print(f"\n🔄 重复的词汇 (已存在于test.txt中):")
        for i, word in enumerate(duplicates, 1):
            print(f"{i:2d}. {word}")
    
    # 保存合并后的词汇表
    output_file = 'merged_vocabulary.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in merged_words:
            f.write(word + '\n')
    
    print(f"\n✅ 合并完成！")
    print(f"📄 已保存: {output_file}")
    print(f"📊 原始test.txt: {len(test_words)} → 合并后: {len(merged_words)} 个词")
    
    # 显示合并后的前20个词
    print(f"\n📝 合并后词汇表前20个词:")
    for i, word in enumerate(merged_words[:20], 1):
        print(f"{i:2d}. {word}")
    
    if len(merged_words) > 20:
        print(f"... 还有 {len(merged_words) - 20} 个词")
    
    # 显示最后20个词（主要是新增的）
    if len(merged_words) > 20:
        print(f"\n📝 最后20个词（主要是新增词汇）:")
        start_idx = max(0, len(merged_words) - 20)
        for i, word in enumerate(merged_words[start_idx:], start_idx + 1):
            print(f"{i:2d}. {word}")
    
    return merged_words

def main():
    """主函数"""
    merged_words = merge_vocabularies()
    
    if merged_words:
        print(f"\n🎯 词汇表已成功合并！")
        print(f"📄 文件: merged_vocabulary.txt")
        print(f"🔢 总词汇数: {len(merged_words)} 个")

if __name__ == "__main__":
    main()
