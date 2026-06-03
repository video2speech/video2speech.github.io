#!/usr/bin/env python3
"""
Process movie_lines.tsv to extract sentences and check if all words are in final_word_list.txt
"""

import re
import csv
import string
from typing import List, Set

def load_word_list(filename: str) -> Set[str]:
    """Load the final word list into a set for fast lookup."""
    with open(filename, 'r', encoding='utf-8') as f:
        words = set()
        for line in f:
            word = line.strip()
            if word:
                words.add(word.lower())  # Store in lowercase for case-insensitive matching
        return words

def tokenize_with_contractions(text: str) -> List[str]:
    """
    Tokenize text into words, preserving contractions like n't, 's, 'll, 'd, etc.
    """
    # Remove quotes and other punctuation but preserve contractions
    # First, handle contractions by adding spaces around them but keeping them together
    
    # Common contractions - make sure they stay as separate tokens
    contractions = [
        r"n't", r"'s", r"'ll", r"'d", r"'re", r"'ve", r"'m",
        # Also handle reverse cases
        r"won't", r"can't", r"shan't", r"shouldn't", r"wouldn't", 
        r"couldn't", r"didn't", r"doesn't", r"don't", r"isn't", 
        r"aren't", r"wasn't", r"weren't", r"hasn't", r"haven't",
        r"hadn't", r"mustn't", r"needn't", r"daren't", r"mayn't"
    ]
    
    # Replace contractions with space + contraction to separate them
    processed_text = text.lower()
    
    # Handle special cases first
    processed_text = re.sub(r"\bwon't\b", "will n't", processed_text)
    processed_text = re.sub(r"\bcan't\b", "can n't", processed_text)
    processed_text = re.sub(r"\bshan't\b", "shall n't", processed_text)
    
    # Handle regular contractions
    processed_text = re.sub(r"\b(\w+)(n't)\b", r"\1 \2", processed_text)
    processed_text = re.sub(r"\b(\w+)('s)\b", r"\1 \2", processed_text)
    processed_text = re.sub(r"\b(\w+)('ll)\b", r"\1 \2", processed_text)
    processed_text = re.sub(r"\b(\w+)('d)\b", r"\1 \2", processed_text)
    processed_text = re.sub(r"\b(\w+)('re)\b", r"\1 \2", processed_text)
    processed_text = re.sub(r"\b(\w+)('ve)\b", r"\1 \2", processed_text)
    processed_text = re.sub(r"\b(\w+)('m)\b", r"\1 \2", processed_text)
    
    # Remove all punctuation except apostrophes in contractions
    processed_text = re.sub(r'[^\w\s\']', ' ', processed_text)
    
    # Split into words and clean up
    words = processed_text.split()
    
    # Clean up any remaining issues
    clean_words = []
    for word in words:
        word = word.strip("'\"")
        if word and word.replace("'", "").isalpha():  # Only keep words with letters
            clean_words.append(word)
    
    return clean_words

def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting on common punctuation
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

def process_movie_lines(tsv_file: str, word_list: Set[str]) -> List[str]:
    """
    Process movie lines and return sentences where all words are in the word list.
    """
    matching_sentences = []
    total_sentences = 0
    
    with open(tsv_file, 'r', encoding='utf-8', errors='ignore') as f:
        # Skip header if exists, or process all lines
        for line_num, line in enumerate(f, 1):
            if line_num % 10000 == 0:
                print(f"Processed {line_num} lines, found {len(matching_sentences)} matching sentences")
            
            try:
                # Split by tab - the format appears to be: ID, user, movie, character, text
                parts = line.strip().split('\t')
                if len(parts) < 5:
                    continue
                
                # The last part should be the dialogue text
                dialogue_text = parts[-1]
                
                # Remove quotes if they wrap the entire text
                if dialogue_text.startswith('"') and dialogue_text.endswith('"'):
                    dialogue_text = dialogue_text[1:-1]
                
                # Split into sentences
                sentences = split_into_sentences(dialogue_text)
                
                for sentence in sentences:
                    if not sentence:
                        continue
                        
                    total_sentences += 1
                    
                    # Tokenize the sentence
                    words = tokenize_with_contractions(sentence)
                    
                    if not words:  # Skip empty sentences
                        continue
                    
                    # Check if all words are in our word list
                    all_words_found = True
                    for word in words:
                        if word.lower() not in word_list:
                            all_words_found = False
                            break
                    
                    if all_words_found:
                        matching_sentences.append(sentence.strip())
                        
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
                continue
    
    print(f"\nProcessing complete!")
    print(f"Total sentences processed: {total_sentences}")
    print(f"Matching sentences found: {len(matching_sentences)}")
    
    return matching_sentences

def main():
    print("Loading word list...")
    word_list = load_word_list('final_word_list.txt')
    print(f"Loaded {len(word_list)} words from final_word_list.txt")
    
    print("\nProcessing movie lines...")
    matching_sentences = process_movie_lines('materials/movie_lines.tsv', word_list)
    
    # Write results to file
    output_file = 'selected_sentences.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence in matching_sentences:
            f.write(sentence + '\n')
    
    print(f"\nResults written to {output_file}")
    print(f"Found {len(matching_sentences)} sentences where all words are in the word list")
    
    # Show first 10 examples
    if matching_sentences:
        print("\nFirst 10 matching sentences:")
        for i, sentence in enumerate(matching_sentences[:10], 1):
            print(f"{i:2d}. {sentence}")

if __name__ == "__main__":
    main()
