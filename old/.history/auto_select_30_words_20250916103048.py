#!/usr/bin/env python3
"""
Auto Select 30 Words from final_word_list.txt
从 final_word_list.txt 自动选择30个词汇，满足音素分布要求
"""

from phoneme_tracker_clean import PhonemeTracker
import time

class AutoWordSelector:
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
    
    def calculate_score(self):
        """计算当前选择的得分（越高越好）"""
        current_dist, _ = self.tracker.get_current_phoneme_distribution()
        score = 0
        
        # 计算达标音素数量
        for phoneme, target in self.tracker.target_distribution.items():
            current = current_dist.get(phoneme, 0)
            if current == target:
                score += 10  # 达标得10分
            elif current < target:
                score -= (target - current) * 2  # 缺少扣分
            else:
                score -= (current - target) * 3  # 超出扣更多分
        
        return score
    
    def should_keep_word(self, word):
        """判断是否应该保留这个词汇"""
        # 添加词汇前的得分
        old_score = self.calculate_score()
        
        # 临时添加词汇
        phonemes = self.tracker.get_word_phonemes(word)
        if not phonemes:
            return False
        
        self.tracker.selected_words.append(word)
        new_score = self.calculate_score()
        self.tracker.selected_words.pop()  # 移除临时添加的词汇
        
        # 如果新得分更好，保留
        return new_score > old_score
    
    def auto_select(self):
        """自动选择30个词汇"""
        print("🎯 开始自动选择30个词汇...")
        print("=" * 50)
        
        # 清空现有选择（可选）
        confirm = input("是否清空当前已选择的词汇？(y/N): ")
        if confirm.lower() in ['y', 'yes']:
            self.tracker.selected_words = []
            self.tracker.save_selected_words()
            print("✅ 已清空现有词汇")
        
        print(f"📝 当前已有 {len(self.tracker.selected_words)} 个词汇")
        print(f"🎯 目标：选择 {self.target_words} 个词汇")
        
        added_count = 0
        skipped_count = 0
        
        for i, word in enumerate(self.word_list):
            if len(self.tracker.selected_words) >= self.target_words:
                break
            
            # 跳过已存在的词汇
            if word in self.tracker.selected_words:
                continue
            
            # 尝试添加词汇
            phonemes = self.tracker.get_word_phonemes(word)
            if not phonemes:
                skipped_count += 1
                continue
            
            # 判断是否应该保留
            if self.should_keep_word(word):
                self.tracker.add_word(word)
                added_count += 1
                
                # 显示进度
                current_count = len(self.tracker.selected_words)
                print(f"✅ [{current_count:2d}/{self.target_words}] 添加: {word:15s} -> /{' '.join(phonemes)}/")
                
                # 每5个词显示一次状态
                if current_count % 5 == 0:
                    self.show_brief_status()
            else:
                skipped_count += 1
                if skipped_count % 20 == 0:  # 每跳过20个显示一次
                    print(f"⏭️  已跳过 {skipped_count} 个不合适的词汇...")
        
        print(f"\n🎉 自动选择完成!")
        print(f"   📝 最终选择: {len(self.tracker.selected_words)} 个词汇")
        print(f"   ✅ 新增: {added_count} 个")
        print(f"   ⏭️  跳过: {skipped_count} 个")
        
        # 显示最终状态
        self.tracker.display_status()
        
        return self.tracker.selected_words
    
    def show_brief_status(self):
        """显示简要状态"""
        current_dist, _ = self.tracker.get_current_phoneme_distribution()
        achieved = sum(1 for p in self.tracker.target_distribution 
                      if current_dist.get(p, 0) == self.tracker.target_distribution[p])
        score = self.calculate_score()
        
        print(f"   📊 达标音素: {achieved}/39 ({achieved/39*100:.1f}%) | 得分: {score}")
    
    def optimize_selection(self):
        """优化当前选择（移除得分较低的词汇）"""
        print("\n🔧 优化词汇选择...")
        
        if len(self.tracker.selected_words) <= self.target_words:
            print("✅ 词汇数量已达标，无需优化")
            return
        
        # 计算每个词汇的贡献度
        word_contributions = {}
        
        for word in self.tracker.selected_words:
            # 计算移除这个词汇后的得分变化
            old_score = self.calculate_score()
            
            # 临时移除
            self.tracker.selected_words.remove(word)
            new_score = self.calculate_score()
            self.tracker.selected_words.append(word)  # 恢复
            
            # 贡献度 = 移除后得分下降程度
            contribution = old_score - new_score
            word_contributions[word] = contribution
        
        # 移除贡献度最低的词汇
        while len(self.tracker.selected_words) > self.target_words:
            # 找到贡献度最低的词汇
            worst_word = min(word_contributions.keys(), key=lambda w: word_contributions[w])
            
            print(f"🗑️  移除贡献度最低的词汇: {worst_word} (贡献度: {word_contributions[worst_word]})")
            self.tracker.remove_word(worst_word)
            del word_contributions[worst_word]
        
        print(f"✅ 优化完成，保留 {len(self.tracker.selected_words)} 个词汇")

def main():
    """主函数"""
    selector = AutoWordSelector()
    
    if not selector.word_list:
        return
    
    print("🎯 自动词汇选择器")
    print("=" * 30)
    print("功能：")
    print("1. 从 final_word_list.txt 按顺序添加词汇")
    print("2. 自动判断词汇是否改善音素分布")
    print("3. 选择30个最优词汇")
    print("4. 自动优化选择结果")
    
    # 显示当前状态
    selector.tracker.display_status()
    
    # 开始自动选择
    selected_words = selector.auto_select()
    
    # 如果超过30个，进行优化
    if len(selected_words) > selector.target_words:
        selector.optimize_selection()
    
    print(f"\n🎉 最终结果：")
    print(f"📝 选中词汇 ({len(selector.tracker.selected_words)}):")
    for i, word in enumerate(selector.tracker.selected_words, 1):
        phonemes = selector.tracker.get_word_phonemes(word)
        if phonemes:
            print(f"   {i:2d}. {word:15s} -> /{' '.join(phonemes)}/")

if __name__ == "__main__":
    main()
