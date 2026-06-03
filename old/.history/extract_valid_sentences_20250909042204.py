#!/usr/bin/env python3
"""
Extract sentences from movie_lines.tsv that meet the criteria:
1. All words are in final_word_list.txt
2. Sentence has >= 3 words
3. Include contractions like n't, 's, 'll, 'd
4. Include punctuation
5. Remove duplicates
"""

import re
import string
from typing import List, Set

def load_word_list(filename: str) -> Set[str]:
    """Load the valid word list."""
    with open(filename, 'r', encoding='utf-8') as f:
        words = set(line.strip().lower() for line in f if line.strip())
    return words

def tokenize_sentence(sentence: str) -> List[str]:
    """
    Tokenize sentence into words, handling contractions properly.
    Keep punctuation as separate tokens.
    """
    # Replace smart quotes and other unicode punctuation with standard ones
    sentence = sentence.replace('"', '"').replace('"', '"')
    sentence = sentence.replace(''', "'").replace(''', "'")
    
    # Split on whitespace first
    tokens = sentence.split()
    
    result = []
    for token in tokens:
        # Handle contractions and punctuation
        # Split contractions like "don't" -> ["do", "n't"]
        # But keep 's, 'll, 'd, 're, 've as separate tokens
        
        # Remove leading/trailing punctuation but keep it
        leading_punct = ""
        trailing_punct = ""
        
        # Extract leading punctuation
        while token and token[0] in string.punctuation:
            leading_punct += token[0]
            token = token[1:]
        
        # Extract trailing punctuation
        while token and token[-1] in string.punctuation:
            trailing_punct = token[-1] + trailing_punct
            token = token[:-1]
        
        if leading_punct:
            result.append(leading_punct)
        
        if token:
            # Handle contractions
            if "'" in token:
                # Common contractions
                contractions = {
                    "n't": ["n't"],
                    "'s": ["'s"],
                    "'ll": ["'ll"],
                    "'d": ["'d"],
                    "'re": ["'re"],
                    "'ve": ["'ve"],
                    "'m": ["'m"]
                }
                
                found_contraction = False
                for contraction, replacement in contractions.items():
                    if token.endswith(contraction):
                        base_word = token[:-len(contraction)]
                        if base_word:
                            result.append(base_word.lower())
                        result.extend(replacement)
                        found_contraction = True
                        break
                
                if not found_contraction:
                    # Handle other apostrophe cases
                    parts = token.split("'")
                    for i, part in enumerate(parts):
                        if part:
                            result.append(part.lower())
                        if i < len(parts) - 1:  # Add apostrophe back except for last part
                            result.append("'")
            else:
                result.append(token.lower())
        
        if trailing_punct:
            result.append(trailing_punct)
    
    return result

def split_into_sentences(text: str) -> List[str]:
    """Split text into individual sentences."""
    # Simple sentence splitting on common sentence terminators
    sentences = re.split(r'[.!?]+', text)
    # Remove empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def is_valid_sentence(tokens: List[str], valid_words: Set[str]) -> bool:
    """
    Check if sentence meets criteria:
    1. All words (non-punctuation tokens) are in valid_words
    2. Has >= 3 words (excluding punctuation)
    """
    word_tokens = [token for token in tokens if token not in string.punctuation and token != "'"]
    
    # Must have at least 3 words
    if len(word_tokens) < 3:
        return False
    
    # All words must be in valid word list
    for word in word_tokens:
        if word.lower() not in valid_words:
            return False
    
    return True

def main():
    print("Loading word list...")
    valid_words = load_word_list('final_word_list.txt')
    print(f"Loaded {len(valid_words)} valid words")
    
    print("Processing movie lines...")
    valid_sentences = set()  # Use set to automatically handle duplicates
    total_lines = 0
    processed_sentences = 0
    
    with open('materials/movie_lines.tsv', 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            
            if line_num % 10000 == 0:
                print(f"Processed {line_num} lines, found {len(valid_sentences)} valid sentences")
            
            # Skip empty lines
            if not line.strip():
                continue
            
            # Parse TSV format - the dialogue is the last column
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
            
            dialogue = parts[-1]  # Last column contains the dialogue
            
            # Split dialogue into sentences
            sentences = split_into_sentences(dialogue)
            
            for sentence in sentences:
                processed_sentences += 1
                tokens = tokenize_sentence(sentence)
                
                if is_valid_sentence(tokens, valid_words):
                    # Reconstruct sentence with proper spacing
                    reconstructed = ""
                    for i, token in enumerate(tokens):
                        if token in string.punctuation:
                            reconstructed += token
                        else:
                            if i > 0 and tokens[i-1] not in string.punctuation:
                                reconstructed += " "
                            reconstructed += token
                    
                    # Add sentence terminator if not present
                    if not reconstructed.endswith(('.', '!', '?')):
                        reconstructed += '.'
                    
                    valid_sentences.add(reconstructed.strip())
    
    print(f"\nProcessing complete!")
    print(f"Total lines processed: {total_lines}")
    print(f"Total sentences processed: {processed_sentences}")
    print(f"Valid sentences found: {len(valid_sentences)}")
    
    # Write results to file
    print("Writing results to valid_sentences.txt...")
    with open('valid_sentences.txt', 'w', encoding='utf-8') as f:
        for sentence in sorted(valid_sentences):
            f.write(sentence + '\n')
    
    print(f"Results saved to valid_sentences.txt")
    
    # Show some examples
    print("\nFirst 10 valid sentences:")
    for i, sentence in enumerate(sorted(valid_sentences)[:10]):
        print(f"{i+1}. {sentence}")

if __name__ == "__main__":
    main()
