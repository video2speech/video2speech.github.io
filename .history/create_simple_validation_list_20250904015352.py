#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def create_simple_validation_list():
    """创建简单的验证列表"""
    
    # 读取JSON结果
    try:
        with open('sentence_validation_results.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"成功加载 {len(results)} 条验证结果")
        
    except Exception as e:
        print(f"读取结果文件失败: {e}")
        return
    
    # 创建简单列表
    validation_list = []
    
    for result in results:
        validation_list.append({
            'line_id': result['line_id'],
            'text': result['original_text'],
            'is_valid': result['is_valid'],
            'invalid_words': result.get('invalid_words', [])
        })
    
    # 保存为Python文件
    with open('validation_list.py', 'w', encoding='utf-8') as f:
        f.write("#!/usr/bin/env python3\n")
        f.write("# -*- coding: utf-8 -*-\n\n")
        f.write('"""\n')
        f.write("电影台词验证列表\n")
        f.write(f"总数: {len(validation_list)} 条\n")
        f.write(f"有效: {sum(1 for item in validation_list if item['is_valid'])} 条\n")
        f.write(f"无效: {sum(1 for item in validation_list if not item['is_valid'])} 条\n")
        f.write('"""\n\n')
        
        f.write("# 验证列表：每个元素包含 line_id, text, is_valid, invalid_words\n")
        f.write("validation_list = [\n")
        
        for i, item in enumerate(validation_list):
            f.write("    {\n")
            f.write(f"        'line_id': '{item['line_id']}',\n")
            f.write(f"        'text': {repr(item['text'])},\n")
            f.write(f"        'is_valid': {item['is_valid']},\n")
            f.write(f"        'invalid_words': {item['invalid_words']}\n")
            f.write("    }")
            
            if i < len(validation_list) - 1:
                f.write(",")
            f.write("\n")
        
        f.write("]\n\n")
        
        # 添加一些便捷函数
        f.write("# 便捷函数\n")
        f.write("def get_valid_sentences():\n")
        f.write("    \"\"\"获取所有有效句子\"\"\"\n")
        f.write("    return [item['text'] for item in validation_list if item['is_valid']]\n\n")
        
        f.write("def get_invalid_sentences():\n")
        f.write("    \"\"\"获取所有无效句子\"\"\"\n")
        f.write("    return [item for item in validation_list if not item['is_valid']]\n\n")
        
        f.write("def get_sentence_by_id(line_id):\n")
        f.write("    \"\"\"根据ID获取句子\"\"\"\n")
        f.write("    for item in validation_list:\n")
        f.write("        if item['line_id'] == line_id:\n")
        f.write("            return item\n")
        f.write("    return None\n\n")
        
        f.write("def get_statistics():\n")
        f.write("    \"\"\"获取统计信息\"\"\"\n")
        f.write("    total = len(validation_list)\n")
        f.write("    valid = sum(1 for item in validation_list if item['is_valid'])\n")
        f.write("    invalid = total - valid\n")
        f.write("    return {\n")
        f.write("        'total': total,\n")
        f.write("        'valid': valid,\n")
        f.write("        'invalid': invalid,\n")
        f.write("        'valid_percentage': valid / total * 100 if total > 0 else 0\n")
        f.write("    }\n")
    
    # 创建简化的文本列表
    with open('validation_simple_list.txt', 'w', encoding='utf-8') as f:
        f.write("# 电影台词验证简单列表\n")
        f.write("# 格式: [行号] [✅/❌] 句子内容\n")
        f.write("#" + "="*80 + "\n\n")
        
        for i, item in enumerate(validation_list, 1):
            status = "✅" if item['is_valid'] else "❌"
            f.write(f"{i:4d}. {status} {item['text']}\n")
    
    print(f"✅ 成功生成验证列表文件:")
    print(f"   - validation_list.py (Python格式)")
    print(f"   - validation_simple_list.txt (简单文本格式)")
    
    # 显示统计信息
    total = len(validation_list)
    valid = sum(1 for item in validation_list if item['is_valid'])
    invalid = total - valid
    
    print(f"\n📊 统计信息:")
    print(f"   总句子数: {total}")
    print(f"   有效句子: {valid} ({valid/total*100:.2f}%)")
    print(f"   无效句子: {invalid} ({invalid/total*100:.2f}%)")
    
    # 显示一些样本
    print(f"\n📝 有效句子样本:")
    valid_samples = [item for item in validation_list if item['is_valid']][:5]
    for item in valid_samples:
        print(f"   ✅ {item['text'][:60]}...")
    
    print(f"\n❌ 无效句子样本:")
    invalid_samples = [item for item in validation_list if not item['is_valid']][:5]
    for item in invalid_samples:
        invalid_words_str = ', '.join(item['invalid_words'][:3])
        print(f"   ❌ {item['text'][:50]}... (无效词: {invalid_words_str})")

if __name__ == "__main__":
    create_simple_validation_list()
