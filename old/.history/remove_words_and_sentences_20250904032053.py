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

def remove_words_and_filter_sentences():
    """移除指定词汇并过滤包含这些词的句子"""
    
    print("=" * 80)
    print("移除低频词汇并过滤相关句子")
    print("=" * 80)
    
    # 下载NLTK数据
    download_nltk_data()
    
    # 要移除的50个词汇（转换为小写）
    words_to_remove = [
        "through", "years", "his", "says", "which", "actually", "used", "has", "family", "into",
        "bring", "those", "off", "hungry", "day", "went", "many", "hundred", "by", "our",
        "next", "week", "outside", "nurse", "ah", "three", "five", "year", "six", "goodbye",
        "twenty", "closer", "38", "bit", "new", "sort", "faith", "their", "7", "1",
        "2", "48", "28", "quite", "computer", "ten", "glasses", "being", "300", "four"
    ]
    
    # 转换为小写集合，便于快速查找
    remove_set = set(word.lower() for word in words_to_remove)
    
    print(f"要移除的词汇数: {len(words_to_remove)} 个")
    
    # 1. 处理词汇列表
    try:
        with open('materials/200_words_list.txt', 'r', encoding='utf-8') as f:
            original_words = [word.strip() for word in f.readlines() if word.strip()]
        
        print(f"原始词汇数: {len(original_words)}")
        
        # 过滤词汇
        filtered_words = []
        removed_words = []
        
        for word in original_words:
            if word.lower() in remove_set:
                removed_words.append(word)
            else:
                filtered_words.append(word)
        
        print(f"移除词汇数: {len(removed_words)}")
        print(f"保留词汇数: {len(filtered_words)}")
        
        # 保存新的词汇列表
        with open('materials/150_words_list.txt', 'w', encoding='utf-8') as f:
            for word in filtered_words:
                f.write(word + '\n')
        
        print(f"✅ 新词汇列表已保存: materials/150_words_list.txt")
        
    except FileNotFoundError:
        print("❌ 找不到词汇列表文件")
        return
    
    # 2. 处理句子列表
    try:
        with open('materials/200_sentences_list.txt', 'r', encoding='utf-8') as f:
            original_sentences = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"\n原始句子数: {len(original_sentences)}")
        
        # 初始化分词器
        tokenizer = TreebankWordTokenizer()
        
        # 过滤句子
        filtered_sentences = []
        removed_sentences = []
        
        for sentence in original_sentences:
            # 分词
            tokens = tokenizer.tokenize(sentence)
            
            # 检查是否包含要移除的词汇
            contains_removed_word = False
            for token in tokens:
                if token.lower() in remove_set:
                    contains_removed_word = True
                    break
            
            if contains_removed_word:
                removed_sentences.append(sentence)
            else:
                filtered_sentences.append(sentence)
        
        print(f"移除句子数: {len(removed_sentences)}")
        print(f"保留句子数: {len(filtered_sentences)}")
        
        # 保存新的句子列表
        with open('materials/150_sentences_list.txt', 'w', encoding='utf-8') as f:
            for sentence in filtered_sentences:
                f.write(sentence + '\n')
        
        print(f"✅ 新句子列表已保存: materials/150_sentences_list.txt")
        
        # 显示一些被移除的句子样本
        print(f"\n🗑️ 被移除的句子样本 (前10个):")
        for i, sentence in enumerate(removed_sentences[:10], 1):
            print(f"{i:2d}. {sentence}")
        
        if len(removed_sentences) > 10:
            print(f"... 还有 {len(removed_sentences) - 10} 个句子被移除")
        
        # 显示保留的句子样本
        print(f"\n✅ 保留的句子样本 (前10个):")
        for i, sentence in enumerate(filtered_sentences[:10], 1):
            print(f"{i:2d}. {sentence}")
        
        # 创建移除报告
        report_file = 'materials/removal_report.txt'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("词汇和句子移除报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"移除时间: {pd.Timestamp.now() if 'pd' in globals() else 'N/A'}\n\n")
            
            f.write("移除的词汇 (50个):\n")
            f.write("-" * 30 + "\n")
            for i, word in enumerate(words_to_remove, 1):
                f.write(f"{i:2d}. {word}\n")
            
            f.write(f"\n统计信息:\n")
            f.write("-" * 30 + "\n")
            f.write(f"原始词汇数: {len(original_words)}\n")
            f.write(f"保留词汇数: {len(filtered_words)}\n")
            f.write(f"移除词汇数: {len(removed_words)}\n\n")
            
            f.write(f"原始句子数: {len(original_sentences)}\n")
            f.write(f"保留句子数: {len(filtered_sentences)}\n")
            f.write(f"移除句子数: {len(removed_sentences)}\n")
            f.write(f"句子保留率: {len(filtered_sentences)/len(original_sentences)*100:.1f}%\n\n")
            
            f.write("被移除的句子列表:\n")
            f.write("-" * 30 + "\n")
            for i, sentence in enumerate(removed_sentences, 1):
                f.write(f"{i:3d}. {sentence}\n")
        
        print(f"📊 详细报告已保存: {report_file}")
        
    except FileNotFoundError:
        print("❌ 找不到句子列表文件")
        return
    
    # 总结
    print(f"\n🎯 处理完成!")
    print(f"📄 生成的文件:")
    print(f"   • materials/150_words_list.txt - 过滤后的词汇列表 ({len(filtered_words)}个词)")
    print(f"   • materials/150_sentences_list.txt - 过滤后的句子列表 ({len(filtered_sentences)}个句子)")
    print(f"   • materials/removal_report.txt - 详细移除报告")
    
    return filtered_words, filtered_sentences

def main():
    """主函数"""
    try:
        import pandas as pd
        globals()['pd'] = pd
    except ImportError:
        pass
    
    filtered_words, filtered_sentences = remove_words_and_filter_sentences()
    
    if filtered_words and filtered_sentences:
        print(f"\n✅ 任务完成！")
        print(f"🔢 词汇: {len(filtered_words)} 个")
        print(f"📝 句子: {len(filtered_sentences)} 个")

if __name__ == "__main__":
    main()
