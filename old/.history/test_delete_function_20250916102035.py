#!/usr/bin/env python3
"""
Test script to demonstrate the delete functionality
测试脚本：演示删除功能
"""

from phoneme_tracker_clean import PhonemeTracker

def test_delete_function():
    """测试删除功能"""
    tracker = PhonemeTracker()
    
    print("🎯 测试删除功能")
    print("=" * 40)
    
    # 先添加一些测试词汇
    test_words = ["hello", "world", "python", "test", "demo"]
    
    print("📝 添加测试词汇...")
    for word in test_words:
        tracker.add_word(word)
    
    print(f"\n📋 当前词汇列表:")
    for i, word in enumerate(tracker.selected_words, 1):
        phonemes = tracker.get_word_phonemes(word)
        if phonemes:
            print(f"   {i}. {word:10s} -> /{' '.join(phonemes)}/")
    
    print(f"\n🗑️  删除功能测试:")
    print("=" * 30)
    
    # 测试按词汇名删除
    print("1. 按词汇名删除 'hello':")
    tracker.remove_word("hello")
    print(f"   剩余词汇: {tracker.selected_words}")
    
    # 测试按编号删除
    print("\n2. 按编号删除第2个词汇:")
    tracker.remove_word("2")
    print(f"   剩余词汇: {tracker.selected_words}")
    
    # 测试删除不存在的词汇
    print("\n3. 尝试删除不存在的词汇 'notexist':")
    tracker.remove_word("notexist")
    
    # 测试删除无效编号
    print("\n4. 尝试删除无效编号 '99':")
    tracker.remove_word("99")
    
    print(f"\n✅ 最终词汇列表:")
    for i, word in enumerate(tracker.selected_words, 1):
        phonemes = tracker.get_word_phonemes(word)
        if phonemes:
            print(f"   {i}. {word:10s} -> /{' '.join(phonemes)}/")
    
    print(f"\n📊 删除功能特点:")
    print("   ✅ 支持按词汇名删除: remove hello")
    print("   ✅ 支持按编号删除: remove 1")
    print("   ✅ 自动保存到文件")
    print("   ✅ 错误提示友好")

if __name__ == "__main__":
    test_delete_function()
