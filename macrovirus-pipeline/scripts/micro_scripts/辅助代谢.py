import argparse
#要求：从a文件中每一行，在b文件第一列tsv文件中检索，将匹配到的输出到另一个文件中，同时命令行输出匹配到的行数。argparse实现，保留表头。特殊，b文件第一列可能有冗余信息，比如说K10__928-cat_2_8是内容，a文件中某一行是K10__928，如果匹配到，就输出这一行，但有可能会匹配到K10__9280-cat_2_8，或许你可以以_作为分隔符进行截取精准匹配
# K10__928-cat_2_8 → 以 K10__928- 开头 → 匹配
# K10__928_abc → 以 K10__928_ 开头 → 匹配
# K10__9280-cat_2_8 → 不会以 K10__928- 或 K10__928_ 开头 → 不匹配
def main():
    parser = argparse.ArgumentParser(description="精准匹配：a文件每行匹配b.tsv第一列前缀，不含误匹配")
    parser.add_argument("-a", "--a_file", required=True, help="查询词文件a")
    parser.add_argument("-b", "--b_file", required=True, help="大TSV文件b")
    parser.add_argument("-o", "--output", required=True, help="输出结果文件")
    args = parser.parse_args()

    # 读取查询词
    print("正在读取查询词文件 a ...")
    query_set = set()
    with open(args.a_file, "r", encoding="utf-8") as f:
        for line in f:
            term = line.strip()
            if term:
                query_set.add(term)

    match_count = 0
    header_copied = False

    print(f"开始检索文件：{args.b_file}")
    with open(args.b_file, "r", encoding="utf-8") as fin, \
         open(args.output, "w", encoding="utf-8") as fout:

        for line in fin:
            # 保留表头
            if not header_copied:
                fout.write(line)
                header_copied = True
                continue

            # 提取第一列
            if "\t" not in line:
                continue
            first_col = line.split("\t", 1)[0].strip()

            # ===================== 核心精准匹配 =====================
            matched = any(
                first_col.startswith(f"{term}_") or  # 以 term_ 开头
                first_col == term or                 # 完全一致
                first_col.startswith(f"{term}-")     # 以 term- 开头
                for term in query_set
            )
            # ======================================================

            if matched:
                fout.write(line)
                match_count += 1

    print("=" * 60)
    print(f"✅ 匹配完成！")
    print(f"📌 成功匹配行数：{match_count}")
    print(f"📄 结果已保存到：{args.output}")
    print("=" * 60)

if __name__ == "__main__":
    main()