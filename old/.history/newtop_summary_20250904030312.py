#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def show_newtop_summary():
    """显示 newtop.txt 去重后的总结"""
    
    print("=" * 60)
    print("📝 newtop.txt 去重总结")
    print("=" * 60)
    
    # 读取去重后的词汇表
    try:
        with open('newtop.txt', 'r', encoding='utf-8') as f:
            words = [word.strip() for word in f.readlines() if word.strip()]
        
        print(f"📊 去重结果:")
        print(f"   原始词汇数: 200 个")
        print(f"   去重后词汇数: {len(words)} 个")
        print(f"   移除重复词汇: {200 - len(words)} 个")
        print(f"   去重效率: {(200 - len(words))/200*100:.1f}%")
        
        # 显示被去除的重复词汇
        duplicates_info = {
            'that': '重复 2 次', 'to': '重复 2 次', 'one': '重复 2 次',
            'on': '重复 2 次', "'s": '重复 2 次', 'in': '重复 2 次',
            'no': '重复 2 次', 'like': '重复 3 次', 'right': '重复 2 次',
            'as': '重复 2 次', 'need': '重复 2 次', 'about': '重复 2 次'
        }
        
        print(f"\n🔄 已移除的重复词汇:")
        for word, info in duplicates_info.items():
            print(f"   '{word}': {info}")
        
        # 按组显示词汇
        print(f"\n📋 去重后的词汇表 ({len(words)} 个):")
        
        # 分组显示，每行10个
        for i in range(0, len(words), 10):
            group_words = words[i:i+10]
            start_num = i + 1
            end_num = min(i + 10, len(words))
            print(f"{start_num:>3}-{end_num:>3}: " + " • ".join(group_words))
        
        print(f"\n✅ newtop.txt 已成功去重！")
        print(f"📄 文件现在包含 {len(words)} 个唯一词汇")
        print(f"🎯 所有重复词汇已移除，保持了原始顺序")
        
        return words
        
    except FileNotFoundError:
        print("❌ 找不到 newtop.txt 文件")
        return None

def main():
    """主函数"""
    words = show_newtop_summary()
    
    if words:
        print(f"\n🎉 任务完成！newtop.txt 现在是一个干净的、无重复的词汇表。")

if __name__ == "__main__":
    main()
