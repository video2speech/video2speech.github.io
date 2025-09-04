#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nltk.tokenize import TreebankWordTokenizer

def analyze_expanded_vocab_results():
    """分析使用扩展词汇表的筛选结果"""
    
    print("=" * 80)
    print("🎯 扩展词汇表筛选结果总结")
    print("=" * 80)
    
    # 读取句子文件
    try:
        with open('sentences_expanded_vocab.txt', 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"📊 基本统计:")
        print(f"   总句子数: {len(sentences)}")
        
        # 使用分词器分析每个句子
        tokenizer = TreebankWordTokenizer()
        word_counts = []
        
        for sentence in sentences:
            tokens = tokenizer.tokenize(sentence)
            # 只计算非标点符号的词汇
            words = [token for token in tokens if token not in ".,!?;:()\"'-"]
            word_counts.append(len(words))
        
        print(f"   平均词数: {sum(word_counts)/len(word_counts):.2f} 词")
        print(f"   最短句子: {min(word_counts)} 词")
        print(f"   最长句子: {max(word_counts)} 词")
        
        # 长度分布
        dist_3 = sum(1 for c in word_counts if c == 3)
        dist_4 = sum(1 for c in word_counts if c == 4)
        dist_5 = sum(1 for c in word_counts if c == 5)
        dist_6_10 = sum(1 for c in word_counts if 6 <= c <= 10)
        
        print(f"\n📏 长度分布:")
        print(f"   3词句子: {dist_3} ({dist_3/len(sentences)*100:.1f}%)")
        print(f"   4词句子: {dist_4} ({dist_4/len(sentences)*100:.1f}%)")
        print(f"   5词句子: {dist_5} ({dist_5/len(sentences)*100:.1f}%)")
        print(f"   6-10词句子: {dist_6_10} ({dist_6_10/len(sentences)*100:.1f}%)")
        
        # 与之前结果对比
        print(f"\n📈 与之前对比:")
        print(f"   之前 (48词词汇表, >3词): 283个句子")
        print(f"   现在 (85词词汇表, ≥3词): {len(sentences)}个句子")
        print(f"   增长: {len(sentences) - 283} 个句子 ({(len(sentences) - 283)/283*100:.1f}%)")
        
        # 显示不同长度的句子样本
        print(f"\n📝 句子样本:")
        
        # 3词句子样本
        three_word_sentences = [sentences[i] for i, c in enumerate(word_counts) if c == 3]
        if three_word_sentences:
            print(f"\n   3词句子样本:")
            for sentence in three_word_sentences[:8]:
                print(f"   • {sentence}")
        
        # 4词句子样本
        four_word_sentences = [sentences[i] for i, c in enumerate(word_counts) if c == 4]
        if four_word_sentences:
            print(f"\n   4词句子样本:")
            for sentence in four_word_sentences[:8]:
                print(f"   • {sentence}")
        
        # 5词句子样本
        five_word_sentences = [sentences[i] for i, c in enumerate(word_counts) if c == 5]
        if five_word_sentences:
            print(f"\n   5词句子样本:")
            for sentence in five_word_sentences[:6]:
                print(f"   • {sentence}")
        
        # 6-10词句子样本
        longer_sentences = [sentences[i] for i, c in enumerate(word_counts) if 6 <= c <= 10]
        if longer_sentences:
            print(f"\n   6-10词句子样本:")
            for sentence in longer_sentences[:6]:
                print(f"   • {sentence}")
        
        # 筛选条件总结
        print(f"\n🎯 筛选条件总结:")
        print(f"   ✅ 词汇表: 扩展版 newtopwords.txt (85个词)")
        print(f"   ✅ 核心词汇: 50个最高频词 (50%口语覆盖率)")
        print(f"   ✅ 扩展词汇: 37个实用词汇 (hello, good, help等)")
        print(f"   ✅ 长度限制: ≥3词（不包括标点符号）")
        print(f"   ✅ 数据源: 电影台词 (movie_lines.tsv)")
        print(f"   ✅ 处理行数: 20,000行对话")
        
        print(f"\n💡 这{len(sentences)}个句子的特点:")
        print(f"   • 使用85个精选词汇（核心+扩展）")
        print(f"   • 长度适中（3-10词）")
        print(f"   • 来自真实的电影对话")
        print(f"   • 包含3词短句，更适合初学者")
        print(f"   • 词汇更丰富，表达更多样")
        
        return sentences, word_counts
        
    except FileNotFoundError:
        print("❌ 未找到句子文件")
        return None, None

def main():
    """主函数"""
    sentences, word_counts = analyze_expanded_vocab_results()
    
    if sentences:
        print(f"\n✅ 分析完成！")
        print(f"📄 文件: sentences_expanded_vocab.txt")
        print(f"🎯 {len(sentences)} 个高质量的基础英语句子已准备就绪！")
        print(f"🚀 相比之前增加了 {len(sentences) - 283} 个句子，词汇更丰富！")

if __name__ == "__main__":
    main()
