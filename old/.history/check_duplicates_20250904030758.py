#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def check_duplicates_in_file(filename):
    """检查文件中是否有重复句子"""
    
    print("=" * 80)
    print(f"检查 {filename} 中的重复句子")
    print("=" * 80)
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sentences = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"总句子数: {len(sentences)}")
        
        # 检查重复（不区分大小写）
        seen = set()
        duplicates = []
        unique_sentences = []
        duplicate_details = {}
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            if sentence_lower in seen:
                duplicates.append((i+1, sentence))  # 记录行号和内容
                if sentence_lower in duplicate_details:
                    duplicate_details[sentence_lower].append((i+1, sentence))
                else:
                    # 找到第一次出现的位置
                    for j, prev_sentence in enumerate(unique_sentences):
                        if prev_sentence.lower() == sentence_lower:
                            duplicate_details[sentence_lower] = [(j+1, prev_sentence), (i+1, sentence)]
                            break
            else:
                seen.add(sentence_lower)
                unique_sentences.append(sentence)
        
        print(f"唯一句子数: {len(unique_sentences)}")
        print(f"重复句子数: {len(duplicates)}")
        
        if duplicates:
            print(f"\n🔄 发现的重复句子:")
            print(f"   总共有 {len(duplicate_details)} 组重复句子")
            
            # 显示重复句子详情
            for i, (sentence_lower, occurrences) in enumerate(duplicate_details.items(), 1):
                print(f"\n{i:2d}. 重复句子组 (出现 {len(occurrences)} 次):")
                for line_num, original_sentence in occurrences:
                    print(f"    第{line_num:4d}行: {original_sentence}")
            
            # 询问是否要去重
            print(f"\n是否要生成去重后的文件？")
            response = input("输入 'y' 或 'yes' 确认，其他键取消: ").lower().strip()
            
            if response in ['y', 'yes']:
                output_filename = filename.replace('.txt', '_deduplicated.txt')
                with open(output_filename, 'w', encoding='utf-8') as f:
                    for sentence in unique_sentences:
                        f.write(sentence + '\n')
                
                print(f"\n✅ 已生成去重文件: {output_filename}")
                print(f"📊 {len(sentences)} → {len(unique_sentences)} 个句子")
                return unique_sentences
            else:
                print(f"\n❌ 已取消去重操作")
                return sentences
        else:
            print(f"\n✅ 没有发现重复句子，文件已经是干净的")
            return sentences
        
    except FileNotFoundError:
        print(f"❌ 找不到文件: {filename}")
        return None
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        return None

def main():
    """主函数"""
    filename = 'sentences_newtop_filtered_200.txt'
    result = check_duplicates_in_file(filename)
    
    if result:
        print(f"\n🎯 检查完成！")

if __name__ == "__main__":
    main()
