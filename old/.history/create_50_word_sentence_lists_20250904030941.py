#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def create_50_word_sentence_lists():
    """创建50词列表和50句子列表"""
    
    print("=" * 80)
    print("创建50词列表和50句子列表")
    print("=" * 80)
    
    # 50个词的列表
    words_50 = [
        "Am", "Are", "Bad", "Bring", "Clean", "Closer", "Comfortable", "Coming", "Computer", "Do",
        "Faith", "Family", "Feel", "Glasses", "Going", "Good", "Goodbye", "Have", "Hello", "Help",
        "Here", "Hope", "How", "Hungry", "I", "Is", "It", "Like", "Music", "My",
        "Need", "No", "Not", "Nurse", "Okay", "Outside", "Please", "Right", "Success", "Tell",
        "That", "They", "Thirsty", "Tired", "Up", "Very", "What", "Where", "Yes", "You"
    ]
    
    # 50个句子的列表
    sentences_50 = [
        "Are you going outside?",
        "Are you tired?",
        "Bring my glasses here",
        "Bring my glasses please",
        "Do not feel bad",
        "Do you feel comfortable?",
        "Faith is good",
        "Hello how are you?",
        "Here is my computer",
        "How do you feel?",
        "How do you like my music?",
        "I am going outside",
        "I am not going",
        "I am not hungry",
        "I am not okay",
        "I am okay",
        "I am outside",
        "I am thirsty",
        "I do not feel comfortable",
        "I feel very comfortable",
        "I feel very hungry",
        "I hope it is clean",
        "I like my nurse",
        "I need my glasses",
        "I need you",
        "It is comfortable",
        "It is good",
        "It is okay",
        "It is right here",
        "My computer is clean",
        "My family is here",
        "My family is outside",
        "My family is very comfortable",
        "My glasses are clean",
        "My glasses are comfortable",
        "My nurse is outside",
        "My nurse is right outside",
        "No",
        "Please bring my glasses here",
        "Please clean it",
        "Please tell my family",
        "That is very clean",
        "They are coming here",
        "They are coming outside",
        "They are going outside",
        "They have faith",
        "What do you do?",
        "Where is it?",
        "Yes",
        "You are not right"
    ]
    
    print(f"📊 统计信息:")
    print(f"   词汇数量: {len(words_50)} 个")
    print(f"   句子数量: {len(sentences_50)} 个")
    
    # 保存50个词的列表
    with open('50_words_list.txt', 'w', encoding='utf-8') as f:
        for word in words_50:
            f.write(word + '\n')
    
    # 保存50个句子的列表
    with open('50_sentences_list.txt', 'w', encoding='utf-8') as f:
        for sentence in sentences_50:
            f.write(sentence + '\n')
    
    # 创建Python格式的文件
    with open('50_words_sentences.py', 'w', encoding='utf-8') as f:
        f.write('#!/usr/bin/env python3\n')
        f.write('# -*- coding: utf-8 -*-\n\n')
        f.write('"""\n')
        f.write('50词和50句子列表\n')
        f.write('用于语音合成和语言学习研究\n')
        f.write('"""\n\n')
        
        # 写入词汇列表
        f.write('# 50个词汇列表\n')
        f.write('words_50 = [\n')
        for i, word in enumerate(words_50):
            f.write(f'    "{word}"')
            if i < len(words_50) - 1:
                f.write(',')
            f.write('\n')
        f.write(']\n\n')
        
        # 写入句子列表
        f.write('# 50个句子列表\n')
        f.write('sentences_50 = [\n')
        for i, sentence in enumerate(sentences_50):
            f.write(f'    "{sentence}"')
            if i < len(sentences_50) - 1:
                f.write(',')
            f.write('\n')
        f.write(']\n\n')
        
        # 添加一些便捷函数
        f.write('def get_words():\n')
        f.write('    """获取50个词汇列表"""\n')
        f.write('    return words_50\n\n')
        
        f.write('def get_sentences():\n')
        f.write('    """获取50个句子列表"""\n')
        f.write('    return sentences_50\n\n')
        
        f.write('def get_word_count():\n')
        f.write('    """获取词汇数量"""\n')
        f.write('    return len(words_50)\n\n')
        
        f.write('def get_sentence_count():\n')
        f.write('    """获取句子数量"""\n')
        f.write('    return len(sentences_50)\n\n')
        
        f.write('if __name__ == "__main__":\n')
        f.write('    print(f"词汇数量: {get_word_count()}")\n')
        f.write('    print(f"句子数量: {get_sentence_count()}")\n')
        f.write('    print("\\n前10个词汇:")\n')
        f.write('    for i, word in enumerate(words_50[:10], 1):\n')
        f.write('        print(f"{i:2d}. {word}")\n')
        f.write('    print("\\n前10个句子:")\n')
        f.write('    for i, sentence in enumerate(sentences_50[:10], 1):\n')
        f.write('        print(f"{i:2d}. {sentence}")\n')
    
    print(f"\n✅ 文件创建完成！")
    print(f"📄 生成的文件:")
    print(f"   • 50_words_list.txt - 50个词汇（纯文本）")
    print(f"   • 50_sentences_list.txt - 50个句子（纯文本）")
    print(f"   • 50_words_sentences.py - Python格式（包含两个列表和便捷函数）")
    
    # 显示词汇列表
    print(f"\n📝 50个词汇:")
    for i in range(0, len(words_50), 10):
        line_words = words_50[i:i+10]
        start_num = i + 1
        end_num = min(i + 10, len(words_50))
        print(f"{start_num:>2}-{end_num:>2}: " + " • ".join(line_words))
    
    # 显示前10个句子作为样本
    print(f"\n📝 前10个句子样本:")
    for i, sentence in enumerate(sentences_50[:10], 1):
        print(f"{i:2d}. {sentence}")
    
    print(f"... 还有 {len(sentences_50) - 10} 个句子")
    
    return words_50, sentences_50

def main():
    """主函数"""
    words, sentences = create_50_word_sentence_lists()
    
    if words and sentences:
        print(f"\n🎯 列表创建完成！")
        print(f"📊 50个词汇 + 50个句子已准备就绪")

if __name__ == "__main__":
    main()
