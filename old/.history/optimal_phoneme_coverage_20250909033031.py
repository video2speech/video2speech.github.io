#!/usr/bin/env python3
"""
Find optimal word set for complete 44 English phoneme coverage
从2_2_spokenvwritten.txt中找到覆盖所有44个英语音素的最小高频词集
"""

import re
from collections import Counter, defaultdict
import csv

# Complete 44 English phonemes (ARPAbet standard)
COMPLETE_44_PHONEMES = {
    # 12 monophthongs (single vowels)
    'IY',  # beat [i]
    'IH',  # bit [ɪ] 
    'EH',  # bet [ɛ]
    'AE',  # bat [æ]
    'AA',  # bot [ɑ]
    'AO',  # bought [ɔ]
    'UH',  # put [ʊ]
    'UW',  # boot [u]
    'AH',  # but [ʌ]
    'ER',  # bird [ɝ]
    'AX',  # about [ə] (schwa)
    'IX',  # roses [ɨ] (barred i)
    
    # 8 diphthongs
    'EY',  # bait [eɪ]
    'AY',  # bite [aɪ]
    'OW',  # boat [oʊ]
    'AW',  # bout [aʊ]
    'OY',  # boy [ɔɪ]
    'IA',  # beer [iə]
    'EA',  # bear [eə]
    'UA',  # tour [uə]
    
    # 24 consonants
    'P',   # pat [p]
    'B',   # bat [b]
    'T',   # tat [t]
    'D',   # dad [d]
    'K',   # cat [k]
    'G',   # gap [g]
    'F',   # fat [f]
    'V',   # vat [v]
    'TH',  # think [θ]
    'DH',  # this [ð]
    'S',   # sat [s]
    'Z',   # zap [z]
    'SH',  # ship [ʃ]
    'ZH',  # measure [ʒ]
    'HH',  # hat [h]
    'M',   # mat [m]
    'N',   # gnat [n]
    'NG',  # hang [ŋ]
    'L',   # lat [l]
    'R',   # rat [r]
    'W',   # wet [w]
    'Y',   # yet [j]
    'CH',  # chat [tʃ]
    'JH'   # jab [dʒ]
}

# Enhanced phoneme mapping with comprehensive word coverage
ENHANCED_WORD_TO_PHONEMES = {
    # High frequency words with clear phoneme mappings
    'the': ['DH', 'AX'],
    'i': ['AY'],
    'you': ['Y', 'UW'],
    'and': ['AX', 'N', 'D'],
    'it': ['IH', 'T'],
    'a': ['AX'],
    'to': ['T', 'UW'],
    'of': ['AX', 'V'],
    'that': ['DH', 'AE', 'T'],
    'in': ['IH', 'N'],
    'we': ['W', 'IY'],
    'is': ['IH', 'Z'],
    'do': ['D', 'UW'],
    'they': ['DH', 'EY'],
    'was': ['W', 'AX', 'Z'],
    'have': ['HH', 'AE', 'V'],
    'what': ['W', 'AX', 'T'],
    'he': ['HH', 'IY'],
    'but': ['B', 'AH', 'T'],
    'for': ['F', 'AO', 'R'],
    'be': ['B', 'IY'],
    'on': ['AO', 'N'],
    'this': ['DH', 'IH', 'S'],
    'know': ['N', 'OW'],
    'well': ['W', 'EH', 'L'],
    'so': ['S', 'OW'],
    'oh': ['OW'],
    'got': ['G', 'AO', 'T'],
    'not': ['N', 'AO', 'T'],
    'are': ['AA', 'R'],
    'if': ['IH', 'F'],
    'with': ['W', 'IH', 'TH'],
    'no': ['N', 'OW'],
    'she': ['SH', 'IY'],
    'at': ['AE', 'T'],
    'there': ['DH', 'EH', 'R'],
    'think': ['TH', 'IH', 'NG', 'K'],
    'yes': ['Y', 'EH', 'S'],
    'just': ['JH', 'AH', 'S', 'T'],
    'all': ['AO', 'L'],
    'can': ['K', 'AE', 'N'],
    'then': ['DH', 'EH', 'N'],
    'get': ['G', 'EH', 'T'],
    'did': ['D', 'IH', 'D'],
    'or': ['AO', 'R'],
    'would': ['W', 'UH', 'D'],
    'them': ['DH', 'EH', 'M'],
    'one': ['W', 'AH', 'N'],
    'up': ['AH', 'P'],
    'go': ['G', 'OW'],
    'now': ['N', 'AW'],
    'your': ['Y', 'UH', 'R'],
    'had': ['HH', 'AE', 'D'],
    'were': ['W', 'ER'],
    'about': ['AX', 'B', 'AW', 'T'],
    'two': ['T', 'UW'],
    'said': ['S', 'EH', 'D'],
    'see': ['S', 'IY'],
    'me': ['M', 'IY'],
    'very': ['V', 'EH', 'R', 'IY'],
    'out': ['AW', 'T'],
    'my': ['M', 'AY'],
    'when': ['W', 'EH', 'N'],
    'mean': ['M', 'IY', 'N'],
    'right': ['R', 'AY', 'T'],
    'from': ['F', 'R', 'AH', 'M'],
    'going': ['G', 'OW', 'IH', 'NG'],
    'say': ['S', 'EY'],
    'been': ['B', 'IH', 'N'],
    'people': ['P', 'IY', 'P', 'AX', 'L'],
    'because': ['B', 'IH', 'K', 'AO', 'Z'],
    'some': ['S', 'AH', 'M'],
    'could': ['K', 'UH', 'D'],
    'will': ['W', 'IH', 'L'],
    'how': ['HH', 'AW'],
    'time': ['T', 'AY', 'M'],
    'who': ['HH', 'UW'],
    'want': ['W', 'AO', 'N', 'T'],
    'like': ['L', 'AY', 'K'],
    'come': ['K', 'AH', 'M'],
    'really': ['R', 'IY', 'AX', 'L', 'IY'],
    'here': ['HH', 'IA', 'R'],  # includes IA phoneme
    'put': ['P', 'UH', 'T'],
    'good': ['G', 'UH', 'D'],
    'as': ['AE', 'Z'],
    'does': ['D', 'AH', 'Z'],
    'any': ['EH', 'N', 'IY'],
    'down': ['D', 'AW', 'N'],
    'where': ['W', 'EA', 'R'],  # includes EA phoneme
    'him': ['HH', 'IH', 'M'],
    'other': ['AH', 'DH', 'ER'],
    'something': ['S', 'AH', 'M', 'TH', 'IH', 'NG'],
    'these': ['DH', 'IY', 'Z'],
    'way': ['W', 'EY'],
    'back': ['B', 'AE', 'K'],
    'should': ['SH', 'UH', 'D'],
    'take': ['T', 'EY', 'K'],
    'thing': ['TH', 'IH', 'NG'],
    'look': ['L', 'UH', 'K'],
    'why': ['W', 'AY'],
    'things': ['TH', 'IH', 'NG', 'Z'],
    'only': ['OW', 'N', 'L', 'IY'],
    'us': ['AH', 'S'],
    'lot': ['L', 'AO', 'T'],
    'make': ['M', 'EY', 'K'],
    'first': ['F', 'ER', 'S', 'T'],
    'okay': ['OW', 'K', 'EY'],
    'more': ['M', 'AO', 'R'],
    'doing': ['D', 'UW', 'IH', 'NG'],
    'done': ['D', 'AH', 'N'],
    'am': ['AE', 'M'],
    'bad': ['B', 'AE', 'D'],
    'coming': ['K', 'AH', 'M', 'IH', 'NG'],
    'feel': ['F', 'IY', 'L'],
    'help': ['HH', 'EH', 'L', 'P'],
    'hope': ['HH', 'OW', 'P'],
    'need': ['N', 'IY', 'D'],
    'please': ['P', 'L', 'IY', 'Z'],
    'tell': ['T', 'EH', 'L'],
    'give': ['G', 'IH', 'V'],
    'thought': ['TH', 'AO', 'T'],
    'again': ['AX', 'G', 'EH', 'N'],
    'might': ['M', 'AY', 'T'],
    'her': ['HH', 'ER'],
    'last': ['L', 'AE', 'S', 'T'],
    'much': ['M', 'AH', 'CH'],
    'still': ['S', 'T', 'IH', 'L'],
    'never': ['N', 'EH', 'V', 'ER'],
    'than': ['DH', 'AE', 'N'],
    'same': ['S', 'EY', 'M'],
    'another': ['AX', 'N', 'AH', 'DH', 'ER'],
    'money': ['M', 'AH', 'N', 'IY'],
    'anything': ['EH', 'N', 'IY', 'TH', 'IH', 'NG'],
    'thank': ['TH', 'AE', 'NG', 'K'],
    'too': ['T', 'UW'],
    'nice': ['N', 'AY', 'S'],
    'work': ['W', 'ER', 'K'],
    'always': ['AO', 'L', 'W', 'EY', 'Z'],
    'tired': ['T', 'AY', 'ER', 'D'],
    'years': ['Y', 'IA', 'R', 'Z'],  # includes IA phoneme
    'through': ['TH', 'R', 'UW'],
    'little': ['L', 'IH', 'T', 'AX', 'L'],
    
    # Additional words for rare phonemes
    'boy': ['B', 'OY'],  # OY phoneme
    'toy': ['T', 'OY'],  # OY phoneme
    'joy': ['JH', 'OY'],  # OY phoneme
    'voice': ['V', 'OY', 'S'],  # OY phoneme
    'choice': ['CH', 'OY', 'S'],  # OY phoneme
    'measure': ['M', 'EH', 'ZH', 'ER'],  # ZH phoneme
    'pleasure': ['P', 'L', 'EH', 'ZH', 'ER'],  # ZH phoneme
    'vision': ['V', 'IH', 'ZH', 'AX', 'N'],  # ZH phoneme
    'decision': ['D', 'IH', 'S', 'IH', 'ZH', 'AX', 'N'],  # ZH phoneme
    'television': ['T', 'EH', 'L', 'AX', 'V', 'IH', 'ZH', 'AX', 'N'],  # ZH phoneme
    'roses': ['R', 'OW', 'Z', 'IX', 'Z'],  # IX phoneme
    'horses': ['HH', 'AO', 'R', 'S', 'IX', 'Z'],  # IX phoneme
    'boxes': ['B', 'AO', 'K', 'S', 'IX', 'Z'],  # IX phoneme
    'near': ['N', 'IA', 'R'],  # IA phoneme
    'beer': ['B', 'IA', 'R'],  # IA phoneme
    'dear': ['D', 'IA', 'R'],  # IA phoneme
    'clear': ['K', 'L', 'IA', 'R'],  # IA phoneme
    'hair': ['HH', 'EA', 'R'],  # EA phoneme
    'care': ['K', 'EA', 'R'],  # EA phoneme
    'bear': ['B', 'EA', 'R'],  # EA phoneme
    'chair': ['CH', 'EA', 'R'],  # EA phoneme
    'poor': ['P', 'UA', 'R'],  # UA phoneme
    'sure': ['SH', 'UA', 'R'],  # UA phoneme
    'tour': ['T', 'UA', 'R'],  # UA phoneme
    'cure': ['K', 'Y', 'UA', 'R'],  # UA phoneme
}

def parse_frequency_file(filename):
    """Parse the spoken/written frequency file"""
    word_frequencies = {}
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines[2:]:  # Skip header lines
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                word = parts[1].lower()  # Word column
                try:
                    freq_spoken = int(parts[2])  # FrSp column
                    word_frequencies[word] = freq_spoken
                except (ValueError, IndexError):
                    continue
    
    return word_frequencies

def get_word_phonemes(word):
    """Get phonemes for a word using enhanced mapping"""
    word = word.lower()
    
    # Handle contractions
    contractions = {
        "n't": 'not',
        "'s": '',  # possessive, skip
        "'ve": 'have',
        "'re": 'are',
        "'ll": 'will',
        "'d": 'would',
        "'m": 'am'
    }
    
    for contraction, expansion in contractions.items():
        if word == contraction:
            word = expansion
            break
    
    if word in ENHANCED_WORD_TO_PHONEMES:
        return ENHANCED_WORD_TO_PHONEMES[word]
    
    # Simple approximation for unknown words
    return approximate_phonemes(word)

def approximate_phonemes(word):
    """Improved phoneme approximation for unknown words"""
    phonemes = []
    i = 0
    while i < len(word):
        char = word[i]
        
        # Handle common letter combinations
        if i < len(word) - 1:
            two_char = word[i:i+2]
            if two_char == 'th':
                phonemes.append('TH' if i == 0 or word[i-1] in 'aeiou' else 'DH')
                i += 2
                continue
            elif two_char == 'sh':
                phonemes.append('SH')
                i += 2
                continue
            elif two_char == 'ch':
                phonemes.append('CH')
                i += 2
                continue
            elif two_char == 'ng':
                phonemes.append('NG')
                i += 2
                continue
            elif two_char == 'oy':
                phonemes.append('OY')
                i += 2
                continue
            elif two_char == 'ou':
                phonemes.append('AW')
                i += 2
                continue
            elif two_char == 'ea':
                phonemes.append('EA')
                i += 2
                continue
            elif two_char == 'ee':
                phonemes.append('IY')
                i += 2
                continue
            elif two_char == 'oo':
                phonemes.append('UW')
                i += 2
                continue
        
        # Single character mappings
        char_to_phoneme = {
            'a': 'AE', 'e': 'EH', 'i': 'IH', 'o': 'AO', 'u': 'AH',
            'b': 'B', 'c': 'K', 'd': 'D', 'f': 'F', 'g': 'G',
            'h': 'HH', 'j': 'JH', 'k': 'K', 'l': 'L', 'm': 'M',
            'n': 'N', 'p': 'P', 'r': 'R', 's': 'S', 't': 'T',
            'v': 'V', 'w': 'W', 'y': 'Y', 'z': 'Z'
        }
        
        if char in char_to_phoneme:
            phonemes.append(char_to_phoneme[char])
        
        i += 1
    
    return phonemes

def find_minimal_phoneme_coverage(word_frequencies):
    """Find minimal set of high-frequency words covering all 44 phonemes"""
    # Create phoneme to words mapping
    phoneme_to_words = defaultdict(list)
    word_to_phonemes_map = {}
    
    for word, freq in word_frequencies.items():
        phonemes = get_word_phonemes(word)
        word_to_phonemes_map[word] = phonemes
        
        for phoneme in phonemes:
            if phoneme in COMPLETE_44_PHONEMES:
                phoneme_to_words[phoneme].append((word, freq))
    
    # Sort words by frequency for each phoneme
    for phoneme in phoneme_to_words:
        phoneme_to_words[phoneme].sort(key=lambda x: x[1], reverse=True)
    
    # Greedy algorithm to find minimal coverage
    covered_phonemes = set()
    selected_words = []
    remaining_phonemes = set(COMPLETE_44_PHONEMES)
    
    # First, add words that are the ONLY source of rare phonemes
    unique_phoneme_words = {}
    for phoneme in COMPLETE_44_PHONEMES:
        if phoneme in phoneme_to_words and len(phoneme_to_words[phoneme]) == 1:
            word, freq = phoneme_to_words[phoneme][0]
            unique_phoneme_words[word] = phoneme
            selected_words.append((word, freq, f"UNIQUE for {phoneme}"))
            covered_phonemes.update(word_to_phonemes_map[word])
            remaining_phonemes.difference_update(word_to_phonemes_map[word])
    
    # Then use greedy approach for remaining phonemes
    while remaining_phonemes:
        best_word = None
        best_score = 0
        best_freq = 0
        best_new_phonemes = set()
        
        # Find word that covers most remaining phonemes with highest frequency
        for word, freq in word_frequencies.items():
            if word in [w[0] for w in selected_words]:
                continue
                
            word_phonemes = set(word_to_phonemes_map.get(word, []))
            new_phonemes = word_phonemes & remaining_phonemes
            
            if new_phonemes:
                # Score = number of new phonemes * log(frequency)
                import math
                score = len(new_phonemes) * math.log(freq + 1)
                
                if score > best_score:
                    best_word = word
                    best_score = score
                    best_freq = freq
                    best_new_phonemes = new_phonemes
        
        if best_word:
            annotation = ""
            if len(best_new_phonemes) == 1:
                phoneme = list(best_new_phonemes)[0]
                # Check if this is the only high-frequency word for this phoneme
                phoneme_words = [w for w, f in phoneme_to_words.get(phoneme, [])]
                if len(phoneme_words) <= 2:  # Very rare phoneme
                    annotation = f"RARE {phoneme}"
            
            selected_words.append((best_word, best_freq, annotation))
            covered_phonemes.update(word_to_phonemes_map[best_word])
            remaining_phonemes.difference_update(word_to_phonemes_map[best_word])
        else:
            # No more words can cover remaining phonemes
            break
    
    return selected_words, covered_phonemes, remaining_phonemes, word_to_phonemes_map, unique_phoneme_words

def analyze_phoneme_coverage(selected_words, word_to_phonemes_map):
    """Analyze which phonemes are covered and which words are unique for certain phonemes"""
    all_covered = set()
    phoneme_word_count = defaultdict(int)
    
    for word, freq, annotation in selected_words:
        phonemes = word_to_phonemes_map.get(word, [])
        all_covered.update(phonemes)
        
        for phoneme in phonemes:
            if phoneme in COMPLETE_44_PHONEMES:
                phoneme_word_count[phoneme] += 1
    
    # Find phonemes that appear in only one selected word
    unique_representations = {}
    for word, freq, annotation in selected_words:
        phonemes = word_to_phonemes_map.get(word, [])
        for phoneme in phonemes:
            if phoneme in COMPLETE_44_PHONEMES and phoneme_word_count[phoneme] == 1:
                unique_representations[word] = unique_representations.get(word, []) + [phoneme]
    
    return all_covered, unique_representations

def main():
    """Main function to find optimal phoneme coverage"""
    print("Finding optimal word set for 44 English phoneme coverage")
    print("="*60)
    
    # Parse frequency file
    word_frequencies = parse_frequency_file('materials/2_2_spokenvwritten.txt')
    print(f"Loaded {len(word_frequencies)} words from frequency file")
    
    # Find minimal coverage
    selected_words, covered_phonemes, remaining_phonemes, word_to_phonemes_map, unique_phoneme_words = find_minimal_phoneme_coverage(word_frequencies)
    
    # Analyze coverage
    all_covered, unique_representations = analyze_phoneme_coverage(selected_words, word_to_phonemes_map)
    
    print(f"\nResults:")
    print(f"- Total words selected: {len(selected_words)}")
    print(f"- Phonemes covered: {len(covered_phonemes)}/44")
    print(f"- Coverage: {len(covered_phonemes)/44*100:.1f}%")
    
    if remaining_phonemes:
        print(f"- Missing phonemes: {sorted(remaining_phonemes)}")
    else:
        print("- ✅ All 44 phonemes covered!")
    
    print(f"\nTop {len(selected_words)} words for complete phoneme coverage:")
    print("-" * 80)
    print(f"{'Rank':<4} {'Word':<15} {'Frequency':<10} {'Phonemes':<25} {'Special'}")
    print("-" * 80)
    
    for i, (word, freq, annotation) in enumerate(selected_words, 1):
        phonemes = word_to_phonemes_map.get(word, [])
        phoneme_str = ' '.join(p for p in phonemes if p in COMPLETE_44_PHONEMES)
        
        special_notes = []
        if annotation:
            special_notes.append(annotation)
        
        if word in unique_representations:
            unique_phonemes = unique_representations[word]
            special_notes.append(f"ONLY for {', '.join(unique_phonemes)}")
        
        special_str = '; '.join(special_notes) if special_notes else ""
        
        print(f"{i:<4} {word:<15} {freq:<10} {phoneme_str:<25} {special_str}")
    
    # Summary of phoneme coverage
    print(f"\nPhoneme coverage summary:")
    print("-" * 40)
    covered_list = sorted(list(covered_phonemes & COMPLETE_44_PHONEMES))
    missing_list = sorted(list(COMPLETE_44_PHONEMES - covered_phonemes))
    
    print(f"✅ Covered ({len(covered_list)}): {' '.join(covered_list)}")
    if missing_list:
        print(f"❌ Missing ({len(missing_list)}): {' '.join(missing_list)}")
    
    return selected_words, covered_phonemes, remaining_phonemes

if __name__ == "__main__":
    selected_words, covered_phonemes, remaining_phonemes = main()
