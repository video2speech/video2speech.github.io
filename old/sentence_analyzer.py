#!/usr/bin/env python3
"""
交互式句子分析器 - 统计词频和音素频率
Interactive Sentence Analyzer - Word and Phoneme Frequency Analysis
"""

import nltk
import re
import json
import os
import string
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    nltk.download('cmudict')

from nltk.corpus import cmudict

class SentenceAnalyzer:
    def __init__(self):
        self.cmu_dict = cmudict.dict()
        self.selected_sentences = []
        self.save_file = "selected_sentences_analyzer.json"
        
        # 标准39个英语音素 (ARPAbet格式)
        self.standard_phonemes = {
            # 元音 (15个)
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
            # 辅音 (24个)
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
        
        # 加载目标词汇集
        self.pick_words = self.load_pick_words()
        
        self.load_selected_sentences()
    
    def load_pick_words(self):
        """加载selected_words.json中的词汇"""
        pick_words = set()
        try:
            with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/selected_words.json', 'r', encoding='utf-8') as f:
                words_list = json.load(f)
                for word in words_list:
                    if word.strip():
                        pick_words.add(word.strip().lower())
        except FileNotFoundError:
            print("❌ 未找到 selected_words.json 文件")
        except json.JSONDecodeError:
            print("❌ selected_words.json 文件格式错误")
        return pick_words
    
    def clean_phoneme(self, phoneme):
        """移除音素的重音标记"""
        return re.sub(r'\d', '', phoneme)
    
    def get_word_phonemes(self, word):
        """获取词汇对应的音素"""
        # 处理缩写
        word_clean = word.lower().replace("'", "")
        
        contraction_map = {
            "nt": "not", "s": "is", "ve": "have", "re": "are", 
            "ll": "will", "d": "would", "m": "am", "em": "them"
        }
        
        if word.startswith("'") and len(word) > 1:
            contraction_part = word[1:].lower()
            if contraction_part in contraction_map:
                word_clean = contraction_map[contraction_part]
        
        # 尝试不同的词汇变形
        for test_word in [word_clean, word.lower(), re.sub(r'[^\w]', '', word.lower())]:
            if test_word in self.cmu_dict:
                phonemes = self.cmu_dict[test_word][0]
                cleaned_phonemes = [self.clean_phoneme(p) for p in phonemes]
                return [p for p in cleaned_phonemes if p in self.standard_phonemes]
        
        return []
    
    def extract_words_from_sentence(self, sentence):
        """从句子中提取单词"""
        # 处理缩写
        sentence = sentence.replace("'t", " not")
        sentence = sentence.replace("'re", " are")  
        sentence = sentence.replace("'ll", " will")
        sentence = sentence.replace("'ve", " have")
        sentence = sentence.replace("'d", " would")
        sentence = sentence.replace("'m", " am")
        sentence = sentence.replace("'s", " is")
        
        # 移除标点符号
        translator = str.maketrans('', '', string.punctuation)
        sentence = sentence.translate(translator)
        
        # 分割单词并转换为小写
        words = sentence.lower().split()
        return words
    
    def save_selected_sentences(self):
        """保存选中的句子到文件"""
        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(self.selected_sentences, f, indent=2, ensure_ascii=False)
    
    def load_selected_sentences(self):
        """从文件加载之前选中的句子"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    self.selected_sentences = json.load(f)
                if self.selected_sentences:
                    print(f"📁 加载了 {len(self.selected_sentences)} 个之前选中的句子")
            except:
                self.selected_sentences = []
        else:
            self.selected_sentences = []
    
    def clean_sentence(self, sentence):
        """清理句子：去除标点符号，保留基本结构，还原大小写"""
        # 去除多余空格
        sentence = sentence.strip()
        
        # 保留缩写中的撇号，但去除其他标点符号
        # 先处理常见缩写
        sentence = re.sub(r'\b(don|won|can|isn|aren|wasn|weren|hasn|haven|hadn|shouldn|wouldn|couldn|didn)\'t\b', r'\1 not', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\b(I|you|we|they)\'re\b', r'\1 are', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\b(I|you|we|they|he|she|it)\'ll\b', r'\1 will', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\b(I|you|we|they|he|she|it)\'ve\b', r'\1 have', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\b(I|you|we|they|he|she|it)\'d\b', r'\1 would', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\bI\'m\b', 'I am', sentence, flags=re.IGNORECASE)
        sentence = re.sub(r'\b(he|she|it)\'s\b', r'\1 is', sentence, flags=re.IGNORECASE)
        
        # 去除剩余的标点符号，但保留空格
        sentence = re.sub(r'[^\w\s]', '', sentence)
        
        # 去除多余空格
        sentence = re.sub(r'\s+', ' ', sentence).strip()
        
        # 还原正确的大小写：句首字母大写，I 大写，其他小写
        if sentence:
            words = sentence.lower().split()
            # 句首字母大写
            if words:
                words[0] = words[0].capitalize()
            # I 总是大写
            for i, word in enumerate(words):
                if word == 'i':
                    words[i] = 'I'
            sentence = ' '.join(words)
        
        return sentence
    
    def add_sentence(self, sentence):
        """添加句子到选中列表"""
        original_sentence = sentence.strip()
        if not original_sentence:
            return False
        
        # 清理句子
        cleaned_sentence = self.clean_sentence(original_sentence)
        if not cleaned_sentence:
            return False
        
        # 检查去重（不考虑大小写）
        cleaned_lower = cleaned_sentence.lower()
        for existing in self.selected_sentences:
            if existing.lower() == cleaned_lower:
                print(f"⚠️  句子已存在: {existing}")
                return False
        
        self.selected_sentences.append(cleaned_sentence)
        self.save_selected_sentences()
        print(f"✅ 添加成功: {cleaned_sentence}")
        if cleaned_sentence != original_sentence:
            print(f"   (原句: {original_sentence})")
        return True
    
    def remove_sentence(self, sentence_or_number):
        """从选中列表移除句子（支持句子内容或编号）"""
        # 尝试按编号删除
        if sentence_or_number.isdigit():
            index = int(sentence_or_number) - 1
            if 0 <= index < len(self.selected_sentences):
                removed_sentence = self.selected_sentences.pop(index)
                self.save_selected_sentences()
                print(f"🗑️  移除成功: #{sentence_or_number} {removed_sentence}")
                return True
            else:
                print(f"❌ 编号无效: {sentence_or_number} (范围: 1-{len(self.selected_sentences)})")
                return False
        
        # 按句子内容删除
        if sentence_or_number in self.selected_sentences:
            self.selected_sentences.remove(sentence_or_number)
            self.save_selected_sentences()
            print(f"🗑️  移除成功: {sentence_or_number}")
            return True
        else:
            print(f"❌ 句子不存在: {sentence_or_number}")
            return False
    
    def analyze_sentences(self):
        """分析选中句子的词频和音素频率"""
        if not self.selected_sentences:
            return Counter(), Counter(), set(), set()
        
        word_counter = Counter()
        phoneme_counter = Counter()
        covered_words = set()
        covered_phonemes = set()
        
        for sentence in self.selected_sentences:
            words = self.extract_words_from_sentence(sentence)
            
            for word in words:
                word_counter[word] += 1
                if word in self.pick_words:
                    covered_words.add(word)
                
                phonemes = self.get_word_phonemes(word)
                for phoneme in phonemes:
                    phoneme_counter[phoneme] += 1
                    covered_phonemes.add(phoneme)
        
        return word_counter, phoneme_counter, covered_words, covered_phonemes
    
    def display_analysis(self):
        """显示当前分析结果"""
        word_freq, phoneme_freq, covered_words, covered_phonemes = self.analyze_sentences()
        
        print("\n" + "=" * 80)
        print("📊 句子分析结果")
        print("=" * 80)
        
        # 显示选中的句子（显示清理后的版本）
        print(f"📝 选中句子 ({len(self.selected_sentences)}):")
        if self.selected_sentences:
            for i, sentence in enumerate(self.selected_sentences, 1):
                print(f"   {i:2d}. {sentence}")
        else:
            print("   (无选中句子)")
        
        if not self.selected_sentences:
            return
        
        # 词汇频率分析
        print(f"\n📚 词汇频率分析 (按频率排序):")
        print("-" * 60)
        
        if word_freq:
            print("🔤 出现的词汇:")
            for word, freq in word_freq.most_common():
                status = "✅" if word in self.pick_words else "❓"
                print(f"   {word:15s}: {freq:3d} 次 {status}")
        
        # 目标词汇覆盖情况
        uncovered_words = self.pick_words - covered_words
        print(f"\n📋 目标词汇覆盖情况:")
        print(f"   总目标词汇: {len(self.pick_words)}")
        print(f"   已覆盖: {len(covered_words)} ({len(covered_words)/len(self.pick_words)*100:.1f}%)")
        print(f"   未覆盖: {len(uncovered_words)} ({len(uncovered_words)/len(self.pick_words)*100:.1f}%)")
        
        if uncovered_words:
            print("   🟡 未覆盖的目标词汇:")
            uncovered_list = sorted(list(uncovered_words))
            for i in range(0, len(uncovered_list), 8):
                group = uncovered_list[i:i+8]
                print(f"      {', '.join(group)}")
        
        # 音素频率分析
        print(f"\n🔊 音素频率分析 (按频率排序):")
        print("-" * 60)
        
        if phoneme_freq:
            print("🎵 出现的音素:")
            for phoneme, freq in phoneme_freq.most_common():
                print(f"   /{phoneme:3s}/: {freq:3d} 次")
        
        # 音素覆盖情况
        uncovered_phonemes = self.standard_phonemes - covered_phonemes
        print(f"\n🎯 39音素覆盖情况:")
        print(f"   总音素: 39")
        print(f"   已覆盖: {len(covered_phonemes)} ({len(covered_phonemes)/39*100:.1f}%)")
        print(f"   未覆盖: {len(uncovered_phonemes)} ({len(uncovered_phonemes)/39*100:.1f}%)")
        
        if uncovered_phonemes:
            print("   🟡 未覆盖的音素:")
            uncovered_list = sorted(list(uncovered_phonemes))
            for i in range(0, len(uncovered_list), 8):
                group = uncovered_list[i:i+8]
                phoneme_str = ', '.join([f"/{p}/" for p in group])
                print(f"      {phoneme_str}")
        
        # 统计摘要
        total_words = sum(word_freq.values())
        total_phonemes = sum(phoneme_freq.values())
        
        print(f"\n📈 统计摘要:")
        print(f"   总词汇实例: {total_words}")
        print(f"   不同词汇数: {len(word_freq)}")
        print(f"   总音素实例: {total_phonemes}")
        print(f"   不同音素数: {len(phoneme_freq)}")
    
    def run_interactive(self):
        """运行交互界面"""
        print("🎯 交互式句子分析器")
        print("=" * 30)
        print("💡 使用说明:")
        print("   📝 直接输入句子 → 添加到分析列表")
        print("   🗑️  remove <句子/编号> → 删除指定句子")
        print("   📊 show → 显示当前分析结果")
        print("   📋 list → 列出所有选中句子")
        print("   🧹 clear → 清空所有句子")
        print("   👋 quit → 退出程序")
        print("   💡 删除例子: remove 1 或 remove This is a test")
        
        # 显示初始状态
        self.display_analysis()
        
        while True:
            try:
                user_input = input(f"\n🎮 输入命令: ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(None, 1)
                cmd = parts[0].lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    print("👋 再见!")
                    break
                
                elif cmd == 'remove' and len(parts) > 1:
                    self.remove_sentence(parts[1])
                    self.display_analysis()
                
                elif cmd == 'show':
                    self.display_analysis()
                
                elif cmd == 'list':
                    print(f"\n📝 当前选中句子 ({len(self.selected_sentences)}):")
                    if self.selected_sentences:
                        for i, sentence in enumerate(self.selected_sentences, 1):
                            print(f"   {i:2d}. {sentence}")
                    else:
                        print("   (无选中句子)")
                
                elif cmd == 'clear':
                    confirm = input("⚠️  确认清空所有句子? (y/N): ")
                    if confirm.lower() in ['y', 'yes']:
                        self.selected_sentences = []
                        self.save_selected_sentences()
                        print("✅ 已清空所有句子")
                        self.display_analysis()
                
                else:
                    # 尝试作为句子添加
                    self.add_sentence(user_input)
                    self.display_analysis()
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

def main():
    """主函数"""
    analyzer = SentenceAnalyzer()
    analyzer.run_interactive()

if __name__ == "__main__":
    main()
