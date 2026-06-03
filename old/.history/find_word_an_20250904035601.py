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

def find_word_in_sentences(filename, target_word):
    """在句子中查找特定词汇"""
    
    print(f"🔍 在 {filename} 中查找词汇: '{target_word}'")
    print("=" * 60)
    
    download_nltk_data()
    
    try:
        # 读取句子文件
        with open(filename, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"总句子数: {len(sentences)}")
        
        # 初始化分词器
        tokenizer = TreebankWordTokenizer()
        
        found_sentences = []
        target_word_lower = target_word.lower()
        
        for i, sentence in enumerate(sentences, 1):
            # 分词
            tokens = tokenizer.tokenize(sentence)
            
            # 检查是否包含目标词汇（转换为小写比较）
            for token in tokens:
                if token.lower() == target_word_lower:
                    found_sentences.append((i, sentence, tokens))
                    break
        
        print(f"\n📊 查找结果:")
        print(f"   找到 {len(found_sentences)} 个包含 '{target_word}' 的句子")
        
        if found_sentences:
            print(f"\n📝 包含 '{target_word}' 的句子:")
            print("-" * 60)
            
            for line_num, sentence, tokens in found_sentences:
                print(f"第 {line_num} 行: {sentence}")
                
                # 显示分词结果，高亮目标词汇
                token_display = []
                for token in tokens:
                    if token.lower() == target_word_lower:
                        token_display.append(f"[{token}]")  # 用方括号高亮
                    else:
                        token_display.append(token)
                
                print(f"   分词: {' '.join(token_display)}")
                print()
        else:
            print(f"\n❌ 没有找到包含 '{target_word}' 的句子")
            
            # 尝试查找相似的词汇
            print(f"\n🔍 查找包含 '{target_word}' 的相似词汇...")
            similar_words = set()
            
            for sentence in sentences:
                tokens = tokenizer.tokenize(sentence)
                for token in tokens:
                    if target_word_lower in token.lower():
                        similar_words.add(token.lower())
            
            if similar_words:
                print(f"   找到相似词汇: {sorted(similar_words)}")
            else:
                print(f"   没有找到包含 '{target_word}' 的相似词汇")
        
        return found_sentences
        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {filename}")
        return []
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        return []

def main():
    """主函数"""
    filename = 'filtered_sentences_150_words_clean.txt'
    target_word = 'an'
    
    found_sentences = find_word_in_sentences(filename, target_word)
    
    if found_sentences:
        print(f"✅ 成功找到 {len(found_sentences)} 个句子包含 '{target_word}'")
    else:
        print(f"⚠️  没有找到包含 '{target_word}' 的句子")

if __name__ == "__main__":
    main()
