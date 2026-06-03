#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import random
import matplotlib.pyplot as plt
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

# Set English font
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class CompleteSentenceProcessor:
    def __init__(self):
        # CMU phoneme set (39 phonemes)
        self.cmu_phonemes = {
            # Vowels (15)
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
            # Consonants (24)
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
        
        # Load data
        self.target_words = self.load_target_words()
        self.all_sentences = self.load_all_sentences()
        
        # Create output directory
        self.output_dir = "/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/newset"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set random seed for reproducible shuffling
        random.seed(42)
        
    def load_target_words(self):
        """Load target words from selected_words.json"""
        try:
            with open('selected_words.json', 'r', encoding='utf-8') as f:
                words = json.load(f)
                return set(word.lower().strip() for word in words if word.strip())
        except Exception as e:
            print(f"❌ Failed to load target words: {e}")
            return set()
    
    def load_all_sentences(self):
        """Load all sentences from selected_sentences_analyzer.json"""
        try:
            with open('selected_sentences_analyzer.json', 'r', encoding='utf-8') as f:
                sentences = json.load(f)
                print(f"📁 Loaded {len(sentences)} sentences from updated file")
                return sentences
        except Exception as e:
            print(f"❌ Failed to load sentences: {e}")
            return []
    
    def clean_sentence(self, sentence):
        """Clean sentence"""
        sentence = sentence.lower()
        sentence = re.sub(r'[^\w\s]', '', sentence)
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        return sentence
    
    def extract_words_from_sentence(self, sentence):
        """Extract words from sentence"""
        clean_text = self.clean_sentence(sentence)
        return set(clean_text.split())
    
    def build_word_sentence_mapping(self):
        """Build word-sentence mapping"""
        print("🔄 Building word-sentence mapping...")
        word_sentence_map = defaultdict(list)
        
        for i, sentence in enumerate(self.all_sentences):
            words = self.extract_words_from_sentence(sentence)
            for word in words:
                if word in self.target_words:
                    word_sentence_map[word].append(i)
        
        # Statistics
        coverage_stats = {}
        for word in self.target_words:
            count = len(word_sentence_map[word])
            coverage_stats[word] = count
            if count == 0:
                print(f"⚠️  Word '{word}' not found in any sentence")
        
        covered_words = sum(1 for count in coverage_stats.values() if count > 0)
        print(f"📊 Word coverage statistics:")
        print(f"   Total target words: {len(self.target_words)}")
        print(f"   Covered words: {covered_words}")
        print(f"   Coverage rate: {covered_words/len(self.target_words)*100:.1f}%")
        
        return word_sentence_map
    
    def greedy_sentence_selection(self, word_sentence_map, max_sentences=50, min_word_coverage=2):
        """Greedy algorithm for sentence selection"""
        print(f"\n🔄 Starting greedy selection algorithm...")
        print(f"   Target sentences: {max_sentences}")
        print(f"   Minimum word coverage: {min_word_coverage}")
        
        selected_indices = set()
        word_coverage_count = defaultdict(int)
        
        # Word rarity for prioritization
        word_rarity = {}
        for word, sentence_list in word_sentence_map.items():
            word_rarity[word] = len(sentence_list)
        
        while len(selected_indices) < max_sentences:
            best_sentence = -1
            best_score = -1
            
            for i, sentence in enumerate(self.all_sentences):
                if i in selected_indices:
                    continue
                
                # Calculate value score for this sentence
                score = 0
                words_in_sentence = self.extract_words_from_sentence(sentence)
                
                for word in words_in_sentence:
                    if word in self.target_words:
                        if word_coverage_count[word] < min_word_coverage:
                            # Higher score for words not meeting minimum coverage
                            rarity_bonus = 1 / max(word_rarity.get(word, 1), 1)
                            score += 10 + rarity_bonus * 5
                        else:
                            # Lower score for words already meeting minimum coverage
                            score += 1
                
                if score > best_score:
                    best_score = score
                    best_sentence = i
            
            if best_sentence == -1:
                print("⚠️  Cannot find more valuable sentences")
                break
            
            # Add best sentence
            selected_indices.add(best_sentence)
            words_in_best = self.extract_words_from_sentence(self.all_sentences[best_sentence])
            
            for word in words_in_best:
                if word in self.target_words:
                    word_coverage_count[word] += 1
            
            # Show progress
            covered_enough = sum(1 for count in word_coverage_count.values() if count >= min_word_coverage)
            total_target_words = len([w for w in self.target_words if w in word_sentence_map])
            
            print(f"   Selected sentence {len(selected_indices)}: score {best_score:.1f} | "
                  f"Sufficiently covered words: {covered_enough}/{total_target_words}")
        
        # Check coverage
        print(f"\n📊 Final coverage:")
        insufficient_words = []
        sufficient_words = []
        
        for word in self.target_words:
            if word in word_coverage_count:
                count = word_coverage_count[word]
                if count >= min_word_coverage:
                    sufficient_words.append((word, count))
                else:
                    insufficient_words.append((word, count))
        
        print(f"   Sufficiently covered words (≥{min_word_coverage} times): {len(sufficient_words)}")
        print(f"   Insufficiently covered words (<{min_word_coverage} times): {len(insufficient_words)}")
        
        if insufficient_words:
            print(f"   🟡 Insufficiently covered words:")
            for word, count in sorted(insufficient_words):
                print(f"      {word}: {count} times")
        
        return list(selected_indices), word_coverage_count
    
    def get_word_phonemes(self, word):
        """Get phonemes of a word"""
        word_lower = word.lower()
        if word_lower in cmu_dict:
            phonemes = cmu_dict[word_lower][0]
            clean_phonemes = []
            for phoneme in phonemes:
                clean_phoneme = re.sub(r'\d', '', phoneme)
                if clean_phoneme in self.cmu_phonemes:
                    clean_phonemes.append(clean_phoneme)
            return clean_phonemes
        return []
    
    def analyze_sentences(self, sentences, title=""):
        """Analyze word and phoneme frequencies"""
        print(f"🔄 Analyzing {title} ({len(sentences)} sentences)...")
        
        word_counter = Counter()
        phoneme_counter = Counter()
        
        for sentence in sentences:
            words = self.clean_sentence(sentence).split()
            for word in words:
                word_counter[word] += 1
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
        
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            for sentence in sentences_to_save:
                f.write(sentence + '\n')
        print(f"✅ Sentences saved to: {filepath}")
    
    def plot_word_distribution(self, word_counter, title, filename):
        """Plot word frequency distribution (show ALL words)"""
        all_words = word_counter.most_common()
        words = [item[0] for item in all_words]
        frequencies = [item[1] for item in all_words]
        
        fig_width = max(20, len(words) * 0.5)
        fig_height = 12
        
        plt.figure(figsize=(fig_width, fig_height))
        bars = plt.bar(range(len(words)), frequencies, color='steelblue', alpha=0.7)
        
        plt.title(f'{title} - Word Frequency Distribution (All Words)', fontsize=18, fontweight='bold')
        plt.xlabel('Words', fontsize=14)
        plt.ylabel('Frequency', fontsize=14)
        
        plt.xticks(range(len(words)), words, rotation=45, ha='right', fontsize=10)
        
        for i, bar in enumerate(bars):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Word frequency chart saved to: {filepath}")
    
    def plot_phoneme_distribution(self, phoneme_counter, title, filename):
        """Plot phoneme frequency distribution (show ALL 39 phonemes)"""
        phoneme_items = phoneme_counter.most_common()
        covered_phonemes = set(phoneme_counter.keys())
        uncovered_phonemes = self.cmu_phonemes - covered_phonemes
        
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
        
        plt.figure(figsize=(20, 12))
        
        colors = ['darkgreen' if freq > 0 else 'red' for freq in all_frequencies]
        bars = plt.bar(range(len(all_phonemes)), all_frequencies, color=colors, alpha=0.7)
        
        plt.title(f'{title} - Phoneme Frequency Distribution (All 39 Phonemes)', fontsize=18, fontweight='bold')
        plt.xlabel('Phonemes', fontsize=14)
        plt.ylabel('Frequency', fontsize=14)
        
        plt.xticks(range(len(all_phonemes)), all_phonemes, rotation=45, ha='right', fontsize=12)
        
        for i, bar in enumerate(bars):
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f'{int(height)}', ha='center', va='bottom', fontsize=10)
            else:
                plt.text(bar.get_x() + bar.get_width()/2., 0.5,
                        '0', ha='center', va='bottom', fontsize=10, color='red')
        
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='darkgreen', alpha=0.7, label='Covered Phonemes'),
                          Patch(facecolor='red', alpha=0.7, label='Uncovered Phonemes')]
        plt.legend(handles=legend_elements, loc='upper right', fontsize=12)
        
        plt.tight_layout()
        
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ Phoneme frequency chart saved to: {filepath}")
    
    def save_selection_results(self, selected_indices, word_coverage):
        """Save selection results to JSON"""
        selected_sentences = [self.all_sentences[i] for i in selected_indices]
        
        results = {
            'selected_sentence_indices': selected_indices,
            'selected_sentences': selected_sentences,
            'word_coverage': dict(word_coverage),
            'statistics': {
                'total_sentences': len(selected_sentences),
                'total_target_words': len(self.target_words),
                'covered_words': len([w for w, c in word_coverage.items() if c > 0]),
                'sufficiently_covered_words': len([w for w, c in word_coverage.items() if c >= 2])
            }
        }
        
        filepath = os.path.join(self.output_dir, 'selected_50_sentences.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"✅ Selection results saved to: {filepath}")
        
        return results
    
    def run_complete_process(self):
        """Run the complete sentence processing workflow"""
        print("🎯 Complete Sentence Processor")
        print("="*80)
        print("Updated workflow for selected_sentences_analyzer.json")
        print("Target: Select 50 sentences covering 50 target words (≥2 occurrences each)")
        print("Output: All files saved to /newset directory")
        
        if not self.target_words:
            print("❌ Unable to load target words")
            return
        
        if not self.all_sentences:
            print("❌ Unable to load sentences")
            return
        
        print(f"📊 Data overview:")
        print(f"   Target words: {len(self.target_words)}")
        print(f"   Candidate sentences: {len(self.all_sentences)}")
        
        # 1. Build word-sentence mapping
        word_sentence_map = self.build_word_sentence_mapping()
        
        # 2. Select optimal 50 sentences
        selected_indices, word_coverage = self.greedy_sentence_selection(word_sentence_map)
        
        # 3. Save selection results
        results = self.save_selection_results(selected_indices, word_coverage)
        
        # 4. Get sentence sets
        selected_sentences = [self.all_sentences[i] for i in selected_indices]
        remaining_sentences = [self.all_sentences[i] for i in range(len(self.all_sentences)) if i not in selected_indices]
        
        print(f"\n📊 Sentence sets:")
        print(f"   Selected: {len(selected_sentences)} sentences")
        print(f"   Remaining: {len(remaining_sentences)} sentences")
        print(f"   Total: {len(self.all_sentences)} sentences")
        
        # 5. Process Task 1: Selected 50 sentences
        print("\n" + "="*80)
        print("📊 Task 1: Processing Selected 50 Sentences")
        print("="*80)
        
        self.save_sentences_to_txt(selected_sentences, 'selected_50_sentences.txt', shuffle=True)
        word_counter, phoneme_counter = self.analyze_sentences(selected_sentences, "Selected 50 Sentences")
        self.plot_word_distribution(word_counter, "Selected 50 Sentences", 'selected_50_word_distribution.png')
        self.plot_phoneme_distribution(phoneme_counter, "Selected 50 Sentences", 'selected_50_phoneme_distribution.png')
        
        print(f"📈 Statistics: Total word instances {sum(word_counter.values())}, Unique words {len(word_counter)}")
        print(f"🔊 Statistics: Total phoneme instances {sum(phoneme_counter.values())}, Unique phonemes {len(phoneme_counter)}")
        
        # 6. Process Task 2: Remaining 300 sentences
        print("\n" + "="*80)
        print("📊 Task 2: Processing Remaining 300 Sentences")
        print("="*80)
        
        self.save_sentences_to_txt(remaining_sentences, 'remaining_300_sentences.txt', shuffle=True)
        word_counter, phoneme_counter = self.analyze_sentences(remaining_sentences, "Remaining 300 Sentences")
        self.plot_word_distribution(word_counter, "Remaining 300 Sentences", 'remaining_300_word_distribution.png')
        self.plot_phoneme_distribution(phoneme_counter, "Remaining 300 Sentences", 'remaining_300_phoneme_distribution.png')
        
        print(f"📈 Statistics: Total word instances {sum(word_counter.values())}, Unique words {len(word_counter)}")
        print(f"🔊 Statistics: Total phoneme instances {sum(phoneme_counter.values())}, Unique phonemes {len(phoneme_counter)}")
        
        # 7. Process Task 3: All 350 sentences
        print("\n" + "="*80)
        print("📊 Task 3: Processing All 350 Sentences")
        print("="*80)
        
        self.save_sentences_to_txt(self.all_sentences, 'all_350_sentences.txt', shuffle=True)
        word_counter, phoneme_counter = self.analyze_sentences(self.all_sentences, "All 350 Sentences")
        self.plot_word_distribution(word_counter, "All 350 Sentences", 'all_350_word_distribution.png')
        self.plot_phoneme_distribution(phoneme_counter, "All 350 Sentences", 'all_350_phoneme_distribution.png')
        
        print(f"📈 Statistics: Total word instances {sum(word_counter.values())}, Unique words {len(word_counter)}")
        print(f"🔊 Statistics: Total phoneme instances {sum(phoneme_counter.values())}, Unique phonemes {len(phoneme_counter)}")
        
        # 8. Summary
        print("\n" + "="*80)
        print("🎉 All Tasks Completed!")
        print("="*80)
        print(f"All files saved to: {self.output_dir}")
        print("\nGenerated Files:")
        print("📄 TXT Files (Shuffled):")
        print("   - selected_50_sentences.txt")
        print("   - remaining_300_sentences.txt")
        print("   - all_350_sentences.txt")
        print("📊 Word Distribution Charts (All Words):")
        print("   - selected_50_word_distribution.png")
        print("   - remaining_300_word_distribution.png")
        print("   - all_350_word_distribution.png")
        print("🔊 Phoneme Distribution Charts (All 39 Phonemes):")
        print("   - selected_50_phoneme_distribution.png")
        print("   - remaining_300_phoneme_distribution.png")
        print("   - all_350_phoneme_distribution.png")
        print("📋 Selection Results:")
        print("   - selected_50_sentences.json")

def main():
    processor = CompleteSentenceProcessor()
    processor.run_complete_process()

if __name__ == "__main__":
    main()


