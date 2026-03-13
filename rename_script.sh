#!/bin/bash

# 创建目标文件夹
mkdir -p "/Users/terry/Downloads/video-recordings-renamed"

echo "开始重命名文件..."

# 处理第一个文件夹
echo "处理第一个文件夹..."
for file in "/Users/terry/Downloads/video-recordings-2026-01-21T01-45-57"/*.mp4; do
    if [[ -f "$file" ]]; then
        # 提取trial序号
        trial=$(basename "$file" | sed -n 's/.*_\([0-9]\+\)-290_.*/\1/p')
        if [[ -n "$trial" ]]; then
            # 生成新文件名: 003d_原文件名
            newname=$(printf "%03d_%s" "$trial" "$(basename "$file")")
            cp "$file" "/Users/terry/Downloads/video-recordings-renamed/$newname"
            echo "✓ $newname"
        fi
    fi
done

# 处理第二个文件夹
echo "处理第二个文件夹..."
for file in "/Users/terry/Downloads/video-recordings-2026-01-20T23-42-47"/*.mp4; do
    if [[ -f "$file" ]]; then
        # 提取trial序号
        trial=$(basename "$file" | sed -n 's/.*_\([0-9]\+\)-290_.*/\1/p')
        if [[ -n "$trial" ]]; then
            # 生成新文件名: 003d_原文件名
            newname=$(printf "%03d_%s" "$trial" "$(basename "$file")")
            cp "$file" "/Users/terry/Downloads/video-recordings-renamed/$newname"
            echo "✓ $newname"
        fi
    fi
done

echo "重命名完成!"
echo "新文件保存在: /Users/terry/Downloads/video-recordings-renamed"
echo "总文件数: $(ls "/Users/terry/Downloads/video-recordings-renamed"/*.mp4 2>/dev/null | wc -l)"