#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nltk.tokenize import TreebankWordTokenizer
import nltk

def download_nltk_data():
    """下载必要的NLTK数据"""
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("正在下载NLTK punkt数据...")
        nltk.download('punkt')

def remove_words_and_sentences():
    """移除指定词汇和包含这些词汇的句子"""
    
    print("=" * 80)
    print("移除指定词汇和相关句子")
    print("=" * 80)
    
    # 需要移除的词汇列表
    words_to_remove = [
        'through', 'years', 'his', 'says', 'which', 'actually', 'used', 'has',
        'family', 'into', 'bring', 'those', 'off', 'hungry', 'day', 'went',
        'many', 'hundred', 'by', 'our', 'next', 'week', 'outside', 'nurse',
        'ah', 'three', 'five', 'year', 'six', 'goodbye', 'twenty', 'closer',
        '38', 'bit', 'new', 'sort', 'faith', 'their', '7', '1', '2', '48',
        '28', 'quite', 'computer', 'ten', 'glasses', 'being', '300', 'four'
    ]
    
    # 转换为小写集合以便快速查找
    words_to_remove_set = set(word.lower() for word in words_to_remove)
    
    print(f"需要移除的词汇数: {len(words_to_remove)}")
    
    # 下载NLTK数据
    download_nltk_data()
    tokenizer = TreebankWordTokenizer()
    
    # 处理词汇列表
    print(f"\n1. 处理词汇列表...")
    try:
        with open('materials/200_words_list.txt', 'r', encoding='utf-8') as f:
            original_words = [word.strip() for word in f.readlines() if word.strip()]
        
        print(f"   原始词汇数: {len(original_words)}")
        
        # 移除指定词汇
        filtered_words = []
        removed_words = []
        
        for word in original_words:
            if word.lower() in words_to_remove_set:
                removed_words.append(word)
            else:
                filtered_words.append(word)
        
        print(f"   移除的词汇数: {len(removed_words)}")
        print(f"   保留的词汇数: {len(filtered_words)}")
        
        # 保存新的词汇列表
        with open('materials/150_words_list.txt', 'w', encoding='utf-8') as f:
            for word in filtered_words:
                f.write(word + '\n')
        
        print(f"   ✅ 已保存新词汇列表: materials/150_words_list.txt")
        
    except FileNotFoundError:
        print("   ❌ 找不到 materials/200_words_list.txt")
        return
    
    # 处理句子列表
    print(f"\n2. 处理句子列表...")
    try:
        with open('materials/200_sentences_list.txt', 'r', encoding='utf-8') as f:
            original_sentences = [sentence.strip() for sentence in f.readlines() if sentence.strip()]
        
        print(f"   原始句子数: {len(original_sentences)}")
        
        # 筛选句子
        filtered_sentences = []
        removed_sentences = []
        
        for sentence in original_sentences:
            # 分词
            tokens = tokenizer.tokenize(sentence)
            
            # 检查是否包含需要移除的词汇
            contains_removed_word = False
            for token in tokens:
                # 跳过标点符号
                if token in ".,!?;:()\"'-":
                    continue
                
                if token.lower() in words_to_remove_set:
                    contains_removed_word = True
                    break
            
            if contains_removed_word:
                removed_sentences.append(sentence)
            else:
                filtered_sentences.append(sentence)
        
        print(f"   移除的句子数: {len(removed_sentences)}")
        print(f"   保留的句子数: {len(filtered_sentences)}")
        
        # 保存新的句子列表
        with open('materials/150_sentences_list.txt', 'w', encoding='utf-8') as f:
            for sentence in filtered_sentences:
                f.write(sentence + '\n')
        
        print(f"   ✅ 已保存新句子列表: materials/150_sentences_list.txt")
        
    except FileNotFoundError:
        print("   ❌ 找不到 materials/200_sentences_list.txt")
        return
    
    # 显示移除的词汇
    print(f"\n📋 移除的词汇列表:")
    for i, word in enumerate(removed_words, 1):
        print(f"{i:2d}. {word}")
    
    # 显示一些被移除的句子样本
    print(f"\n📋 被移除的句子样本 (前10个):")
    for i, sentence in enumerate(removed_sentences[:10], 1):
        print(f"{i:2d}. {sentence}")
    
    if len(removed_sentences) > 10:
        print(f"... 还有 {len(removed_sentences) - 10} 个被移除的句子")
    
    # 显示保留的句子样本
    print(f"\n📋 保留的句子样本 (前10个):")
    for i, sentence in enumerate(filtered_sentences[:10], 1):
        print(f"{i:2d}. {sentence}")
    
    # 创建移除报告
    report_file = 'materials/removal_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("词汇和句子移除报告\n")
        f.write("=" * 50 + "\n\n")
        from datetime import datetime
        f.write(f"移除日期: {datetime.now()}\n\n")
        
        f.write(f"词汇处理结果:\n")
        f.write(f"  原始词汇数: {len(original_words)}\n")
        f.write(f"  移除词汇数: {len(removed_words)}\n")
        f.write(f"  保留词汇数: {len(filtered_words)}\n\n")
        
        f.write(f"句子处理结果:\n")
        f.write(f"  原始句子数: {len(original_sentences)}\n")
        f.write(f"  移除句子数: {len(removed_sentences)}\n")
        f.write(f"  保留句子数: {len(filtered_sentences)}\n\n")
        
        f.write("移除的词汇列表:\n")
        for i, word in enumerate(removed_words, 1):
            f.write(f"{i:2d}. {word}\n")
        
        f.write(f"\n被移除的句子列表:\n")
        for i, sentence in enumerate(removed_sentences, 1):
            f.write(f"{i:3d}. {sentence}\n")
    
    print(f"\n💾 移除报告已保存: {report_file}")
    
    print(f"\n✅ 处理完成！")
    print(f"📄 生成的文件:")
    print(f"   • materials/150_words_list.txt - 新的词汇列表 ({len(filtered_words)} 词)")
    print(f"   • materials/150_sentences_list.txt - 新的句子列表 ({len(filtered_sentences)} 句)")
    print(f"   • {report_file} - 详细移除报告")
    
    return filtered_words, filtered_sentences, removed_words, removed_sentences

def main():
    """主函数"""
    import pandas as pd
    
    result = remove_words_and_sentences()
    
    if result:
        filtered_words, filtered_sentences, removed_words, removed_sentences = result
        print(f"\n🎯 任务完成！")
        print(f"   词汇: {len(removed_words)} 个被移除, {len(filtered_words)} 个保留")
        print(f"   句子: {len(removed_sentences)} 个被移除, {len(filtered_sentences)} 个保留")

if __name__ == "__main__":
    main()
