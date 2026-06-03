#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import nltk
from collections import defaultdict, Counter
from itertools import combinations

class SmartSentenceSelector:
    def __init__(self):
        """智能句子选择器，用于选择覆盖所有目标词汇的最优句子集合"""
        # 尝试下载nltk数据
        try:
            nltk.data.find('corpora/cmudict')
        except LookupError:
            print("📥 下载CMU发音词典...")
            nltk.download('cmudict', quiet=True)
        
        from nltk.corpus import cmudict
        self.cmu_dict = cmudict.dict()
        
        # 39个CMU音素
        self.cmu_phonemes = {
            # 元音 (15个)
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
            # 辅音 (24个)
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
        
        self.target_words = []
        self.sentences = []
        self.selected_sentences = []
    
    def load_data(self):
        """加载目标词汇和句子数据"""
        # 加载目标词汇
        with open('selected_words.json', 'r', encoding='utf-8') as f:
            self.target_words = [word.strip().lower() for word in json.load(f)]
        print(f"📁 加载了 {len(self.target_words)} 个目标词汇")
        
        # 加载句子
        with open('selected_sentences_analyzer.json', 'r', encoding='utf-8') as f:
            self.sentences = json.load(f)
        print(f"📁 加载了 {len(self.sentences)} 个句子")
    
    def clean_text(self, text):
        """清理文本"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def get_words_in_sentence(self, sentence):
        """获取句子中的所有词汇"""
        clean_sentence = self.clean_text(sentence)
        return clean_sentence.split()
    
    def get_phonemes_for_word(self, word):
        """获取单词的音素"""
        clean_word = word.lower().strip()
        if clean_word in self.cmu_dict:
            # 取第一个发音
            phonemes = self.cmu_dict[clean_word][0]
            # 去除重音标记
            clean_phonemes = [re.sub(r'\d', '', p) for p in phonemes]
            # 只保留39个CMU音素
            return [p for p in clean_phonemes if p in self.cmu_phonemes]
        return []
    
    def analyze_sentence_coverage(self, sentence):
        """分析句子覆盖的目标词汇"""
        words = self.get_words_in_sentence(sentence)
        covered_words = []
        for word in words:
            if word in self.target_words:
                covered_words.append(word)
        return covered_words
    
    def greedy_sentence_selection(self, target_count=50):
        """使用贪心算法选择句子"""
        print(f"\n🎯 使用贪心算法选择 {target_count} 个句子...")
        
        # 计算每个句子能覆盖的目标词汇
        sentence_coverage = []
        for i, sentence in enumerate(self.sentences):
            covered = self.analyze_sentence_coverage(sentence)
            sentence_coverage.append({
                'index': i,
                'sentence': sentence,
                'covered_words': covered,
                'coverage_count': len(covered)
            })
        
        # 按覆盖词汇数量排序
        sentence_coverage.sort(key=lambda x: x['coverage_count'], reverse=True)
        
        selected = []
        covered_words_set = set()
        uncovered_words = set(self.target_words)
        
        print(f"📊 开始选择过程...")
        
        # 贪心选择
        for item in sentence_coverage:
            if len(selected) >= target_count:
                break
            
            # 计算这个句子能新增覆盖多少词汇
            new_words = set(item['covered_words']) - covered_words_set
            
            if new_words or len(selected) < 10:  # 前10个句子无论如何都选择
                selected.append(item)
                covered_words_set.update(item['covered_words'])
                uncovered_words -= set(item['covered_words'])
                
                print(f"选择句子 {len(selected):2d}: 新增词汇 {len(new_words)} 个 | {item['sentence'][:60]}{'...' if len(item['sentence']) > 60 else ''}")
        
        # 如果还有未覆盖的词汇，尝试找到包含这些词汇的句子
        if uncovered_words and len(selected) < target_count:
            print(f"\n🔍 寻找包含未覆盖词汇的句子: {uncovered_words}")
            
            for item in sentence_coverage:
                if len(selected) >= target_count:
                    break
                
                if item in selected:
                    continue
                
                # 检查是否包含未覆盖的词汇
                item_words = set(item['covered_words'])
                if item_words & uncovered_words:
                    selected.append(item)
                    covered_words_set.update(item['covered_words'])
                    uncovered_words -= item_words
                    print(f"补充句子 {len(selected):2d}: 覆盖缺失词汇 | {item['sentence'][:60]}{'...' if len(item['sentence']) > 60 else ''}")
        
        self.selected_sentences = selected
        
        print(f"\n✅ 选择完成!")
        print(f"   选中句子数: {len(selected)}")
        print(f"   覆盖词汇数: {len(covered_words_set)}/{len(self.target_words)}")
        print(f"   未覆盖词汇: {uncovered_words}")
        
        return selected, covered_words_set, uncovered_words
    
    def analyze_word_frequency(self):
        """分析词频"""
        word_counter = Counter()
        
        for item in self.selected_sentences:
            words = self.get_words_in_sentence(item['sentence'])
            for word in words:
                word_counter[word] += 1
        
        return word_counter
    
    def analyze_phoneme_frequency(self):
        """分析音素频率"""
        phoneme_counter = Counter()
        
        for item in self.selected_sentences:
            words = self.get_words_in_sentence(item['sentence'])
            for word in words:
                phonemes = self.get_phonemes_for_word(word)
                for phoneme in phonemes:
                    phoneme_counter[phoneme] += 1
        
        return phoneme_counter
    
    def generate_report(self):
        """生成分析报告"""
        if not self.selected_sentences:
            print("❌ 没有选中的句子")
            return
        
        print("\n" + "=" * 80)
        print("📊 选中句子分析报告")
        print("=" * 80)
        
        # 显示选中的句子
        print(f"\n📝 选中的 {len(self.selected_sentences)} 个句子:")
        print("-" * 60)
        for i, item in enumerate(self.selected_sentences, 1):
            covered = ", ".join(item['covered_words']) if item['covered_words'] else "无目标词汇"
            print(f"{i:2d}. {item['sentence']}")
            print(f"    覆盖词汇: {covered}")
        
        # 词频分析
        word_freq = self.analyze_word_frequency()
        print(f"\n📚 词频分析 (前20个高频词):")
        print("-" * 40)
        for word, freq in word_freq.most_common(20):
            status = "✅" if word in self.target_words else "❓"
            print(f"   {word:12s}: {freq:2d} 次 {status}")
        
        # 目标词汇覆盖情况
        covered_target_words = set()
        for item in self.selected_sentences:
            covered_target_words.update(item['covered_words'])
        
        uncovered_target_words = set(self.target_words) - covered_target_words
        
        print(f"\n📋 目标词汇覆盖情况:")
        print(f"   总目标词汇: {len(self.target_words)}")
        print(f"   已覆盖: {len(covered_target_words)} ({len(covered_target_words)/len(self.target_words)*100:.1f}%)")
        print(f"   未覆盖: {len(uncovered_target_words)} ({len(uncovered_target_words)/len(self.target_words)*100:.1f}%)")
        
        if uncovered_target_words:
            print(f"   🟡 未覆盖的目标词汇:")
            uncovered_list = sorted(list(uncovered_target_words))
            for i in range(0, len(uncovered_list), 8):
                group = uncovered_list[i:i+8]
                print(f"      {', '.join(group)}")
        
        # 音素频率分析
        phoneme_freq = self.analyze_phoneme_frequency()
        print(f"\n🔊 音素频率分析 (按频率排序):")
        print("-" * 40)
        for phoneme, freq in phoneme_freq.most_common():
            print(f"   /{phoneme:3s}/: {freq:3d} 次")
        
        # 音素覆盖情况
        covered_phonemes = set(phoneme_freq.keys())
        uncovered_phonemes = self.cmu_phonemes - covered_phonemes
        
        print(f"\n🎯 39音素覆盖情况:")
        print(f"   总音素: {len(self.cmu_phonemes)}")
        print(f"   已覆盖: {len(covered_phonemes)} ({len(covered_phonemes)/len(self.cmu_phonemes)*100:.1f}%)")
        print(f"   未覆盖: {len(uncovered_phonemes)} ({len(uncovered_phonemes)/len(self.cmu_phonemes)*100:.1f}%)")
        
        if uncovered_phonemes:
            print(f"   🟡 未覆盖的音素:")
            uncovered_list = sorted(list(uncovered_phonemes))
            for i in range(0, len(uncovered_list), 10):
                group = uncovered_list[i:i+10]
                print(f"      {', '.join('/' + p + '/' for p in group)}")
        
        # 统计摘要
        total_words = sum(word_freq.values())
        unique_words = len(word_freq)
        total_phonemes = sum(phoneme_freq.values())
        unique_phonemes = len(phoneme_freq)
        
        print(f"\n📈 统计摘要:")
        print(f"   总词汇实例: {total_words}")
        print(f"   不同词汇数: {unique_words}")
        print(f"   总音素实例: {total_phonemes}")
        print(f"   不同音素数: {unique_phonemes}")
    
    def save_results(self, filename="selected_50_sentences.json"):
        """保存选中的句子"""
        if not self.selected_sentences:
            print("❌ 没有句子可保存")
            return
        
        # 保存句子列表
        sentences_only = [item['sentence'] for item in self.selected_sentences]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sentences_only, f, ensure_ascii=False, indent=2)
        
        # 保存详细分析
        detailed_filename = filename.replace('.json', '_detailed.json')
        with open(detailed_filename, 'w', encoding='utf-8') as f:
            json.dump(self.selected_sentences, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到:")
        print(f"   📄 {filename} (句子列表)")
        print(f"   📄 {detailed_filename} (详细分析)")

def main():
    print("🎯 智能句子选择器")
    print("=" * 50)
    print("目标: 从350个句子中选择50个句子，覆盖所有50个目标词汇")
    
    selector = SmartSentenceSelector()
    
    try:
        # 加载数据
        selector.load_data()
        
        # 选择句子
        selected, covered_words, uncovered_words = selector.greedy_sentence_selection(50)
        
        # 生成报告
        selector.generate_report()
        
        # 保存结果
        save_choice = input("\n💾 是否保存选中的句子? (y/N): ").strip().lower()
        if save_choice in ['y', 'yes']:
            selector.save_results()
        
    except FileNotFoundError as e:
        print(f"❌ 文件未找到: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    main()
