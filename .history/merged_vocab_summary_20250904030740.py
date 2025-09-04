#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from nltk.tokenize import TreebankWordTokenizer

def analyze_merged_vocab_results():
    """分析使用 merged_vocabulary.txt 筛选的结果"""
    
    print("=" * 80)
    print("🎯 merged_vocabulary.txt 筛选结果总结")
    print("=" * 80)
    
    # 读取句子文件
    try:
        with open('filtered_sentences_merged_vocab_clean.txt', 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"📊 基本统计:")
        print(f"   总句子数: {len(sentences):,} 个（已去重）")
        print(f"   词汇表: merged_vocabulary.txt (1,200个词)")
        print(f"   长度要求: ≥4词（不包括标点符号）")
        
        # 使用分词器分析每个句子
        tokenizer = TreebankWordTokenizer()
        word_counts = []
        
        for sentence in sentences[:1000]:  # 分析前1000个句子以提高速度
            tokens = tokenizer.tokenize(sentence)
            # 只计算非标点符号的词汇
            words = [token for token in tokens if token not in ".,!?;:()\"'-"]
            word_counts.append(len(words))
        
        if word_counts:
            print(f"   平均词数: {sum(word_counts)/len(word_counts):.2f} 词")
            print(f"   最短句子: {min(word_counts)} 词")
            print(f"   最长句子: {max(word_counts)} 词")
        
        # 长度分布（基于前1000个句子）
        if word_counts:
            dist_4_5 = sum(1 for c in word_counts if 4 <= c <= 5)
            dist_6_10 = sum(1 for c in word_counts if 6 <= c <= 10)
            dist_11_plus = sum(1 for c in word_counts if c > 10)
            
            print(f"\n📏 长度分布（基于前1000个句子样本）:")
            print(f"   4-5词句子: {dist_4_5} ({dist_4_5/len(word_counts)*100:.1f}%)")
            print(f"   6-10词句子: {dist_6_10} ({dist_6_10/len(word_counts)*100:.1f}%)")
            print(f"   >10词句子: {dist_11_plus} ({dist_11_plus/len(word_counts)*100:.1f}%)")
        
        # 与其他词汇表对比
        print(f"\n📈 与其他词汇表对比:")
        print(f"   199词词汇表 (≥4词): 2,211个句子")
        print(f"   1,200词词汇表 (≥4词): {len(sentences):,}个句子")
        print(f"   增长: {len(sentences) - 2211:,} 个句子 ({(len(sentences) - 2211)/2211*100:.1f}%)")
        
        # 显示不同类型的句子样本
        print(f"\n📝 句子样本:")
        
        # 短句样本
        short_sentences = [sentences[i] for i, c in enumerate(word_counts) if 4 <= c <= 5]
        if short_sentences:
            print(f"\n   4-5词短句样本:")
            for sentence in short_sentences[:6]:
                print(f"   • {sentence}")
        
        # 中等长度句子样本
        medium_sentences = [sentences[i] for i, c in enumerate(word_counts) if 6 <= c <= 10]
        if medium_sentences:
            print(f"\n   6-10词中句样本:")
            for sentence in medium_sentences[:6]:
                print(f"   • {sentence}")
        
        # 长句样本
        long_sentences = [sentences[i] for i, c in enumerate(word_counts) if c > 10]
        if long_sentences:
            print(f"\n   >10词长句样本:")
            for sentence in long_sentences[:4]:
                print(f"   • {sentence}")
        
        # 随机句子样本
        print(f"\n   随机句子样本:")
        import random
        random_samples = random.sample(sentences, min(8, len(sentences)))
        for sentence in random_samples:
            print(f"   • {sentence}")
        
        # 筛选条件总结
        print(f"\n🎯 筛选条件总结:")
        print(f"   ✅ 词汇表: merged_vocabulary.txt (1,200个精选词汇)")
        print(f"   ✅ 包含: test.txt (1,284词) + 新增50词，去重后1,200词")
        print(f"   ✅ 长度限制: ≥4词（不包括标点符号）")
        print(f"   ✅ 词汇限制: 所有词汇都必须在词汇表中")
        print(f"   ✅ 数据源: 电影台词 (movie_lines.tsv)")
        print(f"   ✅ 处理行数: 50,000行对话")
        print(f"   ✅ 已去重: 移除了1,722个重复句子")
        
        print(f"\n💡 这{len(sentences):,}个句子的特点:")
        print(f"   • 使用1,200个精选词汇（最丰富的词汇表）")
        print(f"   • 长度适中（4-29词）")
        print(f"   • 来自真实的电影对话")
        print(f"   • 词汇丰富，表达多样")
        print(f"   • 适合各种英语学习级别")
        
        return sentences, word_counts
        
    except FileNotFoundError:
        print("❌ 未找到句子文件")
        return None, None

def main():
    """主函数"""
    sentences, word_counts = analyze_merged_vocab_results()
    
    if sentences:
        print(f"\n✅ 分析完成！")
        print(f"📄 文件: filtered_sentences_merged_vocab_clean.txt")
        print(f"🎯 {len(sentences):,} 个高质量的英语句子已准备就绪！")
        print(f"🚀 这是迄今为止最丰富的句子集合！")

if __name__ == "__main__":
    main()
