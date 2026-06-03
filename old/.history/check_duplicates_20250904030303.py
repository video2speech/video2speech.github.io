#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def check_duplicates_in_test():
    """检查 test.txt 中的重复词汇"""
    
    print("=" * 60)
    print("检查 test.txt 中的重复词汇")
    print("=" * 60)
    
    # 读取 test.txt
    try:
        with open('test.txt', 'r', encoding='utf-8') as f:
            words = [word.strip().lower() for word in f.readlines() if word.strip()]
        
        print(f"test.txt 原始词汇数: {len(words)}")
        
        # 去重
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
        
        # 统计重复词汇的频率
        duplicate_counts = {}
        for word in duplicates:
            duplicate_counts[word] = duplicate_counts.get(word, 0) + 1
        
        print(f"\n🔄 重复词汇统计:")
        for word, count in sorted(duplicate_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   '{word}': 出现 {count + 1} 次")
        
        # 保存去重后的test.txt
        with open('test_cleaned.txt', 'w', encoding='utf-8') as f:
            for word in unique_words:
                f.write(word + '\n')
        
        print(f"\n✅ 已保存去重后的词汇表到: test_cleaned.txt")
        
        return unique_words, duplicates
        
    except FileNotFoundError:
        print("❌ 找不到 test.txt 文件")
        return None, None

def main():
    """主函数"""
    unique_words, duplicates = check_duplicates_in_test()
    
    if unique_words:
        print(f"\n📊 总结:")
        print(f"   原始: 1039 个词汇")
        print(f"   去重: {len(unique_words)} 个词汇")
        print(f"   移除: {len(duplicates)} 个重复")

if __name__ == "__main__":
    main()
