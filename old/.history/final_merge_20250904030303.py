#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def final_merge_vocabularies():
    """使用去重后的test_cleaned.txt与新词汇合并"""
    
    print("=" * 80)
    print("最终合并词汇表 - test_cleaned.txt + 新词汇")
    print("=" * 80)
    
    # 读取去重后的 test_cleaned.txt
    try:
        with open('test_cleaned.txt', 'r', encoding='utf-8') as f:
            test_words = [word.strip().lower() for word in f.readlines() if word.strip()]
        
        print(f"test_cleaned.txt 词汇数: {len(test_words)}")
        
    except FileNotFoundError:
        print("❌ 找不到 test_cleaned.txt 文件")
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
    
    # 首先添加 test_cleaned.txt 的词汇
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
        print(f"\n🔄 重复的词汇 (已存在于test_cleaned.txt中):")
        for i, word in enumerate(duplicates, 1):
            print(f"{i:2d}. {word}")
    
    # 保存最终合并的词汇表
    output_file = 'final_merged_vocabulary.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in merged_words:
            f.write(word + '\n')
    
    print(f"\n✅ 最终合并完成！")
    print(f"📄 已保存到: {output_file}")
    print(f"📊 test_cleaned: {len(test_words)} + 新词汇: {len(new_added)} = 合并后: {len(merged_words)} 个词")
    
    # 显示合并后的前30个词
    print(f"\n📝 最终词汇表前30个词:")
    for i, word in enumerate(merged_words[:30], 1):
        print(f"{i:2d}. {word}")
    
    if len(merged_words) > 30:
        print(f"... 还有 {len(merged_words) - 30} 个词")
    
    # 创建最终统计报告
    final_stats_file = 'final_vocabulary_stats.txt'
    with open(final_stats_file, 'w', encoding='utf-8') as f:
        f.write("最终词汇表合并统计报告\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"源文件: test.txt (原始: 1039词，去重后: {len(test_words)}词)\n")
        f.write(f"新增词汇: {len(new_words)}个\n")
        f.write(f"实际新增: {len(new_added)}个\n")
        f.write(f"重复词汇: {len(duplicates)}个\n\n")
        f.write(f"最终词汇表总数: {len(merged_words)}个\n\n")
        
        f.write("新增的词汇:\n")
        for word in new_added:
            f.write(f"  {word}\n")
        
        f.write("\n重复的词汇:\n")
        for word in duplicates:
            f.write(f"  {word}\n")
        
        f.write(f"\n完整最终词汇表:\n")
        for i, word in enumerate(merged_words, 1):
            f.write(f"{i:3d}. {word}\n")
    
    print(f"📊 最终统计报告已保存到: {final_stats_file}")
    
    return merged_words

def main():
    """主函数"""
    merged_words = final_merge_vocabularies()
    
    if merged_words:
        print(f"\n🎯 最终词汇表合并完成！")
        print(f"📄 输出文件: final_merged_vocabulary.txt")
        print(f"🔢 总计: {len(merged_words)} 个唯一词汇")
        print(f"✨ 这是一个完全去重的高质量词汇表！")

if __name__ == "__main__":
    main()
