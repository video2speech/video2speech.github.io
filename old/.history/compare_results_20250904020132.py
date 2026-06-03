#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def count_lines_in_file(filename):
    """统计文件中的有效句子数量"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 计算非注释行数
        valid_lines = 0
        for line in lines:
            if not line.startswith('#') and line.strip():
                valid_lines += 1
        
        return valid_lines
    except FileNotFoundError:
        return 0

def compare_filter_results():
    """对比修改前后的过滤结果"""
    
    print("=" * 80)
    print("电影台词过滤结果对比")
    print("=" * 80)
    
    # 原始结果（无长度限制）
    original_file = "filtered_movie_sentences.txt"
    original_count = count_lines_in_file(original_file)
    
    # 新结果（8-12词长度限制）
    new_file = "filtered_movie_sentences_8to12words.txt"
    new_count = count_lines_in_file(new_file)
    
    print(f"📊 结果对比:")
    print(f"   原始过滤 (仅词汇限制):     {original_count:4d} 个句子")
    print(f"   新过滤 (词汇+长度8-12词):   {new_count:4d} 个句子")
    
    if original_count > 0:
        reduction_rate = (original_count - new_count) / original_count * 100
        print(f"   减少比例:                  {reduction_rate:.1f}%")
        print(f"   保留比例:                  {100-reduction_rate:.1f}%")
    
    print(f"\n📝 文件位置:")
    print(f"   原始结果: {original_file}")
    print(f"   新结果:   {new_file}")
    
    # 显示一些样本对比
    print(f"\n🔍 新过滤结果样本 (8-12词句子):")
    try:
        with open(new_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        count = 0
        for line in lines:
            if not line.startswith('#') and line.strip():
                print(f"   {line.strip()}")
                count += 1
                if count >= 8:
                    break
                    
    except FileNotFoundError:
        print("   文件未找到")
    
    print(f"\n✅ 修改完成！")
    print(f"   filter_sentences_by_vocabulary.py 已更新")
    print(f"   现在只保留长度为8-12词的句子")

if __name__ == "__main__":
    compare_filter_results()
