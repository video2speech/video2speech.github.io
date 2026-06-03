#!/usr/bin/env python3
"""
Complete 30 Words Selection - 完成30个词汇的选择
更灵活的策略来确保找到30个词汇
"""

from phoneme_tracker_clean import PhonemeTracker

class Complete30WordsSelector:
    def __init__(self):
        self.tracker = PhonemeTracker()
        self.target_words = 30
        
        # 加载 final_word_list.txt
        try:
            with open('/Users/terry/Downloads/video2speech.github.io/video2speech.github.io/final_word_list.txt', 'r') as f:
                self.word_list = [line.strip() for line in f if line.strip()]
            print(f"📚 加载了 {len(self.word_list)} 个候选词汇")
        except FileNotFoundError:
            print("❌ 找不到 final_word_list.txt 文件")
            self.word_list = []
    
    def get_missing_phonemes(self):
        """获取缺失的音素列表"""
        current_dist, _ = self.tracker.get_current_phoneme_distribution()
        missing = []
        
        for phoneme, target in self.tracker.target_distribution.items():
            current = current_dist.get(phoneme, 0)
            if current < target:
                missing.extend([phoneme] * (target - current))
        
        return missing
    
    def word_contains_needed_phonemes(self, word):
        """检查词汇是否包含我们需要的音素"""
        phonemes = self.tracker.get_word_phonemes(word)
        if not phonemes:
            return False, []
        
        missing = self.get_missing_phonemes()
        needed_found = []
        
        for phoneme in phonemes:
            if phoneme in missing:
                needed_found.append(phoneme)
        
        return len(needed_found) > 0, needed_found
    
    def complete_selection(self):
        """完成30个词汇的选择"""
        print("🎯 完成30个词汇选择...")
        print(f"📝 当前已有 {len(self.tracker.selected_words)} 个词汇")
        
        if len(self.tracker.selected_words) >= self.target_words:
            print("✅ 已达到目标数量")
            return
        
        needed = self.target_words - len(self.tracker.selected_words)
        print(f"🎯 还需要 {needed} 个词汇")
        
        # 第一轮：优先选择包含缺失音素的词汇
        print("\n🎯 第一轮：选择包含缺失音素的词汇")
        added_round1 = 0
        
        for word in self.word_list:
            if len(self.tracker.selected_words) >= self.target_words:
                break
            
            if word in self.tracker.selected_words:
                continue
            
            contains_needed, needed_phonemes = self.word_contains_needed_phonemes(word)
            if contains_needed:
                phonemes = self.tracker.get_word_phonemes(word)
                if phonemes:
                    self.tracker.add_word(word)
                    added_round1 += 1
                    print(f"✅ [{len(self.tracker.selected_words):2d}/{self.target_words}] {word:15s} -> /{' '.join(phonemes)}/ (需要: {needed_phonemes})")
        
        print(f"✅ 第一轮添加了 {added_round1} 个词汇")
        
        # 第二轮：如果还不够，选择任何有效的词汇
        if len(self.tracker.selected_words) < self.target_words:
            remaining = self.target_words - len(self.tracker.selected_words)
            print(f"\n🎯 第二轮：还需要 {remaining} 个词汇，选择任何有效词汇")
            added_round2 = 0
            
            for word in self.word_list:
                if len(self.tracker.selected_words) >= self.target_words:
                    break
                
                if word in self.tracker.selected_words:
                    continue
                
                phonemes = self.tracker.get_word_phonemes(word)
                if phonemes:
                    self.tracker.add_word(word)
                    added_round2 += 1
                    print(f"✅ [{len(self.tracker.selected_words):2d}/{self.target_words}] {word:15s} -> /{' '.join(phonemes)}/")
            
            print(f"✅ 第二轮添加了 {added_round2} 个词汇")
        
        print(f"\n🎉 选择完成！")
        print(f"📝 最终选择: {len(self.tracker.selected_words)} 个词汇")
        
        # 显示最终状态
        self.tracker.display_status()
        
        # 显示所有选中的词汇
        print(f"\n📋 完整词汇列表:")
        for i, word in enumerate(self.tracker.selected_words, 1):
            phonemes = self.tracker.get_word_phonemes(word)
            if phonemes:
                print(f"   {i:2d}. {word:15s} -> /{' '.join(phonemes)}/")
    
    def show_progress(self):
        """显示当前进度"""
        current_dist, _ = self.tracker.get_current_phoneme_distribution()
        achieved = sum(1 for p in self.tracker.target_distribution 
                      if current_dist.get(p, 0) == self.tracker.target_distribution[p])
        
        missing = self.get_missing_phonemes()
        print(f"📊 进度: {len(self.tracker.selected_words)}/{self.target_words} 词汇")
        print(f"📊 达标音素: {achieved}/39 ({achieved/39*100:.1f}%)")
        print(f"📊 缺失音素: {len(set(missing))} 种，共 {len(missing)} 个实例")
        
        if missing:
            missing_counts = {}
            for p in missing:
                missing_counts[p] = missing_counts.get(p, 0) + 1
            missing_str = ", ".join([f"/{p}/({c})" for p, c in sorted(missing_counts.items())])
            print(f"📊 缺失详情: {missing_str}")

def main():
    """主函数"""
    selector = Complete30WordsSelector()
    
    if not selector.word_list:
        return
    
    print("🎯 完成30个词汇选择工具")
    print("=" * 40)
    
    # 显示当前状态
    selector.show_progress()
    
    # 完成选择
    selector.complete_selection()

if __name__ == "__main__":
    main()
