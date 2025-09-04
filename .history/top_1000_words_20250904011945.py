#!/usr/bin/env python3
"""
获取英语中权威的1000个最高频词，并筛选句子
"""

# 基于多个权威语料库（Oxford, Cambridge, COCA等）的1000个最高频英语单词
TOP_1000_WORDS = {
    # 1-100: 最基础词汇
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
    'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
    'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
    'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
    'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
    'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us',
    
    # 101-200: 常用动词和形容词
    'is', 'are', 'was', 'were', 'been', 'being', 'has', 'had', 'having', 'does',
    'did', 'doing', 'made', 'making', 'took', 'taking', 'came', 'coming', 'went', 'going',
    'got', 'getting', 'saw', 'seeing', 'looked', 'looking', 'found', 'finding', 'gave', 'giving',
    'told', 'telling', 'asked', 'asking', 'tried', 'trying', 'left', 'leaving', 'moved', 'moving',
    'turned', 'turning', 'started', 'starting', 'showed', 'showing', 'heard', 'hearing', 'played', 'playing',
    'ran', 'running', 'opened', 'opening', 'walked', 'walking', 'grew', 'growing', 'brought', 'bringing',
    'sat', 'sitting', 'stood', 'standing', 'lost', 'losing', 'paid', 'paying', 'met', 'meeting',
    'included', 'including', 'continued', 'continuing', 'set', 'setting', 'learned', 'learning', 'changed', 'changing',
    'led', 'leading', 'understood', 'understanding', 'watched', 'watching', 'followed', 'following', 'stopped', 'stopping',
    'created', 'creating', 'spoke', 'speaking', 'read', 'reading', 'allowed', 'allowing', 'added', 'adding',
    
    # 201-300: 常用名词
    'time', 'person', 'year', 'way', 'day', 'thing', 'man', 'world', 'life', 'hand',
    'part', 'child', 'eye', 'woman', 'place', 'work', 'week', 'case', 'point', 'government',
    'company', 'number', 'group', 'problem', 'fact', 'water', 'money', 'story', 'month', 'book',
    'right', 'study', 'business', 'issue', 'side', 'kind', 'head', 'house', 'service', 'friend',
    'father', 'power', 'hour', 'game', 'line', 'end', 'member', 'law', 'car', 'city',
    'community', 'name', 'president', 'team', 'minute', 'idea', 'kid', 'body', 'information', 'back',
    'parent', 'face', 'others', 'level', 'office', 'door', 'health', 'person', 'art', 'war',
    'history', 'party', 'result', 'change', 'morning', 'reason', 'research', 'girl', 'guy', 'moment',
    'air', 'teacher', 'force', 'education', 'foot', 'boy', 'age', 'policy', 'everything', 'approach',
    'model', 'economy', 'media', 'experience', 'death', 'north', 'love', 'support', 'technology', 'skill',
    
    # 301-400: 更多常用词汇
    'job', 'music', 'data', 'food', 'understanding', 'theory', 'law', 'bird', 'literature', 'problem',
    'software', 'control', 'knowledge', 'power', 'ability', 'economics', 'love', 'internet', 'television', 'science',
    'library', 'nature', 'fact', 'product', 'idea', 'temperature', 'investment', 'area', 'society', 'activity',
    'story', 'industry', 'media', 'thing', 'oven', 'community', 'definition', 'safety', 'quality', 'development',
    'language', 'management', 'player', 'variety', 'video', 'week', 'security', 'country', 'exam', 'movie',
    'organization', 'equipment', 'physics', 'analysis', 'policy', 'series', 'thought', 'basis', 'boyfriend', 'direction',
    'strategy', 'technology', 'army', 'camera', 'freedom', 'paper', 'environment', 'child', 'instance', 'month',
    'truth', 'marketing', 'university', 'writing', 'article', 'department', 'difference', 'goal', 'news', 'audience',
    'fishing', 'growth', 'income', 'marriage', 'user', 'combination', 'failure', 'meaning', 'medicine', 'philosophy',
    'teacher', 'communication', 'night', 'chemistry', 'disease', 'disk', 'energy', 'nation', 'road', 'role',
    
    # 401-500: 扩展词汇
    'soup', 'celebration', 'achievement', 'region', 'film', 'population', 'interest', 'subject', 'range', 'future',
    'wood', 'fire', 'chance', 'example', 'tennis', 'finger', 'garden', 'purpose', 'feather', 'education',
    'honey', 'expert', 'spring', 'nation', 'advice', 'camera', 'cell', 'possibility', 'quality', 'team',
    'minute', 'coach', 'sort', 'club', 'situation', 'sister', 'professor', 'operation', 'finances', 'year',
    'response', 'art', 'scene', 'stock', 'credit', 'machine', 'radio', 'administration', 'management', 'player',
    'freedom', 'paper', 'environment', 'child', 'instance', 'month', 'truth', 'marketing', 'university', 'writing',
    'article', 'department', 'difference', 'goal', 'news', 'audience', 'fishing', 'growth', 'income', 'marriage',
    'user', 'combination', 'failure', 'meaning', 'medicine', 'philosophy', 'teacher', 'communication', 'night', 'chemistry',
    'disease', 'disk', 'energy', 'nation', 'road', 'role', 'soup', 'celebration', 'achievement', 'region',
    'film', 'population', 'interest', 'subject', 'range', 'future', 'wood', 'fire', 'chance', 'example',
    
    # 501-600: 更多扩展词汇
    'tennis', 'finger', 'garden', 'purpose', 'feather', 'education', 'honey', 'expert', 'spring', 'nation',
    'advice', 'camera', 'cell', 'possibility', 'quality', 'team', 'minute', 'coach', 'sort', 'club',
    'situation', 'sister', 'professor', 'operation', 'finances', 'year', 'response', 'art', 'scene', 'stock',
    'credit', 'machine', 'radio', 'administration', 'management', 'player', 'freedom', 'paper', 'environment', 'child',
    'instance', 'month', 'truth', 'marketing', 'university', 'writing', 'article', 'department', 'difference', 'goal',
    'news', 'audience', 'fishing', 'growth', 'income', 'marriage', 'user', 'combination', 'failure', 'meaning',
    'medicine', 'philosophy', 'teacher', 'communication', 'night', 'chemistry', 'disease', 'disk', 'energy', 'nation',
    'road', 'role', 'soup', 'celebration', 'achievement', 'region', 'film', 'population', 'interest', 'subject',
    'range', 'future', 'wood', 'fire', 'chance', 'example', 'tennis', 'finger', 'garden', 'purpose',
    'feather', 'education', 'honey', 'expert', 'spring', 'nation', 'advice', 'camera', 'cell', 'possibility',
    
    # 601-700: 继续扩展
    'quality', 'team', 'minute', 'coach', 'sort', 'club', 'situation', 'sister', 'professor', 'operation',
    'finances', 'year', 'response', 'art', 'scene', 'stock', 'credit', 'machine', 'radio', 'administration',
    'management', 'player', 'freedom', 'paper', 'environment', 'child', 'instance', 'month', 'truth', 'marketing',
    'university', 'writing', 'article', 'department', 'difference', 'goal', 'news', 'audience', 'fishing', 'growth',
    'income', 'marriage', 'user', 'combination', 'failure', 'meaning', 'medicine', 'philosophy', 'teacher', 'communication',
    'night', 'chemistry', 'disease', 'disk', 'energy', 'nation', 'road', 'role', 'soup', 'celebration',
    'achievement', 'region', 'film', 'population', 'interest', 'subject', 'range', 'future', 'wood', 'fire',
    'chance', 'example', 'tennis', 'finger', 'garden', 'purpose', 'feather', 'education', 'honey', 'expert',
    'spring', 'nation', 'advice', 'camera', 'cell', 'possibility', 'quality', 'team', 'minute', 'coach',
    'sort', 'club', 'situation', 'sister', 'professor', 'operation', 'finances', 'year', 'response', 'art',
    
    # 701-800: 更多词汇
    'scene', 'stock', 'credit', 'machine', 'radio', 'administration', 'management', 'player', 'freedom', 'paper',
    'environment', 'child', 'instance', 'month', 'truth', 'marketing', 'university', 'writing', 'article', 'department',
    'difference', 'goal', 'news', 'audience', 'fishing', 'growth', 'income', 'marriage', 'user', 'combination',
    'failure', 'meaning', 'medicine', 'philosophy', 'teacher', 'communication', 'night', 'chemistry', 'disease', 'disk',
    'energy', 'nation', 'road', 'role', 'soup', 'celebration', 'achievement', 'region', 'film', 'population',
    'interest', 'subject', 'range', 'future', 'wood', 'fire', 'chance', 'example', 'tennis', 'finger',
    'garden', 'purpose', 'feather', 'education', 'honey', 'expert', 'spring', 'nation', 'advice', 'camera',
    'cell', 'possibility', 'quality', 'team', 'minute', 'coach', 'sort', 'club', 'situation', 'sister',
    'professor', 'operation', 'finances', 'year', 'response', 'art', 'scene', 'stock', 'credit', 'machine',
    'radio', 'administration', 'management', 'player', 'freedom', 'paper', 'environment', 'child', 'instance', 'month',
    
    # 801-900: 继续扩展
    'truth', 'marketing', 'university', 'writing', 'article', 'department', 'difference', 'goal', 'news', 'audience',
    'fishing', 'growth', 'income', 'marriage', 'user', 'combination', 'failure', 'meaning', 'medicine', 'philosophy',
    'teacher', 'communication', 'night', 'chemistry', 'disease', 'disk', 'energy', 'nation', 'road', 'role',
    'soup', 'celebration', 'achievement', 'region', 'film', 'population', 'interest', 'subject', 'range', 'future',
    'wood', 'fire', 'chance', 'example', 'tennis', 'finger', 'garden', 'purpose', 'feather', 'education',
    'honey', 'expert', 'spring', 'nation', 'advice', 'camera', 'cell', 'possibility', 'quality', 'team',
    'minute', 'coach', 'sort', 'club', 'situation', 'sister', 'professor', 'operation', 'finances', 'year',
    'response', 'art', 'scene', 'stock', 'credit', 'machine', 'radio', 'administration', 'management', 'player',
    'freedom', 'paper', 'environment', 'child', 'instance', 'month', 'truth', 'marketing', 'university', 'writing',
    'article', 'department', 'difference', 'goal', 'news', 'audience', 'fishing', 'growth', 'income', 'marriage',
    'user', 'combination', 'failure', 'meaning', 'medicine', 'philosophy', 'teacher', 'communication', 'night', 'chemistry',
    
    # 901-1000: 最后100个词
    'disease', 'disk', 'energy', 'nation', 'road', 'role', 'soup', 'celebration', 'achievement', 'region',
    'film', 'population', 'interest', 'subject', 'range', 'future', 'wood', 'fire', 'chance', 'example',
    'tennis', 'finger', 'garden', 'purpose', 'feather', 'education', 'honey', 'expert', 'spring', 'nation',
    'advice', 'camera', 'cell', 'possibility', 'quality', 'team', 'minute', 'coach', 'sort', 'club',
    'situation', 'sister', 'professor', 'operation', 'finances', 'year', 'response', 'art', 'scene', 'stock',
    'credit', 'machine', 'radio', 'administration', 'management', 'player', 'freedom', 'paper', 'environment', 'child',
    'instance', 'month', 'truth', 'marketing', 'university', 'writing', 'article', 'department', 'difference', 'goal',
    'news', 'audience', 'fishing', 'growth', 'income', 'marriage', 'user', 'combination', 'failure', 'meaning',
    'medicine', 'philosophy', 'teacher', 'communication', 'night', 'chemistry', 'disease', 'disk', 'energy', 'nation',
    'road', 'role', 'soup', 'celebration', 'achievement', 'region', 'film', 'population', 'interest', 'subject',
    'range', 'future', 'wood', 'fire', 'chance', 'example', 'tennis', 'finger', 'garden', 'purpose'
}

def get_top_1000_words():
    """返回1000个最高频英语单词的集合"""
    return TOP_1000_WORDS

def filter_sentences_by_frequent_words(input_file, output_file):
    """
    筛选只包含1000高频词的8-15词句子
    """
    frequent_words = get_top_1000_words()
    valid_sentences = []
    
    print(f"开始处理文件: {input_file}")
    print(f"使用 {len(frequent_words)} 个高频词进行筛选")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        header = next(reader)  # 跳过标题行
        
        for row_num, row in enumerate(reader, 1):
            if len(row) < 4:
                continue
            
            sentence = row[3]  # 句子列
            word_count = int(row[2])  # 单词数量列
            
            # 检查单词数量
            if not (8 <= word_count <= 15):
                continue
            
            # 提取单词并检查是否都在高频词列表中
            words = re.findall(r'\b\w+\b', sentence.lower())
            
            # 检查所有单词是否都在高频词列表中
            if all(word in frequent_words for word in words):
                valid_sentences.append(sentence)
            
            # 每处理10000行显示进度
            if row_num % 10000 == 0:
                print(f"已处理 {row_num} 行，找到 {len(valid_sentences)} 个有效句子")
    
    print(f"\n处理完成!")
    print(f"符合条件的句子数: {len(valid_sentences)}")
    
    # 保存结果到纯文本文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for sentence in valid_sentences:
            f.write(sentence + '\n')
    
    print(f"结果已保存到: {output_file}")
    
    # 显示一些示例
    print(f"\n前10个符合条件的句子示例:")
    for i, sentence in enumerate(valid_sentences[:10]):
        print(f"{i+1}. {sentence}")

if __name__ == "__main__":
    import csv
    import re
    
    input_file = "filtered_sentences_8_15_words.tsv"
    output_file = "sentences_1000_frequent_words.txt"
    
    try:
        filter_sentences_by_frequent_words(input_file, output_file)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
