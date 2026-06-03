#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import defaultdict, Counter
import nltk
try:
    from nltk.corpus import cmudict
    cmu_dict = cmudict.dict()
except:
    print("正在下载CMU词典...")
    nltk.download('cmudict')
    from nltk.corpus import cmudict
    cmu_dict = cmudict.dict()

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class SentenceAnalysisVisualizer:
    def __init__(self):
        # CMU音素集合（39个）
        self.cmu_phonemes = {
            # 元音 (15个)
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
            # 辅音 (24个)
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
        
        # 加载数据
        self.selected_data = self.load_selected_data()
        self.all_sentences = self.load_all_sentences()
        
    def load_selected_data(self):
        """加载选中的50句数据"""
        try:
            with open('selected_50_sentences.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载选中句子数据失败: {e}")
            return None
    
    def load_all_sentences(self):
        """加载全部350句数据"""
        try:
            with open('selected_sentences_analyzer.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载全部句子数据失败: {e}")
            return []
    
    def clean_sentence(self, sentence):
        """清理句子"""
        sentence = sentence.lower()
        sentence = re.sub(r'[^\w\s]', '', sentence)
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        return sentence
    
    def get_word_phonemes(self, word):
        """获取词汇的音素"""
        word_lower = word.lower()
        if word_lower in cmu_dict:
            # 取第一个发音
            phonemes = cmu_dict[word_lower][0]
            # 清理音素（去除重音标记）
            clean_phonemes = []
            for phoneme in phonemes:
                clean_phoneme = re.sub(r'\d', '', phoneme)
                if clean_phoneme in self.cmu_phonemes:
                    clean_phonemes.append(clean_phoneme)
            return clean_phonemes
        return []
    
    def analyze_sentences(self, sentences, title=""):
        """分析句子集合的词频和音素频率"""
        print(f"🔄 分析 {title} ({len(sentences)} 个句子)...")
        
        word_counter = Counter()
        phoneme_counter = Counter()
        
        for sentence in sentences:
            words = self.clean_sentence(sentence).split()
            for word in words:
                word_counter[word] += 1
                # 音素分析
                phonemes = self.get_word_phonemes(word)
                for phoneme in phonemes:
                    phoneme_counter[phoneme] += 1
        
        return word_counter, phoneme_counter
    
    def save_sentences_to_txt(self, sentences, filename):
        """保存句子到txt文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            for sentence in sentences:
                f.write(sentence + '\n')
        print(f"✅ 句子已保存到: {filename}")
    
    def plot_word_distribution(self, word_counter, title, filename, top_n=30):
        """绘制词频分布图"""
        # 获取前N个高频词
        top_words = word_counter.most_common(top_n)
        words = [item[0] for item in top_words]
        frequencies = [item[1] for item in top_words]
        
        # 创建图表
        plt.figure(figsize=(15, 8))
        bars = plt.bar(range(len(words)), frequencies, color='steelblue', alpha=0.7)
        
        # 设置标题和标签
        plt.title(f'{title} - 词频分布 (前{top_n}个)', fontsize=16, fontweight='bold')
        plt.xlabel('词汇', fontsize=12)
        plt.ylabel('频率', fontsize=12)
        
        # 设置x轴标签
        plt.xticks(range(len(words)), words, rotation=45, ha='right')
        
        # 在柱子上显示数值
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontsize=10)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 词频分布图已保存到: {filename}")
    
    def plot_phoneme_distribution(self, phoneme_counter, title, filename):
        """绘制音素频率分布图"""
        # 获取所有音素，按频率排序
        phoneme_items = phoneme_counter.most_common()
        phonemes = [f"/{item[0]}/" for item in phoneme_items]
        frequencies = [item[1] for item in phoneme_items]
        
        # 创建图表
        plt.figure(figsize=(16, 10))
        bars = plt.bar(range(len(phonemes)), frequencies, color='darkgreen', alpha=0.7)
        
        # 设置标题和标签
        plt.title(f'{title} - 音素频率分布', fontsize=16, fontweight='bold')
        plt.xlabel('音素', fontsize=12)
        plt.ylabel('频率', fontsize=12)
        
        # 设置x轴标签
        plt.xticks(range(len(phonemes)), phonemes, rotation=45, ha='right')
        
        # 在柱子上显示数值
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图片
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 音素频率分布图已保存到: {filename}")
    
    def process_selected_sentences(self):
        """处理选中的50个句子"""
        print("\n" + "="*60)
        print("📊 任务1: 处理选中的50个句子")
        print("="*60)
        
        if not self.selected_data:
            print("❌ 无法加载选中句子数据")
            return
        
        sentences = self.selected_data['selected_sentences']
        
        # 1. 保存句子到txt
        self.save_sentences_to_txt(sentences, 'selected_50_sentences.txt')
        
        # 2. 分析词频和音素频率
        word_counter, phoneme_counter = self.analyze_sentences(sentences, "选中的50个句子")
        
        # 3. 绘制图表
        self.plot_word_distribution(word_counter, "选中的50个句子", 'selected_50_word_distribution.png')
        self.plot_phoneme_distribution(phoneme_counter, "选中的50个句子", 'selected_50_phoneme_distribution.png')
        
        print(f"📈 统计: 总词汇实例 {sum(word_counter.values())}, 不同词汇 {len(word_counter)}")
        print(f"🔊 统计: 总音素实例 {sum(phoneme_counter.values())}, 不同音素 {len(phoneme_counter)}")
    
    def process_remaining_sentences(self):
        """处理剩余的300个句子（350-50）"""
        print("\n" + "="*60)
        print("📊 任务2: 处理剩余的300个句子")
        print("="*60)
        
        if not self.selected_data or not self.all_sentences:
            print("❌ 无法加载必要数据")
            return
        
        # 获取选中句子的索引
        selected_indices = set(self.selected_data['selected_sentence_indices'])
        
        # 获取剩余句子
        remaining_sentences = []
        for i, sentence in enumerate(self.all_sentences):
            if i not in selected_indices:
                remaining_sentences.append(sentence)
        
        print(f"📊 剩余句子数量: {len(remaining_sentences)}")
        
        # 1. 保存句子到txt
        self.save_sentences_to_txt(remaining_sentences, 'remaining_300_sentences.txt')
        
        # 2. 分析词频和音素频率
        word_counter, phoneme_counter = self.analyze_sentences(remaining_sentences, "剩余的300个句子")
        
        # 3. 绘制图表
        self.plot_word_distribution(word_counter, "剩余的300个句子", 'remaining_300_word_distribution.png')
        self.plot_phoneme_distribution(phoneme_counter, "剩余的300个句子", 'remaining_300_phoneme_distribution.png')
        
        print(f"📈 统计: 总词汇实例 {sum(word_counter.values())}, 不同词汇 {len(word_counter)}")
        print(f"🔊 统计: 总音素实例 {sum(phoneme_counter.values())}, 不同音素 {len(phoneme_counter)}")
    
    def process_all_sentences(self):
        """处理全部350个句子"""
        print("\n" + "="*60)
        print("📊 任务3: 处理全部350个句子")
        print("="*60)
        
        if not self.all_sentences:
            print("❌ 无法加载全部句子数据")
            return
        
        # 1. 保存句子到txt
        self.save_sentences_to_txt(self.all_sentences, 'all_350_sentences.txt')
        
        # 2. 分析词频和音素频率
        word_counter, phoneme_counter = self.analyze_sentences(self.all_sentences, "全部350个句子")
        
        # 3. 绘制图表
        self.plot_word_distribution(word_counter, "全部350个句子", 'all_350_word_distribution.png')
        self.plot_phoneme_distribution(phoneme_counter, "全部350个句子", 'all_350_phoneme_distribution.png')
        
        print(f"📈 统计: 总词汇实例 {sum(word_counter.values())}, 不同词汇 {len(word_counter)}")
        print(f"🔊 统计: 总音素实例 {sum(phoneme_counter.values())}, 不同音素 {len(phoneme_counter)}")
    
    def run_all_tasks(self):
        """运行所有任务"""
        print("🎯 句子分析与可视化工具")
        print("="*60)
        print("任务概览:")
        print("1. 选中的50个句子 → txt + 词频图 + 音素图")
        print("2. 剩余的300个句子 → txt + 词频图 + 音素图") 
        print("3. 全部350个句子 → txt + 词频图 + 音素图")
        
        # 执行三个任务
        self.process_selected_sentences()
        self.process_remaining_sentences()
        self.process_all_sentences()
        
        print("\n" + "="*60)
        print("🎉 所有任务完成！")
        print("="*60)
        print("生成的文件:")
        print("📄 TXT文件:")
        print("   - selected_50_sentences.txt")
        print("   - remaining_300_sentences.txt")
        print("   - all_350_sentences.txt")
        print("📊 词频分布图:")
        print("   - selected_50_word_distribution.png")
        print("   - remaining_300_word_distribution.png")
        print("   - all_350_word_distribution.png")
        print("🔊 音素分布图:")
        print("   - selected_50_phoneme_distribution.png")
        print("   - remaining_300_phoneme_distribution.png")
        print("   - all_350_phoneme_distribution.png")

def main():
    # 检查matplotlib是否可用
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("❌ 需要安装matplotlib:")
        print("   pip install matplotlib")
        return
    
    visualizer = SentenceAnalysisVisualizer()
    visualizer.run_all_tasks()

if __name__ == "__main__":
    main()


