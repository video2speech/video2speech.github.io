#!/usr/bin/env python3
"""
Process movie lines to extract sentences that meet specific criteria:
1. All words must be in the final_word_list.txt
2. Sentence must have >= 3 words
3. Include contractions like n't, 's, 'll, 'd as separate words
4. Include punctuation at the end
5. Remove duplicates
"""

import re
from collections import OrderedDict

def load_word_list(filename):
    """Load the allowed word list."""
    with open(filename, 'r', encoding='utf-8') as f:
        words = set(line.strip().lower() for line in f if line.strip())
    return words

def tokenize_sentence(sentence):
    """
    Tokenize sentence including contractions as separate tokens.
    Examples: 
    - "don't" -> ["do", "n't"]
    - "I'm" -> ["I", "'m"] 
    - "we'll" -> ["we", "'ll"]
    - "you'd" -> ["you", "'d"]
    """
    # Handle contractions by splitting them
    # First, handle special cases
    sentence = re.sub(r"\bcan't\b", "can n't", sentence, flags=re.IGNORECASE)
    sentence = re.sub(r"\bwon't\b", "wo n't", sentence, flags=re.IGNORECASE)
    sentence = re.sub(r"\bshan't\b", "sha n't", sentence, flags=re.IGNORECASE)
    
    # Handle n't contractions
    sentence = re.sub(r"([a-zA-Z]+)n't\b", r"\1 n't", sentence)
    
    # Handle 'm, 's, 're, 've, 'll, 'd contractions
    sentence = re.sub(r"([a-zA-Z]+)'(m|s|re|ve|ll|d)\b", r"\1 '\2", sentence)
    
    # Split into tokens, keeping punctuation separate
    tokens = re.findall(r"\w+|'[a-z]+|[.!?;,:]", sentence, re.IGNORECASE)
    
    return tokens

def split_into_sentences(text):
    """Split text into individual sentences."""
    # Split on sentence-ending punctuation, but keep the punctuation
    sentences = re.split(r'([.!?]+)', text)
    
    result = []
    for i in range(0, len(sentences)-1, 2):
        if i+1 < len(sentences):
            sentence = sentences[i].strip()
            punct = sentences[i+1].strip()
            if sentence and punct:
                result.append(sentence + punct)
        elif sentences[i].strip():
            result.append(sentences[i].strip())
    
    # Handle case where last sentence doesn't end with punctuation
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        result.append(sentences[-1].strip())
    
    return result

def process_movie_lines(tsv_file, word_list_file):
    """Process movie lines and extract valid sentences."""
    
    print("Loading word list...")
    allowed_words = load_word_list(word_list_file)
    print(f"Loaded {len(allowed_words)} allowed words")
    
    valid_sentences = OrderedDict()  # Use OrderedDict to maintain order and remove duplicates
    total_lines = 0
    processed_sentences = 0
    valid_count = 0
    
    print("Processing movie lines...")
    
    with open(tsv_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            
            if line_num % 10000 == 0:
                print(f"Processed {line_num} lines...")
            
            # Skip empty lines
            if not line.strip():
                continue
                
            # Parse TSV format - the dialogue is typically the last column
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
                
            dialogue = parts[-1]  # Last column contains the dialogue
            
            # Split dialogue into sentences
            sentences = split_into_sentences(dialogue)
            
            for sentence in sentences:
                processed_sentences += 1
                
                # Tokenize the sentence
                tokens = tokenize_sentence(sentence)
                
                # Filter out punctuation for word checking, but keep for final output
                word_tokens = [token.lower() for token in tokens if re.match(r"\w+|'[a-z]+", token, re.IGNORECASE)]
                
                # Check if sentence has >= 3 words
                if len(word_tokens) < 3:
                    continue
                
                # Check if all words are in allowed list
                all_words_valid = True
                for word in word_tokens:
                    if word not in allowed_words:
                        all_words_valid = False
                        break
                
                if all_words_valid:
                    # Keep original sentence with punctuation
                    sentence_clean = sentence.strip()
                    if sentence_clean and sentence_clean not in valid_sentences:
                        valid_sentences[sentence_clean] = True
                        valid_count += 1
    
    print(f"\nProcessing complete!")
    print(f"Total lines processed: {total_lines}")
    print(f"Total sentences processed: {processed_sentences}")
    print(f"Valid sentences found: {valid_count}")
    print(f"Unique valid sentences: {len(valid_sentences)}")
    
    return list(valid_sentences.keys())

def main():
    tsv_file = "materials/movie_lines.tsv"
    word_list_file = "final_word_list.txt"
    output_file = "selected_sentences.txt"
    
    try:
        valid_sentences = process_movie_lines(tsv_file, word_list_file)
        
        # Write results to file
        with open(output_file, 'w', encoding='utf-8') as f:
            for sentence in valid_sentences:
                f.write(sentence + '\n')
        
        print(f"\nResults written to {output_file}")
        print(f"Total unique valid sentences: {len(valid_sentences)}")
        
        # Show first 10 examples
        print("\nFirst 10 examples:")
        for i, sentence in enumerate(valid_sentences[:10], 1):
            print(f"{i:2d}. {sentence}")
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
