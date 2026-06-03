# English Phoneme Distribution Analysis

This repository contains tools for analyzing the phoneme distribution in English text files. Two versions are provided: a comprehensive analysis tool with accurate phoneme conversion and a simple version that requires no external dependencies.

## Files Analyzed

The analysis processes the following text files from the `materials/` directory:

- `50_sentences_list.txt` - 50 common English sentences
- `50_words_list.txt` - 50 common English words  
- `150_sentences_list.txt` - 150 movie dialogue sentences (15,028 lines)
- `150_words_list.txt` - 150 most common English words

## Usage Options

### Option 1: Comprehensive Analysis (Recommended)

For accurate phoneme analysis using the CMU Pronouncing Dictionary:

```bash
# Install dependencies
pip install -r requirements.txt

# Run comprehensive analysis
python3 phoneme_analysis.py
```

**Features:**
- Accurate phoneme conversion using CMU Pronouncing Dictionary
- Handles word stress and pronunciation variants
- Generates detailed visualizations (bar charts, pie charts, histograms)
- Comprehensive statistical analysis
- Detailed text reports

### Option 2: Simple Analysis (No Dependencies)

For basic analysis without external libraries:

```bash
# Run simple analysis (no installation needed)
python3 simple_phoneme_analysis.py
```

**Features:**
- Basic phoneme mapping using letter-to-sound rules
- No external dependencies required
- Quick analysis suitable for rough estimates
- Text-based output and reports

## Output Files

Both scripts generate detailed reports:

- **Comprehensive version**: `phoneme_analysis_report.txt` + `phoneme_distribution_analysis.png`
- **Simple version**: `simple_phoneme_report.txt`

## Analysis Results

The tools provide:

1. **Overall Statistics**
   - Total words and phonemes processed
   - Unique phoneme count
   - Most frequent phonemes with percentages

2. **Phoneme Classification**
   - Vowel vs consonant distribution
   - Phoneme type identification (ARPAbet format)

3. **File Comparison**
   - Per-file phoneme statistics
   - Top phonemes in each file
   - Vowel/consonant ratios by file

4. **Visualizations** (comprehensive version only)
   - Top 20 phonemes bar chart
   - Vowel/consonant pie chart  
   - Phoneme frequency distribution histogram
   - File comparison chart

## Sample Results

From the analysis of all four files (86,506 words, 225,746 phonemes):

**Top 5 Most Frequent Phonemes:**
1. T (9.75%) - Consonant
2. EH (9.65%) - Vowel  
3. IH (8.15%) - Vowel
4. AO (7.04%) - Vowel
5. N (6.37%) - Consonant

**Overall Distribution:**
- Vowels: 40.27%
- Consonants: 59.73%

## Technical Details

### Phoneme Format

The analysis uses ARPAbet phoneme notation:

**Vowels:** AA, AE, AH, AO, AW, AY, EH, ER, EY, IH, IY, OW, OY, UH, UW

**Consonants:** B, CH, D, DH, F, G, HH, JH, K, L, M, N, NG, P, R, S, SH, T, TH, V, W, Y, Z, ZH

### Dependencies

- **pronouncing**: CMU Pronouncing Dictionary interface
- **matplotlib**: Visualization generation
- **numpy**: Numerical computations

## Limitations

- **Simple version**: Uses basic letter-to-phoneme mapping, less accurate for complex words
- **Comprehensive version**: Requires internet connection for first-time dictionary download
- Both versions handle contractions and basic text cleaning

## Use Cases

- **Linguistic research**: Analyze phoneme patterns in different text types
- **Speech synthesis**: Understand phoneme distributions for voice training
- **Language learning**: Compare phoneme usage across different vocabulary sets
- **Text analysis**: Characterize linguistic properties of text corpora
