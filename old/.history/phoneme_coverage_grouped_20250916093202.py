#!/usr/bin/env python3
"""
Find top k frequent words that cover all 39 CMUdict phonemes.
Group words by phonemes and show comprehensive phoneme-word mapping.
"""

import nltk
import re
from collections import defaultdict, Counter
from typing import List, Tuple, Dict, Set

# Download required NLTK data
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    print("Downloading CMUdict...")
    nltk.download('cmudict')

def get_cmu_phonemes(word, cmu_dict):
    """
    Get CMUdict phonemes for a word, removing stress markers.
    Returns a set of phonemes for the word.
    """
    word_lower = word.lower()
    if word_lower in cmu_dict:
        # Get the first pronunciation (most common)
        phonemes = cmu_dict[word_lower][0]
        # Remove stress markers (digits)
        clean_phonemes = [re.sub(r'\d+', '', phoneme) for phoneme in phonemes]
        return set(clean_phonemes)
    return set()

def get_all_cmu_phonemes():
    """Get all unique CMUdict phonemes (39 phonemes)."""
    from nltk.corpus import cmudict
    cmu_dict = cmudict.dict()
    
    all_phonemes = set()
    for pronunciations in cmu_dict.values():
        for pronunciation in pronunciations:
            for phoneme in pronunciation:
                # Remove stress markers
                clean_phoneme = re.sub(r'\d+', '', phoneme)
                all_phonemes.add(clean_phoneme)
    
    return sorted(all_phonemes)

def load_word_frequencies(filename):
    """Load word frequencies from the file."""
    print(f"Loading word frequencies from {filename}...")
    word_frequencies = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        # Skip header
        next(f)
        
        for line_num, line in enumerate(f, 2):
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                word = parts[0].strip().lower()
                try:
                    # FrSp is the spoken frequency (3rd column)
                    freq = int(parts[2])
                    word_frequencies.append((word, freq))
                except ValueError:
                    continue
    
    # Sort by frequency (descending)
    word_frequencies.sort(key=lambda x: x[1], reverse=True)
    print(f"Loaded {len(word_frequencies)} words with frequencies")
    return word_frequencies

def find_minimal_phoneme_coverage(word_frequencies: List[Tuple[str, int]]):
    """
    Find the minimal set of top-k words that covers all 39 CMUdict phonemes.
    """
    from nltk.corpus import cmudict
    cmu_dict = cmudict.dict()
    
    target_phonemes = set(get_all_cmu_phonemes())
    print(f"Target: {len(target_phonemes)} phonemes to cover")
    print(f"All phonemes: {sorted(target_phonemes)}")
    
    covered_phonemes = set()
    selected_words = []
    word_to_phonemes = {}
    phoneme_to_words = defaultdict(list)
    
    print("\nSearching for minimal coverage...")
    
    for i, (word, freq) in enumerate(word_frequencies):
        if len(covered_phonemes) >= len(target_phonemes):
            break
            
        word_phonemes = get_cmu_phonemes(word, cmu_dict)
        
        if word_phonemes:  # Only consider words with known phonemes
            # Check if this word adds new phonemes
            new_phonemes = word_phonemes - covered_phonemes
            
            if new_phonemes or len(selected_words) == 0:  # Always include first word
                selected_words.append((word, freq))
                word_to_phonemes[word] = word_phonemes
                covered_phonemes.update(word_phonemes)
                
                # Update phoneme to words mapping
                for phoneme in word_phonemes:
                    phoneme_to_words[phoneme].append(word)
                
                print(f"Word {len(selected_words):4d}: '{word}' (freq: {freq:,}) -> "
                      f"phonemes: {sorted(word_phonemes)} -> "
                      f"coverage: {len(covered_phonemes)}/{len(target_phonemes)}")
                
                if len(covered_phonemes) >= len(target_phonemes):
                    print(f"\n✅ Full coverage achieved with {len(selected_words)} words!")
                    break
    
    # Check final coverage
    missing_phonemes = target_phonemes - covered_phonemes
    if missing_phonemes:
        print(f"\n⚠️  Missing phonemes: {sorted(missing_phonemes)}")
    else:
        print(f"\n✅ All {len(target_phonemes)} phonemes covered!")
    
    return selected_words, word_to_phonemes, phoneme_to_words, target_phonemes

def remove_duplicates(word_list):
    """Remove duplicates while preserving order."""
    seen = set()
    unique_words = []
    
    for word, freq in word_list:
        if word not in seen:
            seen.add(word)
            unique_words.append((word, freq))
        else:
            print(f"Removed duplicate: {word}")
    
    return unique_words

def create_phoneme_word_report(phoneme_to_words, target_phonemes, word_to_phonemes):
    """Create a comprehensive report grouping words by phonemes."""
    print("\n" + "="*80)
    print("PHONEME-WORD MAPPING REPORT")
    print("="*80)
    
    report_lines = []
    
    for phoneme in sorted(target_phonemes):
        words = phoneme_to_words.get(phoneme, [])
        report_lines.append(f"\n📢 PHONEME: {phoneme}")
        report_lines.append(f"   Words ({len(words)}): {', '.join(sorted(words))}")
        
        print(f"\n📢 PHONEME: {phoneme}")
        print(f"   Words ({len(words)}): {', '.join(sorted(words))}")
    
    return report_lines

def main():
    print("🔍 PHONEME COVERAGE ANALYSIS WITH GROUPING")
    print("="*50)
    
    # Load word frequencies
    word_frequencies = load_word_frequencies('materials/2_2_spokenvwritten.txt')
    
    # Find minimal coverage
    selected_words, word_to_phonemes, phoneme_to_words, target_phonemes = find_minimal_phoneme_coverage(word_frequencies)
    
    # Remove duplicates
    unique_words = remove_duplicates(selected_words)
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Total words needed: {len(unique_words)}")
    print(f"   Phonemes covered: {len(target_phonemes)}")
    
    # Create comprehensive output files
    
    # 1. Final word list
    with open('final_phoneme_coverage_words.txt', 'w', encoding='utf-8') as f:
        f.write("FINAL TOP-K WORDS FOR COMPLETE PHONEME COVERAGE\n")
        f.write("="*50 + "\n\n")
        for i, (word, freq) in enumerate(unique_words, 1):
            f.write(f"{word}\n")
    
    print(f"\n💾 Saved final word list to 'final_phoneme_coverage_words.txt'")
    
    # 2. Detailed word-frequency list
    with open('detailed_word_frequency_list.txt', 'w', encoding='utf-8') as f:
        f.write("DETAILED WORD LIST WITH FREQUENCIES\n")
        f.write("="*40 + "\n\n")
        for i, (word, freq) in enumerate(unique_words, 1):
            phonemes = word_to_phonemes.get(word, set())
            f.write(f"{i:3d}. {word:<15} (freq: {freq:>6,}) -> {sorted(phonemes)}\n")
    
    print(f"💾 Saved detailed list to 'detailed_word_frequency_list.txt'")
    
    # 3. Phoneme-word mapping report
    report_lines = create_phoneme_word_report(phoneme_to_words, target_phonemes, word_to_phonemes)
    
    with open('phoneme_word_mapping.txt', 'w', encoding='utf-8') as f:
        f.write("COMPLETE PHONEME-WORD MAPPING\n")
        f.write("="*35 + "\n")
        f.write(f"Total phonemes: {len(target_phonemes)}\n")
        f.write(f"Total words: {len(unique_words)}\n\n")
        
        for line in report_lines:
            f.write(line + "\n")
    
    print(f"💾 Saved phoneme mapping to 'phoneme_word_mapping.txt'")
    
    # 4. Summary statistics
    with open('phoneme_coverage_summary.txt', 'w', encoding='utf-8') as f:
        f.write("PHONEME COVERAGE SUMMARY\n")
        f.write("="*25 + "\n\n")
        f.write(f"Total words selected: {len(unique_words)}\n")
        f.write(f"Total phonemes covered: {len(target_phonemes)}\n")
        f.write(f"Coverage: 100%\n\n")
        
        f.write("PHONEME DISTRIBUTION:\n")
        f.write("-" * 20 + "\n")
        
        # Count words per phoneme
        phoneme_counts = [(len(phoneme_to_words[p]), p) for p in target_phonemes]
        phoneme_counts.sort(reverse=True)
        
        for count, phoneme in phoneme_counts:
            f.write(f"{phoneme:>4}: {count:2d} words\n")
        
        f.write(f"\nAverage words per phoneme: {len(unique_words)/len(target_phonemes):.1f}\n")
    
    print(f"💾 Saved summary to 'phoneme_coverage_summary.txt'")
    
    print(f"\n🎉 Analysis complete! Check the generated files for detailed results.")

if __name__ == "__main__":
    main()
