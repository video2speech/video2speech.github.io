#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def compare_wordlist_and_frequency():
    """比较150词表和词频统计结果，找出缺失的词汇"""
    
    print("🔍 比较 150_words_list.txt 和词频统计结果")
    print("=" * 60)
    
    try:
        # 读取150词表
        with open('materials/150_words_list.txt', 'r', encoding='utf-8') as f:
            wordlist_150 = [line.strip().lower() for line in f.readlines() if line.strip()]
        
        print(f"150词表中的词汇数: {len(wordlist_150)}")
        
        # 读取词频统计结果
        frequency_words = set()
        with open('filtered_sentences_150_words_clean_word_frequency_new.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # 找到词频列表的开始位置
            start_reading = False
            for line in lines:
                if "完整词频列表" in line:
                    start_reading = True
                    continue
                if start_reading and line.strip().startswith(tuple('0123456789')):
                    # 解析词频行，格式: "    1. you                     1699    8.05%     8.05%"
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        word = parts[1]  # 第二部分是词汇
                        frequency_words.add(word.lower())
        
        print(f"词频统计中的词汇数: {len(frequency_words)}")
        
        # 找出在150词表中但不在词频统计中的词汇
        missing_from_frequency = []
        for word in wordlist_150:
            if word not in frequency_words:
                missing_from_frequency.append(word)
        
        # 找出在词频统计中但不在150词表中的词汇
        missing_from_wordlist = []
        for word in frequency_words:
            if word not in wordlist_150:
                missing_from_wordlist.append(word)
        
        print(f"\n📊 比较结果:")
        print(f"   在150词表中但未出现在词频统计中的词汇: {len(missing_from_frequency)} 个")
        print(f"   在词频统计中但不在150词表中的词汇: {len(missing_from_wordlist)} 个")
        
        if missing_from_frequency:
            print(f"\n❌ 在150词表中但未出现在句子中的词汇:")
            print("-" * 50)
            for i, word in enumerate(sorted(missing_from_frequency), 1):
                print(f"   {i:>2}. {word}")
        
        if missing_from_wordlist:
            print(f"\n⚠️  在词频统计中但不在150词表中的词汇:")
            print("-" * 50)
            for i, word in enumerate(sorted(missing_from_wordlist), 1):
                print(f"   {i:>2}. {word}")
        
        # 检查150词表中的重复词汇
        wordlist_150_original = []
        with open('materials/150_words_list.txt', 'r', encoding='utf-8') as f:
            wordlist_150_original = [line.strip() for line in f.readlines() if line.strip()]
        
        # 转换为小写进行重复检查
        wordlist_150_lower = [word.lower() for word in wordlist_150_original]
        duplicates = []
        seen = set()
        for i, word in enumerate(wordlist_150_lower):
            if word in seen:
                duplicates.append((i+1, wordlist_150_original[i], word))
            else:
                seen.add(word)
        
        if duplicates:
            print(f"\n🔄 150词表中的重复词汇:")
            print("-" * 50)
            for line_num, original_word, lower_word in duplicates:
                print(f"   第{line_num}行: '{original_word}' (小写: '{lower_word}')")
        
        # 保存详细报告
        with open('wordlist_frequency_comparison.txt', 'w', encoding='utf-8') as f:
            f.write("150词表与词频统计对比报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"150词表中的词汇数: {len(wordlist_150)}\n")
            f.write(f"词频统计中的词汇数: {len(frequency_words)}\n\n")
            
            f.write(f"在150词表中但未出现在词频统计中的词汇 ({len(missing_from_frequency)} 个):\n")
            f.write("-" * 50 + "\n")
            for i, word in enumerate(sorted(missing_from_frequency), 1):
                f.write(f"{i:>2}. {word}\n")
            
            f.write(f"\n在词频统计中但不在150词表中的词汇 ({len(missing_from_wordlist)} 个):\n")
            f.write("-" * 50 + "\n")
            for i, word in enumerate(sorted(missing_from_wordlist), 1):
                f.write(f"{i:>2}. {word}\n")
            
            if duplicates:
                f.write(f"\n150词表中的重复词汇 ({len(duplicates)} 个):\n")
                f.write("-" * 50 + "\n")
                for line_num, original_word, lower_word in duplicates:
                    f.write(f"第{line_num}行: '{original_word}' (小写: '{lower_word}')\n")
        
        print(f"\n💾 详细报告已保存到: wordlist_frequency_comparison.txt")
        
        return missing_from_frequency, missing_from_wordlist, duplicates
        
    except FileNotFoundError as e:
        print(f"❌ 找不到文件: {e}")
        return None, None, None
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        return None, None, None

def main():
    """主函数"""
    missing_freq, missing_wordlist, duplicates = compare_wordlist_and_frequency()
    
    if missing_freq is not None:
        print(f"\n✅ 对比分析完成！")
        if missing_freq:
            print(f"🚨 发现 {len(missing_freq)} 个词汇在150词表中但未在句子中出现")
        if duplicates:
            print(f"🔄 发现 {len(duplicates)} 个重复词汇在150词表中")

if __name__ == "__main__":
    main()
