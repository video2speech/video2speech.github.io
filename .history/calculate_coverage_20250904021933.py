#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

def calculate_word_coverage(filename):
    """计算词频覆盖率"""
    print("=" * 80)
    print("词频覆盖率计算")
    print("=" * 80)
    
    # 读取词频数据
    print(f"正在读取词频数据: {filename}")
    
    try:
        # 读取文件，跳过第一行标题和空行
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        words_data = []
        
        for line in lines[1:]:  # 跳过标题行
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('\t')
            if len(parts) >= 5:
                word = parts[0].strip()
                pos = parts[1].strip()
                
                try:
                    fr_spoken = int(parts[2].strip())  # 口语频率
                    ll = parts[3].strip()  # 对数似然值
                    fr_written = float(parts[4].strip())  # 书面语频率
                    
                    words_data.append({
                        'word': word,
                        'pos': pos,
                        'fr_spoken': fr_spoken,
                        'll': ll,
                        'fr_written': fr_written
                    })
                    
                except (ValueError, IndexError) as e:
                    continue
        
        print(f"成功加载 {len(words_data)} 个词汇")
        
        # 创建DataFrame并按口语频率排序
        df = pd.DataFrame(words_data)
        df = df.sort_values('fr_spoken', ascending=False)
        
        # 计算总频率
        total_frequency = df['fr_spoken'].sum()
        print(f"总口语频率: {total_frequency:,}")
        
        # 计算累积覆盖率
        df['cumulative_freq'] = df['fr_spoken'].cumsum()
        df['coverage_percent'] = (df['cumulative_freq'] / total_frequency) * 100
        
        # 找到50%覆盖率的位置
        coverage_50_idx = df[df['coverage_percent'] >= 50.0].index[0]
        words_for_50_percent = coverage_50_idx + 1  # 因为索引从0开始
        
        # 找到其他关键覆盖率点
        milestones = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]
        coverage_results = []
        
        for milestone in milestones:
            try:
                idx = df[df['coverage_percent'] >= milestone].index[0]
                word_count = idx + 1
                actual_coverage = df.iloc[idx]['coverage_percent']
                top_word = df.iloc[idx]['word']
                
                coverage_results.append({
                    'target_coverage': milestone,
                    'word_count': word_count,
                    'actual_coverage': actual_coverage,
                    'top_word': top_word
                })
            except IndexError:
                pass
        
        # 显示结果
        print(f"\n📊 词频覆盖率分析:")
        print("-" * 60)
        print(f"{'目标覆盖率':<8} {'需要词数':<8} {'实际覆盖率':<12} {'最后一个词'}")
        print("-" * 60)
        
        for result in coverage_results:
            print(f"{result['target_coverage']:>6}%   {result['word_count']:>6}   {result['actual_coverage']:>9.2f}%   {result['top_word']}")
        
        # 重点显示50%覆盖率
        print(f"\n🎯 关键发现:")
        print(f"   需要 {words_for_50_percent} 个最高频词汇才能覆盖 50% 的口语使用频率")
        print(f"   第{words_for_50_percent}个词是: '{df.iloc[coverage_50_idx]['word']}'")
        print(f"   实际覆盖率: {df.iloc[coverage_50_idx]['coverage_percent']:.2f}%")
        
        # 显示前20个最高频词
        print(f"\n📝 前20个最高频词:")
        print("-" * 50)
        print(f"{'排名':<4} {'词汇':<12} {'频率':<8} {'累积覆盖率'}")
        print("-" * 50)
        
        for i in range(min(20, len(df))):
            word = df.iloc[i]['word']
            freq = df.iloc[i]['fr_spoken']
            coverage = df.iloc[i]['coverage_percent']
            print(f"{i+1:>3}. {word:<12} {freq:>6}   {coverage:>8.2f}%")
        
        # 保存详细结果
        output_file = 'word_coverage_analysis.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("词频覆盖率详细分析\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"数据源: {filename}\n")
            f.write(f"总词汇数: {len(df)}\n")
            f.write(f"总频率: {total_frequency:,}\n\n")
            
            f.write("覆盖率里程碑:\n")
            f.write("-" * 40 + "\n")
            for result in coverage_results:
                f.write(f"{result['target_coverage']:>3}%覆盖率: {result['word_count']:>4}个词 (实际{result['actual_coverage']:.2f}%)\n")
            
            f.write(f"\n前100个最高频词详细列表:\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'排名':<4} {'词汇':<15} {'词性':<6} {'频率':<8} {'累积覆盖率'}\n")
            f.write("-" * 60 + "\n")
            
            for i in range(min(100, len(df))):
                row = df.iloc[i]
                f.write(f"{i+1:>3}. {row['word']:<15} {row['pos']:<6} {row['fr_spoken']:>6}   {row['coverage_percent']:>8.2f}%\n")
        
        print(f"\n💾 详细分析已保存到: {output_file}")
        
        return coverage_results
        
    except Exception as e:
        print(f"处理文件时出错: {e}")
        return None

def main():
    """主函数"""
    filename = 'others/2_2_spokenvwritten.txt'
    results = calculate_word_coverage(filename)
    
    if results:
        print(f"\n✅ 分析完成！")
        
        # 找到50%覆盖率的结果
        result_50 = next((r for r in results if r['target_coverage'] == 50), None)
        if result_50:
            print(f"\n🔥 答案: 需要前 {result_50['word_count']} 个最高频词汇来覆盖 50% 的口语使用概率！")

if __name__ == "__main__":
    main()
