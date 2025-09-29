#!/usr/bin/env python3
"""
Save the original order word-phoneme output to a file
将按原始顺序的词汇-音素输出保存到文件
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

def save_original_order_output():
    """Save the original order word-phoneme output to file."""
    
    # Read final word list in original order
    with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/final_word_list.txt', 'r') as f:
        words = [line.strip() for line in f if line.strip()]
    
    print(f"Processing {len(words)} words...")
    
    # Prepare output content
    output_lines = []
    output_lines.append("=" * 80)
    output_lines.append("FINAL WORD LIST - 按原始顺序输出每个词和对应音素")
    output_lines.append("ORIGINAL ORDER WORD-TO-PHONEME MAPPING")
    output_lines.append("=" * 80)
    output_lines.append(f"Total words: {len(words)}")
    output_lines.append("")
    
    mapped_count = 0
    failed_count = 0
    
    for i, word in enumerate(words, 1):
        phonemes = get_word_phonemes(word)
        if phonemes:
            phonemes_str = " ".join(phonemes)
            output_lines.append(f"{i:4d}. {word:20s} -> /{phonemes_str}/")
            mapped_count += 1
        else:
            output_lines.append(f"{i:4d}. {word:20s} -> [NOT FOUND]")
            failed_count += 1
    
    output_lines.append("")
    output_lines.append("=" * 80)
    output_lines.append("SUMMARY:")
    output_lines.append(f"Total words: {len(words)}")
    output_lines.append(f"Successfully mapped: {mapped_count}")
    output_lines.append(f"Failed to map: {failed_count}")
    output_lines.append(f"Success rate: {mapped_count/len(words)*100:.1f}%")
    
    # Save to file
    output_filename = '/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/final_word_list_original_order_phonemes.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\nOutput saved to: {output_filename}")
    print(f"Total lines written: {len(output_lines)}")
    print(f"Successfully mapped: {mapped_count}/{len(words)} ({mapped_count/len(words)*100:.1f}%)")
    
    return output_filename, mapped_count, failed_count

if __name__ == "__main__":
    filename, mapped, failed = save_original_order_output()
    print(f"\n✅ File saved successfully: {filename}")
    print(f"📊 Mapping results: {mapped} success, {failed} failed")


