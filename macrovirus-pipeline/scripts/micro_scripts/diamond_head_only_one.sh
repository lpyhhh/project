#!/bin/bash

### diamond结果，只提取第一个匹配到的序列 行

# ===================== 配置参数（根据你的实际路径修改）=====================
SOURCE_DIR="/media/jjz/hdd/lpy/meige/SCUT-zou/results/diamond"  # 源文件目录（待处理的文件所在目录）
TARGET_DIR="/media/jjz/hdd/lpy/meige/SCUT-zou/results/diamond_only-one"  # 目标目录（处理后的文件保存目录）
# ==========================================================================

# 1. 检查源目录是否存在
if [ ! -d "$SOURCE_DIR" ]; then
    echo "错误：源目录 $SOURCE_DIR 不存在！"
    exit 1
fi

# 2. 创建目标目录（如果不存在）
mkdir -p "$TARGET_DIR"
if [ ! -d "$TARGET_DIR" ]; then
    echo "错误：无法创建目标目录 $TARGET_DIR！"
    exit 1
fi

# 3. 批量处理源目录下的所有文件（排除子目录）
echo "开始批量处理文件，源目录：$SOURCE_DIR，目标目录：$TARGET_DIR"
echo "--------------------------------------------------------"

# 遍历源目录下的所有普通文件（非目录）
for file in "$SOURCE_DIR"/*; do
    # 只处理普通文件（跳过目录、链接等）
    if [ -f "$file" ]; then
        # 获取文件名（不含路径）
        filename=$(basename "$file")
        # 处理文件并输出到目标目录，保持原文件名
        awk '!seen[$1]++' "$file" > "$TARGET_DIR/$filename"
        
        # 检查处理是否成功
        if [ $? -eq 0 ]; then
            echo "✅ 成功处理：$filename"
        else
            echo "❌ 处理失败：$filename"
        fi
    fi
done

echo "--------------------------------------------------------"
echo "批量处理完成！所有处理后的文件已保存到：$TARGET_DIR"