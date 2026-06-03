#!/usr/bin/env python3
"""
Enhanced Phoneme Distribution Analysis with Detailed Report

This script provides a comprehensive analysis of phoneme distribution
and generates both a detailed text report and visualization.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import Counter
import re
from datetime import datetime

# The 44 English phonemes with detailed descriptions
PHONEME_INFO = {
    # Vowels
    'AA': {'ipa': 'ɑ', 'type': 'vowel', 'description': 'low back unrounded vowel (father)'},
    'AE': {'ipa': 'æ', 'type': 'vowel', 'description': 'low front unrounded vowel (cat)'},
    'AH': {'ipa': 'ʌ', 'type': 'vowel', 'description': 'mid central unrounded vowel (cut)'},
    'AO': {'ipa': 'ɔ', 'type': 'vowel', 'description': 'low back rounded vowel (caught)'},
    'AW': {'ipa': 'aʊ', 'type': 'diphthong', 'description': 'low front to high back diphthong (how)'},
    'AY': {'ipa': 'aɪ', 'type': 'diphthong', 'description': 'low front to high front diphthong (hide)'},
    'EH': {'ipa': 'ɛ', 'type': 'vowel', 'description': 'mid front unrounded vowel (red)'},
    'ER': {'ipa': 'ɝ', 'type': 'vowel', 'description': 'mid central r-colored vowel (her)'},
    'EY': {'ipa': 'eɪ', 'type': 'diphthong', 'description': 'mid front to high front diphthong (say)'},
    'IH': {'ipa': 'ɪ', 'type': 'vowel', 'description': 'high front lax vowel (hit)'},
    'IY': {'ipa': 'i', 'type': 'vowel', 'description': 'high front tense vowel (see)'},
    'OW': {'ipa': 'oʊ', 'type': 'diphthong', 'description': 'mid back to high back diphthong (show)'},
    'OY': {'ipa': 'ɔɪ', 'type': 'diphthong', 'description': 'mid back to high front diphthong (toy)'},
    'UH': {'ipa': 'ʊ', 'type': 'vowel', 'description': 'high back lax vowel (put)'},
    'UW': {'ipa': 'u', 'type': 'vowel', 'description': 'high back tense vowel (too)'},
    
    # Consonants
    'B': {'ipa': 'b', 'type': 'stop', 'description': 'voiced bilabial stop (be)'},
    'CH': {'ipa': 'tʃ', 'type': 'affricate', 'description': 'voiceless postalveolar affricate (cheese)'},
    'D': {'ipa': 'd', 'type': 'stop', 'description': 'voiced alveolar stop (dee)'},
    'DH': {'ipa': 'ð', 'type': 'fricative', 'description': 'voiced dental fricative (thee)'},
    'F': {'ipa': 'f', 'type': 'fricative', 'description': 'voiceless labiodental fricative (fee)'},
    'G': {'ipa': 'g', 'type': 'stop', 'description': 'voiced velar stop (green)'},
    'HH': {'ipa': 'h', 'type': 'fricative', 'description': 'voiceless glottal fricative (he)'},
    'JH': {'ipa': 'dʒ', 'type': 'affricate', 'description': 'voiced postalveolar affricate (gee)'},
    'K': {'ipa': 'k', 'type': 'stop', 'description': 'voiceless velar stop (key)'},
    'L': {'ipa': 'l', 'type': 'liquid', 'description': 'lateral approximant (lee)'},
    'M': {'ipa': 'm', 'type': 'nasal', 'description': 'bilabial nasal (me)'},
    'N': {'ipa': 'n', 'type': 'nasal', 'description': 'alveolar nasal (knee)'},
    'NG': {'ipa': 'ŋ', 'type': 'nasal', 'description': 'velar nasal (ping)'},
    'P': {'ipa': 'p', 'type': 'stop', 'description': 'voiceless bilabial stop (pee)'},
    'R': {'ipa': 'r', 'type': 'liquid', 'description': 'retroflex approximant (read)'},
    'S': {'ipa': 's', 'type': 'fricative', 'description': 'voiceless alveolar fricative (sea)'},
    'SH': {'ipa': 'ʃ', 'type': 'fricative', 'description': 'voiceless postalveolar fricative (she)'},
    'T': {'ipa': 't', 'type': 'stop', 'description': 'voiceless alveolar stop (tea)'},
    'TH': {'ipa': 'θ', 'type': 'fricative', 'description': 'voiceless dental fricative (theta)'},
    'V': {'ipa': 'v', 'type': 'fricative', 'description': 'voiced labiodental fricative (vee)'},
    'W': {'ipa': 'w', 'type': 'glide', 'description': 'labial-velar approximant (we)'},
    'Y': {'ipa': 'j', 'type': 'glide', 'description': 'palatal approximant (yield)'},
    'Z': {'ipa': 'z', 'type': 'fricative', 'description': 'voiced alveolar fricative (zee)'},
    'ZH': {'ipa': 'ʒ', 'type': 'fricative', 'description': 'voiced postalveolar fricative (seizure)'}
}

def run_analysis():
    """Run the main phoneme analysis and capture results."""
    # Import the analysis functions from the main script
    import phoneme_analysis as pa
    
    file_paths = [
        'materials/50_sentences_list.txt',
        'materials/50_words_list.txt', 
        'materials/150_sentences_list.txt',
        'materials/150_words_list.txt'
    ]
    
    phoneme_data, total_phonemes = pa.analyze_phoneme_distribution(file_paths)
    return phoneme_data, total_phonemes, file_paths

def generate_detailed_report(phoneme_data, total_phonemes, file_paths):
    """Generate a comprehensive phoneme analysis report."""
    report_filename = f"phoneme_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        # Header
        f.write("="*80 + "\n")
        f.write("COMPREHENSIVE ENGLISH PHONEME DISTRIBUTION ANALYSIS REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total phonemes analyzed: {total_phonemes:,}\n")
        f.write(f"Unique phonemes found: {len(phoneme_data)}\n")
        f.write(f"Files analyzed: {len(file_paths)}\n")
        for i, filepath in enumerate(file_paths, 1):
            f.write(f"  {i}. {filepath}\n")
        f.write("\n")
        
        # Summary statistics
        f.write("SUMMARY STATISTICS\n")
        f.write("-"*50 + "\n")
        if phoneme_data:
            most_common = phoneme_data[0]
            least_common = phoneme_data[-1]
            f.write(f"Most frequent phoneme: {most_common[0]} ({most_common[1]:,} occurrences, {most_common[1]/total_phonemes*100:.2f}%)\n")
            f.write(f"Least frequent phoneme: {least_common[0]} ({least_common[1]:,} occurrences, {least_common[1]/total_phonemes*100:.2f}%)\n")
            
            # Calculate averages
            avg_frequency = total_phonemes / len(phoneme_data)
            f.write(f"Average frequency per phoneme: {avg_frequency:.2f}\n")
            
            # Count by type
            type_counts = {}
            for phoneme, count in phoneme_data:
                if phoneme in PHONEME_INFO:
                    ptype = PHONEME_INFO[phoneme]['type']
                    type_counts[ptype] = type_counts.get(ptype, 0) + count
            
            f.write(f"\nPhoneme distribution by type:\n")
            for ptype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = count / total_phonemes * 100
                f.write(f"  {ptype.capitalize()}: {count:,} ({percentage:.2f}%)\n")
        
        f.write("\n")
        
        # Detailed phoneme breakdown
        f.write("DETAILED PHONEME ANALYSIS\n")
        f.write("-"*80 + "\n")
        f.write(f"{'Rank':<4} {'ARPAbet':<8} {'IPA':<6} {'Type':<12} {'Count':<8} {'%':<6} {'Description'}\n")
        f.write("-"*80 + "\n")
        
        for i, (phoneme, count) in enumerate(phoneme_data, 1):
            percentage = count / total_phonemes * 100
            
            if phoneme in PHONEME_INFO:
                info = PHONEME_INFO[phoneme]
                ipa = info['ipa']
                ptype = info['type']
                description = info['description']
            else:
                ipa = phoneme
                ptype = 'unknown'
                description = 'phoneme mapping not found'
            
            f.write(f"{i:<4} {phoneme:<8} {ipa:<6} {ptype:<12} {count:<8} {percentage:<6.2f} {description}\n")
        
        f.write("\n")
        
        # Top 10 analysis
        f.write("TOP 10 MOST FREQUENT PHONEMES\n")
        f.write("-"*50 + "\n")
        top_10_total = sum(count for _, count in phoneme_data[:10])
        f.write(f"Top 10 phonemes represent {top_10_total/total_phonemes*100:.2f}% of all phonemes\n\n")
        
        for i, (phoneme, count) in enumerate(phoneme_data[:10], 1):
            percentage = count / total_phonemes * 100
            ipa = PHONEME_INFO.get(phoneme, {}).get('ipa', phoneme)
            f.write(f"{i:2}. {phoneme} [{ipa}]: {count:,} occurrences ({percentage:.2f}%)\n")
        
        f.write("\n")
        
        # Analysis insights
        f.write("ANALYSIS INSIGHTS\n")
        f.write("-"*50 + "\n")
        
        # Most common consonant and vowel
        consonants = [(p, c) for p, c in phoneme_data if PHONEME_INFO.get(p, {}).get('type') in ['stop', 'fricative', 'affricate', 'nasal', 'liquid', 'glide']]
        vowels = [(p, c) for p, c in phoneme_data if PHONEME_INFO.get(p, {}).get('type') in ['vowel', 'diphthong']]
        
        if consonants:
            most_common_consonant = consonants[0]
            f.write(f"Most frequent consonant: {most_common_consonant[0]} ({most_common_consonant[1]:,} occurrences)\n")
        
        if vowels:
            most_common_vowel = vowels[0]
            f.write(f"Most frequent vowel: {most_common_vowel[0]} ({most_common_vowel[1]:,} occurrences)\n")
        
        # Coverage analysis
        expected_phonemes = set(PHONEME_INFO.keys())
        found_phonemes = set(p for p, _ in phoneme_data)
        missing_phonemes = expected_phonemes - found_phonemes
        
        f.write(f"\nPhoneme coverage: {len(found_phonemes)}/44 standard English phonemes found\n")
        if missing_phonemes:
            f.write(f"Missing phonemes: {', '.join(sorted(missing_phonemes))}\n")
        
        f.write("\n")
        f.write("="*80 + "\n")
        f.write("END OF REPORT\n")
        f.write("="*80 + "\n")
    
    return report_filename

def create_enhanced_visualization(phoneme_data, total_phonemes):
    """Create an enhanced visualization with multiple charts."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 15))
    
    # Chart 1: Full distribution (top 30)
    top_30 = phoneme_data[:30]
    phonemes, counts = zip(*top_30)
    
    bars1 = ax1.bar(range(len(phonemes)), counts, color='skyblue', edgecolor='navy', alpha=0.7)
    ax1.set_title('Top 30 Phonemes Distribution', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Phonemes (ARPAbet)')
    ax1.set_ylabel('Frequency Count')
    ax1.set_xticks(range(len(phonemes)))
    ax1.set_xticklabels(phonemes, rotation=45, ha='right')
    ax1.grid(axis='y', alpha=0.3)
    
    # Chart 2: Top 10 with percentages
    top_10 = phoneme_data[:10]
    phonemes_10, counts_10 = zip(*top_10)
    percentages = [c/total_phonemes*100 for c in counts_10]
    
    bars2 = ax2.bar(range(len(phonemes_10)), percentages, color='lightcoral', edgecolor='darkred', alpha=0.7)
    ax2.set_title('Top 10 Phonemes (Percentage)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Phonemes (ARPAbet)')
    ax2.set_ylabel('Percentage (%)')
    ax2.set_xticks(range(len(phonemes_10)))
    ax2.set_xticklabels(phonemes_10, rotation=45, ha='right')
    ax2.grid(axis='y', alpha=0.3)
    
    # Add percentage labels on bars
    for i, pct in enumerate(percentages):
        ax2.text(i, pct + 0.1, f'{pct:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    # Chart 3: Phoneme types distribution
    type_counts = {}
    for phoneme, count in phoneme_data:
        if phoneme in PHONEME_INFO:
            ptype = PHONEME_INFO[phoneme]['type']
            type_counts[ptype] = type_counts.get(ptype, 0) + count
    
    types, type_counts_list = zip(*sorted(type_counts.items(), key=lambda x: x[1], reverse=True))
    colors = plt.cm.Set3(range(len(types)))
    
    wedges, texts, autotexts = ax3.pie(type_counts_list, labels=types, autopct='%1.1f%%', 
                                      colors=colors, startangle=90)
    ax3.set_title('Distribution by Phoneme Type', fontsize=14, fontweight='bold')
    
    # Chart 4: Cumulative frequency
    cumulative = []
    running_total = 0
    for _, count in phoneme_data[:20]:  # Top 20 for clarity
        running_total += count
        cumulative.append(running_total / total_phonemes * 100)
    
    ax4.plot(range(1, len(cumulative) + 1), cumulative, 'o-', linewidth=2, markersize=6, color='green')
    ax4.set_title('Cumulative Frequency (Top 20)', fontsize=14, fontweight='bold')
    ax4.set_xlabel('Phoneme Rank')
    ax4.set_ylabel('Cumulative Percentage (%)')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(1, len(cumulative))
    ax4.set_ylim(0, max(cumulative) + 5)
    
    plt.tight_layout()
    plt.savefig('enhanced_phoneme_analysis.png', dpi=300, bbox_inches='tight')
    print("Enhanced visualization saved as 'enhanced_phoneme_analysis.png'")

def main():
    """Main function for enhanced phoneme analysis."""
    print("Enhanced Phoneme Distribution Analysis")
    print("="*50)
    
    # Run analysis
    phoneme_data, total_phonemes, file_paths = run_analysis()
    
    # Generate detailed report
    report_file = generate_detailed_report(phoneme_data, total_phonemes, file_paths)
    print(f"Detailed report saved as: {report_file}")
    
    # Create enhanced visualization
    create_enhanced_visualization(phoneme_data, total_phonemes)
    
    print(f"\nAnalysis complete!")
    print(f"- Total phonemes analyzed: {total_phonemes:,}")
    print(f"- Unique phonemes found: {len(phoneme_data)}")
    print(f"- Files processed: {len(file_paths)}")

if __name__ == "__main__":
    main()
