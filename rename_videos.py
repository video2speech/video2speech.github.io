#!/usr/bin/env python3
import os
import re
import shutil

def extract_trial_number(filename):
    """从文件名中提取trial序号"""
    # 匹配 _数字-290_ 的模式
    match = re.search(r'_(\d+)-290_', filename)
    if match:
        return int(match.group(1))
    return None

def analyze_videos():
    # 源文件夹
    source_dirs = [
        "/Users/terry/Downloads/video-recordings-2026-01-21T01-45-57",
        "/Users/terry/Downloads/video-recordings-2026-01-20T23-42-47"
    ]

    # 收集所有文件
    all_files = []
    trial_numbers = set()

    for source_dir in source_dirs:
        if not os.path.exists(source_dir):
            print(f"警告: 源文件夹不存在 {source_dir}")
            continue

        for filename in os.listdir(source_dir):
            if filename.endswith('.mp4'):
                trial_num = extract_trial_number(filename)
                if trial_num is not None:
                    all_files.append((source_dir, filename, trial_num))
                    trial_numbers.add(trial_num)

    # 排序文件（按trial序号）
    all_files.sort(key=lambda x: x[2])

    # 输出统计信息
    print("=== Trial 序号统计 ===")
    print(f"总共找到 {len(trial_numbers)} 个不同的trial序号")
    print(f"trial序号范围: {min(trial_numbers)} - {max(trial_numbers)}")

    missing_trials = []
    for i in range(min(trial_numbers), max(trial_numbers) + 1):
        if i not in trial_numbers:
            missing_trials.append(i)

    if missing_trials:
        print(f"缺失的trial序号 ({len(missing_trials)} 个): {missing_trials[:20]}")
        if len(missing_trials) > 20:
            print("... 还有更多缺失的序号")

    print(f"\n=== 文件列表 (按trial序号排序) ===")
    for source_dir, filename, trial_num in all_files:
        folder_name = os.path.basename(source_dir)
        print("3d"
    print(f"\n=== 重命名示例 ===")
    print("如果要在新文件夹中重命名，将会变成:")
    for source_dir, filename, trial_num in all_files[:5]:  # 只显示前5个示例
        new_filename = "03d"        print(f"  {filename}")
        print(f"  -> {new_filename}")
    if len(all_files) > 5:
        print(f"  ... 还有 {len(all_files) - 5} 个文件")

    print("\n要重命名文件，请手动创建目标文件夹并运行以下命令:")
    print("mkdir -p /Users/terry/Downloads/video-recordings-renamed")
    print("然后使用文件管理器复制并重命名文件，或使用以下bash命令:")
    print()
    print("# 对于第一个文件夹:")
    print('for file in "/Users/terry/Downloads/video-recordings-2026-01-21T01-45-57"/*.mp4; do')
    print('  trial=$(basename "$file" | sed -n "s/.*_\\([0-9]\\+\\)-290_.*/\\1/p")')
    print('  newname=$(printf "%03d_%s" "$trial" "$(basename "$file")")')
    print('  cp "$file" "/Users/terry/Downloads/video-recordings-renamed/$newname"')
    print('done')
    print()
    print("# 对于第二个文件夹:")
    print('for file in "/Users/terry/Downloads/video-recordings-2026-01-20T23-42-47"/*.mp4; do')
    print('  trial=$(basename "$file" | sed -n "s/.*_\\([0-9]\\+\\)-290_.*/\\1/p")')
    print('  newname=$(printf "%03d_%s" "$trial" "$(basename "$file")")')
    print('  cp "$file" "/Users/terry/Downloads/video-recordings-renamed/$newname"')
    print('done')

if __name__ == "__main__":
    analyze_videos()