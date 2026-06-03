#!/usr/bin/env python3
"""
Find the minimum number of top frequent words that cover all 39 CMUdict phonemes.
"""

import re
from collections import Counter, defaultdict
from typing import List, Set, Tuple, Dict
import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import nltk
    from nltk.corpus import cmudict
except ImportError:
    print("Installing required packages...")
    install_package("nltk")
    import nltk
    from nltk.corpus import cmudict

# Download CMUdict if not already present
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    print("Downloading CMUdict...")
    nltk.download('cmudict')

def load_word_frequencies(file_path: str) -> List[Tuple[str, int]]:
    """
    Load word frequencies from the materials file.
    Returns list of (word, frequency) tuples sorted by frequency descending.
    """
    words_freq = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip header lines
    for line in lines[2:]:  # Skip first two lines (header)
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) >= 3:
            word = parts[0].strip()
            try:
                # Use spoken frequency (FrSp) - column 2
                freq = int(parts[2])
                words_freq.append((word, freq))
            except (ValueError, IndexError):
                continue
    
    # Sort by frequency descending
    words_freq.sort(key=lambda x: x[1], reverse=True)
    return words_freq

def get_cmu_phonemes(word: str, cmu_dict) -> Set[str]:
    """
    Get CMUdict phonemes for a word.
    Returns set of phonemes (without stress markers).
    """
    phonemes = set()
    word_lower = word.lower()
    
    if word_lower in cmu_dict:
        # Get all pronunciations for this word
        pronunciations = cmu_dict[word_lower]
        for pronunciation in pronunciations:
            # Remove stress markers (digits) from phonemes
            clean_phonemes = [re.sub(r'\d', '', p) for p in pronunciation]
            phonemes.update(clean_phonemes)
    
    return phonemes

def get_all_cmu_phonemes() -> Set[str]:
    """
    Get all unique phonemes from CMUdict (without stress markers).
    """
    cmu_dict = cmudict.dict()
    all_phonemes = set()
    
    for pronunciations in cmu_dict.values():
        for pronunciation in pronunciations:
            clean_phonemes = [re.sub(r'\d', '', p) for p in pronunciation]
            all_phonemes.update(clean_phonemes)
    
    return all_phonemes

def find_minimal_coverage(word_frequencies: List[Tuple[str, int]]) -> Tuple[int, List[str], Dict[str, Set[str]]]:
    """
    Find minimum k such that top k words cover all CMUdict phonemes.
    Returns (k, top_k_words, word_to_phonemes_map).
    """
    cmu_dict = cmudict.dict()
    all_phonemes = get_all_cmu_phonemes()
    
    print(f"Total CMUdict phonemes to cover: {len(all_phonemes)}")
    print(f"All phonemes: {sorted(all_phonemes)}")
    print()
    
    covered_phonemes = set()
    word_to_phonemes = {}
    top_k_words = []
    
    for i, (word, freq) in enumerate(word_frequencies):
        word_phonemes = get_cmu_phonemes(word, cmu_dict)
        
        if word_phonemes:  # Only include words that have phoneme representation
            top_k_words.append(word)
            word_to_phonemes[word] = word_phonemes
            covered_phonemes.update(word_phonemes)
            
            print(f"k={len(top_k_words)}: '{word}' (freq={freq}) -> phonemes: {sorted(word_phonemes)}")
            print(f"   Covered so far: {len(covered_phonemes)}/{len(all_phonemes)} phonemes")
            
            if covered_phonemes == all_phonemes:
                print(f"\n✓ All {len(all_phonemes)} phonemes covered with k={len(top_k_words)} words!")
                break
            
            missing = all_phonemes - covered_phonemes
            print(f"   Missing: {sorted(missing)}")
            print()
    
    return len(top_k_words), top_k_words, word_to_phonemes

def analyze_single_phoneme_words(word_to_phonemes: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """
    Find words that are the sole representation of certain phonemes.
    """
    phoneme_to_words = defaultdict(list)
    
    # Build reverse mapping
    for word, phonemes in word_to_phonemes.items():
        for phoneme in phonemes:
            phoneme_to_words[phoneme].append(word)
    
    # Find phonemes with only one word
    single_phoneme_words = {}
    for phoneme, words in phoneme_to_words.items():
        if len(words) == 1:
            single_phoneme_words[phoneme] = words
    
    return single_phoneme_words

def main():
    file_path = "materials/2_2_spokenvwritten.txt"
    
    print("Loading word frequencies...")
    word_frequencies = load_word_frequencies(file_path)
    print(f"Loaded {len(word_frequencies)} words with frequencies")
    print()
    
    print("Finding minimal coverage...")
    k, top_k_words, word_to_phonemes = find_minimal_coverage(word_frequencies)
    
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    print(f"\nMinimum k = {k}")
    print(f"Top {k} words that cover all CMUdict phonemes:")
    print()
    
    # Remove duplicates while preserving order
    seen = set()
    unique_words = []
    for word in top_k_words:
        if word not in seen:
            seen.add(word)
            unique_words.append(word)
    
    print("Final word list (duplicates removed):")
    for i, word in enumerate(unique_words, 1):
        phonemes = word_to_phonemes[word]
        print(f"{i:2d}. {word:<15} -> {sorted(phonemes)}")
    
    print(f"\nTotal unique words: {len(unique_words)}")
    
    # Analyze single phoneme representations
    print("\n" + "-"*40)
    print("SINGLE PHONEME REPRESENTATIONS")
    print("-"*40)
    
    single_phoneme_words = analyze_single_phoneme_words(word_to_phonemes)
    
    if single_phoneme_words:
        print("Words that are the only representation of certain phonemes:")
        for phoneme, words in single_phoneme_words.items():
            word = words[0]
            print(f"  {word:<15} -> ONLY word with phoneme '{phoneme}'")
    else:
        print("No words are sole representations of phonemes in this set.")
    
    # Show coverage statistics
    all_phonemes = get_all_cmu_phonemes()
    covered_phonemes = set()
    for phonemes in word_to_phonemes.values():
        covered_phonemes.update(phonemes)
    
    print(f"\nCoverage verification:")
    print(f"  Total CMUdict phonemes: {len(all_phonemes)}")
    print(f"  Covered phonemes: {len(covered_phonemes)}")
    print(f"  Coverage: {len(covered_phonemes)/len(all_phonemes)*100:.1f}%")
    
    if covered_phonemes != all_phonemes:
        missing = all_phonemes - covered_phonemes
        print(f"  Missing phonemes: {sorted(missing)}")

if __name__ == "__main__":
    main()
