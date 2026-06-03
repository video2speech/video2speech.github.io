#!/usr/bin/env python3
"""
Phoneme Coverage Analyzer
Finds the minimum set of top k frequent words that cover all 44 English phonemes.
"""

import re
from collections import defaultdict, Counter
import sys

# The 44 English phonemes (IPA symbols)
ENGLISH_PHONEMES = {
    # Consonants (24)
    'p', 'b', 't', 'd', 'k', 'g', 'f', 'v', 'θ', 'ð', 's', 'z', 'ʃ', 'ʒ', 
    'h', 'tʃ', 'dʒ', 'm', 'n', 'ŋ', 'l', 'r', 'w', 'j',
    # Vowels (20)
    'i', 'ɪ', 'e', 'ɛ', 'æ', 'ɑ', 'ɔ', 'o', 'ʊ', 'u', 'ʌ', 'ə', 'ɜ', 'aɪ', 
    'aʊ', 'ɔɪ', 'eɪ', 'oʊ', 'ɪər', 'ɛər'
}

# Simplified phoneme mapping for common English words
# This is a basic mapping - in practice, you'd use a proper phonetic dictionary
WORD_TO_PHONEMES = {
    'the': ['ð', 'ə'],
    'i': ['aɪ'],
    'you': ['j', 'u'],
    'and': ['æ', 'n', 'd'],
    'it': ['ɪ', 't'],
    'a': ['ə'],
    's': ['s'],
    'to': ['t', 'u'],
    'of': ['ʌ', 'v'],
    'that': ['ð', 'æ', 't'],
    'n\'t': ['n', 't'],
    'in': ['ɪ', 'n'],
    'we': ['w', 'i'],
    'is': ['ɪ', 'z'],
    'do': ['d', 'u'],
    'they': ['ð', 'eɪ'],
    'er': ['ɜ', 'r'],
    'was': ['w', 'ʌ', 'z'],
    'yeah': ['j', 'æ'],
    'have': ['h', 'æ', 'v'],
    'what': ['w', 'ʌ', 't'],
    'he': ['h', 'i'],
    'but': ['b', 'ʌ', 't'],
    'for': ['f', 'ɔ', 'r'],
    'erm': ['ɜ', 'r', 'm'],
    'be': ['b', 'i'],
    'on': ['ɔ', 'n'],
    'this': ['ð', 'ɪ', 's'],
    'know': ['n', 'oʊ'],
    'well': ['w', 'ɛ', 'l'],
    'so': ['s', 'oʊ'],
    'oh': ['oʊ'],
    'got': ['g', 'ɔ', 't'],
    've': ['v'],
    'not': ['n', 'ɔ', 't'],
    'are': ['ɑ', 'r'],
    'if': ['ɪ', 'f'],
    'with': ['w', 'ɪ', 'θ'],
    'no': ['n', 'oʊ'],
    're': ['r'],
    'she': ['ʃ', 'i'],
    'at': ['æ', 't'],
    'there': ['ð', 'ɛər'],
    'think': ['θ', 'ɪ', 'ŋ', 'k'],
    'yes': ['j', 'ɛ', 's'],
    'just': ['dʒ', 'ʌ', 's', 't'],
}

def load_word_frequencies(filename):
    """Load word frequencies from the data file."""
    words_freq = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip header lines
    for line in lines[2:]:  # Skip first two lines (header)
        line = line.strip()
        if not line:
            continue
            
        parts = line.split('\t')
        if len(parts) >= 6:
            word = parts[0].strip()
            try:
                freq_spoken = int(parts[2]) if parts[2].strip() else 0
                words_freq.append((word, freq_spoken))
            except ValueError:
                continue
    
    return words_freq

def get_word_phonemes(word):
    """Get phonemes for a word. Uses simplified mapping or basic rules."""
    word_lower = word.lower()
    
    # Check if we have a direct mapping
    if word_lower in WORD_TO_PHONEMES:
        return set(WORD_TO_PHONEMES[word_lower])
    
    # Basic heuristic mapping for unknown words
    phonemes = set()
    
    # Simple letter-to-phoneme mapping (very basic)
    letter_to_phoneme = {
        'a': 'æ', 'e': 'ɛ', 'i': 'ɪ', 'o': 'ɔ', 'u': 'ʌ',
        'b': 'b', 'c': 'k', 'd': 'd', 'f': 'f', 'g': 'g',
        'h': 'h', 'j': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm',
        'n': 'n', 'p': 'p', 'q': 'k', 'r': 'r', 's': 's',
        't': 't', 'v': 'v', 'w': 'w', 'x': 'k', 'y': 'j', 'z': 'z'
    }
    
    for char in word_lower:
        if char in letter_to_phoneme:
            phonemes.add(letter_to_phoneme[char])
    
    return phonemes

def find_minimum_k_words(words_freq):
    """Find minimum k words that cover all 44 English phonemes."""
    covered_phonemes = set()
    selected_words = []
    phoneme_coverage = {}
    
    print(f"Target: Cover all {len(ENGLISH_PHONEMES)} English phonemes")
    print("English phonemes:", sorted(ENGLISH_PHONEMES))
    print()
    
    for i, (word, freq) in enumerate(words_freq):
        word_phonemes = get_word_phonemes(word)
        
        # Only consider words that add new phonemes
        new_phonemes = word_phonemes - covered_phonemes
        if new_phonemes or len(selected_words) == 0:
            selected_words.append((word, freq, word_phonemes))
            covered_phonemes.update(word_phonemes)
            phoneme_coverage[word] = word_phonemes
            
            print(f"Word {len(selected_words)}: '{word}' (freq: {freq})")
            print(f"  Phonemes: {sorted(word_phonemes)}")
            print(f"  New phonemes: {sorted(new_phonemes)}")
            print(f"  Total covered: {len(covered_phonemes)}/{len(ENGLISH_PHONEMES)}")
            print()
            
            # Check if we've covered all phonemes
            if len(covered_phonemes) >= len(ENGLISH_PHONEMES):
                break
    
    return selected_words, covered_phonemes, phoneme_coverage

def analyze_single_phoneme_words(selected_words, phoneme_coverage):
    """Identify words that are the only representation of certain phonemes."""
    phoneme_to_words = defaultdict(list)
    
    # Map each phoneme to words that contain it
    for word, phonemes in phoneme_coverage.items():
        for phoneme in phonemes:
            phoneme_to_words[phoneme].append(word)
    
    single_phoneme_words = {}
    for phoneme, words in phoneme_to_words.items():
        if len(words) == 1:
            single_phoneme_words[words[0]] = phoneme
    
    return single_phoneme_words

def main():
    filename = 'materials/2_2_spokenvwritten.txt'
    
    print("Loading word frequencies...")
    words_freq = load_word_frequencies(filename)
    print(f"Loaded {len(words_freq)} words")
    print()
    
    # Sort by frequency (descending)
    words_freq.sort(key=lambda x: x[1], reverse=True)
    
    print("Finding minimum k words to cover all phonemes...")
    selected_words, covered_phonemes, phoneme_coverage = find_minimum_k_words(words_freq)
    
    print("="*60)
    print("RESULTS")
    print("="*60)
    
    print(f"Minimum k = {len(selected_words)} words needed to cover all phonemes")
    print(f"Covered phonemes: {len(covered_phonemes)}/{len(ENGLISH_PHONEMES)}")
    
    if len(covered_phonemes) < len(ENGLISH_PHONEMES):
        missing = ENGLISH_PHONEMES - covered_phonemes
        print(f"Missing phonemes: {sorted(missing)}")
    
    print()
    print("TOP K WORDS (no duplicates):")
    print("-" * 40)
    
    # Remove duplicates while preserving order
    seen_words = set()
    unique_selected_words = []
    for word, freq, phonemes in selected_words:
        if word not in seen_words:
            seen_words.add(word)
            unique_selected_words.append((word, freq, phonemes))
    
    # Analyze single phoneme representations
    single_phoneme_words = analyze_single_phoneme_words(unique_selected_words, phoneme_coverage)
    
    for i, (word, freq, phonemes) in enumerate(unique_selected_words, 1):
        marker = ""
        if word in single_phoneme_words:
            marker = f" [UNIQUE for phoneme: {single_phoneme_words[word]}]"
        
        print(f"{i:2d}. {word} (frequency: {freq}){marker}")
        print(f"    Phonemes: {sorted(phonemes)}")
        print()

if __name__ == "__main__":
    main()
