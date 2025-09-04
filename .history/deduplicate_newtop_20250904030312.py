#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def deduplicate_newtop():
    """去除 newtop.txt 中的重复词汇，保持原始顺序"""
    
    print("=" * 60)
    print("去除 newtop.txt 中的重复词汇")
    print("=" * 60)
    
    # 读取原文件
    try:
        with open('newtop.txt', 'r', encoding='utf-8') as f:
            words = [word.strip().lower() for word in f.readlines() if word.strip()]
        
        print(f"原始词汇数: {len(words)}")
        
        # 去重，保持原始顺序
        unique_words = []
        seen = set()
        duplicates = []
        
        for word in words:
            if word not in seen:
                unique_words.append(word)
                seen.add(word)
            else:
                duplicates.append(word)
        
        print(f"去重后词汇数: {len(unique_words)}")
        print(f"重复词汇数: {len(duplicates)}")
        
        # 显示重复的词汇
        if duplicates:
            print(f"\n🔄 发现的重复词汇:")
            duplicate_counts = {}
            for word in duplicates:
                duplicate_counts[word] = duplicate_counts.get(word, 0) + 1
            
            for word, count in duplicate_counts.items():
                print(f"   '{word}': 重复 {count + 1} 次")
        
        # 保存去重后的文件
        with open('newtop.txt', 'w', encoding='utf-8') as f:
            for word in unique_words:
                f.write(word + '\n')
        
        print(f"\n✅ 去重完成！")
        print(f"📄 已更新: newtop.txt")
        print(f"📊 {len(words)} → {len(unique_words)} 个词汇")
        
        # 显示前20个词汇
        print(f"\n📝 去重后前20个词汇:")
        for i, word in enumerate(unique_words[:20], 1):
            print(f"{i:2d}. {word}")
        
        if len(unique_words) > 20:
            print(f"... 还有 {len(unique_words) - 20} 个词")
        
        return unique_words
        
    except FileNotFoundError:
        print("❌ 找不到 newtop.txt 文件")
        return None

def main():
    """主函数"""
    unique_words = deduplicate_newtop()
    
    if unique_words:
        print(f"\n🎯 去重完成！newtop.txt 现在包含 {len(unique_words)} 个唯一词汇。")

if __name__ == "__main__":
    main()
