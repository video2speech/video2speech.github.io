#!/usr/bin/env python3
"""
Output words from final_word_list.txt in original order with their phonemes
按照原始顺序输出每个词和对应的音素
"""

import nltk
from collections import defaultdict
import re

# Download required NLTK data
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    nltk.download('cmudict')

from nltk.corpus import cmudict

# Get CMU Pronouncing Dictionary
cmu_dict = cmudict.dict()

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
    
    return None  # Return None if not found

def output_words_with_phonemes():
    """Output each word with its phonemes in original order."""
    
    # Read final word list in original order
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/final_word_list.txt', 'r') as f:
        words = [line.strip() for line in f if line.strip()]
    
    print("=" * 80)
    print("FINAL WORD LIST - 按原始顺序输出每个词和对应音素")
    print("ORIGINAL ORDER WORD-TO-PHONEME MAPPING")
    print("=" * 80)
    print(f"Total words: {len(words)}")
    print("")
    
    mapped_count = 0
    failed_count = 0
    
    for i, word in enumerate(words, 1):
        phonemes = get_word_phonemes(word)
        if phonemes:
            phonemes_str = " ".join(phonemes)
            print(f"{i:4d}. {word:20s} -> /{phonemes_str}/")
            mapped_count += 1
        else:
            print(f"{i:4d}. {word:20s} -> [NOT FOUND]")
            failed_count += 1
    
    print("")
    print("=" * 80)
    print("SUMMARY:")
    print(f"Total words: {len(words)}")
    print(f"Successfully mapped: {mapped_count}")
    print(f"Failed to map: {failed_count}")
    print(f"Success rate: {mapped_count/len(words)*100:.1f}%")
    
    return words, mapped_count, failed_count

if __name__ == "__main__":
    words, mapped, failed = output_words_with_phonemes()


