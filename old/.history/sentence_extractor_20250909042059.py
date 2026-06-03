#!/usr/bin/env python3
"""
Extract sentences from movie_lines.tsv that contain only words from final_word_list.txt
and have at least 3 words.
"""

import re
import string

def load_word_list(filename):
    """Load the word list from file into a set for fast lookup."""
    with open(filename, 'r', encoding='utf-8') as f:
        words = set()
        for line in f:
            word = line.strip()
            if word:
                words.add(word.lower())
        return words

def tokenize_sentence(sentence):
    """
    Tokenize a sentence into words, preserving contractions like n't, 's, 'll, 'd
    """
    # Remove quotes and other punctuation except sentence-ending punctuation
    # Keep contractions intact
    sentence = sentence.strip()
    
    # Handle contractions - split them appropriately
    # n't, 's, 'll, 'd, 're, 've should be separate tokens
    contractions = {
        "n't": " n't",
        "'s": " 's", 
        "'ll": " 'll",
        "'d": " 'd",
        "'re": " 're",
        "'ve": " 've"
    }
    
    # Replace contractions with space + contraction
    for contraction, replacement in contractions.items():
        sentence = sentence.replace(contraction, replacement)
    
    # Remove most punctuation but keep sentence endings
    sentence_endings = '.!?'
    
    # Split on whitespace and punctuation, but preserve sentence endings
    tokens = []
    current_sentence = ""
    
    # First, let's handle this more simply
    # Remove all punctuation except sentence endings and contractions
    cleaned = ""
    i = 0
    while i < len(sentence):
        char = sentence[i]
        if char.isalnum() or char.isspace():
            cleaned += char
        elif char == "'" and i + 1 < len(sentence) and sentence[i:i+2] in ["'s", "'t", "'d", "'m", "'l", "'v", "'r"]:
            # This is part of a contraction
            cleaned += char
        elif char in sentence_endings:
            cleaned += " " + char + " "
        else:
            cleaned += " "
        i += 1
    
    # Split into tokens
    tokens = cleaned.split()
    
    return tokens

def extract_sentences(text):
    """Extract individual sentences from text."""
    # Split on sentence endings
    sentences = re.split(r'[.!?]+', text)
    result = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Add back a period for consistency
            result.append(sentence + ".")
    
    return result

def check_sentence(sentence, word_set):
    """
    Check if a sentence contains only words from the word set and has >= 3 words.
    Returns (is_valid, word_count, tokens_with_punct)
    """
    tokens = tokenize_sentence(sentence)
    
    # Separate words from punctuation
    words = []
    punctuation = []
    
    for token in tokens:
        if token in '.!?':
            punctuation.append(token)
        else:
            words.append(token.lower())
    
    # Check if all words are in the word set
    all_words_valid = True
    for word in words:
        if word not in word_set:
            all_words_valid = False
            break
    
    # Check length requirement
    has_min_length = len(words) >= 3
    
    return all_words_valid and has_min_length, len(words), tokens

def main():
    print("Loading word list...")
    word_set = load_word_list('final_word_list.txt')
    print(f"Loaded {len(word_set)} words")
    
    print("Processing movie lines...")
    
    valid_sentences = []
    total_lines = 0
    total_sentences = 0
    
    with open('materials/movie_lines.tsv', 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            
            # Parse TSV format: skip the first few columns to get to the actual text
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
                
            # The last part should be the actual dialogue
            dialogue = parts[-1]
            
            # Extract sentences from the dialogue
            sentences = extract_sentences(dialogue)
            
            for sentence in sentences:
                total_sentences += 1
                is_valid, word_count, tokens = check_sentence(sentence, word_set)
                
                if is_valid:
                    valid_sentences.append(sentence)
            
            # Progress indicator
            if line_num % 50000 == 0:
                print(f"Processed {line_num} lines, found {len(valid_sentences)} valid sentences")
    
    print(f"\nProcessing complete!")
    print(f"Total lines processed: {total_lines}")
    print(f"Total sentences extracted: {total_sentences}")
    print(f"Valid sentences found: {len(valid_sentences)}")
    
    # Write valid sentences to output file
    output_file = 'selected_sentences.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence in valid_sentences:
            f.write(sentence + '\n')
    
    print(f"Valid sentences written to: {output_file}")
    
    # Show some examples
    print(f"\nFirst 10 valid sentences:")
    for i, sentence in enumerate(valid_sentences[:10], 1):
        print(f"{i:2d}. {sentence}")

if __name__ == "__main__":
    main()
