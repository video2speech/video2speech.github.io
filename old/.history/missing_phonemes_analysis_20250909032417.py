#!/usr/bin/env python3
"""
分析缺少的音素 - 找出44个标准英语音素中哪些没有在文档中出现
"""

import phoneme_analysis as pa

# 标准的44个英语音素 (完整版)
STANDARD_44_PHONEMES = {
    # 元音 (15个单元音 + 5个双元音 = 20个)
    'AA',  # father [ɑ]
    'AE',  # cat [æ] 
    'AH',  # cut [ʌ]
    'AO',  # caught [ɔ]
    'EH',  # red [ɛ]
    'ER',  # her [ɝ]
    'IH',  # hit [ɪ]
    'IY',  # see [i]
    'UH',  # put [ʊ]
    'UW',  # too [u]
    'AW',  # how [aʊ] (双元音)
    'AY',  # hide [aɪ] (双元音)
    'EY',  # say [eɪ] (双元音)
    'OW',  # show [oʊ] (双元音)
    'OY',  # toy [ɔɪ] (双元音)
    
    # 辅音 (24个)
    'B',   # be [b]
    'CH',  # cheese [tʃ]
    'D',   # dee [d]
    'DH',  # thee [ð]
    'F',   # fee [f]
    'G',   # green [g]
    'HH',  # he [h]
    'JH',  # gee [dʒ]
    'K',   # key [k]
    'L',   # lee [l]
    'M',   # me [m]
    'N',   # knee [n]
    'NG',  # ping [ŋ]
    'P',   # pee [p]
    'R',   # read [r]
    'S',   # sea [s]
    'SH',  # she [ʃ]
    'T',   # tea [t]
    'TH',  # theta [θ]
    'V',   # vee [v]
    'W',   # we [w]
    'Y',   # yield [j]
    'Z',   # zee [z]
    'ZH'   # seizure [ʒ]
}

def analyze_missing_phonemes():
    """分析缺少的音素"""
    print("分析缺少的音素")
    print("="*50)
    
    # 运行原始分析
    file_paths = [
        'materials/50_sentences_list.txt',
        'materials/50_words_list.txt', 
        'materials/150_sentences_list.txt',
        'materials/150_words_list.txt'
    ]
    
    phoneme_data, total_phonemes = pa.analyze_phoneme_distribution(file_paths)
    found_phonemes = set(phoneme for phoneme, _ in phoneme_data)
    
    print(f"标准英语音素总数: {len(STANDARD_44_PHONEMES)}")
    print(f"在文档中找到的音素数: {len(found_phonemes)}")
    print(f"总音素出现次数: {total_phonemes:,}")
    print()
    
    # 找出缺少的音素
    missing_phonemes = STANDARD_44_PHONEMES - found_phonemes
    print(f"缺少的音素 ({len(missing_phonemes)}个):")
    if missing_phonemes:
        for phoneme in sorted(missing_phonemes):
            ipa = pa.ENGLISH_PHONEMES.get(phoneme, phoneme)
            description = get_phoneme_description(phoneme)
            print(f"  {phoneme} [{ipa}] - {description}")
    else:
        print("  没有缺少的音素！")
    
    print()
    
    # 显示找到的音素
    print(f"找到的音素 ({len(found_phonemes)}个):")
    found_list = [(p, c) for p, c in phoneme_data]
    for phoneme, count in found_list:
        if phoneme in STANDARD_44_PHONEMES:
            ipa = pa.ENGLISH_PHONEMES.get(phoneme, phoneme)
            percentage = count / total_phonemes * 100
            print(f"  {phoneme} [{ipa}]: {count:,} ({percentage:.2f}%)")
        else:
            print(f"  {phoneme} [未知]: {count:,} (非标准音素)")
    
    print()
    
    # 分析为什么缺少这些音素
    analyze_why_missing(missing_phonemes)
    
    return missing_phonemes, found_phonemes

def get_phoneme_description(phoneme):
    """获取音素描述"""
    descriptions = {
        'AA': '低后不圆唇元音 (father)',
        'AE': '低前不圆唇元音 (cat)', 
        'AH': '中央不圆唇元音 (cut)',
        'AO': '低后圆唇元音 (caught)',
        'AW': '双元音 (how)',
        'AY': '双元音 (hide)',
        'EH': '中前不圆唇元音 (red)',
        'ER': '中央R音化元音 (her)',
        'EY': '双元音 (say)',
        'IH': '高前松元音 (hit)',
        'IY': '高前紧元音 (see)',
        'OW': '双元音 (show)',
        'OY': '双元音 (toy)',
        'UH': '高后松元音 (put)',
        'UW': '高后紧元音 (too)',
        'B': '浊双唇塞音 (be)',
        'CH': '清后齿龈塞擦音 (cheese)',
        'D': '浊齿龈塞音 (dee)',
        'DH': '浊齿间擦音 (thee)',
        'F': '清唇齿擦音 (fee)',
        'G': '浊软腭塞音 (green)',
        'HH': '清声门擦音 (he)',
        'JH': '浊后齿龈塞擦音 (gee)',
        'K': '清软腭塞音 (key)',
        'L': '侧音 (lee)',
        'M': '双唇鼻音 (me)',
        'N': '齿龈鼻音 (knee)',
        'NG': '软腭鼻音 (ping)',
        'P': '清双唇塞音 (pee)',
        'R': '卷舌近音 (read)',
        'S': '清齿龈擦音 (sea)',
        'SH': '清后齿龈擦音 (she)',
        'T': '清齿龈塞音 (tea)',
        'TH': '清齿间擦音 (theta)',
        'V': '浊唇齿擦音 (vee)',
        'W': '唇软腭近音 (we)',
        'Y': '硬腭近音 (yield)',
        'Z': '浊齿龈擦音 (zee)',
        'ZH': '浊后齿龈擦音 (seizure)'
    }
    return descriptions.get(phoneme, '未知音素')

def analyze_why_missing(missing_phonemes):
    """分析为什么缺少这些音素"""
    print("缺少音素的可能原因分析:")
    print("-" * 30)
    
    # 检查词汇映射表中是否包含这些音素
    all_mapped_phonemes = set()
    for word, phonemes in pa.WORD_TO_PHONEMES.items():
        all_mapped_phonemes.update(phonemes)
    
    missing_from_mapping = missing_phonemes - all_mapped_phonemes
    
    if missing_from_mapping:
        print(f"1. 词汇映射表中完全缺少的音素 ({len(missing_from_mapping)}个):")
        for phoneme in sorted(missing_from_mapping):
            description = get_phoneme_description(phoneme)
            print(f"   {phoneme} - {description}")
        print("   → 需要添加包含这些音素的单词到映射表中")
        print()
    
    # 检查哪些音素在映射表中存在但在文档中没有出现
    in_mapping_but_missing = missing_phonemes & all_mapped_phonemes
    if in_mapping_but_missing:
        print(f"2. 映射表中存在但文档中没有相关单词的音素 ({len(in_mapping_but_missing)}个):")
        for phoneme in sorted(in_mapping_but_missing):
            # 找出包含此音素的单词
            words_with_phoneme = [word for word, phonemes in pa.WORD_TO_PHONEMES.items() 
                                if phoneme in phonemes]
            description = get_phoneme_description(phoneme)
            print(f"   {phoneme} - {description}")
            print(f"      包含此音素的映射单词: {', '.join(words_with_phoneme[:5])}")
        print("   → 这些单词可能没有在分析的文档中出现")
        print()
    
    # 建议改进措施
    print("改进建议:")
    print("1. 扩展词汇映射表，添加更多包含缺少音素的常见单词")
    print("2. 改进音素近似算法，更好地处理未知单词")
    print("3. 使用完整的CMU发音词典进行更准确的音素转换")
    print("4. 检查文档内容是否足够丰富以覆盖所有音素")

def suggest_missing_words():
    """建议包含缺少音素的单词"""
    print("\n建议添加的单词 (包含缺少的音素):")
    print("-" * 40)
    
    suggestions = {
        'OY': ['boy', 'toy', 'joy', 'coin', 'voice'],
        'ZH': ['measure', 'pleasure', 'vision', 'decision', 'television'],
        'NG': ['sing', 'ring', 'thing', 'young', 'long'],
        'CH': ['chair', 'teach', 'watch', 'much', 'which'],
        'JH': ['judge', 'large', 'bridge', 'age', 'page'],
        'SH': ['ship', 'wash', 'fish', 'wish', 'push'],
        'TH': ['think', 'three', 'month', 'both', 'nothing'],
        'UH': ['book', 'look', 'good', 'could', 'should'],
        'ER': ['first', 'word', 'work', 'learn', 'turn'],
        'AW': ['house', 'about', 'down', 'town', 'sound'],
        'OW': ['home', 'phone', 'note', 'boat', 'coat'],
        'EY': ['day', 'say', 'way', 'play', 'name']
    }
    
    for phoneme, words in suggestions.items():
        ipa = pa.ENGLISH_PHONEMES.get(phoneme, phoneme)
        print(f"{phoneme} [{ipa}]: {', '.join(words)}")

if __name__ == "__main__":
    missing, found = analyze_missing_phonemes()
    suggest_missing_words()
    
    print(f"\n总结:")
    print(f"- 标准英语音素: 44个")
    print(f"- 找到的音素: {len(found)}个")
    print(f"- 缺少的音素: {len(missing)}个")
    print(f"- 覆盖率: {len(found)/44*100:.1f}%")
