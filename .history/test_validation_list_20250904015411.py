#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 导入验证列表
from validation_list import validation_list, get_valid_sentences, get_invalid_sentences, get_statistics

def test_validation_list():
    """测试验证列表功能"""
    
    print("=" * 80)
    print("电影台词验证列表测试")
    print("=" * 80)
    
    # 获取统计信息
    stats = get_statistics()
    print(f"📊 统计信息:")
    print(f"   总句子数: {stats['total']}")
    print(f"   有效句子: {stats['valid']} ({stats['valid_percentage']:.2f}%)")
    print(f"   无效句子: {stats['invalid']}")
    
    # 显示前10个条目
    print(f"\n📝 前10个验证结果:")
    for i, item in enumerate(validation_list[:10], 1):
        status = "✅" if item['is_valid'] else "❌"
        text_preview = item['text'][:50] + ("..." if len(item['text']) > 50 else "")
        print(f"{i:2d}. {status} {text_preview}")
        if not item['is_valid'] and item['invalid_words']:
            print(f"     无效词: {', '.join(item['invalid_words'][:5])}")
    
    # 获取有效句子样本
    valid_sentences = get_valid_sentences()
    print(f"\n✅ 有效句子样本 (共{len(valid_sentences)}个):")
    for sentence in valid_sentences[:8]:
        print(f"   • {sentence}")
    
    # 获取无效句子样本
    invalid_sentences = get_invalid_sentences()
    print(f"\n❌ 无效句子样本 (共{len(invalid_sentences)}个):")
    for item in invalid_sentences[:5]:
        invalid_words_str = ', '.join(item['invalid_words'][:3])
        print(f"   • {item['text'][:60]}...")
        print(f"     无效词: {invalid_words_str}")
    
    # 按长度分析
    print(f"\n📏 按句子长度分析:")
    length_stats = {}
    for item in validation_list:
        length = len(item['text'])
        if length <= 20:
            category = "短句 (≤20字符)"
        elif length <= 50:
            category = "中句 (21-50字符)"
        else:
            category = "长句 (>50字符)"
        
        if category not in length_stats:
            length_stats[category] = {'total': 0, 'valid': 0}
        
        length_stats[category]['total'] += 1
        if item['is_valid']:
            length_stats[category]['valid'] += 1
    
    for category, data in length_stats.items():
        valid_rate = data['valid'] / data['total'] * 100 if data['total'] > 0 else 0
        print(f"   {category}: {data['valid']}/{data['total']} ({valid_rate:.1f}%)")
    
    # 最常见的无效词
    print(f"\n🚫 最常见的无效词 (TOP 10):")
    invalid_word_count = {}
    for item in validation_list:
        if not item['is_valid']:
            for word in item['invalid_words']:
                invalid_word_count[word] = invalid_word_count.get(word, 0) + 1
    
    # 排序并显示前10个
    sorted_invalid_words = sorted(invalid_word_count.items(), key=lambda x: x[1], reverse=True)
    for word, count in sorted_invalid_words[:10]:
        print(f"   '{word}': {count}次")

if __name__ == "__main__":
    test_validation_list()
