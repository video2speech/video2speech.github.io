#!/usr/bin/env python3
"""
Phoneme Distribution Analysis for English Text Files

This script analyzes the distribution of 44 English phonemes across multiple text files
and generates a histogram sorted from most to least frequent.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import re
import os

# Carnegie Mellon University Pronouncing Dictionary phoneme mapping
# Mapping common English words to their phonemes using ARPAbet
# This is a simplified mapping - in a production system, you'd use a full CMU dict or phoneme library

# The 44 English phonemes (ARPAbet notation)
ENGLISH_PHONEMES = {
    # Vowels (20)
    'AA': 'ɑ',   # father
    'AE': 'æ',   # cat
    'AH': 'ʌ',   # cut
    'AO': 'ɔ',   # caught
    'AW': 'aʊ',  # how
    'AY': 'aɪ',  # hide
    'EH': 'ɛ',   # red
    'ER': 'ɝ',   # her
    'EY': 'eɪ',  # say
    'IH': 'ɪ',   # hit
    'IY': 'i',   # see
    'OW': 'oʊ',  # show
    'OY': 'ɔɪ',  # toy
    'UH': 'ʊ',   # put
    'UW': 'u',   # too
    
    # Consonants (24)
    'B': 'b',    # be
    'CH': 'tʃ',  # cheese
    'D': 'd',    # dee
    'DH': 'ð',   # thee
    'F': 'f',    # fee
    'G': 'g',    # green
    'HH': 'h',   # he
    'JH': 'dʒ',  # gee
    'K': 'k',    # key
    'L': 'l',    # lee
    'M': 'm',    # me
    'N': 'n',    # knee
    'NG': 'ŋ',   # ping
    'P': 'p',    # pee
    'R': 'r',    # read
    'S': 's',    # sea
    'SH': 'ʃ',   # she
    'T': 't',    # tea
    'TH': 'θ',   # theta
    'V': 'v',    # vee
    'W': 'w',    # we
    'Y': 'j',    # yield
    'Z': 'z',    # zee
    'ZH': 'ʒ'    # seizure
}

# Simplified phoneme mapping for common English words
# In a full implementation, you'd use the complete CMU Pronouncing Dictionary
WORD_TO_PHONEMES = {
    # Common words from the files
    'the': ['DH', 'AH'],
    'i': ['AY'],
    'you': ['Y', 'UW'],
    'and': ['AH', 'N', 'D'],
    'it': ['IH', 'T'],
    'a': ['AH'],
    'to': ['T', 'UW'],
    'of': ['AH', 'V'],
    'that': ['DH', 'AE', 'T'],
    'in': ['IH', 'N'],
    'we': ['W', 'IY'],
    'is': ['IH', 'Z'],
    'do': ['D', 'UW'],
    'they': ['DH', 'EY'],
    'was': ['W', 'AH', 'Z'],
    'yeah': ['Y', 'AE'],
    'have': ['HH', 'AE', 'V'],
    'what': ['W', 'AH', 'T'],
    'he': ['HH', 'IY'],
    'but': ['B', 'AH', 'T'],
    'for': ['F', 'AO', 'R'],
    'be': ['B', 'IY'],
    'on': ['AO', 'N'],
    'this': ['DH', 'IH', 'S'],
    'know': ['N', 'OW'],
    'well': ['W', 'EH', 'L'],
    'so': ['S', 'OW'],
    'oh': ['OW'],
    'got': ['G', 'AO', 'T'],
    'not': ['N', 'AO', 'T'],
    'are': ['AA', 'R'],
    'if': ['IH', 'F'],
    'with': ['W', 'IH', 'TH'],
    'no': ['N', 'OW'],
    'she': ['SH', 'IY'],
    'at': ['AE', 'T'],
    'there': ['DH', 'EH', 'R'],
    'think': ['TH', 'IH', 'NG', 'K'],
    'yes': ['Y', 'EH', 'S'],
    'just': ['JH', 'AH', 'S', 'T'],
    'all': ['AO', 'L'],
    'can': ['K', 'AE', 'N'],
    'then': ['DH', 'EH', 'N'],
    'get': ['G', 'EH', 'T'],
    'did': ['D', 'IH', 'D'],
    'or': ['AO', 'R'],
    'would': ['W', 'UH', 'D'],
    'them': ['DH', 'EH', 'M'],
    'one': ['W', 'AH', 'N'],
    'up': ['AH', 'P'],
    'go': ['G', 'OW'],
    'now': ['N', 'AW'],
    'your': ['Y', 'UH', 'R'],
    'had': ['HH', 'AE', 'D'],
    'were': ['W', 'ER'],
    'about': ['AH', 'B', 'AW', 'T'],
    'two': ['T', 'UW'],
    'said': ['S', 'EH', 'D'],
    'see': ['S', 'IY'],
    'me': ['M', 'IY'],
    'very': ['V', 'EH', 'R', 'IY'],
    'out': ['AW', 'T'],
    'my': ['M', 'AY'],
    'when': ['W', 'EH', 'N'],
    'mean': ['M', 'IY', 'N'],
    'right': ['R', 'AY', 'T'],
    'from': ['F', 'R', 'AH', 'M'],
    'going': ['G', 'OW', 'IH', 'NG'],
    'say': ['S', 'EY'],
    'been': ['B', 'IH', 'N'],
    'people': ['P', 'IY', 'P', 'AH', 'L'],
    'because': ['B', 'IH', 'K', 'AO', 'Z'],
    'some': ['S', 'AH', 'M'],
    'could': ['K', 'UH', 'D'],
    'will': ['W', 'IH', 'L'],
    'how': ['HH', 'AW'],
    'time': ['T', 'AY', 'M'],
    'who': ['HH', 'UW'],
    'want': ['W', 'AO', 'N', 'T'],
    'like': ['L', 'AY', 'K'],
    'come': ['K', 'AH', 'M'],
    'really': ['R', 'IY', 'L', 'IY'],
    'here': ['HH', 'IH', 'R'],
    'put': ['P', 'UH', 'T'],
    'good': ['G', 'UH', 'D'],
    'as': ['AE', 'Z'],
    'does': ['D', 'AH', 'Z'],
    'any': ['EH', 'N', 'IY'],
    'down': ['D', 'AW', 'N'],
    'where': ['W', 'EH', 'R'],
    'him': ['HH', 'IH', 'M'],
    'other': ['AH', 'DH', 'ER'],
    'something': ['S', 'AH', 'M', 'TH', 'IH', 'NG'],
    'these': ['DH', 'IY', 'Z'],
    'way': ['W', 'EY'],
    'back': ['B', 'AE', 'K'],
    'should': ['SH', 'UH', 'D'],
    'take': ['T', 'EY', 'K'],
    'thing': ['TH', 'IH', 'NG'],
    'look': ['L', 'UH', 'K'],
    'why': ['W', 'AY'],
    'things': ['TH', 'IH', 'NG', 'Z'],
    'only': ['OW', 'N', 'L', 'IY'],
    'us': ['AH', 'S'],
    'lot': ['L', 'AO', 'T'],
    'make': ['M', 'EY', 'K'],
    'first': ['F', 'ER', 'S', 'T'],
    'okay': ['OW', 'K', 'EY'],
    'more': ['M', 'AO', 'R'],
    'doing': ['D', 'UW', 'IH', 'NG'],
    'done': ['D', 'AH', 'N'],
    'am': ['AE', 'M'],
    'bad': ['B', 'AE', 'D'],
    'coming': ['K', 'AH', 'M', 'IH', 'NG'],
    'feel': ['F', 'IY', 'L'],
    'help': ['HH', 'EH', 'L', 'P'],
    'hope': ['HH', 'OW', 'P'],
    'need': ['N', 'IY', 'D'],
    'please': ['P', 'L', 'IY', 'Z'],
    'tell': ['T', 'EH', 'L'],
    'give': ['G', 'IH', 'V'],
    'thought': ['TH', 'AO', 'T'],
    'again': ['AH', 'G', 'EH', 'N'],
    'might': ['M', 'AY', 'T'],
    'her': ['HH', 'ER'],
    'last': ['L', 'AE', 'S', 'T'],
    'much': ['M', 'AH', 'CH'],
    'still': ['S', 'T', 'IH', 'L'],
    'never': ['N', 'EH', 'V', 'ER'],
    'than': ['DH', 'AE', 'N'],
    'same': ['S', 'EY', 'M'],
    'another': ['AH', 'N', 'AH', 'DH', 'ER'],
    'money': ['M', 'AH', 'N', 'IY'],
    'anything': ['EH', 'N', 'IY', 'TH', 'IH', 'NG'],
    'thank': ['TH', 'AE', 'NG', 'K'],
    'too': ['T', 'UW'],
    'nice': ['N', 'AY', 'S'],
    'work': ['W', 'ER', 'K'],
    'always': ['AO', 'L', 'W', 'EY', 'Z'],
    'tired': ['T', 'AY', 'ER', 'D'],
    'years': ['Y', 'IH', 'R', 'Z'],
    'through': ['TH', 'R', 'UW'],
    'little': ['L', 'IH', 'T', 'AH', 'L'],
    
    # Additional words from the other files
    'outside': ['AW', 'T', 'S', 'AY', 'D'],
    'bring': ['B', 'R', 'IH', 'NG'],
    'glasses': ['G', 'L', 'AE', 'S', 'IH', 'Z'],
    'comfortable': ['K', 'AH', 'M', 'F', 'ER', 'T', 'AH', 'B', 'AH', 'L'],
    'faith': ['F', 'EY', 'TH'],
    'hello': ['HH', 'AH', 'L', 'OW'],
    'computer': ['K', 'AH', 'M', 'P', 'Y', 'UW', 'T', 'ER'],
    'hungry': ['HH', 'AH', 'NG', 'G', 'R', 'IY'],
    'thirsty': ['TH', 'ER', 'S', 'T', 'IY'],
    'clean': ['K', 'L', 'IY', 'N'],
    'nurse': ['N', 'ER', 'S'],
    'family': ['F', 'AE', 'M', 'AH', 'L', 'IY'],
    'music': ['M', 'Y', 'UW', 'Z', 'IH', 'K'],
    'closer': ['K', 'L', 'OW', 'S', 'ER'],
    'goodbye': ['G', 'UH', 'D', 'B', 'AY'],
    'success': ['S', 'AH', 'K', 'S', 'EH', 'S'],
}

def text_to_phonemes(text):
    """Convert text to phonemes using our simplified mapping."""
    # Clean and normalize text
    text = text.lower()
    text = re.sub(r"[^\w\s']", '', text)  # Remove punctuation except apostrophes
    text = re.sub(r"'s\b", '', text)  # Remove possessive 's
    text = re.sub(r"n't\b", ' not', text)  # Expand contractions
    text = re.sub(r"'re\b", ' are', text)
    text = re.sub(r"'ve\b", ' have', text)
    text = re.sub(r"'ll\b", ' will', text)
    text = re.sub(r"'d\b", ' would', text)
    text = re.sub(r"'m\b", ' am', text)
    
    words = text.split()
    phonemes = []
    
    for word in words:
        if word in WORD_TO_PHONEMES:
            phonemes.extend(WORD_TO_PHONEMES[word])
        else:
            # For unknown words, make a simple approximation based on spelling
            phonemes.extend(approximate_phonemes(word))
    
    return phonemes

def approximate_phonemes(word):
    """Simple phoneme approximation for unknown words."""
    phonemes = []
    i = 0
    while i < len(word):
        char = word[i]
        
        # Handle common letter combinations
        if i < len(word) - 1:
            two_char = word[i:i+2]
            if two_char == 'th':
                phonemes.append('TH' if i == 0 or word[i-1] in 'aeiou' else 'DH')
                i += 2
                continue
            elif two_char == 'sh':
                phonemes.append('SH')
                i += 2
                continue
            elif two_char == 'ch':
                phonemes.append('CH')
                i += 2
                continue
            elif two_char == 'ng':
                phonemes.append('NG')
                i += 2
                continue
        
        # Single character mappings (simplified)
        char_to_phoneme = {
            'a': 'AE', 'e': 'EH', 'i': 'IH', 'o': 'AO', 'u': 'AH',
            'b': 'B', 'c': 'K', 'd': 'D', 'f': 'F', 'g': 'G',
            'h': 'HH', 'j': 'JH', 'k': 'K', 'l': 'L', 'm': 'M',
            'n': 'N', 'p': 'P', 'r': 'R', 's': 'S', 't': 'T',
            'v': 'V', 'w': 'W', 'y': 'Y', 'z': 'Z'
        }
        
        if char in char_to_phoneme:
            phonemes.append(char_to_phoneme[char])
        
        i += 1
    
    return phonemes

def read_file_content(filepath):
    """Read and return the content of a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: File {filepath} not found")
        return ""

def analyze_phoneme_distribution(file_paths):
    """Analyze phoneme distribution across multiple files."""
    all_phonemes = []
    
    for filepath in file_paths:
        print(f"Processing {filepath}...")
        content = read_file_content(filepath)
        
        # Split content into lines and process each line
        lines = content.strip().split('\n')
        for line in lines:
            # Remove line numbers if present (format: "    N|content")
            line = re.sub(r'^\s*\d+\|', '', line)
            phonemes = text_to_phonemes(line)
            all_phonemes.extend(phonemes)
    
    # Count phoneme frequencies
    phoneme_counts = Counter(all_phonemes)
    
    # Sort by frequency (descending)
    sorted_phonemes = sorted(phoneme_counts.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_phonemes, len(all_phonemes)

def create_histogram(phoneme_data, total_phonemes):
    """Create and display a histogram of phoneme distribution."""
    phonemes, counts = zip(*phoneme_data) if phoneme_data else ([], [])
    
    # Create figure with larger size for better readability
    plt.figure(figsize=(15, 8))
    
    # Create bars
    bars = plt.bar(range(len(phonemes)), counts, color='skyblue', edgecolor='navy', alpha=0.7)
    
    # Customize the plot
    plt.title('English Phoneme Distribution Analysis\n(Sorted from Most to Least Frequent)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Phonemes (ARPAbet notation)', fontsize=12, fontweight='bold')
    plt.ylabel('Frequency Count', fontsize=12, fontweight='bold')
    
    # Set x-axis labels
    plt.xticks(range(len(phonemes)), phonemes, rotation=45, ha='right')
    
    # Add value labels on top of bars
    for i, (phoneme, count) in enumerate(zip(phonemes, counts)):
        plt.text(i, count + max(counts) * 0.01, str(count), 
                ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # Add grid for better readability
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Add statistics text
    plt.figtext(0.02, 0.02, f'Total phonemes analyzed: {total_phonemes}', 
                fontsize=10, style='italic')
    
    # Save the plot
    plt.savefig('phoneme_distribution.png', dpi=300, bbox_inches='tight')
    print(f"\nHistogram saved as 'phoneme_distribution.png'")

def print_statistics(phoneme_data, total_phonemes):
    """Print detailed statistics about the phoneme distribution."""
    print(f"\n{'='*60}")
    print("PHONEME DISTRIBUTION ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Total phonemes analyzed: {total_phonemes}")
    print(f"Unique phonemes found: {len(phoneme_data)}")
    print(f"{'='*60}")
    
    print(f"\n{'Rank':<4} {'Phoneme':<8} {'IPA':<6} {'Count':<8} {'Percentage':<10}")
    print("-" * 40)
    
    for i, (phoneme, count) in enumerate(phoneme_data[:20], 1):  # Show top 20
        percentage = (count / total_phonemes) * 100
        ipa_symbol = ENGLISH_PHONEMES.get(phoneme, phoneme)
        print(f"{i:<4} {phoneme:<8} {ipa_symbol:<6} {count:<8} {percentage:<10.2f}%")
    
    if len(phoneme_data) > 20:
        print(f"... and {len(phoneme_data) - 20} more phonemes")

def main():
    """Main function to run the phoneme analysis."""
    # Define the file paths
    file_paths = [
        'materials/50_sentences_list.txt',
        'materials/50_words_list.txt',
        'materials/150_sentences_list.txt',
        'materials/150_words_list.txt'
    ]
    
    print("English Phoneme Distribution Analysis")
    print("=" * 40)
    
    # Analyze phoneme distribution
    phoneme_data, total_phonemes = analyze_phoneme_distribution(file_paths)
    
    # Print statistics
    print_statistics(phoneme_data, total_phonemes)
    
    # Create and display histogram
    create_histogram(phoneme_data, total_phonemes)
    
    print(f"\nAnalysis complete! Processed {len(file_paths)} files.")

if __name__ == "__main__":
    main()
