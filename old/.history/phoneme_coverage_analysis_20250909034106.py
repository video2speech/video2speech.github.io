#!/usr/bin/env python3
"""
Phoneme Coverage Analysis Script

This script finds the minimum number of top frequent words needed to cover
all 44 English phonemes from the materials/2_2_spokenvwritten.txt file.
"""

import re
from collections import Counter, defaultdict
from typing import List, Set, Tuple, Dict
import nltk
from nltk.corpus import cmudict

# Download required NLTK data
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    nltk.download('cmudict')

def load_cmu_dict():
    """Load CMU Pronouncing Dictionary"""
    return cmudict.dict()

def extract_phonemes_from_arpabet(arpabet_list: List[str]) -> Set[str]:
    """Extract phonemes from CMU dict ARPABET representation"""
    phonemes = set()
    for pronunciation in arpabet_list:
        for phone in pronunciation:
            # Remove stress markers (0, 1, 2) from vowels
            clean_phone = re.sub(r'[0-2]', '', phone)
            phonemes.add(clean_phone)
    return phonemes

def get_english_phonemes() -> Set[str]:
    """Get the standard set of 44 English phonemes in ARPABET format"""
    # Standard English phonemes in ARPABET notation (44 phonemes)
    consonants = {
        'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 
        'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
    }  # 24 consonants
    
    vowels = {
        'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 
        'OW', 'OY', 'UH', 'UW'
    }  # 15 vowels
    
    # Additional phonemes - 5 more to make 44 total
    additional = {'AX', 'IX', 'UX', 'Q', 'X'}  # schwa variants and others
    
    return consonants | vowels | additional

def parse_frequency_file(filename: str) -> List[Tuple[str, int]]:
    """Parse the frequency file and return sorted list of (word, frequency) tuples"""
    words_freq = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip header lines
    for line in lines[2:]:  # Skip first two lines (header)
        line = line.strip()
        if not line:
            continue
            
        parts = line.split('\t')
        if len(parts) >= 3:
            word = parts[0].strip().lower()
            try:
                # Use spoken frequency (FrSp) - column index 2
                freq = int(parts[2])
                words_freq.append((word, freq))
            except ValueError:
                continue
    
    # Sort by frequency (descending)
    words_freq.sort(key=lambda x: x[1], reverse=True)
    return words_freq

def find_minimal_phoneme_coverage(words_freq: List[Tuple[str, int]], 
                                cmu_dict: Dict[str, List[List[str]]], 
                                target_phonemes: Set[str]) -> Tuple[int, List[str], Dict[str, Set[str]]]:
    """
    Find minimum k such that top k words cover all target phonemes
    
    Returns:
        - k: minimum number of words needed
        - words: list of the k words
        - word_phonemes: mapping of word to its phonemes
    """
    covered_phonemes = set()
    selected_words = []
    word_phonemes = {}
    
    print(f"Target: {len(target_phonemes)} phonemes")
    print(f"Available words: {len(words_freq)}")
    
    for i, (word, freq) in enumerate(words_freq):
        # Clean word (remove punctuation, handle contractions)
        clean_word = re.sub(r"[^\w']", "", word)
        
        if clean_word in cmu_dict:
            # Get phonemes for this word
            pronunciations = cmu_dict[clean_word]
            word_phoneme_set = extract_phonemes_from_arpabet(pronunciations)
            
            # Add to selected words
            selected_words.append(word)
            word_phonemes[word] = word_phoneme_set
            
            # Update covered phonemes
            covered_phonemes.update(word_phoneme_set)
            
            if i % 100 == 0:
                print(f"Processed {i+1} words, covered {len(covered_phonemes)}/{len(target_phonemes)} phonemes")
            
            # Check if we've covered all phonemes
            if covered_phonemes >= target_phonemes:
                print(f"All phonemes covered with {len(selected_words)} words!")
                return len(selected_words), selected_words, word_phonemes
    
    print(f"Could not cover all phonemes. Covered {len(covered_phonemes)}/{len(target_phonemes)}")
    print(f"Missing phonemes: {target_phonemes - covered_phonemes}")
    return len(selected_words), selected_words, word_phonemes

def find_unique_phoneme_words(word_phonemes: Dict[str, Set[str]]) -> Dict[str, str]:
    """Find words that are the only representatives of certain phonemes"""
    phoneme_to_words = defaultdict(list)
    
    # Map each phoneme to words that contain it
    for word, phonemes in word_phonemes.items():
        for phoneme in phonemes:
            phoneme_to_words[phoneme].append(word)
    
    # Find phonemes with only one word
    unique_phoneme_words = {}
    for phoneme, words in phoneme_to_words.items():
        if len(words) == 1:
            unique_phoneme_words[phoneme] = words[0]
    
    return unique_phoneme_words

def main():
    print("=== Phoneme Coverage Analysis ===\n")
    
    # Load CMU dictionary
    print("Loading CMU Pronouncing Dictionary...")
    cmu_dict = load_cmu_dict()
    
    # Get target phonemes
    target_phonemes = get_english_phonemes()
    print(f"Target phonemes ({len(target_phonemes)}): {sorted(target_phonemes)}\n")
    
    # Parse frequency file
    print("Parsing frequency file...")
    words_freq = parse_frequency_file('materials/2_2_spokenvwritten.txt')
    print(f"Loaded {len(words_freq)} words with frequencies\n")
    
    # Find minimal coverage
    print("Finding minimal phoneme coverage...")
    k, selected_words, word_phonemes = find_minimal_phoneme_coverage(
        words_freq, cmu_dict, target_phonemes
    )
    
    # Remove duplicates while preserving order
    unique_words = []
    seen = set()
    for word in selected_words:
        if word not in seen:
            unique_words.append(word)
            seen.add(word)
    
    print(f"\n=== RESULTS ===")
    print(f"Minimum k = {len(unique_words)}")
    print(f"Top {len(unique_words)} words needed to cover all {len(target_phonemes)} English phonemes:\n")
    
    # Find unique phoneme representatives
    unique_phoneme_words = find_unique_phoneme_words(word_phonemes)
    
    # Output results
    for i, word in enumerate(unique_words, 1):
        phonemes = word_phonemes.get(word, set())
        phoneme_str = ', '.join(sorted(phonemes))
        
        # Check if this word is unique for any phoneme
        unique_phonemes = [p for p, w in unique_phoneme_words.items() if w == word]
        unique_marker = ""
        if unique_phonemes:
            unique_marker = f" [UNIQUE for: {', '.join(sorted(unique_phonemes))}]"
        
        print(f"{i:3d}. {word:<15} -> {phoneme_str}{unique_marker}")
    
    # Summary
    all_covered = set()
    for phonemes in word_phonemes.values():
        all_covered.update(phonemes)
    
    print(f"\nSummary:")
    print(f"- Words selected: {len(unique_words)}")
    print(f"- Phonemes covered: {len(all_covered)}/{len(target_phonemes)}")
    print(f"- Unique phoneme words: {len(unique_phoneme_words)}")
    
    if len(all_covered) < len(target_phonemes):
        missing = target_phonemes - all_covered
        print(f"- Missing phonemes: {sorted(missing)}")

if __name__ == "__main__":
    main()
