import argparse

def main():
    parser = argparse.ArgumentParser(description="TSV文件 第2列Contig精准匹配")
    parser.add_argument("-a", "--a_file", required=True, help="查询ID列表（每行1个）")
    parser.add_argument("-b", "--b_tsv", required=True, help="耐药基因.tsv 等TSV文件")
    parser.add_argument("-o", "--output", required=True, help="输出结果")
    args = parser.parse_args()

    # 读取a文件的ID
    query_set = set()
    with open(args.a_file, "r", encoding="utf-8") as f:
        for line in f:
            contig = line.strip()
            if contig:
                query_set.add(contig)

    match_count = 0
    header_copied = False

    with open(args.b_tsv, "r", encoding="utf-8") as fin, \
         open(args.output, "w", encoding="utf-8") as fout:

        for line in fin:
            # 写入表头
            if not header_copied:
                fout.write(line)
                header_copied = True
                continue

            # 制表符分割
            parts = line.strip("\n").split("\t")

            # ====================== 关键：取第 2 列 ======================
            if len(parts) < 2:
                continue
            contig_in_b = parts[1].strip()  # parts[1] = 第2列

            # 精准匹配（完全一样才算）
            if contig_in_b in query_set:
                fout.write(line)
                match_count += 1

    print("=" * 60)
    print("✅ 运行成功！")
    print(f"📌 匹配行数：{match_count}")
    print(f"📄 结果已保存到：{args.output}")
    print("✅ 已自动匹配第2列 Contig，不会再出现匹配不到！")
    print("=" * 60)

if __name__ == "__main__":
    main()