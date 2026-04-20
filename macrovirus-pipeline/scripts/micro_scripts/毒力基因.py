import argparse
#要求：从a文件中每一行，在b文件第一列tsv文件中检索，将匹配到的输出到另一个文件中，同时命令行输出匹配到的行数。argparse实现，保留表头。特殊，b文件第一列可能有冗余信息，比如说K10__928_1是内容，a文件中某一行是K10__928，如果匹配到，就输出这一行，但有可能会匹配到K10__9280_1，或许你可以以_作为分隔符进行截取精准匹配
def main():
    parser = argparse.ArgumentParser(description="精准匹配：a文件每行 → 匹配b.tsv第一列（按_分割前缀）")
    parser.add_argument("-a", "--a_file", required=True, help="查询词文件，每行一个")
    parser.add_argument("-b", "--b_file", required=True, help="被检索的大TSV文件（第一列用于匹配）")
    parser.add_argument("-o", "--output", required=True, help="输出结果文件")
    args = parser.parse_args()

    # 1. 读取a文件所有查询词（去重、去空行）
    print("正在读取查询文件 a ...")
    query_set = set()
    with open(args.a_file, "r", encoding="utf-8") as f:
        for line in f:
            term = line.strip()
            if term:
                query_set.add(term)

    # 2. 遍历大文件b，精准匹配前缀（按 _ 分割）
    match_count = 0
    header_copied = False

    print(f"开始检索大文件：{args.b_file}")
    with open(args.b_file, "r", encoding="utf-8") as fin, \
         open(args.output, "w", encoding="utf-8") as fout:

        for line in fin:
            # 保留表头
            if not header_copied:
                fout.write(line)
                header_copied = True
                continue

            # 取第一列（按tab分割）
            if "\t" not in line:
                continue
            first_col = line.split("\t", 1)[0].strip()

            # ====================== 核心精准匹配 ======================
            # 按 _ 分割，取前面所有部分拼接成前缀，精准匹配a中的内容
            parts = first_col.split("_")
            matched = False
            for i in range(1, len(parts)):
                prefix = "_".join(parts[:i])  # 生成 K10__928 这种前缀
                if prefix in query_set:
                    matched = True
                    break
            # =========================================================

            if matched:
                fout.write(line)
                match_count += 1

    # 输出结果
    print("=" * 60)
    print(f"✅ 匹配完成！")
    print(f"📌 成功匹配行数：{match_count}")
    print(f"📄 结果已保存到：{args.output}")
    print("=" * 60)

if __name__ == "__main__":
    main()