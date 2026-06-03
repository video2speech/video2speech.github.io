#!/usr/bin/env python3
"""
找到覆盖所有44个英语音素的最小词汇集合
从 materials/2_2_spokenvwritten.txt 中的高频词开始
"""

import re
from collections import Counter

# 完整的44个英语音素 (基于CMU ARPAbet标准)
ALL_44_PHONEMES = {
    # 单元音 (12个)
    'IY', 'IH', 'EH', 'AE', 'AA', 'AO', 'UH', 'UW', 'AH', 'ER', 'AX', 'IX',
    # 双元音 (8个)
    'EY', 'AY', 'OW', 'AW', 'OY', 'IA', 'EA', 'UA',
    # 辅音 (24个)
    'P', 'B', 'T', 'D', 'K', 'G', 'F', 'V', 'TH', 'DH', 'S', 'Z',
    'SH', 'ZH', 'HH', 'M', 'N', 'NG', 'L', 'R', 'W', 'Y', 'CH', 'JH'
}

# 扩展的词汇到音素映射表 (包含更多高频词)
COMPREHENSIVE_WORD_TO_PHONEMES = {
    # 高频词
    'the': ['DH', 'AH'],
    'i': ['AY'],
    'you': ['Y', 'UW'],
    'and': ['AH', 'N', 'D'],
    'it': ['IH', 'T'],
    'a': ['AH'],
    'to': ['T', 'UW'],
    'of': ['AH', 'V'],
    'that': ['DH', 'AE', 'T'],
    'in': ['IH', 'N'],
    'we': ['W', 'IY'],
    'is': ['IH', 'Z'],
    'do': ['D', 'UW'],
    'they': ['DH', 'EY'],
    'was': ['W', 'AH', 'Z'],
    'have': ['HH', 'AE', 'V'],
    'what': ['W', 'AH', 'T'],
    'he': ['HH', 'IY'],
    'but': ['B', 'AH', 'T'],
    'for': ['F', 'AO', 'R'],
    'be': ['B', 'IY'],
    'on': ['AO', 'N'],
    'this': ['DH', 'IH', 'S'],
    'know': ['N', 'OW'],
    'well': ['W', 'EH', 'L'],
    'so': ['S', 'OW'],
    'got': ['G', 'AO', 'T'],
    'not': ['N', 'AO', 'T'],
    'are': ['AA', 'R'],
    'if': ['IH', 'F'],
    'with': ['W', 'IH', 'TH'],
    'no': ['N', 'OW'],
    'she': ['SH', 'IY'],
    'at': ['AE', 'T'],
    'there': ['DH', 'EH', 'R'],
    'think': ['TH', 'IH', 'NG', 'K'],
    'yes': ['Y', 'EH', 'S'],
    'just': ['JH', 'AH', 'S', 'T'],
    'all': ['AO', 'L'],
    'can': ['K', 'AE', 'N'],
    'then': ['DH', 'EH', 'N'],
    'get': ['G', 'EH', 'T'],
    'did': ['D', 'IH', 'D'],
    'or': ['AO', 'R'],
    'would': ['W', 'UH', 'D'],
    'them': ['DH', 'EH', 'M'],
    'one': ['W', 'AH', 'N'],
    'up': ['AH', 'P'],
    'go': ['G', 'OW'],
    'now': ['N', 'AW'],
    'your': ['Y', 'UH', 'R'],
    'had': ['HH', 'AE', 'D'],
    'were': ['W', 'ER'],
    'about': ['AH', 'B', 'AW', 'T'],
    'two': ['T', 'UW'],
    'said': ['S', 'EH', 'D'],
    'see': ['S', 'IY'],
    'me': ['M', 'IY'],
    'very': ['V', 'EH', 'R', 'IY'],
    'out': ['AW', 'T'],
    'my': ['M', 'AY'],
    'when': ['W', 'EH', 'N'],
    'mean': ['M', 'IY', 'N'],
    'right': ['R', 'AY', 'T'],
    'from': ['F', 'R', 'AH', 'M'],
    'going': ['G', 'OW', 'IH', 'NG'],
    'say': ['S', 'EY'],
    'been': ['B', 'IH', 'N'],
    'people': ['P', 'IY', 'P', 'AH', 'L'],
    'because': ['B', 'IH', 'K', 'AO', 'Z'],
    'some': ['S', 'AH', 'M'],
    'could': ['K', 'UH', 'D'],
    'will': ['W', 'IH', 'L'],
    'how': ['HH', 'AW'],
    'time': ['T', 'AY', 'M'],
    'who': ['HH', 'UW'],
    'want': ['W', 'AO', 'N', 'T'],
    'like': ['L', 'AY', 'K'],
    'come': ['K', 'AH', 'M'],
    'really': ['R', 'IY', 'L', 'IY'],
    'here': ['HH', 'IA', 'R'],  # 包含 IA 音素
    'put': ['P', 'UH', 'T'],
    'good': ['G', 'UH', 'D'],
    'as': ['AE', 'Z'],
    'does': ['D', 'AH', 'Z'],
    'any': ['EH', 'N', 'IY'],
    'down': ['D', 'AW', 'N'],
    'where': ['W', 'EA', 'R'],  # 包含 EA 音素
    'him': ['HH', 'IH', 'M'],
    'other': ['AH', 'DH', 'ER'],
    'something': ['S', 'AH', 'M', 'TH', 'IH', 'NG'],
    'these': ['DH', 'IY', 'Z'],
    'way': ['W', 'EY'],
    'back': ['B', 'AE', 'K'],
    'should': ['SH', 'UH', 'D'],
    'take': ['T', 'EY', 'K'],
    'thing': ['TH', 'IH', 'NG'],
    'look': ['L', 'UH', 'K'],
    'why': ['W', 'AY'],
    'things': ['TH', 'IH', 'NG', 'Z'],
    'only': ['OW', 'N', 'L', 'IY'],
    'us': ['AH', 'S'],
    'lot': ['L', 'AO', 'T'],
    'make': ['M', 'EY', 'K'],
    'first': ['F', 'ER', 'S', 'T'],
    'more': ['M', 'AO', 'R'],
    'doing': ['D', 'UW', 'IH', 'NG'],
    'done': ['D', 'AH', 'N'],
    'am': ['AE', 'M'],
    'bad': ['B', 'AE', 'D'],
    'coming': ['K', 'AH', 'M', 'IH', 'NG'],
    'feel': ['F', 'IY', 'L'],
    'help': ['HH', 'EH', 'L', 'P'],
    'hope': ['HH', 'OW', 'P'],
    'need': ['N', 'IY', 'D'],
    'please': ['P', 'L', 'IY', 'Z'],
    'tell': ['T', 'EH', 'L'],
    'give': ['G', 'IH', 'V'],
    'thought': ['TH', 'AO', 'T'],
    'again': ['AH', 'G', 'EH', 'N'],
    'might': ['M', 'AY', 'T'],
    'her': ['HH', 'ER'],
    'last': ['L', 'AE', 'S', 'T'],
    'much': ['M', 'AH', 'CH'],
    'still': ['S', 'T', 'IH', 'L'],
    'never': ['N', 'EH', 'V', 'ER'],
    'than': ['DH', 'AE', 'N'],
    'same': ['S', 'EY', 'M'],
    'another': ['AH', 'N', 'AH', 'DH', 'ER'],
    'money': ['M', 'AH', 'N', 'IY'],
    'anything': ['EH', 'N', 'IY', 'TH', 'IH', 'NG'],
    'thank': ['TH', 'AE', 'NG', 'K'],
    'too': ['T', 'UW'],
    'nice': ['N', 'AY', 'S'],
    'work': ['W', 'ER', 'K'],
    'always': ['AO', 'L', 'W', 'EY', 'Z'],
    'years': ['Y', 'IH', 'R', 'Z'],
    'through': ['TH', 'R', 'UW'],
    'little': ['L', 'IH', 'T', 'AH', 'L'],
    'house': ['HH', 'AW', 'S'],
    'home': ['HH', 'OW', 'M'],
    'school': ['S', 'K', 'UW', 'L'],
    'life': ['L', 'AY', 'F'],
    'hand': ['HH', 'AE', 'N', 'D'],
    'part': ['P', 'AA', 'R', 'T'],
    'child': ['CH', 'AY', 'L', 'D'],
    'eye': ['AY'],
    'woman': ['W', 'UH', 'M', 'AH', 'N'],
    'man': ['M', 'AE', 'N'],
    'year': ['Y', 'IH', 'R'],
    'government': ['G', 'AH', 'V', 'ER', 'N', 'M', 'AH', 'N', 'T'],
    'company': ['K', 'AH', 'M', 'P', 'AH', 'N', 'IY'],
    'system': ['S', 'IH', 'S', 'T', 'AH', 'M'],
    'program': ['P', 'R', 'OW', 'G', 'R', 'AE', 'M'],
    'question': ['K', 'W', 'EH', 'S', 'CH', 'AH', 'N'],
    'number': ['N', 'AH', 'M', 'B', 'ER'],
    'public': ['P', 'AH', 'B', 'L', 'IH', 'K'],
    'new': ['N', 'UW'],
    'old': ['OW', 'L', 'D'],
    'great': ['G', 'R', 'EY', 'T'],
    'small': ['S', 'M', 'AO', 'L'],
    'large': ['L', 'AA', 'R', 'JH'],
    'national': ['N', 'AE', 'SH', 'AH', 'N', 'AH', 'L'],
    'local': ['L', 'OW', 'K', 'AH', 'L'],
    'long': ['L', 'AO', 'NG'],
    'high': ['HH', 'AY'],
    'different': ['D', 'IH', 'F', 'ER', 'AH', 'N', 'T'],
    'important': ['IH', 'M', 'P', 'AO', 'R', 'T', 'AH', 'N', 'T'],
    'early': ['ER', 'L', 'IY'],
    'young': ['Y', 'AH', 'NG'],
    
    # 特殊音素的词汇
    'boy': ['B', 'OY'],  # OY 音素
    'toy': ['T', 'OY'],  # OY 音素
    'joy': ['JH', 'OY'],  # OY 音素
    'voice': ['V', 'OY', 'S'],  # OY 音素
    'choice': ['CH', 'OY', 'S'],  # OY 音素
    'measure': ['M', 'EH', 'ZH', 'ER'],  # ZH 音素
    'pleasure': ['P', 'L', 'EH', 'ZH', 'ER'],  # ZH 音素
    'vision': ['V', 'IH', 'ZH', 'AH', 'N'],  # ZH 音素
    'decision': ['D', 'IH', 'S', 'IH', 'ZH', 'AH', 'N'],  # ZH 音素
    'television': ['T', 'EH', 'L', 'AH', 'V', 'IH', 'ZH', 'AH', 'N'],  # ZH 音素
    'roses': ['R', 'OW', 'Z', 'IX', 'Z'],  # IX 音素
    'horses': ['HH', 'AO', 'R', 'S', 'IX', 'Z'],  # IX 音素
    'boxes': ['B', 'AO', 'K', 'S', 'IX', 'Z'],  # IX 音素
    'sofa': ['S', 'OW', 'F', 'AX'],  # AX 音素
    'china': ['CH', 'AY', 'N', 'AX'],  # AX 音素
    'comma': ['K', 'AO', 'M', 'AX'],  # AX 音素
    'near': ['N', 'IA', 'R'],  # IA 音素
    'dear': ['D', 'IA', 'R'],  # IA 音素
    'clear': ['K', 'L', 'IA', 'R'],  # IA 音素
    'hair': ['HH', 'EA', 'R'],  # EA 音素
    'care': ['K', 'EA', 'R'],  # EA 音素
    'share': ['SH', 'EA', 'R'],  # EA 音素
    'poor': ['P', 'UA', 'R'],  # UA 音素
    'sure': ['SH', 'UA', 'R'],  # UA 音素
    'tour': ['T', 'UA', 'R'],  # UA 音素
}

def read_word_frequency_file(filename):
    """读取词频文件并返回按频率排序的词汇列表"""
    words_with_freq = []
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines[2:]:  # 跳过头两行
        line = line.strip()
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) >= 3:
            word = parts[1].lower().strip()  # 第二列是单词
            try:
                freq = int(parts[3])  # 第四列是频率 (FrSp)
                if word and len(word) > 0:  # 确保单词不为空
                    words_with_freq.append((word, freq))
            except (ValueError, IndexError):
                continue
    
    # 按频率降序排序
    words_with_freq.sort(key=lambda x: x[1], reverse=True)
    return words_with_freq

def get_word_phonemes(word):
    """获取单词的音素"""
    # 清理单词
    clean_word = re.sub(r"[^\w']", '', word.lower())
    
    if clean_word in COMPREHENSIVE_WORD_TO_PHONEMES:
        return COMPREHENSIVE_WORD_TO_PHONEMES[clean_word]
    else:
        # 简单的近似映射
        return approximate_phonemes(clean_word)

def approximate_phonemes(word):
    """简单的音素近似算法"""
    phonemes = []
    i = 0
    while i < len(word):
        char = word[i]
        
        # 处理常见字母组合
        if i < len(word) - 1:
            two_char = word[i:i+2]
            if two_char == 'th':
                phonemes.append('TH' if i == 0 or word[i-1] not in 'aeiou' else 'DH')
                i += 2
                continue
            elif two_char == 'sh':
                phonemes.append('SH')
                i += 2
                continue
            elif two_char == 'ch':
                phonemes.append('CH')
                i += 2
                continue
            elif two_char == 'ng':
                phonemes.append('NG')
                i += 2
                continue
            elif two_char == 'oy':
                phonemes.append('OY')
                i += 2
                continue
        
        # 单字符映射
        char_to_phoneme = {
            'a': 'AE', 'e': 'EH', 'i': 'IH', 'o': 'AO', 'u': 'AH',
            'b': 'B', 'c': 'K', 'd': 'D', 'f': 'F', 'g': 'G',
            'h': 'HH', 'j': 'JH', 'k': 'K', 'l': 'L', 'm': 'M',
            'n': 'N', 'p': 'P', 'r': 'R', 's': 'S', 't': 'T',
            'v': 'V', 'w': 'W', 'y': 'Y', 'z': 'Z'
        }
        
        if char in char_to_phoneme:
            phonemes.append(char_to_phoneme[char])
        
        i += 1
    
    return phonemes

def find_minimal_coverage(words_with_freq):
    """找到覆盖所有44个音素的最小词汇集合"""
    covered_phonemes = set()
    selected_words = []
    phoneme_to_words = {}  # 记录每个音素首次出现的单词
    unique_phoneme_words = {}  # 记录只在一个单词中出现的音素
    
    print("正在分析词汇覆盖情况...")
    print("="*60)
    
    for i, (word, freq) in enumerate(words_with_freq):
        if len(covered_phonemes) >= 44:  # 已经覆盖所有音素
            break
            
        phonemes = get_word_phonemes(word)
        new_phonemes = set(phonemes) & ALL_44_PHONEMES - covered_phonemes
        
        if new_phonemes:  # 如果这个词包含新的音素
            selected_words.append((word, freq, phonemes, new_phonemes))
            covered_phonemes.update(new_phonemes)
            
            # 记录音素首次出现的单词
            for phoneme in new_phonemes:
                if phoneme not in phoneme_to_words:
                    phoneme_to_words[phoneme] = word
            
            print(f"第{i+1:3d}词: {word:<15} (频率:{freq:>6}) -> 新音素: {sorted(new_phonemes)}")
            print(f"      音素: {phonemes}")
            print(f"      已覆盖: {len(covered_phonemes)}/44 音素")
            print()
    
    # 检查哪些音素只在一个单词中出现
    phoneme_count = {}
    for word, freq, phonemes, new_phonemes in selected_words:
        for phoneme in phonemes:
            if phoneme in ALL_44_PHONEMES:
                if phoneme not in phoneme_count:
                    phoneme_count[phoneme] = []
                phoneme_count[phoneme].append(word)
    
    for phoneme, words in phoneme_count.items():
        if len(words) == 1:
            unique_phoneme_words[phoneme] = words[0]
    
    return selected_words, covered_phonemes, phoneme_to_words, unique_phoneme_words

def main():
    """主函数"""
    print("寻找覆盖所有44个英语音素的最小高频词汇集合")
    print("="*60)
    
    # 读取词频文件
    filename = 'materials/2_2_spokenvwritten.txt'
    words_with_freq = read_word_frequency_file(filename)
    print(f"从 {filename} 读取了 {len(words_with_freq)} 个词汇")
    print()
    
    # 找到最小覆盖集合
    selected_words, covered_phonemes, phoneme_to_words, unique_phoneme_words = find_minimal_coverage(words_with_freq)
    
    print("="*60)
    print("最终结果")
    print("="*60)
    
    print(f"总共需要 {len(selected_words)} 个高频词来覆盖所有44个英语音素")
    print(f"覆盖的音素数量: {len(covered_phonemes)}/44")
    print()
    
    if len(covered_phonemes) < 44:
        missing = ALL_44_PHONEMES - covered_phonemes
        print(f"仍然缺少的音素: {sorted(missing)}")
        print()
    
    print("最终词汇列表 (按添加顺序):")
    print("-" * 60)
    
    # 去重并保持顺序
    seen_words = set()
    final_words = []
    for word, freq, phonemes, new_phonemes in selected_words:
        if word not in seen_words:
            seen_words.add(word)
            final_words.append((word, freq, phonemes, new_phonemes))
    
    for i, (word, freq, phonemes, new_phonemes) in enumerate(final_words, 1):
        unique_markers = []
        for phoneme in phonemes:
            if phoneme in unique_phoneme_words and unique_phoneme_words[phoneme] == word:
                unique_markers.append(f"{phoneme}*")
        
        unique_str = f" [独有: {', '.join(unique_markers)}]" if unique_markers else ""
        
        print(f"{i:2d}. {word:<15} (频率:{freq:>6}) -> {phonemes}{unique_str}")
    
    print()
    print("标记说明:")
    print("* = 该音素只在这个单词中出现 (单一表示)")
    print()
    
    print("音素覆盖详情:")
    print("-" * 40)
    for phoneme in sorted(ALL_44_PHONEMES):
        if phoneme in phoneme_to_words:
            marker = "*" if phoneme in unique_phoneme_words else ""
            print(f"{phoneme:<3} -> {phoneme_to_words[phoneme]}{marker}")
        else:
            print(f"{phoneme:<3} -> 未覆盖")

if __name__ == "__main__":
    main()
