#!/usr/bin/env python3
"""
English Phoneme Distribution Analysis Tool

This script analyzes the phoneme distribution in text files using the CMU Pronouncing Dictionary.
It processes multiple text files and provides comprehensive phoneme statistics.

Required: pip install pronouncing matplotlib numpy
"""

import os
import re
import pronouncing
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Tuple, Set

class PhonemeAnalyzer:
    """Analyzes phoneme distribution in text files."""
    
    def __init__(self):
        """Initialize the phoneme analyzer."""
        self.phoneme_counts = Counter()
        self.word_counts = Counter()
        self.file_phoneme_counts = defaultdict(Counter)
        self.total_words = 0
        self.total_phonemes = 0
        
        # Common English phonemes (ARPAbet format used by CMU dict)
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
        # Handle contractions by splitting them
        text = re.sub(r"'(s|t|re|ve|ll|d|m)\b", r" \1", text)
        text = re.sub(r"n't\b", " not", text)
        # Convert to lowercase and split into words
        return text.lower()
    
    def get_phonemes(self, word: str) -> List[str]:
        """Get phonemes for a word using the CMU Pronouncing Dictionary."""
        # Get phonemes from pronouncing library
        phoneme_list = pronouncing.phones_for_word(word)
        
        if not phoneme_list:
            # If word not found, try to handle common cases
            if word in ["'s", "s"]:
                return ["S"]
            elif word in ["'t", "t"]:
                return ["T"]
            elif word in ["'re", "re"]:
                return ["R"]
            elif word in ["'ve", "ve"]:
                return ["V"]
            elif word in ["'ll", "ll"]:
                return ["L"]
            elif word in ["'d", "d"]:
                return ["D"]
            elif word in ["'m", "m"]:
                return ["M"]
            else:
                return []
        
        # Take the first pronunciation and remove stress markers
        phonemes = phoneme_list[0].split()
        # Remove stress numbers (0, 1, 2)
        phonemes = [re.sub(r'[0-9]', '', phoneme) for phoneme in phonemes]
        
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
                    # Clean the line
                    cleaned_text = self.clean_text(line.strip())
                    words = cleaned_text.split()
                    
                    for word in words:
                        if word:  # Skip empty strings
                            self.word_counts[word] += 1
                            word_count += 1
                            
                            # Get phonemes for the word
                            phonemes = self.get_phonemes(word)
                            
                            if phonemes:
                                for phoneme in phonemes:
                                    self.phoneme_counts[phoneme] += 1
                                    file_phonemes[phoneme] += 1
                                    phoneme_count += 1
                            else:
                                print(f"Warning: No phonemes found for word '{word}' in {file_path}:{line_num}")
        
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
        print("=== English Phoneme Distribution Analysis ===\n")
        
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
                         if self.remove_stress(phoneme) in self.vowel_phonemes)
        consonant_count = sum(count for phoneme, count in self.phoneme_counts.items() 
                             if self.remove_stress(phoneme) in self.consonant_phonemes)
        
        print(f"\n=== Vowel vs Consonant Distribution ===")
        print(f"Vowels: {vowel_count} ({vowel_count/self.total_phonemes*100:.2f}%)")
        print(f"Consonants: {consonant_count} ({consonant_count/self.total_phonemes*100:.2f}%)")
        print(f"Other/Unknown: {self.total_phonemes - vowel_count - consonant_count}")
    
    def remove_stress(self, phoneme: str) -> str:
        """Remove stress markers from phoneme."""
        return re.sub(r'[0-9]', '', phoneme)
    
    def get_phoneme_type(self, phoneme: str) -> str:
        """Determine if phoneme is vowel or consonant."""
        clean_phoneme = self.remove_stress(phoneme)
        if clean_phoneme in self.vowel_phonemes:
            return "Vowel"
        elif clean_phoneme in self.consonant_phonemes:
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
                             if self.remove_stress(phoneme) in self.vowel_phonemes)
            consonant_count = sum(count for phoneme, count in phoneme_counts.items() 
                                 if self.remove_stress(phoneme) in self.consonant_phonemes)
            
            if total_phonemes_file > 0:
                vowel_ratio = vowel_count / total_phonemes_file
                print(f"  Vowel ratio: {vowel_ratio:.3f}")
    
    def create_visualization(self, output_dir: str = ".") -> None:
        """Create visualization of phoneme distribution."""
        if not self.phoneme_counts:
            print("No data to visualize!")
            return
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('English Phoneme Distribution Analysis', fontsize=16)
        
        # 1. Top 20 phonemes bar chart
        top_20 = self.phoneme_counts.most_common(20)
        phonemes, counts = zip(*top_20)
        
        ax1.bar(range(len(phonemes)), counts, color='skyblue', alpha=0.7)
        ax1.set_xlabel('Phonemes')
        ax1.set_ylabel('Frequency')
        ax1.set_title('Top 20 Most Frequent Phonemes')
        ax1.set_xticks(range(len(phonemes)))
        ax1.set_xticklabels(phonemes, rotation=45)
        
        # 2. Vowel vs Consonant pie chart
        vowel_count = sum(count for phoneme, count in self.phoneme_counts.items() 
                         if self.remove_stress(phoneme) in self.vowel_phonemes)
        consonant_count = sum(count for phoneme, count in self.phoneme_counts.items() 
                             if self.remove_stress(phoneme) in self.consonant_phonemes)
        other_count = self.total_phonemes - vowel_count - consonant_count
        
        labels = ['Vowels', 'Consonants']
        sizes = [vowel_count, consonant_count]
        colors = ['lightcoral', 'lightskyblue']
        
        if other_count > 0:
            labels.append('Other')
            sizes.append(other_count)
            colors.append('lightgray')
        
        ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Vowel vs Consonant Distribution')
        
        # 3. Phoneme frequency distribution
        all_counts = list(self.phoneme_counts.values())
        ax3.hist(all_counts, bins=20, color='lightgreen', alpha=0.7, edgecolor='black')
        ax3.set_xlabel('Frequency')
        ax3.set_ylabel('Number of Phonemes')
        ax3.set_title('Phoneme Frequency Distribution')
        
        # 4. File comparison (if multiple files)
        if len(self.file_phoneme_counts) > 1:
            file_names = list(self.file_phoneme_counts.keys())
            file_totals = [sum(counts.values()) for counts in self.file_phoneme_counts.values()]
            
            ax4.bar(range(len(file_names)), file_totals, color='orange', alpha=0.7)
            ax4.set_xlabel('Files')
            ax4.set_ylabel('Total Phonemes')
            ax4.set_title('Phoneme Count by File')
            ax4.set_xticks(range(len(file_names)))
            ax4.set_xticklabels([name.replace('.txt', '') for name in file_names], rotation=45)
        else:
            ax4.text(0.5, 0.5, 'Multiple files needed\nfor comparison', 
                    horizontalalignment='center', verticalalignment='center', 
                    transform=ax4.transAxes, fontsize=12)
            ax4.set_title('File Comparison (N/A)')
        
        plt.tight_layout()
        
        # Save the plot
        output_path = os.path.join(output_dir, 'phoneme_distribution_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\nVisualization saved to: {output_path}")
        
        # Show the plot
        plt.show()
    
    def save_detailed_report(self, output_path: str = "phoneme_analysis_report.txt") -> None:
        """Save a detailed text report."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("ENGLISH PHONEME DISTRIBUTION ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
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
        
        print(f"Detailed report saved to: {output_path}")


def main():
    """Main function to run the phoneme analysis."""
    # File paths to analyze
    base_dir = "/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/materials"
    
    files_to_analyze = [
        os.path.join(base_dir, "50_sentences_list.txt"),
        os.path.join(base_dir, "50_words_list.txt"),
        os.path.join(base_dir, "150_sentences_list.txt"),
        os.path.join(base_dir, "150_words_list.txt")
    ]
    
    # Create analyzer instance
    analyzer = PhonemeAnalyzer()
    
    # Analyze files
    analyzer.analyze_files(files_to_analyze)
    
    # Print statistics
    analyzer.print_phoneme_statistics()
    analyzer.print_file_comparison()
    
    # Create visualization
    try:
        analyzer.create_visualization()
    except Exception as e:
        print(f"Error creating visualization: {e}")
        print("Make sure matplotlib is installed: pip install matplotlib")
    
    # Save detailed report
    analyzer.save_detailed_report()
    
    print(f"\n=== Analysis Complete ===")
    print(f"Processed {analyzer.total_words} words and {analyzer.total_phonemes} phonemes")


if __name__ == "__main__":
    main()
