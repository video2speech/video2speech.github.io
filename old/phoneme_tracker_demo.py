#!/usr/bin/env python3
"""
Phoneme Tracker Demo - 简化版音素追踪演示
"""

import nltk
import re
import json
import os
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    nltk.download('cmudict')

from nltk.corpus import cmudict

class PhonemeTrackerDemo:
    def __init__(self):
        self.cmu_dict = cmudict.dict()
        self.selected_words = []
        
        # Target phoneme distribution
        self.target_distribution = {
            'AH': 3, 'T': 3, 'N': 3, 'S': 3,
            'L': 2, 'IH': 2, 'R': 2,
            'D': 1, 'IY': 1, 'K': 1, 'EH': 1, 'M': 1, 'P': 1, 'ER': 1, 'Z': 1,
            'AA': 1, 'B': 1, 'EY': 1, 'F': 1, 'W': 1, 'AE': 1, 'AO': 1, 'AY': 1,
            'V': 1, 'NG': 1, 'OW': 1, 'HH': 1, 'UW': 1, 'G': 1, 'Y': 1, 'SH': 1,
            'JH': 1, 'CH': 1, 'DH': 1, 'TH': 1, 'AW': 1, 'UH': 1, 'OY': 1, 'ZH': 1
        }
        
        # Phoneme display order
        self.phoneme_order = [
            'AH', 'T', 'N', 'S',  # High frequency (3 each)
            'L', 'IH', 'R',       # Mid frequency (2 each)
            'D', 'IY', 'K', 'EH', 'M', 'P', 'ER', 'Z',
            'AA', 'B', 'EY', 'F', 'W', 'AE', 'AO', 'AY',
            'V', 'NG', 'OW', 'HH', 'UW', 'G', 'Y', 'SH',
            'JH', 'CH', 'DH', 'TH', 'AW', 'UH', 'OY', 'ZH'
        ]
    
    def clean_phoneme(self, phoneme):
        """Remove stress markers from phoneme."""
        return re.sub(r'\d', '', phoneme)
    
    def get_word_phonemes(self, word):
        """Get phonemes for a word using CMU dictionary."""
        word_lower = word.lower()
        if word_lower in self.cmu_dict:
            phonemes = self.cmu_dict[word_lower][0]
            return [self.clean_phoneme(p) for p in phonemes]
        return None
    
    def add_word(self, word):
        """Add a word to the selected list."""
        word = word.strip()
        if word and word not in self.selected_words:
            phonemes = self.get_word_phonemes(word)
            if phonemes:
                self.selected_words.append(word)
                print(f"✅ 添加成功: {word} -> /{' '.join(phonemes)}/")
                return True
            else:
                print(f"❌ 未找到音素: {word}")
                return False
        elif word in self.selected_words:
            print(f"⚠️  词汇已存在: {word}")
            return False
        return False
    
    def get_current_phoneme_distribution(self):
        """Calculate current phoneme distribution from selected words."""
        phoneme_counter = Counter()
        
        for word in self.selected_words:
            phonemes = self.get_word_phonemes(word)
            if phonemes:
                for phoneme in phonemes:
                    if phoneme in self.target_distribution:
                        phoneme_counter[phoneme] += 1
        
        return phoneme_counter
    
    def display_status(self):
        """Display current phoneme distribution status."""
        current_dist = self.get_current_phoneme_distribution()
        
        print("\n" + "=" * 70)
        print("当前选中词汇音素分布状态")
        print("=" * 70)
        
        print(f"选中词汇 ({len(self.selected_words)}):")
        for i, word in enumerate(self.selected_words, 1):
            phonemes = self.get_word_phonemes(word)
            if phonemes:
                print(f"  {i:2d}. {word:15s} -> /{' '.join(phonemes)}/")
        
        print(f"\n音素分布状态:")
        print("-" * 50)
        
        # High frequency phonemes
        print("高频音素 (目标: 3个):")
        for phoneme in ['AH', 'T', 'N', 'S']:
            current = current_dist.get(phoneme, 0)
            target = self.target_distribution[phoneme]
            status = "✅" if current == target else "🟡"
            print(f"  /{phoneme:3s}/: {current:2d} (目标: {target}) {status}")
        
        # Mid frequency phonemes
        print("\n中频音素 (目标: 2个):")
        for phoneme in ['L', 'IH', 'R']:
            current = current_dist.get(phoneme, 0)
            target = self.target_distribution[phoneme]
            status = "✅" if current == target else "🟡"
            print(f"  /{phoneme:3s}/: {current:2d} (目标: {target}) {status}")
        
        # Low frequency phonemes
        print("\n低频音素 (目标: 1个):")
        low_freq = [p for p in self.phoneme_order if p not in ['AH', 'T', 'N', 'S', 'L', 'IH', 'R']]
        
        for i in range(0, len(low_freq), 4):
            group = low_freq[i:i+4]
            line_parts = []
            for phoneme in group:
                current = current_dist.get(phoneme, 0)
                target = self.target_distribution[phoneme]
                status = "✅" if current == target else "🟡"
                line_parts.append(f"/{phoneme:3s}/: {current} {status}")
            print(f"  {' | '.join(line_parts)}")
        
        # Summary
        total_current = sum(current_dist.values())
        total_target = sum(self.target_distribution.values())
        achieved = sum(1 for p in self.target_distribution if current_dist.get(p, 0) == self.target_distribution[p])
        
        print(f"\n统计摘要:")
        print(f"  总音素实例: {total_current}/{total_target}")
        print(f"  达标音素: {achieved}/39 ({achieved/39*100:.1f}%)")

def demo():
    """Run a demo of the phoneme tracker."""
    tracker = PhonemeTrackerDemo()
    
    print("🎯 音素追踪工具演示")
    print("=" * 30)
    
    # # Demo: add some words
    # demo_words = ["the", "and", "you", "that", "was", "for", "are"]
    
    # print("演示: 添加一些常用词汇...")
    # for word in demo_words:
    #     tracker.add_word(word)
    
    # Show status
    tracker.display_status()
    
    print("\n" + "=" * 70)
    print("🎮 交互模式 - 输入词汇或 'quit' 退出")
    print("=" * 70)
    
    while True:
        try:
            user_input = input("\n输入词汇: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 再见!")
                break
            elif user_input.lower() == 'show':
                tracker.display_status()
            elif user_input:
                tracker.add_word(user_input)
                tracker.display_status()
        except KeyboardInterrupt:
            print("\n👋 再见!")
            break

if __name__ == "__main__":
    demo()


