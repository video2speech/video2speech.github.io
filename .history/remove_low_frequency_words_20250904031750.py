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

def remove_low_frequency_words():
    """移除低频词汇并过滤句子"""
    
    print("=" * 80)
    print("移除低频词汇并过滤句子")
    print("=" * 80)
    
    # 下载NLTK数据
    download_nltk_data()
    
    # 要移除的低频词汇列表
    words_to_remove = [
        "through", "years", "his", "says", "which", "actually", "used", "has", 
        "family", "into", "bring", "those", "off", "hungry", "day", "went",
        "many", "hundred", "by", "our", "next", "week", "outside", "nurse",
        "ah", "three", "five", "year", "six", "goodbye", "twenty", "closer",
        "38", "bit", "new", "sort", "faith", "their", "7", "1", "2", "48",
        "28", "quite", "computer", "ten", "glasses", "being", "300", "four"
    ]
    
    # 转换为小写集合，便于比较
    words_to_remove_set = set(word.lower() for word in words_to_remove)
    
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
            if word.lower() not in words_to_remove_set:
                filtered_words.append(word)
            else:
                removed_words.append(word)
        
        print(f"过滤后词汇数: {len(filtered_words)}")
        print(f"实际移除词汇数: {len(removed_words)}")
        
        # 保存过滤后的词汇列表
        with open('materials/150_words_list.txt', 'w', encoding='utf-8') as f:
            for word in filtered_words:
                f.write(word + '\n')
        
        print(f"✅ 已保存过滤后的词汇列表: materials/150_words_list.txt")
        
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
            sentence_words = set(token.lower() for token in tokens if token not in ".,!?;:()\"'-")
            
            # 如果句子中没有要移除的词汇，则保留
            if not sentence_words.intersection(words_to_remove_set):
                filtered_sentences.append(sentence)
            else:
                # 找出句子中包含的要移除的词汇
                found_words = sentence_words.intersection(words_to_remove_set)
                removed_sentences.append((sentence, list(found_words)))
        
        print(f"过滤后句子数: {len(filtered_sentences)}")
        print(f"移除句子数: {len(removed_sentences)}")
        
        # 保存过滤后的句子列表
        with open('materials/150_sentences_list.txt', 'w', encoding='utf-8') as f:
            for sentence in filtered_sentences:
                f.write(sentence + '\n')
        
        print(f"✅ 已保存过滤后的句子列表: materials/150_sentences_list.txt")
        
    except FileNotFoundError:
        print("❌ 找不到句子列表文件")
        return
    
    # 3. 生成详细报告
    report_file = 'materials/removal_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("低频词汇移除报告\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("移除的词汇列表:\n")
        f.write("-" * 30 + "\n")
        for i, word in enumerate(removed_words, 1):
            f.write(f"{i:2d}. {word}\n")
        
        f.write(f"\n词汇统计:\n")
        f.write("-" * 30 + "\n")
        f.write(f"原始词汇数: {len(original_words)}\n")
        f.write(f"移除词汇数: {len(removed_words)}\n")
        f.write(f"保留词汇数: {len(filtered_words)}\n")
        
        f.write(f"\n句子统计:\n")
        f.write("-" * 30 + "\n")
        f.write(f"原始句子数: {len(original_sentences)}\n")
        f.write(f"移除句子数: {len(removed_sentences)}\n")
        f.write(f"保留句子数: {len(filtered_sentences)}\n")
        
        f.write(f"\n移除的句子样本 (前20个):\n")
        f.write("-" * 50 + "\n")
        for i, (sentence, found_words) in enumerate(removed_sentences[:20], 1):
            f.write(f"{i:2d}. {sentence[:60]}{'...' if len(sentence) > 60 else ''}\n")
            f.write(f"    包含词汇: {', '.join(found_words)}\n\n")
    
    print(f"📄 已保存详细报告: {report_file}")
    
    # 4. 显示统计摘要
    print(f"\n📊 处理结果摘要:")
    print(f"   词汇列表: {len(original_words)} → {len(filtered_words)} 个")
    print(f"   句子列表: {len(original_sentences)} → {len(filtered_sentences)} 个")
    print(f"   移除词汇: {len(removed_words)} 个")
    print(f"   移除句子: {len(removed_sentences)} 个")
    
    # 显示一些被移除的句子样本
    print(f"\n🗑️ 被移除的句子样本 (前5个):")
    for i, (sentence, found_words) in enumerate(removed_sentences[:5], 1):
        print(f"{i}. {sentence}")
        print(f"   包含词汇: {', '.join(found_words)}")
    
    # 显示保留的句子样本
    print(f"\n✅ 保留的句子样本 (前5个):")
    for i, sentence in enumerate(filtered_sentences[:5], 1):
        print(f"{i}. {sentence}")
    
    return filtered_words, filtered_sentences

def main():
    """主函数"""
    filtered_words, filtered_sentences = remove_low_frequency_words()
    
    if filtered_words and filtered_sentences:
        print(f"\n🎯 处理完成！")
        print(f"📄 生成的文件:")
        print(f"   • materials/150_words_list.txt - 过滤后的词汇列表")
        print(f"   • materials/150_sentences_list.txt - 过滤后的句子列表")
        print(f"   • materials/removal_report.txt - 详细移除报告")

if __name__ == "__main__":
    main()
