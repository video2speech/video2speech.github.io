#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def find_missing_words():
    """找出在150词表中但没有在新词频统计中出现的词汇"""
    
    print("🔍 查找在150词表中但未出现在新词频统计中的词汇")
    print("=" * 70)
    
    try:
        # 读取150词表
        with open('materials/150_words_list.txt', 'r', encoding='utf-8') as f:
            wordlist_150 = [line.strip() for line in f.readlines() if line.strip()]
        
        # 转换为小写并去重
        wordlist_150_lower = [word.lower() for word in wordlist_150]
        wordlist_150_unique = list(dict.fromkeys(wordlist_150_lower))  # 保持顺序去重
        
        print(f"150词表中的词汇数: {len(wordlist_150)} (原始)")
        print(f"150词表中的唯一词汇数: {len(wordlist_150_unique)} (去重后)")
        
        # 读取新的词频统计结果
        frequency_words = set()
        with open('filtered_sentences_150_words_frequency.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # 找到词频列表的开始位置
            start_reading = False
            for line in lines:
                if "完整词频列表" in line:
                    start_reading = True
                    continue
                if start_reading and line.strip() and line.strip()[0].isdigit():
                    # 解析词频行，格式: "    1. you                     1699    8.05%"
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[0].endswith('.'):
                        word = parts[1]  # 第二部分是词汇
                        frequency_words.add(word.lower())
        
        print(f"新词频统计中的词汇数: {len(frequency_words)}")
        
        # 找出在150词表中但不在词频统计中的词汇
        missing_words = []
        for word in wordlist_150_unique:
            if word not in frequency_words:
                missing_words.append(word)
        
        # 找出在词频统计中但不在150词表中的词汇
        extra_words = []
        for word in frequency_words:
            if word not in wordlist_150_lower:
                extra_words.append(word)
        
        print(f"\n📊 分析结果:")
        print(f"   在150词表中但未出现在新词频统计中: {len(missing_words)} 个")
        print(f"   在新词频统计中但不在150词表中: {len(extra_words)} 个")
        
        if missing_words:
            print(f"\n❌ 在150词表中但未出现在句子中的词汇:")
            print("-" * 60)
            for i, word in enumerate(sorted(missing_words), 1):
                # 找到原始形式
                original_forms = [w for w in wordlist_150 if w.lower() == word]
                original_form = original_forms[0] if original_forms else word
                print(f"   {i:>2}. {word} (原始: '{original_form}')")
        else:
            print(f"\n✅ 所有150词表中的词汇都在句子中出现了！")
        
        if extra_words:
            print(f"\n⚠️  在新词频统计中但不在150词表中的词汇:")
            print("-" * 60)
            for i, word in enumerate(sorted(extra_words), 1):
                print(f"   {i:>2}. {word}")
        
        # 检查150词表中的重复词汇
        duplicates = []
        seen = {}
        for i, word in enumerate(wordlist_150):
            word_lower = word.lower()
            if word_lower in seen:
                duplicates.append((i+1, word, word_lower, seen[word_lower]))
            else:
                seen[word_lower] = (i+1, word)
        
        if duplicates:
            print(f"\n🔄 150词表中的重复词汇:")
            print("-" * 60)
            for line_num, word, word_lower, (first_line, first_word) in duplicates:
                print(f"   第{line_num}行: '{word}' (重复，首次出现在第{first_line}行: '{first_word}')")
        
        # 保存详细报告
        with open('missing_words_analysis_new.txt', 'w', encoding='utf-8') as f:
            f.write("150词表与新词频统计对比分析\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"150词表中的词汇数: {len(wordlist_150)} (原始)\n")
            f.write(f"150词表中的唯一词汇数: {len(wordlist_150_unique)} (去重后)\n")
            f.write(f"新词频统计中的词汇数: {len(frequency_words)}\n\n")
            
            f.write(f"在150词表中但未出现在新词频统计中的词汇 ({len(missing_words)} 个):\n")
            f.write("-" * 60 + "\n")
            for i, word in enumerate(sorted(missing_words), 1):
                original_forms = [w for w in wordlist_150 if w.lower() == word]
                original_form = original_forms[0] if original_forms else word
                f.write(f"{i:>2}. {word} (原始: '{original_form}')\n")
            
            f.write(f"\n在新词频统计中但不在150词表中的词汇 ({len(extra_words)} 个):\n")
            f.write("-" * 60 + "\n")
            for i, word in enumerate(sorted(extra_words), 1):
                f.write(f"{i:>2}. {word}\n")
            
            if duplicates:
                f.write(f"\n150词表中的重复词汇 ({len(duplicates)} 个):\n")
                f.write("-" * 60 + "\n")
                for line_num, word, word_lower, (first_line, first_word) in duplicates:
                    f.write(f"第{line_num}行: '{word}' (重复，首次出现在第{first_line}行: '{first_word}')\n")
        
        print(f"\n💾 详细报告已保存到: missing_words_analysis_new.txt")
        
        return missing_words, extra_words, duplicates
        
    except FileNotFoundError as e:
        print(f"❌ 找不到文件: {e}")
        return None, None, None
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        return None, None, None

def main():
    """主函数"""
    missing_words, extra_words, duplicates = find_missing_words()
    
    if missing_words is not None:
        print(f"\n✅ 分析完成！")
        if missing_words:
            print(f"🚨 发现 {len(missing_words)} 个词汇在150词表中但未在新筛选的句子中出现")
        else:
            print(f"🎉 所有150词表中的词汇都在新筛选的句子中出现了！")
        
        if extra_words:
            print(f"⚠️  发现 {len(extra_words)} 个额外词汇在新词频统计中")
        
        if duplicates:
            print(f"🔄 发现 {len(duplicates)} 个重复词汇在150词表中")

if __name__ == "__main__":
    main()
