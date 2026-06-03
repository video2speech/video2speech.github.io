#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import random
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from collections import defaultdict, Counter
import nltk
try:
    from nltk.corpus import cmudict
    cmu_dict = cmudict.dict()
except:
    print("Downloading CMU dictionary...")
    nltk.download('cmudict')
    from nltk.corpus import cmudict
    cmu_dict = cmudict.dict()

# Set English font and disable unicode minus
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class ImprovedSentenceVisualizer:
    def __init__(self):
        # CMU phoneme set (39 phonemes)
        self.cmu_phonemes = {
            # Vowels (15)
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
            # Consonants (24)
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
        
        # Load data
        self.selected_data = self.load_selected_data()
        self.all_sentences = self.load_all_sentences()
        
        # Set random seed for reproducible shuffling
        random.seed(42)
        
    def load_selected_data(self):
        """Load selected 50 sentences data"""
        try:
            with open('selected_50_sentences.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load selected sentences data: {e}")
            return None
    
    def load_all_sentences(self):
        """Load all 350 sentences data"""
        try:
            with open('selected_sentences_analyzer.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load all sentences data: {e}")
            return []
    
    def clean_sentence(self, sentence):
        """Clean sentence"""
        sentence = sentence.lower()
        sentence = re.sub(r'[^\w\s]', '', sentence)
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        return sentence
    
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
    
    def analyze_sentences(self, sentences, title=""):
        """Analyze word and phoneme frequencies of sentence collection"""
        print(f"🔄 Analyzing {title} ({len(sentences)} sentences)...")
        
        word_counter = Counter()
        phoneme_counter = Counter()
        
        for sentence in sentences:
            words = self.clean_sentence(sentence).split()
            for word in words:
                word_counter[word] += 1
                # Phoneme analysis
                phonemes = self.get_word_phonemes(word)
                for phoneme in phonemes:
                    phoneme_counter[phoneme] += 1
        
        return word_counter, phoneme_counter
    
    def save_sentences_to_txt(self, sentences, filename, shuffle=True):
        """Save sentences to txt file with optional shuffling"""
        sentences_to_save = sentences.copy()
        if shuffle:
            random.shuffle(sentences_to_save)
            print(f"🔀 Shuffled {len(sentences_to_save)} sentences")
        
        with open(filename, 'w', encoding='utf-8') as f:
            for sentence in sentences_to_save:
                f.write(sentence + '\n')
        print(f"✅ Sentences saved to: {filename}")
    
    def plot_word_distribution(self, word_counter, title, filename):
        """Plot word frequency distribution (show ALL words)"""
        # Get all words sorted by frequency
        all_words = word_counter.most_common()
        words = [item[0] for item in all_words]
        frequencies = [item[1] for item in all_words]
        
        # Calculate figure size based on number of words
        fig_width = max(20, len(words) * 0.5)
        fig_height = 12
        
        # Create chart
        plt.figure(figsize=(fig_width, fig_height))
        bars = plt.bar(range(len(words)), frequencies, color='steelblue', alpha=0.7)
        
        # Set title and labels (ALL IN ENGLISH)
        plt.title(f'{title} - Word Frequency Distribution (All Words)', fontsize=18, fontweight='bold')
        plt.xlabel('Words', fontsize=14)
        plt.ylabel('Frequency', fontsize=14)
        
        # Set x-axis labels
        plt.xticks(range(len(words)), words, rotation=45, ha='right', fontsize=10)
        
        # Show values on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save image
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Word frequency chart saved to: {filename}")
    
    def plot_phoneme_distribution(self, phoneme_counter, title, filename):
        """Plot phoneme frequency distribution (show ALL phonemes)"""
        # Get all phonemes sorted by frequency, including zero-frequency ones
        phoneme_items = phoneme_counter.most_common()
        covered_phonemes = set(phoneme_counter.keys())
        uncovered_phonemes = self.cmu_phonemes - covered_phonemes
        
        # Combine covered and uncovered phonemes
        all_phonemes = []
        all_frequencies = []
        
        # Add covered phonemes (sorted by frequency)
        for phoneme, freq in phoneme_items:
            all_phonemes.append(f"/{phoneme}/")
            all_frequencies.append(freq)
        
        # Add uncovered phonemes (with 0 frequency)
        for phoneme in sorted(uncovered_phonemes):
            all_phonemes.append(f"/{phoneme}/")
            all_frequencies.append(0)
        
        # Create chart
        plt.figure(figsize=(20, 12))
        
        # Color bars: blue for covered, red for uncovered
        colors = ['darkgreen' if freq > 0 else 'red' for freq in all_frequencies]
        bars = plt.bar(range(len(all_phonemes)), all_frequencies, color=colors, alpha=0.7)
        
        # Set title and labels (ALL IN ENGLISH)
        plt.title(f'{title} - Phoneme Frequency Distribution (All 39 Phonemes)', fontsize=18, fontweight='bold')
        plt.xlabel('Phonemes', fontsize=14)
        plt.ylabel('Frequency', fontsize=14)
        
        # Set x-axis labels
        plt.xticks(range(len(all_phonemes)), all_phonemes, rotation=45, ha='right', fontsize=12)
        
        # Show values on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{int(height)}', ha='center', va='bottom', fontsize=10)
            else:
                plt.text(bar.get_x() + bar.get_width()/2., 0.5,
                        '0', ha='center', va='bottom', fontsize=10, color='red')
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='darkgreen', alpha=0.7, label='Covered Phonemes'),
                          Patch(facecolor='red', alpha=0.7, label='Uncovered Phonemes')]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=12)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save image
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Phoneme frequency chart saved to: {filename}")
    
    def process_selected_sentences(self):
        """Process selected 50 sentences"""
        print("\n" + "="*70)
        print("📊 Task 1: Processing Selected 50 Sentences")
        print("="*70)
        
        if not self.selected_data:
            print("❌ Unable to load selected sentences data")
            return
        
        sentences = self.selected_data['selected_sentences']
        
        # 1. Save sentences to txt (shuffled)
        self.save_sentences_to_txt(sentences, 'selected_50_sentences_shuffled.txt', shuffle=True)
        
        # 2. Analyze word and phoneme frequencies
        word_counter, phoneme_counter = self.analyze_sentences(sentences, "Selected 50 Sentences")
        
        # 3. Create charts (ALL words and phonemes)
        self.plot_word_distribution(word_counter, "Selected 50 Sentences", 'selected_50_word_distribution_full.png')
        self.plot_phoneme_distribution(phoneme_counter, "Selected 50 Sentences", 'selected_50_phoneme_distribution_full.png')
        
        print(f"📈 Statistics: Total word instances {sum(word_counter.values())}, Unique words {len(word_counter)}")
        print(f"🔊 Statistics: Total phoneme instances {sum(phoneme_counter.values())}, Unique phonemes {len(phoneme_counter)}")
    
    def process_remaining_sentences(self):
        """Process remaining 300 sentences (350-50)"""
        print("\n" + "="*70)
        print("📊 Task 2: Processing Remaining 300 Sentences")
        print("="*70)
        
        if not self.selected_data or not self.all_sentences:
            print("❌ Unable to load necessary data")
            return
        
        # Get selected sentence indices
        selected_indices = set(self.selected_data['selected_sentence_indices'])
        
        # Get remaining sentences
        remaining_sentences = []
        for i, sentence in enumerate(self.all_sentences):
            if i not in selected_indices:
                remaining_sentences.append(sentence)
        
        print(f"📊 Number of remaining sentences: {len(remaining_sentences)}")
        
        # 1. Save sentences to txt (shuffled)
        self.save_sentences_to_txt(remaining_sentences, 'remaining_300_sentences_shuffled.txt', shuffle=True)
        
        # 2. Analyze word and phoneme frequencies
        word_counter, phoneme_counter = self.analyze_sentences(remaining_sentences, "Remaining 300 Sentences")
        
        # 3. Create charts (ALL words and phonemes)
        self.plot_word_distribution(word_counter, "Remaining 300 Sentences", 'remaining_300_word_distribution_full.png')
        self.plot_phoneme_distribution(phoneme_counter, "Remaining 300 Sentences", 'remaining_300_phoneme_distribution_full.png')
        
        print(f"📈 Statistics: Total word instances {sum(word_counter.values())}, Unique words {len(word_counter)}")
        print(f"🔊 Statistics: Total phoneme instances {sum(phoneme_counter.values())}, Unique phonemes {len(phoneme_counter)}")
    
    def process_all_sentences(self):
        """Process all 350 sentences"""
        print("\n" + "="*70)
        print("📊 Task 3: Processing All 350 Sentences")
        print("="*70)
        
        if not self.all_sentences:
            print("❌ Unable to load all sentences data")
            return
        
        # 1. Save sentences to txt (shuffled)
        self.save_sentences_to_txt(self.all_sentences, 'all_350_sentences_shuffled.txt', shuffle=True)
        
        # 2. Analyze word and phoneme frequencies
        word_counter, phoneme_counter = self.analyze_sentences(self.all_sentences, "All 350 Sentences")
        
        # 3. Create charts (ALL words and phonemes)
        self.plot_word_distribution(word_counter, "All 350 Sentences", 'all_350_word_distribution_full.png')
        self.plot_phoneme_distribution(phoneme_counter, "All 350 Sentences", 'all_350_phoneme_distribution_full.png')
        
        print(f"📈 Statistics: Total word instances {sum(word_counter.values())}, Unique words {len(word_counter)}")
        print(f"🔊 Statistics: Total phoneme instances {sum(phoneme_counter.values())}, Unique phonemes {len(phoneme_counter)}")
    
    def run_all_tasks(self):
        """Run all tasks"""
        print("🎯 Improved Sentence Analysis & Visualization Tool")
        print("="*70)
        print("Task Overview:")
        print("1. Selected 50 sentences → shuffled txt + full word chart + full phoneme chart")
        print("2. Remaining 300 sentences → shuffled txt + full word chart + full phoneme chart") 
        print("3. All 350 sentences → shuffled txt + full word chart + full phoneme chart")
        print("\nKey Improvements:")
        print("- All text in charts is in English")
        print("- Show ALL words and ALL phonemes (not just top ones)")
        print("- Shuffle sentence order in txt files")
        print("- Color-code covered/uncovered phonemes")
        
        # Execute three tasks
        self.process_selected_sentences()
        self.process_remaining_sentences()
        self.process_all_sentences()
        
        print("\n" + "="*70)
        print("🎉 All Tasks Completed!")
        print("="*70)
        print("Generated Files:")
        print("📄 TXT Files (Shuffled):")
        print("   - selected_50_sentences_shuffled.txt")
        print("   - remaining_300_sentences_shuffled.txt")
        print("   - all_350_sentences_shuffled.txt")
        print("📊 Word Distribution Charts (Full):")
        print("   - selected_50_word_distribution_full.png")
        print("   - remaining_300_word_distribution_full.png")
        print("   - all_350_word_distribution_full.png")
        print("🔊 Phoneme Distribution Charts (All 39 Phonemes):")
        print("   - selected_50_phoneme_distribution_full.png")
        print("   - remaining_300_phoneme_distribution_full.png")
        print("   - all_350_phoneme_distribution_full.png")

def main():
    # Check if matplotlib is available
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("❌ Need to install matplotlib:")
        print("   pip install matplotlib")
        return
    
    visualizer = ImprovedSentenceVisualizer()
    visualizer.run_all_tasks()

if __name__ == "__main__":
    main()


