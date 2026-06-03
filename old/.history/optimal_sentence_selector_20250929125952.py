#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
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

class OptimalSentenceSelector:
    def __init__(self):
        self.target_words = self.load_target_words()
        self.sentences = self.load_sentences()
        self.selected_sentences = []
        self.word_coverage = defaultdict(list)  # word -> list of sentence indices
        
        # CMU音素集合（39个）
        self.cmu_phonemes = {
            # 元音 (15个)
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
            # 辅音 (24个)
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
    
    def load_target_words(self):
        """加载目标词汇"""
        try:
            with open('selected_words.json', 'r', encoding='utf-8') as f:
                words = json.load(f)
                return set(word.lower().strip() for word in words if word.strip())
        except Exception as e:
            print(f"❌ 加载目标词汇失败: {e}")
            return set()
    
    def load_sentences(self):
        """加载句子"""
        try:
            with open('selected_sentences_analyzer.json', 'r', encoding='utf-8') as f:
                sentences = json.load(f)
                print(f"📁 加载了 {len(sentences)} 个句子")
                return sentences
        except Exception as e:
            print(f"❌ 加载句子失败: {e}")
            return []
    
    def clean_sentence(self, sentence):
        """清理句子"""
        sentence = sentence.lower()
        sentence = re.sub(r'[^\w\s]', '', sentence)
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        return sentence
    
    def extract_words_from_sentence(self, sentence):
        """从句子中提取词汇"""
        clean_text = self.clean_sentence(sentence)
        return set(clean_text.split())
    
    def build_word_sentence_mapping(self):
        """构建词汇-句子映射"""
        print("🔄 构建词汇-句子映射...")
        word_sentence_map = defaultdict(list)
        
        for i, sentence in enumerate(self.sentences):
            words = self.extract_words_from_sentence(sentence)
            for word in words:
                if word in self.target_words:
                    word_sentence_map[word].append(i)
        
        # 统计每个目标词出现在多少句子中
        coverage_stats = {}
        for word in self.target_words:
            count = len(word_sentence_map[word])
            coverage_stats[word] = count
            if count == 0:
                print(f"⚠️  词汇 '{word}' 未在任何句子中找到")
        
        print(f"📊 词汇覆盖统计:")
        covered_words = sum(1 for count in coverage_stats.values() if count > 0)
        print(f"   目标词汇总数: {len(self.target_words)}")
        print(f"   有覆盖的词汇: {covered_words}")
        print(f"   覆盖率: {covered_words/len(self.target_words)*100:.1f}%")
        
        return word_sentence_map
    
    def greedy_sentence_selection(self, word_sentence_map, max_sentences=50, min_word_coverage=2):
        """贪心算法选择句子"""
        print(f"\n🔄 开始贪心选择算法...")
        print(f"   目标句子数: {max_sentences}")
        print(f"   每个词最少覆盖次数: {min_word_coverage}")
        
        selected_indices = set()
        word_coverage_count = defaultdict(int)
        
        # 优先选择覆盖稀有词汇的句子
        word_rarity = {}
        for word, sentence_list in word_sentence_map.items():
            word_rarity[word] = len(sentence_list)
        
        while len(selected_indices) < max_sentences:
            best_sentence = -1
            best_score = -1
            
            for i, sentence in enumerate(self.sentences):
                if i in selected_indices:
                    continue
                
                # 计算这个句子的价值得分
                score = 0
                words_in_sentence = self.extract_words_from_sentence(sentence)
                
                for word in words_in_sentence:
                    if word in self.target_words:
                        # 如果这个词还没达到最小覆盖要求，给更高分
                        if word_coverage_count[word] < min_word_coverage:
                            # 稀有词汇给更高分
                            rarity_bonus = 1 / max(word_rarity.get(word, 1), 1)
                            score += 10 + rarity_bonus * 5
                        else:
                            # 已经满足最小覆盖的词汇给较低分
                            score += 1
                
                if score > best_score:
                    best_score = score
                    best_sentence = i
            
            if best_sentence == -1:
                print("⚠️  无法找到更多有价值的句子")
                break
            
            # 添加最佳句子
            selected_indices.add(best_sentence)
            words_in_best = self.extract_words_from_sentence(self.sentences[best_sentence])
            
            for word in words_in_best:
                if word in self.target_words:
                    word_coverage_count[word] += 1
            
            # 显示进度
            covered_enough = sum(1 for count in word_coverage_count.values() if count >= min_word_coverage)
            total_target_words = len([w for w in self.target_words if w in word_sentence_map])
            
            print(f"   选择第 {len(selected_indices)} 句: 得分 {best_score:.1f} | "
                  f"充分覆盖词汇: {covered_enough}/{total_target_words}")
        
        # 检查覆盖情况
        print(f"\n📊 最终覆盖情况:")
        insufficient_words = []
        sufficient_words = []
        
        for word in self.target_words:
            if word in word_coverage_count:
                count = word_coverage_count[word]
                if count >= min_word_coverage:
                    sufficient_words.append((word, count))
                else:
                    insufficient_words.append((word, count))
        
        print(f"   充分覆盖的词汇 (≥{min_word_coverage}次): {len(sufficient_words)}")
        print(f"   不充分覆盖的词汇 (<{min_word_coverage}次): {len(insufficient_words)}")
        
        if insufficient_words:
            print(f"   🟡 不充分覆盖的词汇:")
            for word, count in sorted(insufficient_words):
                print(f"      {word}: {count} 次")
        
        return list(selected_indices), word_coverage_count
    
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
    
    def analyze_selected_sentences(self, selected_indices):
        """分析选中的句子"""
        selected_sentences = [self.sentences[i] for i in selected_indices]
        
        print(f"\n📊 分析选中的 {len(selected_sentences)} 个句子...")
        
        # 词频分析
        word_counter = Counter()
        phoneme_counter = Counter()
        
        for sentence in selected_sentences:
            words = self.extract_words_from_sentence(sentence)
            for word in words:
                word_counter[word] += 1
                # 音素分析
                phonemes = self.get_word_phonemes(word)
                for phoneme in phonemes:
                    phoneme_counter[phoneme] += 1
        
        # 目标词汇覆盖分析
        target_word_coverage = {}
        for word in self.target_words:
            count = word_counter.get(word, 0)
            target_word_coverage[word] = count
        
        return {
            'sentences': selected_sentences,
            'word_frequencies': dict(word_counter),
            'phoneme_frequencies': dict(phoneme_counter),
            'target_word_coverage': target_word_coverage
        }
    
    def display_analysis(self, analysis):
        """显示分析结果"""
        print("\n" + "=" * 80)
        print("📊 选中句子分析结果")
        print("=" * 80)
        
        # 显示选中的句子
        print(f"\n📝 选中的 {len(analysis['sentences'])} 个句子:")
        print("-" * 60)
        for i, sentence in enumerate(analysis['sentences'], 1):
            print(f"{i:2d}. {sentence}")
        
        # 词频分析
        print(f"\n📚 词频分析 (按频率排序):")
        print("-" * 60)
        word_freq = Counter(analysis['word_frequencies'])
        for word, freq in word_freq.most_common(30):  # 显示前30个
            status = "✅" if word in self.target_words else "❓"
            print(f"   {word:15s}: {freq:3d} 次 {status}")
        
        # 目标词汇覆盖情况
        coverage = analysis['target_word_coverage']
        covered_words = {w: c for w, c in coverage.items() if c > 0}
        uncovered_words = {w: c for w, c in coverage.items() if c == 0}
        sufficient_coverage = {w: c for w, c in coverage.items() if c >= 2}
        
        print(f"\n📋 目标词汇覆盖情况:")
        print(f"   总目标词汇: {len(self.target_words)}")
        print(f"   有覆盖词汇: {len(covered_words)} ({len(covered_words)/len(self.target_words)*100:.1f}%)")
        print(f"   充分覆盖词汇 (≥2次): {len(sufficient_coverage)} ({len(sufficient_coverage)/len(self.target_words)*100:.1f}%)")
        print(f"   未覆盖词汇: {len(uncovered_words)} ({len(uncovered_words)/len(self.target_words)*100:.1f}%)")
        
        if uncovered_words:
            print(f"   🟡 未覆盖的目标词汇:")
            uncovered_list = sorted(list(uncovered_words.keys()))
            for i in range(0, len(uncovered_list), 8):
                group = uncovered_list[i:i+8]
                print(f"      {', '.join(group)}")
        
        # 音素频率分析
        print(f"\n🔊 音素频率分析 (按频率排序):")
        print("-" * 60)
        phoneme_freq = Counter(analysis['phoneme_frequencies'])
        for phoneme, freq in phoneme_freq.most_common():
            print(f"   /{phoneme:3s}/: {freq:3d} 次")
        
        # 音素覆盖情况
        covered_phonemes = set(analysis['phoneme_frequencies'].keys())
        uncovered_phonemes = self.cmu_phonemes - covered_phonemes
        
        print(f"\n🎯 39音素覆盖情况:")
        print(f"   总音素: 39")
        print(f"   已覆盖: {len(covered_phonemes)} ({len(covered_phonemes)/39*100:.1f}%)")
        print(f"   未覆盖: {len(uncovered_phonemes)} ({len(uncovered_phonemes)/39*100:.1f}%)")
        
        if uncovered_phonemes:
            print(f"   🟡 未覆盖的音素:")
            uncovered_list = sorted(list(uncovered_phonemes))
            for i in range(0, len(uncovered_list), 8):
                group = uncovered_list[i:i+8]
                print(f"      {', '.join('/' + p + '/' for p in group)}")
        
        # 统计摘要
        total_words = sum(analysis['word_frequencies'].values())
        total_phonemes = sum(analysis['phoneme_frequencies'].values())
        unique_words = len(analysis['word_frequencies'])
        unique_phonemes = len(analysis['phoneme_frequencies'])
        
        print(f"\n📈 统计摘要:")
        print(f"   总词汇实例: {total_words}")
        print(f"   不同词汇数: {unique_words}")
        print(f"   总音素实例: {total_phonemes}")
        print(f"   不同音素数: {unique_phonemes}")
    
    def save_results(self, selected_indices, analysis, filename="selected_50_sentences.json"):
        """保存结果"""
        results = {
            'selected_sentence_indices': selected_indices,
            'selected_sentences': analysis['sentences'],
            'word_frequencies': analysis['word_frequencies'],
            'phoneme_frequencies': analysis['phoneme_frequencies'],
            'target_word_coverage': analysis['target_word_coverage'],
            'statistics': {
                'total_sentences': len(analysis['sentences']),
                'total_words': sum(analysis['word_frequencies'].values()),
                'unique_words': len(analysis['word_frequencies']),
                'total_phonemes': sum(analysis['phoneme_frequencies'].values()),
                'unique_phonemes': len(analysis['phoneme_frequencies']),
                'target_words_covered': len([w for w, c in analysis['target_word_coverage'].items() if c > 0]),
                'target_words_sufficient': len([w for w, c in analysis['target_word_coverage'].items() if c >= 2])
            }
        }
        
        # 保存JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存文本报告
        txt_filename = filename.replace('.json', '_report.txt')
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write("选中句子分析报告\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("选中的句子:\n")
            f.write("-" * 30 + "\n")
            for i, sentence in enumerate(analysis['sentences'], 1):
                f.write(f"{i:2d}. {sentence}\n")
            
            f.write("\n词频统计 (按频率排序):\n")
            f.write("-" * 30 + "\n")
            word_freq = Counter(analysis['word_frequencies'])
            for word, freq in word_freq.most_common():
                status = "✅" if word in self.target_words else "❓"
                f.write(f"{word:15s}: {freq:3d} 次 {status}\n")
            
            f.write("\n音素频率统计 (按频率排序):\n")
            f.write("-" * 30 + "\n")
            phoneme_freq = Counter(analysis['phoneme_frequencies'])
            for phoneme, freq in phoneme_freq.most_common():
                f.write(f"/{phoneme:3s}/: {freq:3d} 次\n")
        
        print(f"✅ 结果已保存到:")
        print(f"   📄 {filename} (JSON格式)")
        print(f"   📄 {txt_filename} (文本报告)")

def main():
    print("🎯 最优句子选择器")
    print("=" * 50)
    print("目标: 从350个句子中选出50句，覆盖50个目标词汇，每个词至少出现2次")
    
    selector = OptimalSentenceSelector()
    
    if not selector.target_words:
        print("❌ 无法加载目标词汇")
        return
    
    if not selector.sentences:
        print("❌ 无法加载句子")
        return
    
    print(f"📊 数据概况:")
    print(f"   目标词汇数: {len(selector.target_words)}")
    print(f"   候选句子数: {len(selector.sentences)}")
    
    # 构建词汇-句子映射
    word_sentence_map = selector.build_word_sentence_mapping()
    
    # 贪心选择句子
    selected_indices, word_coverage = selector.greedy_sentence_selection(word_sentence_map)
    
    # 分析结果
    analysis = selector.analyze_selected_sentences(selected_indices)
    
    # 显示分析
    selector.display_analysis(analysis)
    
    # 保存结果
    save_choice = input("\n💾 是否保存结果? (y/N): ").strip().lower()
    if save_choice in ['y', 'yes']:
        selector.save_results(selected_indices, analysis)

if __name__ == "__main__":
    main()


