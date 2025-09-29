#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import matplotlib.pyplot as plt
from collections import Counter
import nltk
try:
    from nltk.corpus import cmudict
    cmu_dict = cmudict.dict()
except:
    print("Downloading CMU dictionary...")
    nltk.download('cmudict')
    from nltk.corpus import cmudict
    cmu_dict = cmudict.dict()

# Set English font
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class WordsAnalyzer:
    def __init__(self):
        # CMU phoneme set (39 phonemes)
        self.cmu_phonemes = {
            # Vowels (15)
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
            # Consonants (24)
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
        
        # Create output directory
        self.output_dir = "/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/newset"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_words(self):
        """Load words from selected_words.json"""
        try:
            with open('selected_words.json', 'r', encoding='utf-8') as f:
                words = json.load(f)
                # Clean and normalize words
                clean_words = [word.strip().lower() for word in words if word.strip()]
                print(f"📁 Loaded {len(clean_words)} words from selected_words.json")
                return clean_words
        except Exception as e:
            print(f"❌ Failed to load words: {e}")
            return []
    
    def get_word_phonemes(self, word):
        """Get phonemes of a word"""
        word_lower = word.lower()
        if word_lower in cmu_dict:
            # Take first pronunciation
            phonemes = cmu_dict[word_lower][0]
            # Clean phonemes (remove stress markers)
            clean_phonemes = []
            for phoneme in phonemes:
                clean_phoneme = re.sub(r'\d', '', phoneme)
                if clean_phoneme in self.cmu_phonemes:
                    clean_phonemes.append(clean_phoneme)
            return clean_phonemes
        return []
    
    def analyze_words(self, words):
        """Analyze word and phoneme frequencies"""
        print(f"🔄 Analyzing {len(words)} words...")
        
        # Word frequency (each word appears once, so frequency = 1 for all)
        word_counter = Counter(words)
        
        # Phoneme frequency
        phoneme_counter = Counter()
        words_with_phonemes = 0
        words_without_phonemes = []
        
        for word in words:
            phonemes = self.get_word_phonemes(word)
            if phonemes:
                words_with_phonemes += 1
                for phoneme in phonemes:
                    phoneme_counter[phoneme] += 1
            else:
                words_without_phonemes.append(word)
        
        print(f"📊 Analysis results:")
        print(f"   Words with phonemes: {words_with_phonemes}")
        print(f"   Words without phonemes: {len(words_without_phonemes)}")
        if words_without_phonemes:
            print(f"   Words not found in CMU dict: {', '.join(words_without_phonemes)}")
        
        return word_counter, phoneme_counter
    
    def save_words_to_txt(self, words, filename):
        """Save words to txt file (one word per line)"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            for word in words:
                f.write(word + '\n')
        print(f"✅ Words saved to: {filepath}")
    
    def plot_word_distribution(self, word_counter, title, filename):
        """Plot word frequency distribution"""
        # Since each word appears once, we'll sort alphabetically for consistency
        words = sorted(word_counter.keys())
        frequencies = [word_counter[word] for word in words]
        
        fig_width = max(20, len(words) * 0.4)
        fig_height = 10
        
        plt.figure(figsize=(fig_width, fig_height))
        bars = plt.bar(range(len(words)), frequencies, color='steelblue', alpha=0.7)
        
        plt.title(f'{title} - Word Distribution (All {len(words)} Words)', fontsize=18, fontweight='bold')
        plt.xlabel('Words', fontsize=14)
        plt.ylabel('Count', fontsize=14)
        
        plt.xticks(range(len(words)), words, rotation=45, ha='right', fontsize=10)
        
        # Show values on bars (all should be 1)
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Word distribution chart saved to: {filepath}")
    
    def plot_phoneme_distribution(self, phoneme_counter, title, filename):
        """Plot phoneme frequency distribution (sorted by frequency)"""
        # Get all phonemes sorted by frequency
        phoneme_items = phoneme_counter.most_common()
        covered_phonemes = set(phoneme_counter.keys())
        uncovered_phonemes = self.cmu_phonemes - covered_phonemes
        
        all_phonemes = []
        all_frequencies = []
        
        # Add covered phonemes (sorted by frequency, high to low)
        for phoneme, freq in phoneme_items:
            all_phonemes.append(f"/{phoneme}/")
            all_frequencies.append(freq)
        
        # Add uncovered phonemes (with 0 frequency)
        for phoneme in sorted(uncovered_phonemes):
            all_phonemes.append(f"/{phoneme}/")
            all_frequencies.append(0)
        
        plt.figure(figsize=(20, 12))
        
        # Color bars: green for covered, red for uncovered
        colors = ['darkgreen' if freq > 0 else 'red' for freq in all_frequencies]
        bars = plt.bar(range(len(all_phonemes)), all_frequencies, color=colors, alpha=0.7)
        
        plt.title(f'{title} - Phoneme Frequency Distribution (All 39 Phonemes, Sorted by Frequency)', 
                 fontsize=18, fontweight='bold')
        plt.xlabel('Phonemes', fontsize=14)
        plt.ylabel('Frequency', fontsize=14)
        
        plt.xticks(range(len(all_phonemes)), all_phonemes, rotation=45, ha='right', fontsize=12)
        
        # Show values on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{int(height)}', ha='center', va='bottom', fontsize=10)
            else:
                plt.text(bar.get_x() + bar.get_width()/2., 0.05,
                        '0', ha='center', va='bottom', fontsize=10, color='red')
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='darkgreen', alpha=0.7, label='Covered Phonemes'),
                          Patch(facecolor='red', alpha=0.7, label='Uncovered Phonemes')]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=12)
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Phoneme frequency chart saved to: {filepath}")
    
    def run_analysis(self):
        """Run the complete word analysis"""
        print("🎯 Words Analyzer for selected_words.json")
        print("="*60)
        print("Task: Analyze word list and create distribution charts")
        print(f"Output: All files saved to {self.output_dir}")
        
        # 1. Load words
        words = self.load_words()
        if not words:
            print("❌ No words to analyze")
            return
        
        # 2. Save words to txt file (one word per line)
        self.save_words_to_txt(words, 'selected_words_list.txt')
        
        # 3. Analyze word and phoneme frequencies
        word_counter, phoneme_counter = self.analyze_words(words)
        
        # 4. Create word distribution chart
        self.plot_word_distribution(word_counter, "Selected Words", 'selected_words_distribution.png')
        
        # 5. Create phoneme distribution chart
        self.plot_phoneme_distribution(phoneme_counter, "Selected Words", 'selected_words_phoneme_distribution.png')
        
        # 6. Display statistics
        print(f"\n📊 Analysis Summary:")
        print(f"   Total words: {len(words)}")
        print(f"   Unique words: {len(word_counter)}")
        print(f"   Total phoneme instances: {sum(phoneme_counter.values())}")
        print(f"   Unique phonemes covered: {len(phoneme_counter)}")
        print(f"   Phoneme coverage: {len(phoneme_counter)}/39 ({len(phoneme_counter)/39*100:.1f}%)")
        
        # Show top phonemes
        if phoneme_counter:
            print(f"\n🔊 Top 10 most frequent phonemes:")
            for i, (phoneme, freq) in enumerate(phoneme_counter.most_common(10), 1):
                print(f"   {i:2d}. /{phoneme}/: {freq} times")
        
        # Show uncovered phonemes
        covered_phonemes = set(phoneme_counter.keys())
        uncovered_phonemes = self.cmu_phonemes - covered_phonemes
        if uncovered_phonemes:
            print(f"\n🟡 Uncovered phonemes ({len(uncovered_phonemes)}):")
            uncovered_list = sorted(list(uncovered_phonemes))
            for i in range(0, len(uncovered_list), 8):
                group = uncovered_list[i:i+8]
                print(f"      {', '.join('/' + p + '/' for p in group)}")
        
        # 7. Summary
        print("\n" + "="*60)
        print("🎉 Analysis Completed!")
        print("="*60)
        print(f"Files saved to: {self.output_dir}")
        print("\nGenerated Files:")
        print("📄 Word List:")
        print("   - selected_words_list.txt")
        print("📊 Word Distribution Chart:")
        print("   - selected_words_distribution.png")
        print("🔊 Phoneme Distribution Chart:")
        print("   - selected_words_phoneme_distribution.png")

def main():
    analyzer = WordsAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()


