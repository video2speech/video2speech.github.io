#!/usr/bin/env python3
"""
Legal Terms Phoneme Analysis Script
Analyzes legal terms and groups them by phonemes, sorted by frequency.
"""

import nltk
from collections import defaultdict, Counter
import re

# Download required NLTK data
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    nltk.download('cmudict')

from nltk.corpus import cmudict

# Get CMU Pronouncing Dictionary
cmu_dict = cmudict.dict()

# Standard 39 English phonemes (ARPAbet format)
STANDARD_PHONEMES = {
    # Vowels (15)
    'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
    # Consonants (24)
    'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
}

def clean_phoneme(phoneme):
    """Remove stress markers from phoneme."""
    return re.sub(r'\d', '', phoneme)

def get_word_phonemes(word):
    """Get phonemes for a word using CMU dictionary."""
    word_lower = word.lower()
    if word_lower in cmu_dict:
        # Get first pronunciation (most common)
        phonemes = cmu_dict[word_lower][0]
        # Clean stress markers
        return [clean_phoneme(p) for p in phonemes]
    else:
        print(f"Warning: '{word}' not found in CMU dictionary")
        return []

def analyze_legal_terms_phonemes():
    """Analyze phonemes in legal terms."""
    
    # Read legal terms
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/materials/legal_terms', 'r') as f:
        legal_terms = [line.strip() for line in f if line.strip()]
    
    print(f"Analyzing {len(legal_terms)} legal terms...")
    
    # Track phonemes and their associated words
    phoneme_to_words = defaultdict(set)
    phoneme_counts = Counter()
    word_phonemes = {}
    
    # Process each legal term
    for term in legal_terms:
        phonemes = get_word_phonemes(term)
        if phonemes:
            word_phonemes[term] = phonemes
            for phoneme in phonemes:
                if phoneme in STANDARD_PHONEMES:
                    phoneme_to_words[phoneme].add(term)
                    phoneme_counts[phoneme] += 1
    
    # Sort phonemes by frequency (most to least represented)
    sorted_phonemes = phoneme_counts.most_common()
    
    # Create comprehensive report
    report = []
    report.append("=" * 80)
    report.append("LEGAL TERMS PHONEME ANALYSIS")
    report.append("=" * 80)
    report.append(f"Total legal terms analyzed: {len(legal_terms)}")
    report.append(f"Terms with phoneme data: {len(word_phonemes)}")
    report.append(f"Phonemes found: {len(phoneme_counts)}")
    report.append("")
    
    # Phoneme frequency summary
    report.append("PHONEME FREQUENCY SUMMARY:")
    report.append("-" * 40)
    for phoneme, count in sorted_phonemes:
        percentage = (count / sum(phoneme_counts.values())) * 100
        report.append(f"{phoneme:3s}: {count:3d} occurrences ({percentage:5.1f}%)")
    report.append("")
    
    # Detailed phoneme analysis (sorted by frequency)
    report.append("DETAILED PHONEME ANALYSIS (Most to Least Frequent):")
    report.append("=" * 60)
    
    for phoneme, count in sorted_phonemes:
        words = sorted(list(phoneme_to_words[phoneme]))
        word_count = len(words)
        percentage = (count / sum(phoneme_counts.values())) * 100
        
        report.append(f"\n/{phoneme}/ - {count} total occurrences in {word_count} words ({percentage:.1f}%)")
        report.append("-" * 50)
        
        # Show words containing this phoneme
        words_per_line = 8
        for i in range(0, len(words), words_per_line):
            line_words = words[i:i + words_per_line]
            report.append("  " + ", ".join(line_words))
    
    # Check for missing phonemes
    missing_phonemes = STANDARD_PHONEMES - set(phoneme_counts.keys())
    if missing_phonemes:
        report.append(f"\nMISSING PHONEMES ({len(missing_phonemes)}):")
        report.append("-" * 30)
        for phoneme in sorted(missing_phonemes):
            report.append(f"/{phoneme}/ - Not represented in legal terms")
    
    # Word-to-phoneme mapping
    report.append("\n" + "=" * 60)
    report.append("WORD-TO-PHONEME MAPPING:")
    report.append("=" * 60)
    
    for word in sorted(word_phonemes.keys()):
        phonemes_str = " ".join(word_phonemes[word])
        report.append(f"{word:15s} -> /{phonemes_str}/")
    
    return "\n".join(report), phoneme_counts, phoneme_to_words

if __name__ == "__main__":
    report, counts, word_mapping = analyze_legal_terms_phonemes()
    
    # Save report
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/legal_terms_phoneme_report.txt', 'w') as f:
        f.write(report)
    
    print("Analysis complete! Report saved to 'legal_terms_phoneme_report.txt'")
    print("\nTop 10 most frequent phonemes:")
    for phoneme, count in counts.most_common(10):
        print(f"  /{phoneme}/: {count} occurrences")


