#!/usr/bin/env python3
"""
Analyze phoneme frequency distribution in the final word list.
"""

import subprocess
import sys
from collections import defaultdict, Counter

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

def get_cmu_phonemes(word, cmu_dict):
    """Get CMUdict phonemes for a word, removing stress markers."""
    word_lower = word.lower()
    if word_lower in cmu_dict:
        # Take the first pronunciation and remove stress markers
        phonemes = cmu_dict[word_lower][0]
        return set([p.rstrip('012') for p in phonemes])
    return set()

def main():
    # Load the final word list
    with open('final_word_list.txt', 'r') as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"Analyzing {len(words)} words...")
    
    # Load CMUdict
    cmu_dict = cmudict.dict()
    
    # Count phoneme occurrences
    phoneme_count = Counter()
    phoneme_to_words = defaultdict(list)
    
    for word in words:
        phonemes = get_cmu_phonemes(word, cmu_dict)
        for phoneme in phonemes:
            phoneme_count[phoneme] += 1
            phoneme_to_words[phoneme].append(word)
    
    print("\n" + "="*60)
    print("PHONEME FREQUENCY ANALYSIS")
    print("="*60)
    
    # Sort phonemes by frequency (ascending)
    sorted_phonemes = sorted(phoneme_count.items(), key=lambda x: x[1])
    
    print(f"\nTotal unique phonemes found: {len(sorted_phonemes)}")
    print("\nPhoneme frequency distribution (phoneme: count):")
    print("-" * 50)
    
    for phoneme, count in sorted_phonemes:
        print(f"{phoneme:>4}: {count:>4} words")
    
    print("\n" + "="*60)
    print("DETAILED PHONEME-TO-WORDS MAPPING")
    print("="*60)
    
    for phoneme, count in sorted_phonemes:
        words_list = phoneme_to_words[phoneme]
        print(f"\n{phoneme} ({count} words):")
        # Show first 10 words, then indicate if there are more
        if len(words_list) <= 10:
            print(f"  {', '.join(words_list)}")
        else:
            print(f"  {', '.join(words_list[:10])}, ... and {len(words_list)-10} more")
    
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    counts = list(phoneme_count.values())
    print(f"Minimum phoneme frequency: {min(counts)}")
    print(f"Maximum phoneme frequency: {max(counts)}")
    print(f"Average phoneme frequency: {sum(counts)/len(counts):.1f}")
    print(f"Median phoneme frequency: {sorted(counts)[len(counts)//2]}")
    
    # Show phonemes with minimum frequency (most restrictive)
    min_freq = min(counts)
    min_phonemes = [p for p, c in phoneme_count.items() if c == min_freq]
    print(f"\nMost restrictive phonemes (frequency = {min_freq}):")
    for phoneme in min_phonemes:
        words_list = phoneme_to_words[phoneme]
        print(f"  {phoneme}: {', '.join(words_list)}")

if __name__ == "__main__":
    main()



