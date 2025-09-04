#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def merge_vocabularies():
    """合并 test.txt 和新词汇，去重并保持顺序"""
    
    print("=" * 80)
    print("合并词汇表 - test.txt + 新词汇")
    print("=" * 80)
    
    # 读取 test.txt 中的词汇
    try:
        with open('test.txt', 'r', encoding='utf-8') as f:
            test_words = [word.strip().lower() for word in f.readlines() if word.strip()]
        
        print(f"test.txt 词汇数: {len(test_words)}")
        
    except FileNotFoundError:
        print("❌ 找不到 test.txt 文件")
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
    print(f"📄 已保存到: {output_file}")
    print(f"📊 test.txt: {len(test_words)} + 新词汇: {len(new_added)} = 合并后: {len(merged_words)} 个词")
    
    # 显示合并后的前30个词
    print(f"\n📝 合并后词汇表前30个词:")
    for i, word in enumerate(merged_words[:30], 1):
        print(f"{i:2d}. {word}")
    
    if len(merged_words) > 30:
        print(f"... 还有 {len(merged_words) - 30} 个词")
    
    # 创建统计报告
    stats_file = 'vocabulary_merge_stats.txt'
    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("词汇表合并统计报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"源文件1: test.txt\n")
        f.write(f"源文件1词汇数: {len(test_words)}\n\n")
        f.write(f"新增词汇数: {len(new_words)}\n")
        f.write(f"实际新增: {len(new_added)}\n")
        f.write(f"重复词汇: {len(duplicates)}\n\n")
        f.write(f"合并后总词汇数: {len(merged_words)}\n\n")
        
        f.write("新增的词汇:\n")
        for word in new_added:
            f.write(f"  {word}\n")
        
        f.write("\n重复的词汇:\n")
        for word in duplicates:
            f.write(f"  {word}\n")
        
        f.write(f"\n完整词汇表:\n")
        for i, word in enumerate(merged_words, 1):
            f.write(f"{i:3d}. {word}\n")
    
    print(f"📊 统计报告已保存到: {stats_file}")
    
    return merged_words

def main():
    """主函数"""
    merged_words = merge_vocabularies()
    
    if merged_words:
        print(f"\n🎯 词汇表合并完成！")
        print(f"📄 输出文件: merged_vocabulary.txt")
        print(f"🔢 总计: {len(merged_words)} 个唯一词汇")

if __name__ == "__main__":
    main()
