#!/usr/bin/env python3
"""
Test script to demonstrate phoneme color coding
测试脚本：演示音素颜色标记功能
"""

from phoneme_tracker_clean import PhonemeTracker

def test_color_coding():
    """测试颜色标记功能"""
    tracker = PhonemeTracker()
    
    print("🎯 测试音素颜色标记功能")
    print("=" * 40)
    
    # 添加一些测试词汇来展示不同状态
    test_words = [
        "the",      # /DH AH/ - 给AH增加1个
        "that",     # /DH AE T/ - 给T增加1个
        "this",     # /DH IH S/ - 给S增加1个
        "these",    # /DH IY Z/ - 给Z增加1个
        "then",     # /DH EH N/ - 给N增加1个
        "there",    # /DH EH R/ - 给R增加1个
        "they",     # /DH EY/ - 给EY增加1个
        "them",     # /DH EH M/ - 给M增加1个
        "through",  # /TH R UW/ - 给TH,R,UW各增加1个
        "three",    # /TH R IY/ - 给TH,R,IY各增加1个
        "think",    # /TH IH NG K/ - 给TH,IH,NG,K各增加1个
        "things",   # /TH IH NG Z/ - 给Z再增加1个(超出目标)
        "another",  # /AH N AH DH ER/ - 给AH增加2个,N增加1个
        "about",    # /AH B AW T/ - 给AH再增加1个(超出目标)
    ]
    
    print("添加测试词汇...")
    for word in test_words:
        tracker.add_word(word)
    
    print("\n" + "="*60)
    print("🎨 颜色标记说明:")
    print("   ✅ 绿色 - 达到目标数量")
    print("   🟡 黄色 - 少于目标数量") 
    print("   🔴 红色 - 超过目标数量")
    print("="*60)
    
    # 显示状态
    tracker.display_status()

if __name__ == "__main__":
    test_color_coding()
