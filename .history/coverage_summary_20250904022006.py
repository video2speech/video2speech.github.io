#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def create_visual_summary():
    """创建视觉化的覆盖率总结"""
    
    print("=" * 80)
    print("🎯 词频覆盖率分析结果总结")
    print("=" * 80)
    
    # 关键数据
    coverage_data = [
        (10, 3, "the, I, you"),
        (20, 8, "+ and, it, a, 's, to"),
        (30, 16, "+ of, that, n't, in, we, is, do, they"),
        (40, 29, "+ er, was, yeah, have, for, are, with, but, know, like, so, or"),
        (50, 49, "+ this, can, he, not, me, what, on, get, would, up, if, go, out, about, just, think, one, all"),
        (60, 84, "+ will, see, at, there, right, my, well, got, oh, now, her, him, time, back, she"),
        (70, 151, "+ way, come, say, who, could, want, how, then, make, your, were"),
        (80, 349, "+ more, here, did, when, take, good, some, where, why, two"),
        (90, 1039, "+ 690 more words"),
        (95, 2036, "+ 997 more words"),
        (99, 3867, "+ 1831 more words")
    ]
    
    print("📊 覆盖率里程碑:")
    print("-" * 60)
    
    for coverage, words, examples in coverage_data:
        bar_length = coverage // 2  # 每2%一个字符
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{coverage:>3}% |{bar}| {words:>4} 词")
        if coverage <= 50:
            print(f"     关键词: {examples}")
        print()
    
    print("🔥 关键发现:")
    print(f"   • 仅需 49 个词就能覆盖 50% 的口语使用频率！")
    print(f"   • 前3个词(the, I, you)就覆盖了 10.11%")
    print(f"   • 前8个词就覆盖了 20.86%")
    print(f"   • 前16个词就覆盖了 30.67%")
    print(f"   • 前29个词就覆盖了 40.35%")
    
    print(f"\n📈 语言学习启示:")
    print(f"   • 掌握前50个最高频词 = 理解一半的口语内容")
    print(f"   • 掌握前100个词 ≈ 理解60%的口语内容") 
    print(f"   • 掌握前1000个词 ≈ 理解90%的口语内容")
    print(f"   • 这体现了著名的'帕累托法则'(80/20法则)")
    
    print(f"\n🎯 实用建议:")
    print(f"   • 初学者：重点掌握前50个超高频词")
    print(f"   • 进阶者：扩展到前500-1000个高频词")
    print(f"   • 高级者：掌握前2000个词可达到95%覆盖率")
    
    # 创建前49个词的列表
    top_49_words = [
        "the", "I", "you", "and", "it", "a", "'s", "to", "of", "that",
        "n't", "in", "we", "is", "do", "they", "er", "was", "yeah", "have",
        "for", "are", "with", "but", "know", "like", "so", "or", "this", "can",
        "he", "not", "me", "what", "on", "get", "would", "up", "if", "go",
        "out", "about", "just", "think", "one", "all", "will", "see", "at"
    ]
    
    print(f"\n📝 50%覆盖率的前49个关键词:")
    print("-" * 60)
    
    # 分行显示，每行10个词
    for i in range(0, len(top_49_words), 10):
        line_words = top_49_words[i:i+10]
        print(f"{i+1:>2}-{min(i+10, len(top_49_words)):>2}: " + " • ".join(line_words))
    
    print(f"\n💡 这49个词就是英语口语的'黄金词汇'！")

if __name__ == "__main__":
    create_visual_summary()