#!/usr/bin/env python3
"""
Simple English Phoneme Distribution Analysis Tool (No External Dependencies)

This script provides a basic phoneme analysis using a built-in phoneme mapping
without requiring external libraries. For more accurate results, use phoneme_analysis.py
with the pronouncing library.

Usage: python simple_phoneme_analysis.py
"""

import os
import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

class SimplePhonemeAnalyzer:
    """Simple phoneme analyzer using basic English phoneme mapping."""
    
    def __init__(self):
        """Initialize with basic phoneme mappings."""
        self.phoneme_counts = Counter()
        self.word_counts = Counter()
        self.file_phoneme_counts = defaultdict(Counter)
        self.total_words = 0
        self.total_phonemes = 0
        
        # Basic English letter to phoneme mapping (simplified)
        # This is a very basic approximation - real phoneme analysis requires proper dictionaries
        self.letter_to_phoneme = {
            'a': ['AE', 'AH', 'EY'],  # context-dependent
            'b': ['B'],
            'c': ['K', 'S'],  # context-dependent
            'd': ['D'],
            'e': ['EH', 'IY'],  # context-dependent
            'f': ['F'],
            'g': ['G', 'JH'],  # context-dependent
            'h': ['HH'],
            'i': ['IH', 'AY'],  # context-dependent
            'j': ['JH'],
            'k': ['K'],
            'l': ['L'],
            'm': ['M'],
            'n': ['N'],
            'o': ['AO', 'OW'],  # context-dependent
            'p': ['P'],
            'q': ['K', 'W'],  # qu sound
            'r': ['R'],
            's': ['S', 'Z'],  # context-dependent
            't': ['T'],
            'u': ['UH', 'UW'],  # context-dependent
            'v': ['V'],
            'w': ['W'],
            'x': ['K', 'S'],  # ks sound
            'y': ['Y', 'IH'],  # context-dependent
            'z': ['Z']
        }
        
        # Common letter combinations to phonemes
        self.digraph_to_phoneme = {
            'th': ['TH', 'DH'],  # thin vs this
            'sh': ['SH'],
            'ch': ['CH'],
            'ph': ['F'],
            'wh': ['W', 'HH'],
            'ng': ['NG'],
            'ck': ['K'],
            'gh': ['F', ''],  # rough vs night
            'oo': ['UW', 'UH'],  # boot vs book
            'ee': ['IY'],
            'ea': ['IY', 'EH'],  # beat vs bread
            'ou': ['AW', 'UW'],  # out vs you
            'ow': ['AW', 'OW'],  # cow vs show
            'ai': ['EY'],
            'ay': ['EY'],
            'ey': ['EY'],
            'oy': ['OY'],
            'oi': ['OY'],
            'au': ['AO'],
            'aw': ['AO'],
        }
        
        # Vowel and consonant phonemes
        self.vowel_phonemes = {
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 
            'IY', 'OW', 'OY', 'UH', 'UW'
        }
        
        self.consonant_phonemes = {
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 
            'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
    
    def clean_text(self, text: str) -> str:
        """Clean text by removing punctuation and converting to lowercase."""
        # Remove punctuation and special characters, keep only letters and spaces
        text = re.sub(r"[^\w\s']", " ", text)
        # Handle contractions
        text = re.sub(r"'(s|t|re|ve|ll|d|m)\b", r" \1", text)
        text = re.sub(r"n't\b", " not", text)
        return text.lower()
    
    def simple_word_to_phonemes(self, word: str) -> List[str]:
        """Convert word to phonemes using simple rules (approximation only)."""
        if not word:
            return []
        
        phonemes = []
        i = 0
        word = word.lower()
        
        while i < len(word):
            # Check for digraphs first
            if i < len(word) - 1:
                digraph = word[i:i+2]
                if digraph in self.digraph_to_phoneme:
                    # Use first phoneme option for simplicity
                    phoneme_options = self.digraph_to_phoneme[digraph]
                    if phoneme_options and phoneme_options[0]:  # Skip empty strings
                        phonemes.append(phoneme_options[0])
                    i += 2
                    continue
            
            # Single letter
            letter = word[i]
            if letter in self.letter_to_phoneme:
                # Use first phoneme option for simplicity
                phoneme_options = self.letter_to_phoneme[letter]
                phonemes.append(phoneme_options[0])
            
            i += 1
        
        return phonemes
    
    def process_file(self, file_path: str) -> Tuple[int, int]:
        """Process a single file and return word count and phoneme count."""
        print(f"Processing: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"Warning: File not found - {file_path}")
            return 0, 0
        
        word_count = 0
        phoneme_count = 0
        file_phonemes = Counter()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line_num, line in enumerate(file, 1):
                    cleaned_text = self.clean_text(line.strip())
                    words = cleaned_text.split()
                    
                    for word in words:
                        if word:
                            self.word_counts[word] += 1
                            word_count += 1
                            
                            # Get phonemes for the word
                            phonemes = self.simple_word_to_phonemes(word)
                            
                            for phoneme in phonemes:
                                self.phoneme_counts[phoneme] += 1
                                file_phonemes[phoneme] += 1
                                phoneme_count += 1
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return 0, 0
        
        # Store file-specific phoneme counts
        filename = os.path.basename(file_path)
        self.file_phoneme_counts[filename] = file_phonemes
        
        print(f"  - Words: {word_count}, Phonemes: {phoneme_count}")
        return word_count, phoneme_count
    
    def analyze_files(self, file_paths: List[str]) -> None:
        """Analyze multiple files."""
        print("=== Simple English Phoneme Distribution Analysis ===")
        print("Note: This uses simplified phoneme mapping. For accurate results, use phoneme_analysis.py\n")
        
        total_words = 0
        total_phonemes = 0
        
        for file_path in file_paths:
            words, phonemes = self.process_file(file_path)
            total_words += words
            total_phonemes += phonemes
        
        self.total_words = total_words
        self.total_phonemes = total_phonemes
        
        print(f"\nTotal words processed: {total_words}")
        print(f"Total phonemes found: {total_phonemes}")
        print(f"Unique phonemes: {len(self.phoneme_counts)}")
    
    def print_phoneme_statistics(self) -> None:
        """Print detailed phoneme statistics."""
        print("\n=== Phoneme Distribution Statistics ===")
        
        if not self.phoneme_counts:
            print("No phonemes found!")
            return
        
        # Sort phonemes by frequency
        sorted_phonemes = self.phoneme_counts.most_common()
        
        print(f"\nTop 20 Most Frequent Phonemes:")
        print("-" * 50)
        print(f"{'Phoneme':<10} {'Count':<8} {'Percentage':<12} {'Type'}")
        print("-" * 50)
        
        for i, (phoneme, count) in enumerate(sorted_phonemes[:20]):
            percentage = (count / self.total_phonemes) * 100
            phoneme_type = self.get_phoneme_type(phoneme)
            print(f"{phoneme:<10} {count:<8} {percentage:<12.2f} {phoneme_type}")
        
        # Vowel vs Consonant distribution
        vowel_count = sum(count for phoneme, count in self.phoneme_counts.items() 
                         if phoneme in self.vowel_phonemes)
        consonant_count = sum(count for phoneme, count in self.phoneme_counts.items() 
                             if phoneme in self.consonant_phonemes)
        
        print(f"\n=== Vowel vs Consonant Distribution ===")
        print(f"Vowels: {vowel_count} ({vowel_count/self.total_phonemes*100:.2f}%)")
        print(f"Consonants: {consonant_count} ({consonant_count/self.total_phonemes*100:.2f}%)")
        print(f"Other/Unknown: {self.total_phonemes - vowel_count - consonant_count}")
    
    def get_phoneme_type(self, phoneme: str) -> str:
        """Determine if phoneme is vowel or consonant."""
        if phoneme in self.vowel_phonemes:
            return "Vowel"
        elif phoneme in self.consonant_phonemes:
            return "Consonant"
        else:
            return "Unknown"
    
    def print_file_comparison(self) -> None:
        """Print comparison between files."""
        print("\n=== Per-File Phoneme Statistics ===")
        
        for filename, phoneme_counts in self.file_phoneme_counts.items():
            total_phonemes_file = sum(phoneme_counts.values())
            print(f"\n{filename}:")
            print(f"  Total phonemes: {total_phonemes_file}")
            
            # Top 5 phonemes for this file
            top_phonemes = phoneme_counts.most_common(5)
            print(f"  Top 5 phonemes: {', '.join([f'{p}({c})' for p, c in top_phonemes])}")
            
            # Vowel/consonant ratio for this file
            vowel_count = sum(count for phoneme, count in phoneme_counts.items() 
                             if phoneme in self.vowel_phonemes)
            consonant_count = sum(count for phoneme, count in phoneme_counts.items() 
                                 if phoneme in self.consonant_phonemes)
            
            if total_phonemes_file > 0:
                vowel_ratio = vowel_count / total_phonemes_file
                print(f"  Vowel ratio: {vowel_ratio:.3f}")
    
    def save_report(self, output_path: str = "simple_phoneme_report.txt") -> None:
        """Save a detailed text report."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("SIMPLE ENGLISH PHONEME DISTRIBUTION ANALYSIS REPORT\n")
            f.write("=" * 55 + "\n")
            f.write("Note: This analysis uses simplified phoneme mapping.\n")
            f.write("For accurate results, use the full phoneme_analysis.py script.\n\n")
            
            f.write(f"Total words processed: {self.total_words}\n")
            f.write(f"Total phonemes found: {self.total_phonemes}\n")
            f.write(f"Unique phonemes: {len(self.phoneme_counts)}\n\n")
            
            # Complete phoneme list
            f.write("COMPLETE PHONEME DISTRIBUTION:\n")
            f.write("-" * 50 + "\n")
            f.write(f"{'Phoneme':<10} {'Count':<8} {'Percentage':<12} {'Type'}\n")
            f.write("-" * 50 + "\n")
            
            sorted_phonemes = self.phoneme_counts.most_common()
            for phoneme, count in sorted_phonemes:
                percentage = (count / self.total_phonemes) * 100
                phoneme_type = self.get_phoneme_type(phoneme)
                f.write(f"{phoneme:<10} {count:<8} {percentage:<12.2f} {phoneme_type}\n")
            
            # File-specific analysis
            f.write(f"\n\nFILE-SPECIFIC ANALYSIS:\n")
            f.write("=" * 30 + "\n")
            
            for filename, phoneme_counts in self.file_phoneme_counts.items():
                f.write(f"\n{filename}:\n")
                f.write("-" * len(filename) + "\n")
                
                total_file_phonemes = sum(phoneme_counts.values())
                f.write(f"Total phonemes: {total_file_phonemes}\n")
                
                # Top phonemes for this file
                top_phonemes = phoneme_counts.most_common(10)
                f.write("Top 10 phonemes:\n")
                for phoneme, count in top_phonemes:
                    percentage = (count / total_file_phonemes) * 100 if total_file_phonemes > 0 else 0
                    f.write(f"  {phoneme}: {count} ({percentage:.2f}%)\n")
        
        print(f"Simple analysis report saved to: {output_path}")


def main():
    """Main function to run the simple phoneme analysis."""
    # File paths to analyze
    base_dir = "/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/materials"
    
    files_to_analyze = [
        os.path.join(base_dir, "50_sentences_list.txt"),
        os.path.join(base_dir, "50_words_list.txt"),
        os.path.join(base_dir, "150_sentences_list.txt"),
        os.path.join(base_dir, "150_words_list.txt")
    ]
    
    # Create analyzer instance
    analyzer = SimplePhonemeAnalyzer()
    
    # Analyze files
    analyzer.analyze_files(files_to_analyze)
    
    # Print statistics
    analyzer.print_phoneme_statistics()
    analyzer.print_file_comparison()
    
    # Save report
    analyzer.save_report()
    
    print(f"\n=== Simple Analysis Complete ===")
    print(f"Processed {analyzer.total_words} words and {analyzer.total_phonemes} phonemes")
    print("\nFor more accurate phoneme analysis, install dependencies and use phoneme_analysis.py:")
    print("pip install -r requirements.txt")
    print("python phoneme_analysis.py")


if __name__ == "__main__":
    main()
