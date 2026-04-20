#!/usr/bin/env python
import argparse
import sys
"""
要求：从a文件中每一行，在b文件第一列tsv文件中检索，将匹配到的输出到另一个文件中，同时命令行输出匹配到的行数。argparse实现，保留表头。b文件有500M，几十万行
"""
def main():
    parser = argparse.ArgumentParser(description="从a文件每行查询，匹配b文件tsv第一列，输出匹配结果并统计行数")
    parser.add_argument("-a", "--a_file", required=True, help="查询词文件，每行一个")
    parser.add_argument("-b", "--b_file", required=True, help="被检索的TSV文件（大文件）")
    parser.add_argument("-o", "--output", required=True, help="输出匹配结果的文件")
    args = parser.parse_args()

    # 第一步：读取a文件所有查询词（去重）
    print("正在读取查询词文件 a ...")
    with open(args.a_file, "r", encoding="utf-8") as f:
        query_set = {line.strip("\r\n") for line in f if line.strip()}

    # 第二步：遍历大文件 b，匹配第一列，输出结果
    match_count = 0
    header_written = False

    print(f"开始检索大文件 {args.b_file} ...")
    with open(args.b_file, "r", encoding="utf-8") as fin, open(args.output, "w", encoding="utf-8") as fout:
        for line in fin:
            # 处理表头
            if not header_written:
                fout.write(line)
                header_written = True
                continue

            # 按Tab切分，取第一列
            cols = line.split("\t", 1)
            if not cols:
                continue
            first_col = cols[0].strip()

            # 匹配
            if first_col in query_set:
                fout.write(line)
                match_count += 1

    # 输出结果
    print("=" * 60)
    print(f"✅ 匹配完成！")
    print(f"🔍 总匹配行数：{match_count}")
    print(f"📄 结果已保存到：{args.output}")
    print("=" * 60)

if __name__ == "__main__":
    main()