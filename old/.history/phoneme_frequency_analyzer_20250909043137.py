#!/usr/bin/env python3
"""
Convert selected sentences to CMU phonemes and analyze frequency distribution.
"""

import subprocess
import sys
import re
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np

def install_package(package):
    """Install a package using pip"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required packages
try:
    import nltk
    from nltk.corpus import cmudict
    import matplotlib.pyplot as plt
except ImportError:
    print("Installing required packages...")
    install_package("nltk")
    install_package("matplotlib")
    import nltk
    from nltk.corpus import cmudict
    import matplotlib.pyplot as plt

# Download CMUdict if not already present
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    print("Downloading CMUdict...")
    nltk.download('cmudict')

def clean_word(word):
    """Clean a word by removing punctuation and converting to lowercase."""
    # Remove punctuation but keep contractions like n't, 's, etc.
    word = re.sub(r'^[^\w\']+|[^\w\']+$', '', word.lower())
    return word

def get_cmu_phonemes(word, cmu_dict):
    """Get CMUdict phonemes for a word, removing stress markers."""
    word_clean = clean_word(word)
    if not word_clean:
        return []
    
    # Handle contractions and special cases
    if word_clean in cmu_dict:
        # Take the first pronunciation and remove stress markers
        phonemes = cmu_dict[word_clean][0]
        return [p.rstrip('012') for p in phonemes]
    return []

def tokenize_sentence(sentence):
    """Tokenize a sentence into words, preserving contractions."""
    # Split on whitespace and punctuation, but keep contractions together
    tokens = re.findall(r"\b\w+(?:'\w+)?\b|\S", sentence)
    return tokens

def process_sentences(filename):
    """Process all sentences and extract phonemes."""
    print(f"Loading CMUdict...")
    cmu_dict = cmudict.dict()
    
    print(f"Processing sentences from {filename}...")
    
    phoneme_counter = Counter()
    total_sentences = 0
    processed_sentences = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"Processed {line_num} lines...")
            
            sentence = line.strip()
            if not sentence:
                continue
                
            total_sentences += 1
            words = tokenize_sentence(sentence)
            sentence_phonemes = []
            
            for word in words:
                phonemes = get_cmu_phonemes(word, cmu_dict)
                sentence_phonemes.extend(phonemes)
            
            if sentence_phonemes:
                processed_sentences += 1
                for phoneme in sentence_phonemes:
                    phoneme_counter[phoneme] += 1
    
    print(f"Total sentences: {total_sentences}")
    print(f"Sentences with phonemes: {processed_sentences}")
    print(f"Total phonemes found: {sum(phoneme_counter.values())}")
    print(f"Unique phonemes: {len(phoneme_counter)}")
    
    return phoneme_counter

def create_histogram(phoneme_counter):
    """Create and save a histogram of phoneme frequencies."""
    # Sort phonemes by frequency (high to low)
    sorted_phonemes = phoneme_counter.most_common()
    
    if not sorted_phonemes:
        print("No phonemes found!")
        return
    
    phonemes = [item[0] for item in sorted_phonemes]
    frequencies = [item[1] for item in sorted_phonemes]
    
    # Calculate percentages
    total_count = sum(frequencies)
    percentages = [(freq / total_count) * 100 for freq in frequencies]
    
    # Create the histogram
    plt.figure(figsize=(15, 8))
    bars = plt.bar(range(len(phonemes)), percentages, color='skyblue', edgecolor='navy', alpha=0.7)
    
    # Customize the plot
    plt.title('Phoneme Frequency Distribution in Selected Sentences', fontsize=16, fontweight='bold')
    plt.xlabel('Phonemes', fontsize=12)
    plt.ylabel('Percentage (%)', fontsize=12)
    
    # Set x-axis labels
    plt.xticks(range(len(phonemes)), phonemes, rotation=45, ha='right')
    
    # Add percentage labels on top of bars
    for i, (bar, percentage) in enumerate(zip(bars, percentages)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(percentages)*0.01, 
                f'{percentage:.2f}%', ha='center', va='bottom', fontsize=8)
    
    # Add grid for better readability
    plt.grid(axis='y', alpha=0.3)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('phoneme_frequency_histogram.png', dpi=300, bbox_inches='tight')
    plt.savefig('phoneme_frequency_histogram.pdf', bbox_inches='tight')
    
    print("Histogram saved as 'phoneme_frequency_histogram.png' and 'phoneme_frequency_histogram.pdf'")
    
    # Display frequency table
    print("\n" + "="*60)
    print("PHONEME FREQUENCY ANALYSIS")
    print("="*60)
    print(f"{'Rank':<4} {'Phoneme':<8} {'Frequency':<12} {'Percentage':<10}")
    print("-" * 40)
    
    total_count = sum(frequencies)
    for rank, (phoneme, freq) in enumerate(sorted_phonemes, 1):
        percentage = (freq / total_count) * 100
        print(f"{rank:<4} {phoneme:<8} {freq:<12,} {percentage:<10.2f}%")
    
    return sorted_phonemes

def main():
    filename = 'selected_sentences.txt'
    
    print("Starting phoneme frequency analysis...")
    phoneme_counter = process_sentences(filename)
    
    if phoneme_counter:
        sorted_phonemes = create_histogram(phoneme_counter)
        
        # Save detailed results to file
        with open('phoneme_frequency_report.txt', 'w') as f:
            f.write("CMU Phoneme Frequency Analysis Report\n")
            f.write("="*50 + "\n\n")
            f.write(f"Total phonemes analyzed: {sum(phoneme_counter.values()):,}\n")
            f.write(f"Unique phonemes found: {len(phoneme_counter)}\n\n")
            f.write(f"{'Rank':<4} {'Phoneme':<8} {'Frequency':<12} {'Percentage':<10}\n")
            f.write("-" * 40 + "\n")
            
            total_count = sum(phoneme_counter.values())
            for rank, (phoneme, freq) in enumerate(sorted_phonemes, 1):
                percentage = (freq / total_count) * 100
                f.write(f"{rank:<4} {phoneme:<8} {freq:<12,} {percentage:<10.2f}%\n")
        
        print("Detailed report saved as 'phoneme_frequency_report.txt'")
    else:
        print("No phonemes found in the input file!")

if __name__ == "__main__":
    main()
