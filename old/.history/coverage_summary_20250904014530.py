#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def print_coverage_summary():
    """打印词频覆盖率总结"""
    
    print("=" * 60)
    print("           英语口语词频覆盖率分析报告")
    print("=" * 60)
    print()
    
    print("📊 数据来源: 2_2_spokenvwritten.txt")
    print("📚 总词汇数: 4,840 个词")
    print("🔢 总频率: 939,317")
    print()
    
    print("📈 词频覆盖率分析:")
    print("-" * 40)
    
    # 1200词列表
    coverage_1200 = 91.12
    frequency_1200 = 855913
    print(f"🎯 前 1,200 个词:")
    print(f"   ├─ 覆盖率: {coverage_1200:.2f}%")
    print(f"   ├─ 频率总和: {frequency_1200:,}")
    print(f"   └─ 平均频率: {frequency_1200/1200:.2f}")
    print()
    
    # 2000词列表
    coverage_2000 = 94.78
    frequency_2000 = 890315
    print(f"🎯 前 2,000 个词:")
    print(f"   ├─ 覆盖率: {coverage_2000:.2f}%")
    print(f"   ├─ 频率总和: {frequency_2000:,}")
    print(f"   └─ 平均频率: {frequency_2000/2000:.2f}")
    print()
    
    # 增量分析
    diff_words = 2000 - 1200
    diff_coverage = coverage_2000 - coverage_1200
    diff_frequency = frequency_2000 - frequency_1200
    
    print("📊 增量分析 (从1200词到2000词):")
    print("-" * 40)
    print(f"➕ 增加词数: {diff_words} 个")
    print(f"📈 增加覆盖率: {diff_coverage:.2f}%")
    print(f"🔢 增加频率: {diff_frequency:,}")
    print(f"📊 新增词平均频率: {diff_frequency/diff_words:.2f}")
    print()
    
    # 效率分析
    print("💡 效率分析:")
    print("-" * 40)
    print(f"• 前1200词用{1200/4840*100:.1f}%的词汇覆盖了{coverage_1200:.1f}%的频率")
    print(f"• 前2000词用{2000/4840*100:.1f}%的词汇覆盖了{coverage_2000:.1f}%的频率")
    print(f"• 增加{diff_words}词({diff_words/4840*100:.1f}%词汇)仅增加{diff_coverage:.2f}%覆盖率")
    print()
    
    # 建议
    print("🎯 学习建议:")
    print("-" * 40)
    print("✅ 优先掌握前1200词 - 性价比最高")
    print(f"   └─ 用25%的词汇量覆盖91%的日常口语")
    print()
    print("⚡ 进阶学习前2000词")
    print(f"   └─ 额外800词可再提升4%的覆盖率")
    print()
    
    # 可视化进度条
    print("📊 覆盖率可视化:")
    print("-" * 40)
    
    def draw_progress_bar(percentage, width=40):
        filled = int(width * percentage / 100)
        bar = "█" * filled + "░" * (width - filled)
        return f"|{bar}| {percentage:.1f}%"
    
    print(f"1200词: {draw_progress_bar(coverage_1200)}")
    print(f"2000词: {draw_progress_bar(coverage_2000)}")
    print()
    
    print("=" * 60)
    print("💾 生成的文件:")
    print("   • top_1200_words.py - 1200词Python列表")
    print("   • top_2000_words.py - 2000词Python列表") 
    print("   • top_1200_words_simple.txt - 1200词文本文件")
    print("   • top_2000_words_simple.txt - 2000词文本文件")
    print("   • word_lists_comparison.txt - 详细对比报告")
    print("=" * 60)

if __name__ == "__main__":
    print_coverage_summary()
