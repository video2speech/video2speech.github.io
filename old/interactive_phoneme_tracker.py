#!/usr/bin/env python3
"""
Interactive Phoneme Tracker
交互式音素追踪工具 - 选择词汇并追踪音素分布
"""

import nltk
import re
import json
import os
from collections import Counter, defaultdict
from colorama import Colorama, Fore, Back, Style, init

# Initialize colorama for cross-platform colored output
init(autoreset=True)

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
        
        # Target phoneme distribution (from our calculation)
        self.target_distribution = {
            'AH': 3, 'T': 3, 'N': 3, 'S': 3,
            'L': 2, 'IH': 2, 'R': 2,
            'D': 1, 'IY': 1, 'K': 1, 'EH': 1, 'M': 1, 'P': 1, 'ER': 1, 'Z': 1,
            'AA': 1, 'B': 1, 'EY': 1, 'F': 1, 'W': 1, 'AE': 1, 'AO': 1, 'AY': 1,
            'V': 1, 'NG': 1, 'OW': 1, 'HH': 1, 'UW': 1, 'G': 1, 'Y': 1, 'SH': 1,
            'JH': 1, 'CH': 1, 'DH': 1, 'TH': 1, 'AW': 1, 'UH': 1, 'OY': 1, 'ZH': 1
        }
        
        # Phoneme display order
        self.phoneme_order = [
            'AH', 'T', 'N', 'S',  # High frequency (3 each)
            'L', 'IH', 'R',       # Mid frequency (2 each)
            'D', 'IY', 'K', 'EH', 'M', 'P', 'ER', 'Z',     # Low frequency (1 each)
            'AA', 'B', 'EY', 'F', 'W', 'AE', 'AO', 'AY',
            'V', 'NG', 'OW', 'HH', 'UW', 'G', 'Y', 'SH',
            'JH', 'CH', 'DH', 'TH', 'AW', 'UH', 'OY', 'ZH'
        ]
        
        self.load_selected_words()
    
    def clean_phoneme(self, phoneme):
        """Remove stress markers from phoneme."""
        return re.sub(r'\d', '', phoneme)
    
    def get_word_phonemes(self, word):
        """Get phonemes for a word using CMU dictionary."""
        # Handle contractions and special cases
        word_clean = word.lower().replace("'", "")
        
        # Special handling for common contractions
        contraction_map = {
            "nt": "not", "s": "is", "ve": "have", "re": "are", 
            "ll": "will", "d": "would", "m": "am", "em": "them"
        }
        
        # Check if it's a contraction
        if word.startswith("'") and len(word) > 1:
            contraction_part = word[1:].lower()
            if contraction_part in contraction_map:
                word_clean = contraction_map[contraction_part]
        
        # Try different variations
        for test_word in [word_clean, word.lower(), re.sub(r'[^\w]', '', word.lower())]:
            if test_word in self.cmu_dict:
                phonemes = self.cmu_dict[test_word][0]
                return [self.clean_phoneme(p) for p in phonemes]
        
        return None
    
    def save_selected_words(self):
        """Save selected words to file."""
        with open(self.save_file, 'w') as f:
            json.dump(self.selected_words, f, indent=2)
    
    def load_selected_words(self):
        """Load previously selected words from file."""
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, 'r') as f:
                    self.selected_words = json.load(f)
            except:
                self.selected_words = []
        else:
            self.selected_words = []
    
    def add_word(self, word):
        """Add a word to the selected list."""
        word = word.strip()
        if word and word not in self.selected_words:
            phonemes = self.get_word_phonemes(word)
            if phonemes:
                self.selected_words.append(word)
                self.save_selected_words()
                print(f"{Fore.GREEN}✅ 添加成功: {word} -> /{' '.join(phonemes)}/")
                return True
            else:
                print(f"{Fore.RED}❌ 未找到音素: {word}")
                return False
        elif word in self.selected_words:
            print(f"{Fore.YELLOW}⚠️  词汇已存在: {word}")
            return False
        return False
    
    def remove_word(self, word):
        """Remove a word from the selected list."""
        if word in self.selected_words:
            self.selected_words.remove(word)
            self.save_selected_words()
            print(f"{Fore.CYAN}🗑️  移除成功: {word}")
            return True
        else:
            print(f"{Fore.RED}❌ 词汇不存在: {word}")
            return False
    
    def get_current_phoneme_distribution(self):
        """Calculate current phoneme distribution from selected words."""
        phoneme_counter = Counter()
        word_phonemes = {}
        
        for word in self.selected_words:
            phonemes = self.get_word_phonemes(word)
            if phonemes:
                word_phonemes[word] = phonemes
                for phoneme in phonemes:
                    if phoneme in self.target_distribution:
                        phoneme_counter[phoneme] += 1
        
        return phoneme_counter, word_phonemes
    
    def display_phoneme_status(self):
        """Display current phoneme distribution with color coding."""
        current_dist, word_phonemes = self.get_current_phoneme_distribution()
        
        print("\n" + "=" * 80)
        print(f"{Style.BRIGHT}当前选中词汇音素分布状态")
        print("=" * 80)
        
        print(f"{Style.BRIGHT}选中词汇 ({len(self.selected_words)}):")
        if self.selected_words:
            for i, word in enumerate(self.selected_words, 1):
                phonemes = word_phonemes.get(word, [])
                phoneme_str = ' '.join(phonemes) if phonemes else "未找到"
                print(f"  {i:2d}. {word:15s} -> /{phoneme_str}/")
        else:
            print("  (无选中词汇)")
        
        print(f"\n{Style.BRIGHT}音素分布状态:")
        print("-" * 60)
        
        # Group phonemes by target count
        high_freq = ['AH', 'T', 'N', 'S']  # Target: 3
        mid_freq = ['L', 'IH', 'R']        # Target: 2
        low_freq = [p for p in self.phoneme_order if p not in high_freq + mid_freq]  # Target: 1
        
        # Display high frequency phonemes
        print(f"{Style.BRIGHT}高频音素 (目标: 3个):")
        for phoneme in high_freq:
            current = current_dist.get(phoneme, 0)
            target = self.target_distribution[phoneme]
            status = self.get_status_color(current, target)
            print(f"  /{phoneme:3s}/: {status}{current:2d}{Style.RESET_ALL} (目标: {target})")
        
        print(f"\n{Style.BRIGHT}中频音素 (目标: 2个):")
        for phoneme in mid_freq:
            current = current_dist.get(phoneme, 0)
            target = self.target_distribution[phoneme]
            status = self.get_status_color(current, target)
            print(f"  /{phoneme:3s}/: {status}{current:2d}{Style.RESET_ALL} (目标: {target})")
        
        print(f"\n{Style.BRIGHT}低频音素 (目标: 1个):")
        # Display in groups of 4 for better readability
        for i in range(0, len(low_freq), 4):
            group = low_freq[i:i+4]
            line_parts = []
            for phoneme in group:
                current = current_dist.get(phoneme, 0)
                target = self.target_distribution[phoneme]
                status = self.get_status_color(current, target)
                line_parts.append(f"/{phoneme:3s}/: {status}{current}{Style.RESET_ALL}")
            print(f"  {' | '.join(line_parts)}")
        
        # Summary statistics
        total_current = sum(current_dist.values())
        total_target = sum(self.target_distribution.values())
        achieved = sum(1 for p in self.target_distribution if current_dist.get(p, 0) == self.target_distribution[p])
        
        print(f"\n{Style.BRIGHT}统计摘要:")
        print(f"  总音素实例: {total_current}/{total_target}")
        print(f"  达标音素: {achieved}/39 ({achieved/39*100:.1f}%)")
        print(f"  选中词汇: {len(self.selected_words)}")
        
        # Show missing and excess
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
            print(f"{Fore.YELLOW}  缺少: {', '.join(missing)}")
        if excess:
            print(f"{Fore.YELLOW}  超出: {', '.join(excess)}")
    
    def get_status_color(self, current, target):
        """Get color code based on current vs target."""
        if current == target:
            return f"{Fore.GREEN}"
        elif current < target:
            return f"{Back.YELLOW}{Fore.BLACK}"
        else:
            return f"{Back.YELLOW}{Fore.BLACK}"
    
    def run_interactive(self):
        """Run the interactive interface."""
        print(f"{Style.BRIGHT}{Fore.CYAN}🎯 交互式音素追踪工具")
        print(f"{Style.BRIGHT}{Fore.CYAN}Interactive Phoneme Tracker")
        print("=" * 50)
        
        while True:
            print(f"\n{Style.BRIGHT}命令选项:")
            print("1. add <词汇>     - 添加词汇")
            print("2. remove <词汇>  - 移除词汇")
            print("3. show          - 显示当前状态")
            print("4. list          - 列出所有选中词汇")
            print("5. clear         - 清空所有词汇")
            print("6. quit          - 退出程序")
            
            try:
                command = input(f"\n{Fore.CYAN}请输入命令: {Style.RESET_ALL}").strip()
                
                if not command:
                    continue
                
                parts = command.split(None, 1)
                cmd = parts[0].lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    print(f"{Fore.GREEN}👋 再见!")
                    break
                
                elif cmd == 'add' and len(parts) > 1:
                    self.add_word(parts[1])
                    self.display_phoneme_status()
                
                elif cmd == 'remove' and len(parts) > 1:
                    self.remove_word(parts[1])
                    self.display_phoneme_status()
                
                elif cmd == 'show':
                    self.display_phoneme_status()
                
                elif cmd == 'list':
                    print(f"\n{Style.BRIGHT}当前选中词汇 ({len(self.selected_words)}):")
                    if self.selected_words:
                        for i, word in enumerate(self.selected_words, 1):
                            print(f"  {i:2d}. {word}")
                    else:
                        print("  (无选中词汇)")
                
                elif cmd == 'clear':
                    confirm = input(f"{Fore.YELLOW}确认清空所有词汇? (y/N): {Style.RESET_ALL}")
                    if confirm.lower() in ['y', 'yes']:
                        self.selected_words = []
                        self.save_selected_words()
                        print(f"{Fore.GREEN}✅ 已清空所有词汇")
                        self.display_phoneme_status()
                
                else:
                    print(f"{Fore.RED}❌ 无效命令. 请使用 add/remove/show/list/clear/quit")
            
            except KeyboardInterrupt:
                print(f"\n{Fore.GREEN}👋 再见!")
                break
            except Exception as e:
                print(f"{Fore.RED}❌ 错误: {e}")

def main():
    """Main function to run the phoneme tracker."""
    tracker = PhonemeTracker()
    
    # Show initial status
    tracker.display_phoneme_status()
    
    # Run interactive interface
    tracker.run_interactive()

if __name__ == "__main__":
    # Install colorama if not available
    try:
        import colorama
    except ImportError:
        print("Installing colorama for colored output...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
        import colorama
    
    main()


