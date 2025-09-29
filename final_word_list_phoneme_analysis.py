#!/usr/bin/env python3
"""
Final Word List Phoneme Analysis Script
Analyzes the complete final word list and groups words by phonemes, sorted by frequency.
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
    # Handle contractions and special cases
    word_clean = word.lower().replace("'", "")
    
    # Special handling for common contractions
    contraction_map = {
        "nt": "not",      # n't -> not
        "s": "is",        # 's -> is (or possessive, but we'll use 'is')
        "ve": "have",     # 've -> have
        "re": "are",      # 're -> are
        "ll": "will",     # 'll -> will
        "d": "would",     # 'd -> would (or had, but we'll use 'would')
        "m": "am",        # 'm -> am
        "em": "them"      # 'em -> them
    }
    
    # Check if it's a contraction
    if word.startswith("'") and len(word) > 1:
        contraction_part = word[1:].lower()
        if contraction_part in contraction_map:
            word_clean = contraction_map[contraction_part]
    
    # Try the cleaned word
    if word_clean in cmu_dict:
        phonemes = cmu_dict[word_clean][0]
        return [clean_phoneme(p) for p in phonemes]
    
    # Try original word
    word_lower = word.lower()
    if word_lower in cmu_dict:
        phonemes = cmu_dict[word_lower][0]
        return [clean_phoneme(p) for p in phonemes]
    
    # Try without punctuation
    word_no_punct = re.sub(r'[^\w]', '', word.lower())
    if word_no_punct in cmu_dict:
        phonemes = cmu_dict[word_no_punct][0]
        return [clean_phoneme(p) for p in phonemes]
    
    print(f"Warning: '{word}' not found in CMU dictionary")
    return []

def analyze_final_word_list_phonemes():
    """Analyze phonemes in the final word list."""
    
    # Read final word list
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/final_word_list.txt', 'r') as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"Analyzing {len(words)} words from final word list...")
    
    # Track phonemes and their associated words
    phoneme_to_words = defaultdict(set)
    phoneme_counts = Counter()
    word_phonemes = {}
    failed_words = []
    
    # Process each word
    for word in words:
        phonemes = get_word_phonemes(word)
        if phonemes:
            word_phonemes[word] = phonemes
            for phoneme in phonemes:
                if phoneme in STANDARD_PHONEMES:
                    phoneme_to_words[phoneme].add(word)
                    phoneme_counts[phoneme] += 1
        else:
            failed_words.append(word)
    
    # Sort phonemes by frequency (most to least represented)
    sorted_phonemes = phoneme_counts.most_common()
    
    # Create comprehensive report
    report = []
    report.append("=" * 80)
    report.append("FINAL WORD LIST PHONEME ANALYSIS")
    report.append("=" * 80)
    report.append(f"Total words analyzed: {len(words)}")
    report.append(f"Words with phoneme data: {len(word_phonemes)}")
    report.append(f"Words failed to map: {len(failed_words)}")
    report.append(f"Phonemes found: {len(phoneme_counts)} out of 39 standard phonemes")
    report.append(f"Total phoneme occurrences: {sum(phoneme_counts.values())}")
    report.append("")
    
    # Failed words summary
    if failed_words:
        report.append("WORDS NOT FOUND IN CMU DICTIONARY:")
        report.append("-" * 40)
        failed_per_line = 10
        for i in range(0, len(failed_words), failed_per_line):
            line_words = failed_words[i:i + failed_per_line]
            report.append("  " + ", ".join(line_words))
        report.append("")
    
    # Phoneme frequency summary
    report.append("PHONEME FREQUENCY SUMMARY (Most to Least Frequent):")
    report.append("-" * 60)
    for i, (phoneme, count) in enumerate(sorted_phonemes, 1):
        percentage = (count / sum(phoneme_counts.values())) * 100
        word_count = len(phoneme_to_words[phoneme])
        report.append(f"{i:2d}. /{phoneme:3s}/: {count:4d} occurrences ({percentage:5.1f}%) in {word_count:4d} words")
    report.append("")
    
    # Detailed phoneme analysis (sorted by frequency)
    report.append("DETAILED PHONEME ANALYSIS (Most to Least Frequent):")
    report.append("=" * 80)
    
    for i, (phoneme, count) in enumerate(sorted_phonemes, 1):
        words_list = sorted(list(phoneme_to_words[phoneme]))
        word_count = len(words_list)
        percentage = (count / sum(phoneme_counts.values())) * 100
        
        report.append(f"\n{i:2d}. /{phoneme}/ - {count} total occurrences in {word_count} words ({percentage:.1f}%)")
        report.append("-" * 70)
        
        # Show words containing this phoneme (wrap to multiple lines)
        words_per_line = 10
        for j in range(0, len(words_list), words_per_line):
            line_words = words_list[j:j + words_per_line]
            report.append("    " + ", ".join(line_words))
    
    # Check for missing phonemes
    missing_phonemes = STANDARD_PHONEMES - set(phoneme_counts.keys())
    if missing_phonemes:
        report.append(f"\n\nMISSING PHONEMES ({len(missing_phonemes)} out of 39):")
        report.append("=" * 50)
        for phoneme in sorted(missing_phonemes):
            report.append(f"/{phoneme}/ - Not represented in final word list")
    else:
        report.append(f"\n\nALL 39 STANDARD PHONEMES ARE REPRESENTED!")
    
    # Statistics summary
    report.append(f"\n\nSTATISTICS SUMMARY:")
    report.append("=" * 30)
    report.append(f"Total words: {len(words)}")
    report.append(f"Successfully mapped: {len(word_phonemes)} ({len(word_phonemes)/len(words)*100:.1f}%)")
    report.append(f"Failed to map: {len(failed_words)} ({len(failed_words)/len(words)*100:.1f}%)")
    report.append(f"Phonemes represented: {len(phoneme_counts)}/39 ({len(phoneme_counts)/39*100:.1f}%)")
    report.append(f"Total phoneme instances: {sum(phoneme_counts.values())}")
    report.append(f"Average phonemes per word: {sum(phoneme_counts.values())/len(word_phonemes):.1f}")
    
    # Top and bottom phonemes
    if sorted_phonemes:
        report.append(f"\nMost frequent phoneme: /{sorted_phonemes[0][0]}/ ({sorted_phonemes[0][1]} occurrences)")
        report.append(f"Least frequent phoneme: /{sorted_phonemes[-1][0]}/ ({sorted_phonemes[-1][1]} occurrences)")
    
    return "\n".join(report), phoneme_counts, phoneme_to_words, word_phonemes, failed_words

def generate_word_to_phoneme_mapping(word_phonemes):
    """Generate a separate detailed word-to-phoneme mapping."""
    mapping_report = []
    mapping_report.append("=" * 80)
    mapping_report.append("COMPLETE WORD-TO-PHONEME MAPPING")
    mapping_report.append("=" * 80)
    mapping_report.append(f"Total mapped words: {len(word_phonemes)}")
    mapping_report.append("")
    
    for word in sorted(word_phonemes.keys(), key=str.lower):
        phonemes_str = " ".join(word_phonemes[word])
        mapping_report.append(f"{word:20s} -> /{phonemes_str}/")
    
    return "\n".join(mapping_report)

if __name__ == "__main__":
    print("Starting comprehensive phoneme analysis of final word list...")
    
    report, counts, word_mapping, word_phonemes, failed = analyze_final_word_list_phonemes()
    
    # Save main report
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/final_word_list_phoneme_report.txt', 'w') as f:
        f.write(report)
    
    # Save word-to-phoneme mapping
    mapping_report = generate_word_to_phoneme_mapping(word_phonemes)
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/final_word_list_phoneme_mapping.txt', 'w') as f:
        f.write(mapping_report)
    
    print("\nAnalysis complete!")
    print(f"Main report saved to 'final_word_list_phoneme_report.txt'")
    print(f"Word mapping saved to 'final_word_list_phoneme_mapping.txt'")
    print(f"\nQuick Summary:")
    print(f"- Total words: {len(word_phonemes) + len(failed)}")
    print(f"- Successfully mapped: {len(word_phonemes)}")
    print(f"- Phonemes found: {len(counts)}/39")
    
    if counts:
        print(f"\nTop 10 most frequent phonemes:")
        for i, (phoneme, count) in enumerate(counts.most_common(10), 1):
            percentage = (count / sum(counts.values())) * 100
            print(f"  {i:2d}. /{phoneme}/: {count} occurrences ({percentage:.1f}%)")


