#!/usr/bin/env python3
"""
Improved vocabulary comparison with proper contraction splitting.
Split contractions like "action's" into "action" + "'s"
"""

import re
from collections import Counter

def split_contractions(text):
    """
    Split contractions and possessives properly.
    Examples:
    - "action's" -> ["action", "'s"]
    - "don't" -> ["do", "n't"]
    - "I'll" -> ["I", "'ll"]
    - "you're" -> ["you", "'re"]
    """
    tokens = []
    
    # First, find all word-like tokens
    word_tokens = re.findall(r"\b\w+(?:'\w+)?\b", text.lower())
    
    for token in word_tokens:
        if "'" in token:
            # Split contractions
            if token.endswith("'s"):
                # Possessive: "action's" -> ["action", "'s"]
                base = token[:-2]
                if base:  # Make sure base is not empty
                    tokens.extend([base, "'s"])
            elif token.endswith("n't"):
                # Negative: "don't" -> ["do", "n't"]
                base = token[:-3]
                if base:
                    tokens.extend([base, "n't"])
            elif token.endswith("'ll"):
                # Will: "I'll" -> ["I", "'ll"]
                base = token[:-3]
                if base:
                    tokens.extend([base, "'ll"])
            elif token.endswith("'re"):
                # Are: "you're" -> ["you", "'re"]
                base = token[:-3]
                if base:
                    tokens.extend([base, "'re"])
            elif token.endswith("'ve"):
                # Have: "I've" -> ["I", "'ve"]
                base = token[:-3]
                if base:
                    tokens.extend([base, "'ve"])
            elif token.endswith("'d"):
                # Would/Had: "I'd" -> ["I", "'d"]
                base = token[:-2]
                if base:
                    tokens.extend([base, "'d"])
            elif token.endswith("'m"):
                # Am: "I'm" -> ["I", "'m"]
                base = token[:-2]
                if base:
                    tokens.extend([base, "'m"])
            else:
                # Other contractions, keep as is for now
                tokens.append(token)
        else:
            # Regular word
            tokens.append(token)
    
    return tokens

def extract_vocabulary_from_sentences_improved(filename):
    """Extract all unique words from sentences file with proper contraction splitting."""
    print(f"Extracting vocabulary from {filename} with contraction splitting...")
    vocabulary = set()
    word_count = Counter()
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"Processed {line_num} lines...")
            
            sentence = line.strip()
            if not sentence:
                continue
            
            # Split contractions properly
            tokens = split_contractions(sentence)
            
            for token in tokens:
                vocabulary.add(token)
                word_count[token] += 1
    
    print(f"Found {len(vocabulary)} unique words/tokens in sentences")
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
    # Extract vocabulary from selected sentences with improved splitting
    sentences_vocab, word_count = extract_vocabulary_from_sentences_improved('selected_sentences.txt')
    
    # Load final word list
    final_words = load_final_word_list('final_word_list.txt')
    
    # Find words in final_word_list but not in sentences
    unused_words = final_words - sentences_vocab
    
    # Find words in sentences but not in final_word_list
    extra_words = sentences_vocab - final_words
    
    print("\n" + "="*70)
    print("IMPROVED VOCABULARY COMPARISON ANALYSIS")
    print("="*70)
    
    print(f"\nSet1 (sentences vocabulary with split contractions): {len(sentences_vocab)} unique tokens")
    print(f"Set2 (final word list): {len(final_words)} unique words")
    print(f"Words in Set2 but NOT in Set1: {len(unused_words)} words")
    print(f"Words in Set1 but NOT in Set2: {len(extra_words)} words")
    
    # Calculate coverage
    used_words = final_words & sentences_vocab
    coverage = (len(used_words) / len(final_words)) * 100 if final_words else 0
    
    print(f"Coverage: {len(used_words)}/{len(final_words)} = {coverage:.2f}%")
    
    # Save unused words to file
    if unused_words:
        print(f"\nSaving {len(unused_words)} unused words to 'unused_words_improved.txt'...")
        with open('unused_words_improved.txt', 'w', encoding='utf-8') as f:
            f.write("Words in final_word_list.txt but NOT used in selected_sentences.txt\n")
            f.write("(After proper contraction splitting)\n")
            f.write("="*60 + "\n\n")
            for word in sorted(unused_words):
                f.write(f"{word}\n")
        
        print("Unused words:")
        for i, word in enumerate(sorted(unused_words), 1):
            print(f"{i:2d}. {word}")
    
    # Save extra words to file (should be much fewer now)
    if extra_words:
        print(f"\nSaving {len(extra_words)} extra words to 'extra_words_improved.txt'...")
        with open('extra_words_improved.txt', 'w', encoding='utf-8') as f:
            f.write("Words in selected_sentences.txt but NOT in final_word_list.txt\n")
            f.write("(After proper contraction splitting)\n")
            f.write("="*60 + "\n\n")
            for word in sorted(extra_words):
                freq = word_count[word]
                f.write(f"{word} ({freq} times)\n")
        
        print(f"First 20 extra words (with frequency):")
        extra_words_sorted = sorted([(word_count[word], word) for word in extra_words], reverse=True)
        for i, (freq, word) in enumerate(extra_words_sorted[:20], 1):
            print(f"{i:2d}. {word} ({freq} times)")
        
        if len(extra_words) > 20:
            print(f"... and {len(extra_words) - 20} more (see extra_words_improved.txt)")
    
    # Show most frequent contractions
    contraction_tokens = ["'s", "n't", "'ll", "'re", "'ve", "'d", "'m"]
    print(f"\nContraction frequencies:")
    for token in contraction_tokens:
        if token in word_count:
            print(f"  {token}: {word_count[token]:,} times")
    
    # Create summary report
    with open('vocabulary_comparison_improved_report.txt', 'w', encoding='utf-8') as f:
        f.write("IMPROVED VOCABULARY COMPARISON REPORT\n")
        f.write("(With proper contraction splitting)\n")
        f.write("="*50 + "\n\n")
        f.write(f"Set1 (sentences vocabulary): {len(sentences_vocab):,} unique tokens\n")
        f.write(f"Set2 (final word list): {len(final_words):,} unique words\n")
        f.write(f"Words used from Set2: {len(used_words):,} words\n")
        f.write(f"Words unused from Set2: {len(unused_words):,} words\n")
        f.write(f"Extra words in Set1: {len(extra_words):,} words\n")
        f.write(f"Coverage of final word list: {coverage:.2f}%\n\n")
        
        f.write("CONTRACTION FREQUENCIES:\n")
        f.write("-" * 25 + "\n")
        for token in contraction_tokens:
            if token in word_count:
                f.write(f"{token}: {word_count[token]:,} times\n")
        
        f.write(f"\nANALYSIS:\n")
        f.write("-" * 20 + "\n")
        if coverage >= 95:
            f.write("✅ Excellent coverage! Almost all words from the final list are used.\n")
        elif coverage >= 90:
            f.write("✅ Very good coverage! Most words from the final list are used.\n")
        elif coverage >= 75:
            f.write("✓ Good coverage, but some words are underutilized.\n")
        elif coverage >= 50:
            f.write("⚠ Moderate coverage, many words are not used.\n")
        else:
            f.write("❌ Poor coverage, most words are not used in sentences.\n")
    
    print("\nDetailed report saved as 'vocabulary_comparison_improved_report.txt'")

if __name__ == "__main__":
    main()




