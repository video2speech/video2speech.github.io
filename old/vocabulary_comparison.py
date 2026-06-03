#!/usr/bin/env python3
"""
Compare vocabulary between selected_sentences.txt and final_word_list.txt
Find words in final_word_list.txt that are not used in selected_sentences.txt
"""

import re
from collections import Counter

def tokenize_with_contractions(text):
    """
    Tokenize text preserving contractions like 'm, 's, 'll, n't, etc.
    """
    # Pattern to match words with contractions
    # This will capture: word, 's, 'll, 'm, n't, 'd, 're, 've, etc.
    pattern = r"\b\w+(?:'\w+)?\b|'\w+"
    tokens = re.findall(pattern, text.lower())
    return tokens

def extract_vocabulary_from_sentences(filename):
    """Extract all unique words from sentences file."""
    print(f"Extracting vocabulary from {filename}...")
    vocabulary = set()
    word_count = Counter()
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"Processed {line_num} lines...")
            
            sentence = line.strip()
            if not sentence:
                continue
            
            # Tokenize the sentence
            tokens = tokenize_with_contractions(sentence)
            
            for token in tokens:
                vocabulary.add(token)
                word_count[token] += 1
    
    print(f"Found {len(vocabulary)} unique words in sentences")
    return vocabulary, word_count

def load_final_word_list(filename):
    """Load the final word list."""
    print(f"Loading final word list from {filename}...")
    words = set()
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip().lower()
            if word:
                words.add(word)
    
    print(f"Loaded {len(words)} words from final word list")
    return words

def main():
    # Extract vocabulary from selected sentences
    sentences_vocab, word_count = extract_vocabulary_from_sentences('selected_sentences.txt')
    
    # Load final word list
    final_words = load_final_word_list('final_word_list.txt')
    
    # Find words in final_word_list but not in sentences
    unused_words = final_words - sentences_vocab
    
    # Find words in sentences but not in final_word_list
    extra_words = sentences_vocab - final_words
    
    print("\n" + "="*70)
    print("VOCABULARY COMPARISON ANALYSIS")
    print("="*70)
    
    print(f"\nSet1 (sentences vocabulary): {len(sentences_vocab)} unique words")
    print(f"Set2 (final word list): {len(final_words)} unique words")
    print(f"Words in Set2 but NOT in Set1: {len(unused_words)} words")
    print(f"Words in Set1 but NOT in Set2: {len(extra_words)} words")
    
    # Calculate coverage
    used_words = final_words & sentences_vocab
    coverage = (len(used_words) / len(final_words)) * 100 if final_words else 0
    
    print(f"Coverage: {len(used_words)}/{len(final_words)} = {coverage:.2f}%")
    
    # Save unused words to file
    if unused_words:
        print(f"\nSaving {len(unused_words)} unused words to 'unused_words.txt'...")
        with open('unused_words.txt', 'w', encoding='utf-8') as f:
            f.write("Words in final_word_list.txt but NOT used in selected_sentences.txt\n")
            f.write("="*60 + "\n\n")
            for word in sorted(unused_words):
                f.write(f"{word}\n")
        
        print("First 20 unused words:")
        for i, word in enumerate(sorted(unused_words)[:20], 1):
            print(f"{i:2d}. {word}")
        
        if len(unused_words) > 20:
            print(f"... and {len(unused_words) - 20} more (see unused_words.txt)")
    
    # Save extra words to file
    if extra_words:
        print(f"\nSaving {len(extra_words)} extra words to 'extra_words.txt'...")
        with open('extra_words.txt', 'w', encoding='utf-8') as f:
            f.write("Words in selected_sentences.txt but NOT in final_word_list.txt\n")
            f.write("="*60 + "\n\n")
            for word in sorted(extra_words):
                # Show frequency for extra words
                freq = word_count[word]
                f.write(f"{word} ({freq} times)\n")
        
        print("First 20 extra words (with frequency):")
        extra_words_sorted = sorted([(word_count[word], word) for word in extra_words], reverse=True)
        for i, (freq, word) in enumerate(extra_words_sorted[:20], 1):
            print(f"{i:2d}. {word} ({freq} times)")
        
        if len(extra_words) > 20:
            print(f"... and {len(extra_words) - 20} more (see extra_words.txt)")
    
    # Create summary report
    with open('vocabulary_comparison_report.txt', 'w', encoding='utf-8') as f:
        f.write("VOCABULARY COMPARISON REPORT\n")
        f.write("="*50 + "\n\n")
        f.write(f"Set1 (sentences vocabulary): {len(sentences_vocab):,} unique words\n")
        f.write(f"Set2 (final word list): {len(final_words):,} unique words\n")
        f.write(f"Words used from Set2: {len(used_words):,} words\n")
        f.write(f"Words unused from Set2: {len(unused_words):,} words\n")
        f.write(f"Extra words in Set1: {len(extra_words):,} words\n")
        f.write(f"Coverage of final word list: {coverage:.2f}%\n\n")
        
        f.write("ANALYSIS:\n")
        f.write("-" * 20 + "\n")
        if coverage >= 90:
            f.write("✅ Excellent coverage! Most words from the final list are used.\n")
        elif coverage >= 75:
            f.write("✓ Good coverage, but some words are underutilized.\n")
        elif coverage >= 50:
            f.write("⚠ Moderate coverage, many words are not used.\n")
        else:
            f.write("❌ Poor coverage, most words are not used in sentences.\n")
    
    print("\nDetailed report saved as 'vocabulary_comparison_report.txt'")

if __name__ == "__main__":
    main()



