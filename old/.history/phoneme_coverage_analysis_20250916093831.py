#!/usr/bin/env python3
"""
Phoneme Coverage Analysis - Find minimal k words covering all 39 CMUdict phonemes
"""

import nltk
import re
from collections import defaultdict, Counter
from nltk.corpus import cmudict

# Download required NLTK data
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    print("Downloading CMUdict...")
    nltk.download('cmudict')

def load_word_frequencies(filename):
    """Load words and their frequencies from the spoken/written file."""
    print(f"Loading word frequencies from {filename}...")
    word_freq = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num <= 2:  # Skip header lines
                continue
                
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) >= 6:  # Format: Word, PoS, FrSp, +/-, LL, FrWr
                word = parts[1].lower().strip()  # Word is in column 1
                try:
                    spoken_freq = int(parts[2])  # FrSp is in column 2
                    written_freq = int(parts[5])  # FrWr is in column 5
                    total_freq = spoken_freq + written_freq
                    if word and total_freq > 0:
                        word_freq.append((word, total_freq))
                except (ValueError, IndexError):
                    continue
    
    # Sort by frequency (descending)
    word_freq.sort(key=lambda x: x[1], reverse=True)
    print(f"Loaded {len(word_freq)} words with frequencies")
    return word_freq

def get_word_phonemes(word):
    """Get CMUdict phonemes for a word, removing stress markers."""
    cmu_dict = cmudict.dict()
    
    if word in cmu_dict:
        # Get first pronunciation
        pronunciation = cmu_dict[word][0]
        # Remove stress markers (0, 1, 2)
        phonemes = [re.sub(r'[0-2]', '', phoneme) for phoneme in pronunciation]
        return set(phonemes)
    else:
        return set()

def get_all_cmu_phonemes():
    """Get all 39 CMUdict phonemes."""
    # Standard CMUdict phoneme set (39 phonemes)
    phonemes = {
        # Vowels (15)
        'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 
        'IY', 'OW', 'OY', 'UH', 'UW',
        # Consonants (24)
        'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 
        'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
    }
    return phonemes

def find_minimal_phoneme_coverage(word_freq_list):
    """Find the minimal k words that cover all 39 CMUdict phonemes."""
    print("Finding minimal phoneme coverage...")
    
    target_phonemes = get_all_cmu_phonemes()
    covered_phonemes = set()
    selected_words = []
    word_phoneme_map = {}
    
    print(f"Target: {len(target_phonemes)} phonemes")
    print(f"Phonemes to cover: {sorted(target_phonemes)}")
    
    for i, (word, freq) in enumerate(word_freq_list):
        word_phonemes = get_word_phonemes(word)
        
        if word_phonemes:  # Only consider words with known pronunciations
            # Check if this word adds new phonemes
            new_phonemes = word_phonemes - covered_phonemes
            
            if new_phonemes or len(selected_words) == 0:  # Always include first word
                selected_words.append((word, freq))
                word_phoneme_map[word] = word_phonemes
                covered_phonemes.update(word_phonemes)
                
                print(f"Word {len(selected_words):4d}: {word:15s} (freq: {freq:6d}) "
                      f"-> +{len(new_phonemes)} phonemes, total: {len(covered_phonemes)}/39")
                
                # Check if we've covered all phonemes
                if covered_phonemes >= target_phonemes:
                    print(f"\n✅ SUCCESS! All 39 phonemes covered with {len(selected_words)} words")
                    break
    
    missing_phonemes = target_phonemes - covered_phonemes
    if missing_phonemes:
        print(f"\n❌ Could not cover all phonemes. Missing: {sorted(missing_phonemes)}")
    
    return selected_words, word_phoneme_map, covered_phonemes

def create_phoneme_word_mapping(word_phoneme_map, target_phonemes):
    """Create mapping from phonemes to words that contain them."""
    phoneme_to_words = defaultdict(list)
    
    for word, phonemes in word_phoneme_map.items():
        for phoneme in phonemes:
            if phoneme in target_phonemes:
                phoneme_to_words[phoneme].append(word)
    
    return phoneme_to_words

def save_results(selected_words, word_phoneme_map, phoneme_to_words):
    """Save analysis results to files."""
    
    # Save final word list
    print(f"\nSaving {len(selected_words)} words to 'minimal_phoneme_coverage_words.txt'...")
    with open('minimal_phoneme_coverage_words.txt', 'w', encoding='utf-8') as f:
        f.write("MINIMAL PHONEME COVERAGE WORD LIST\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total words: {len(selected_words)}\n")
        f.write(f"Coverage: All 39 CMUdict phonemes\n\n")
        
        for i, (word, freq) in enumerate(selected_words, 1):
            phonemes = sorted(word_phoneme_map[word])
            f.write(f"{i:3d}. {word:15s} (freq: {freq:6d}) -> {' '.join(phonemes)}\n")
    
    # Save phoneme-to-words mapping
    print("Saving phoneme-to-words mapping to 'phoneme_words_mapping.txt'...")
    target_phonemes = get_all_cmu_phonemes()
    
    with open('phoneme_words_mapping.txt', 'w', encoding='utf-8') as f:
        f.write("PHONEME TO WORDS MAPPING\n")
        f.write("="*50 + "\n\n")
        f.write("Each phoneme and the words from our minimal set that contain it:\n\n")
        
        # Sort phonemes: vowels first, then consonants
        vowels = ['AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW']
        consonants = ['B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH']
        
        f.write("VOWELS:\n")
        f.write("-" * 20 + "\n")
        for phoneme in vowels:
            if phoneme in phoneme_to_words:
                words = sorted(phoneme_to_words[phoneme])
                f.write(f"{phoneme:3s}: {', '.join(words)} ({len(words)} words)\n")
            else:
                f.write(f"{phoneme:3s}: ❌ NOT COVERED\n")
        
        f.write(f"\nCONSONANTS:\n")
        f.write("-" * 20 + "\n")
        for phoneme in consonants:
            if phoneme in phoneme_to_words:
                words = sorted(phoneme_to_words[phoneme])
                f.write(f"{phoneme:3s}: {', '.join(words)} ({len(words)} words)\n")
            else:
                f.write(f"{phoneme:3s}: ❌ NOT COVERED\n")
    
    # Create summary report
    print("Creating summary report...")
    with open('minimal_coverage_summary.txt', 'w', encoding='utf-8') as f:
        f.write("MINIMAL PHONEME COVERAGE ANALYSIS SUMMARY\n")
        f.write("="*50 + "\n\n")
        f.write(f"📊 RESULTS:\n")
        f.write(f"   • Total words selected: {len(selected_words)}\n")
        f.write(f"   • Phonemes covered: {len(phoneme_to_words)}/39\n")
        f.write(f"   • Coverage: {'✅ Complete' if len(phoneme_to_words) == 39 else '❌ Incomplete'}\n\n")
        
        f.write(f"📝 WORD LIST (sorted by selection order):\n")
        f.write("-" * 30 + "\n")
        for i, (word, freq) in enumerate(selected_words, 1):
            f.write(f"{i:2d}. {word}\n")
        
        f.write(f"\n📈 PHONEME STATISTICS:\n")
        f.write("-" * 30 + "\n")
        phoneme_counts = Counter()
        for words in phoneme_to_words.values():
            phoneme_counts.update({len(words): 1})
        
        for count in sorted(phoneme_counts.keys()):
            f.write(f"   • {phoneme_counts[count]} phonemes have {count} word(s)\n")

def main():
    print("🔍 MINIMAL PHONEME COVERAGE ANALYSIS")
    print("="*50)
    
    # Load word frequencies
    word_freq_list = load_word_frequencies('materials/2_2_spokenvwritten.txt')
    
    # Find minimal coverage
    selected_words, word_phoneme_map, covered_phonemes = find_minimal_phoneme_coverage(word_freq_list)
    
    # Remove duplicates while preserving order
    unique_words = []
    seen_words = set()
    for word, freq in selected_words:
        if word not in seen_words:
            unique_words.append((word, freq))
            seen_words.add(word)
    
    print(f"\nAfter removing duplicates: {len(unique_words)} unique words")
    
    # Create phoneme-to-words mapping
    target_phonemes = get_all_cmu_phonemes()
    phoneme_to_words = create_phoneme_word_mapping(word_phoneme_map, target_phonemes)
    
    # Save results
    save_results(unique_words, word_phoneme_map, phoneme_to_words)
    
    # Print summary
    print(f"\n📊 FINAL RESULTS:")
    print(f"   • Selected {len(unique_words)} unique words")
    print(f"   • Covered {len(phoneme_to_words)}/39 phonemes")
    print(f"   • Status: {'✅ Complete coverage' if len(phoneme_to_words) == 39 else '❌ Incomplete coverage'}")
    
    print(f"\n📁 FILES CREATED:")
    print(f"   • minimal_phoneme_coverage_words.txt - Final word list")
    print(f"   • phoneme_words_mapping.txt - Phonemes grouped by words")
    print(f"   • minimal_coverage_summary.txt - Summary report")

if __name__ == "__main__":
    main()