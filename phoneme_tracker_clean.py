#!/usr/bin/env python3
"""
Clean Phoneme Tracker - 纯净版音素追踪工具
确保映射到39个标准CMU音素，不包含演示词汇
"""

import nltk
import re
import json
import os
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('corpora/cmudict')
except LookupError:
    nltk.download('cmudict')

from nltk.corpus import cmudict

class PhonemeTracker:
    def __init__(self):
        self.cmu_dict = cmudict.dict()
        self.selected_words = []
        self.save_file = "selected_words.json"
        
        # 标准39个英语音素 (ARPAbet格式)
        self.standard_phonemes = {
            # 元音 (15个)
            'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW',
            # 辅音 (24个)
            'B', 'CH', 'D', 'DH', 'F', 'G', 'HH', 'JH', 'K', 'L', 'M', 'N', 'NG', 'P', 'R', 'S', 'SH', 'T', 'TH', 'V', 'W', 'Y', 'Z', 'ZH'
        }
        
        # 目标音素分布
        self.target_distribution = {
            'AH': 3, 'T': 3, 'N': 3, 'S': 3,
            'L': 2, 'IH': 2, 'R': 2,
            'D': 1, 'IY': 1, 'K': 1, 'EH': 1, 'M': 1, 'P': 1, 'ER': 1, 'Z': 1,
            'AA': 1, 'B': 1, 'EY': 1, 'F': 1, 'W': 1, 'AE': 1, 'AO': 1, 'AY': 1,
            'V': 1, 'NG': 1, 'OW': 1, 'HH': 1, 'UW': 1, 'G': 1, 'Y': 1, 'SH': 1,
            'JH': 1, 'CH': 1, 'DH': 1, 'TH': 1, 'AW': 1, 'UH': 1, 'OY': 1, 'ZH': 1
        }
        
        # 音素显示顺序
        self.phoneme_order = [
            'AH', 'T', 'N', 'S',  # 高频 (3个)
            'L', 'IH', 'R',       # 中频 (2个)
            'D', 'IY', 'K', 'EH', 'M', 'P', 'ER', 'Z',     # 低频 (1个)
            'AA', 'B', 'EY', 'F', 'W', 'AE', 'AO', 'AY',
            'V', 'NG', 'OW', 'HH', 'UW', 'G', 'Y', 'SH',
            'JH', 'CH', 'DH', 'TH', 'AW', 'UH', 'OY', 'ZH'
        ]
        
        self.load_selected_words()
    
    def clean_phoneme(self, phoneme):
        """移除音素的重音标记"""
        return re.sub(r'\d', '', phoneme)
    
    def get_word_phonemes(self, word):
        """获取词汇对应的音素，确保只返回标准39个音素"""
        # 处理缩写和特殊情况
        word_clean = word.lower().replace("'", "")
        
        # 常见缩写映射
        contraction_map = {
            "nt": "not", "s": "is", "ve": "have", "re": "are", 
            "ll": "will", "d": "would", "m": "am", "em": "them"
        }
        
        # 检查是否为缩写
        if word.startswith("'") and len(word) > 1:
            contraction_part = word[1:].lower()
            if contraction_part in contraction_map:
                word_clean = contraction_map[contraction_part]
        
        # 尝试不同的词汇变形
        for test_word in [word_clean, word.lower(), re.sub(r'[^\w]', '', word.lower())]:
            if test_word in self.cmu_dict:
                phonemes = self.cmu_dict[test_word][0]
                cleaned_phonemes = [self.clean_phoneme(p) for p in phonemes]
                # 只返回标准39个音素中的音素
                valid_phonemes = [p for p in cleaned_phonemes if p in self.standard_phonemes]
                return valid_phonemes if valid_phonemes else None
        
        return None
    
    def save_selected_words(self):
        """保存选中的词汇到文件"""
        with open(self.save_file, 'w', encoding='utf-8') as f:
            json.dump(self.selected_words, f, indent=2, ensure_ascii=False)
    
    def load_selected_words(self):
        """从文件加载之前选中的词汇"""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r', encoding='utf-8') as f:
                    self.selected_words = json.load(f)
                if self.selected_words:
                    print(f"📁 加载了 {len(self.selected_words)} 个之前选中的词汇")
            except:
                self.selected_words = []
        else:
            self.selected_words = []
    
    def add_word(self, word):
        """添加词汇到选中列表"""
        word = word.strip()
        if not word:
            return False
            
        if word in self.selected_words:
            print(f"⚠️  词汇已存在: {word}")
            return False
        
        phonemes = self.get_word_phonemes(word)
        if phonemes:
            self.selected_words.append(word)
            self.save_selected_words()
            print(f"✅ 添加成功: {word} -> /{' '.join(phonemes)}/")
            return True
        else:
            print(f"❌ 未找到音素或不在标准39音素中: {word}")
            return False
    
    def remove_word(self, word):
        """从选中列表移除词汇"""
        if word in self.selected_words:
            self.selected_words.remove(word)
            self.save_selected_words()
            print(f"🗑️  移除成功: {word}")
            return True
        else:
            print(f"❌ 词汇不存在: {word}")
            return False
    
    def get_current_phoneme_distribution(self):
        """计算当前选中词汇的音素分布"""
        phoneme_counter = Counter()
        word_phonemes_map = {}
        
        for word in self.selected_words:
            phonemes = self.get_word_phonemes(word)
            if phonemes:
                word_phonemes_map[word] = phonemes
                for phoneme in phonemes:
                    phoneme_counter[phoneme] += 1
        
        return phoneme_counter, word_phonemes_map
    
    def display_status(self):
        """显示当前音素分布状态"""
        current_dist, word_phonemes_map = self.get_current_phoneme_distribution()
        
        print("\n" + "=" * 75)
        print("🎯 当前选中词汇音素分布状态")
        print("=" * 75)
        
        print(f"📝 选中词汇 ({len(self.selected_words)}):")
        if self.selected_words:
            for i, word in enumerate(self.selected_words, 1):
                phonemes = word_phonemes_map.get(word, [])
                if phonemes:
                    print(f"   {i:2d}. {word:15s} -> /{' '.join(phonemes)}/")
                else:
                    print(f"   {i:2d}. {word:15s} -> [无有效音素]")
        else:
            print("   (无选中词汇)")
        
        print(f"\n📊 音素分布状态:")
        print("-" * 60)
        
        # 高频音素 (目标: 3个)
        print("🔴 高频音素 (目标: 3个):")
        for phoneme in ['AH', 'T', 'N', 'S']:
            current = current_dist.get(phoneme, 0)
            target = self.target_distribution[phoneme]
            if current >= target:
                status = "✅"  # 达到或超过目标都标绿
            else:
                status = "🟡"  # 少了标黄
            print(f"   /{phoneme:3s}/: {current:2d} (目标: {target}) {status}")
        
        # 中频音素 (目标: 2个)
        print("\n🟠 中频音素 (目标: 2个):")
        for phoneme in ['L', 'IH', 'R']:
            current = current_dist.get(phoneme, 0)
            target = self.target_distribution[phoneme]
            if current >= target:
                status = "✅"  # 达到或超过目标都标绿
            else:
                status = "🟡"  # 少了标黄
            print(f"   /{phoneme:3s}/: {current:2d} (目标: {target}) {status}")
        
        # 低频音素 (目标: 1个)
        print("\n🟢 低频音素 (目标: 1个):")
        low_freq = [p for p in self.phoneme_order if p not in ['AH', 'T', 'N', 'S', 'L', 'IH', 'R']]
        
        for i in range(0, len(low_freq), 4):
            group = low_freq[i:i+4]
            line_parts = []
            for phoneme in group:
                current = current_dist.get(phoneme, 0)
                target = self.target_distribution[phoneme]
                if current >= target:
                    status = "✅"  # 达到或超过目标都标绿
                else:
                    status = "🟡"  # 少了标黄
                line_parts.append(f"/{phoneme:3s}/: {current} {status}")
            print(f"   {' | '.join(line_parts)}")
        
        # 统计摘要
        total_current = sum(current_dist.values())
        total_target = sum(self.target_distribution.values())
        achieved = sum(1 for p in self.target_distribution if current_dist.get(p, 0) >= self.target_distribution[p])
        
        print(f"\n📈 统计摘要:")
        print(f"   总音素实例: {total_current}/{total_target}")
        print(f"   达标音素: {achieved}/39 ({achieved/39*100:.1f}%)")
        print(f"   选中词汇: {len(self.selected_words)}")
        
        # 显示缺少和超出的音素
        missing = []
        excess = []
        for phoneme in self.phoneme_order:
            current = current_dist.get(phoneme, 0)
            target = self.target_distribution[phoneme]
            if current < target:
                missing.append(f"/{phoneme}/ (-{target-current})")
            elif current > target:
                excess.append(f"/{phoneme}/ (+{current-target})")
        
        if missing:
            print(f"   🟡 需要更多: {', '.join(missing)}")
        if excess:
            print(f"   🟡 超出目标: {', '.join(excess)}")
    
    def run_interactive(self):
        """运行交互界面"""
        print("🎯 音素追踪工具")
        print("=" * 30)
        print("💡 提示:")
        print("   - 直接输入词汇添加")
        print("   - 'remove <词汇>' 移除词汇")
        print("   - 'show' 显示状态")
        print("   - 'list' 列出所有词汇")
        print("   - 'clear' 清空所有词汇")
        print("   - 'quit' 退出程序")
        
        # 显示初始状态
        self.display_status()
        
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
                    self.remove_word(parts[1])
                    self.display_status()
                
                elif cmd == 'show':
                    self.display_status()
                
                elif cmd == 'list':
                    print(f"\n📝 当前选中词汇 ({len(self.selected_words)}):")
                    if self.selected_words:
                        for i, word in enumerate(self.selected_words, 1):
                            print(f"   {i:2d}. {word}")
                    else:
                        print("   (无选中词汇)")
                
                elif cmd == 'clear':
                    confirm = input("⚠️  确认清空所有词汇? (y/N): ")
                    if confirm.lower() in ['y', 'yes']:
                        self.selected_words = []
                        self.save_selected_words()
                        print("✅ 已清空所有词汇")
                        self.display_status()
                
                else:
                    # 尝试作为词汇添加
                    self.add_word(user_input)
                    self.display_status()
                
            except KeyboardInterrupt:
                print("\n👋 再见!")
                break
            except Exception as e:
                print(f"❌ 错误: {e}")

def main():
    """主函数"""
    tracker = PhonemeTracker()
    tracker.run_interactive()

if __name__ == "__main__":
    main()
