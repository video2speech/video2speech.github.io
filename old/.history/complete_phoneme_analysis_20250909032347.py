#!/usr/bin/env python3
"""
完整的44个英语音素分析 - 基于CMU ARPAbet标准
"""

import phoneme_analysis as pa

# 完整的44个英语音素 (基于CMU ARPAbet标准)
COMPLETE_44_PHONEMES = {
    # 元音 (15个单元音)
    'AA',  # odd [ɑ] - low back unrounded vowel
    'AE',  # at [æ] - low front unrounded vowel  
    'AH',  # hut [ʌ] - mid central unrounded vowel
    'AO',  # ought [ɔ] - low back rounded vowel
    'EH',  # Ed [ɛ] - mid front unrounded vowel
    'ER',  # hurt [ɝ] - mid central r-colored vowel
    'IH',  # it [ɪ] - high front lax vowel
    'IY',  # eat [i] - high front tense vowel
    'UH',  # hood [ʊ] - high back lax vowel
    'UW',  # two [u] - high back tense vowel
    
    # 双元音 (5个)
    'AW',  # how [aʊ] - low front to high back
    'AY',  # hide [aɪ] - low front to high front
    'EY',  # say [eɪ] - mid front to high front
    'OW',  # show [oʊ] - mid back to high back
    'OY',  # toy [ɔɪ] - low back to high front
    
    # 辅音 (24个)
    'B',   # be [b] - voiced bilabial stop
    'CH',  # cheese [tʃ] - voiceless postalveolar affricate
    'D',   # dee [d] - voiced alveolar stop
    'DH',  # thee [ð] - voiced dental fricative
    'F',   # fee [f] - voiceless labiodental fricative
    'G',   # green [g] - voiced velar stop
    'HH',  # he [h] - voiceless glottal fricative
    'JH',  # gee [dʒ] - voiced postalveolar affricate
    'K',   # key [k] - voiceless velar stop
    'L',   # lee [l] - lateral approximant
    'M',   # me [m] - bilabial nasal
    'N',   # knee [n] - alveolar nasal
    'NG',  # ping [ŋ] - velar nasal
    'P',   # pee [p] - voiceless bilabial stop
    'R',   # read [r] - retroflex approximant
    'S',   # sea [s] - voiceless alveolar fricative
    'SH',  # she [ʃ] - voiceless postalveolar fricative
    'T',   # tea [t] - voiceless alveolar stop
    'TH',  # theta [θ] - voiceless dental fricative
    'V',   # vee [v] - voiced labiodental fricative
    'W',   # we [w] - labial-velar approximant
    'Y',   # yield [j] - palatal approximant
    'Z',   # zee [z] - voiced alveolar fricative
    'ZH'   # seizure [ʒ] - voiced postalveolar fricative
}

def detailed_missing_analysis():
    """详细分析缺少的音素"""
    print("完整的44个英语音素分析")
    print("="*60)
    
    # 运行分析
    file_paths = [
        'materials/50_sentences_list.txt',
        'materials/50_words_list.txt', 
        'materials/150_sentences_list.txt',
        'materials/150_words_list.txt'
    ]
    
    phoneme_data, total_phonemes = pa.analyze_phoneme_distribution(file_paths)
    found_phonemes = set(phoneme for phoneme, _ in phoneme_data)
    
    print(f"标准英语音素总数: {len(COMPLETE_44_PHONEMES)} (44个)")
    print(f"在文档中找到的音素数: {len(found_phonemes)}")
    print(f"总音素出现次数: {total_phonemes:,}")
    print(f"覆盖率: {len(found_phonemes)/len(COMPLETE_44_PHONEMES)*100:.1f}%")
    print()
    
    # 找出缺少的音素
    missing_phonemes = COMPLETE_44_PHONEMES - found_phonemes
    print(f"缺少的音素 ({len(missing_phonemes)}个):")
    if missing_phonemes:
        for phoneme in sorted(missing_phonemes):
            ipa = pa.ENGLISH_PHONEMES.get(phoneme, phoneme)
            print(f"  {phoneme} [{ipa}] - {get_phoneme_example(phoneme)}")
    else:
        print("  恭喜！找到了所有44个标准英语音素！")
    
    print()
    
    # 检查是否有非标准音素
    extra_phonemes = found_phonemes - COMPLETE_44_PHONEMES
    if extra_phonemes:
        print(f"发现的非标准音素 ({len(extra_phonemes)}个):")
        for phoneme in sorted(extra_phonemes):
            count = next(count for p, count in phoneme_data if p == phoneme)
            print(f"  {phoneme}: {count:,} 次 (可能是映射错误)")
        print()
    
    # 显示找到的标准音素
    found_standard = found_phonemes & COMPLETE_44_PHONEMES
    print(f"找到的标准音素 ({len(found_standard)}个):")
    found_data = [(p, c) for p, c in phoneme_data if p in COMPLETE_44_PHONEMES]
    found_data.sort(key=lambda x: x[1], reverse=True)
    
    for i, (phoneme, count) in enumerate(found_data, 1):
        percentage = count / total_phonemes * 100
        ipa = pa.ENGLISH_PHONEMES.get(phoneme, phoneme)
        print(f"  {i:2d}. {phoneme} [{ipa}]: {count:,} ({percentage:.2f}%)")
    
    return missing_phonemes, found_standard

def get_phoneme_example(phoneme):
    """获取音素的例词"""
    examples = {
        'AA': 'father, hot, lot',
        'AE': 'cat, bat, had', 
        'AH': 'cut, but, love',
        'AO': 'caught, law, saw',
        'EH': 'red, bed, head',
        'ER': 'her, bird, word',
        'IH': 'hit, bit, sit',
        'IY': 'see, eat, beat',
        'UH': 'put, book, good',
        'UW': 'too, blue, food',
        'AW': 'how, now, cow',
        'AY': 'hide, my, pie',
        'EY': 'say, day, make',
        'OW': 'show, go, boat',
        'OY': 'toy, boy, coin',
        'B': 'be, cab, about',
        'CH': 'cheese, watch, nature',
        'D': 'dee, had, do',
        'DH': 'thee, this, bathe',
        'F': 'fee, if, phone',
        'G': 'green, big, dog',
        'HH': 'he, house, who',
        'JH': 'gee, large, gym',
        'K': 'key, make, school',
        'L': 'lee, all, play',
        'M': 'me, some, time',
        'N': 'knee, in, know',
        'NG': 'ping, sing, think',
        'P': 'pee, happy, stop',
        'R': 'read, very, try',
        'S': 'sea, pass, city',
        'SH': 'she, wash, sure',
        'T': 'tea, it, stop',
        'TH': 'theta, think, both',
        'V': 'vee, have, very',
        'W': 'we, away, queen',
        'Y': 'yield, yes, use',
        'Z': 'zee, has, zero',
        'ZH': 'seizure, measure, vision'
    }
    return examples.get(phoneme, '未知例词')

def suggest_improvements():
    """建议改进措施"""
    print("\n改进建议:")
    print("-" * 40)
    print("1. 扩展词汇映射表:")
    print("   - 添加包含 OY 音素的词: boy, toy, joy, voice, choice")
    print("   - 添加包含 ZH 音素的词: measure, pleasure, vision, decision")
    print()
    print("2. 改进近似算法:")
    print("   - 更好地处理字母组合 'oy' -> OY")
    print("   - 识别 's' 在某些词中的 ZH 音素 (measure)")
    print()
    print("3. 使用更完整的发音词典:")
    print("   - 考虑使用 CMU Pronouncing Dictionary")
    print("   - 或者 NLTK 的音素转换工具")

if __name__ == "__main__":
    missing, found = detailed_missing_analysis()
    suggest_improvements()
    
    print(f"\n最终总结:")
    print(f"✓ 找到音素: {len(found)}/44")
    print(f"✗ 缺少音素: {len(missing)}/44") 
    print(f"📊 覆盖率: {len(found)/44*100:.1f}%")
    
    if len(missing) <= 2:
        print("🎉 覆盖率很高！只需要少量改进。")
    elif len(missing) <= 5:
        print("👍 覆盖率不错，需要一些改进。")
    else:
        print("⚠️  需要大幅改进音素映射。")
