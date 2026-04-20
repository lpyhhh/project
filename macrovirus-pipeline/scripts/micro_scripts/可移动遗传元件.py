import argparse
import csv
"""
要求：从a文件中每一行，在b文件的contig列csv文件中检索，将匹配到的输出到另一个文件中，同时命令行输出匹配到的行数。argparse实现，保留表头。
特殊，b文件contig列可能有冗余信息，比如说K10__9280是内容，a文件中某一行是K10__928，这样会错误匹配K10__9280，精准匹配contig
"""
def main():
    parser = argparse.ArgumentParser(description="从a文件精准匹配b.csv的contig列，完全相等才算匹配")
    parser.add_argument("-a", "--a_file", required=True, help="查询ID列表，每行一个")
    parser.add_argument("-b", "--b_csv", required=True, help="要检索的大CSV文件（含contig列）")
    parser.add_argument("-o", "--output", required=True, help="输出匹配结果CSV")
    parser.add_argument("-c", "--contig_col", default="contig", help="指定contig列名，默认contig")
    args = parser.parse_args()

    # 1. 读取a文件所有ID（去重、去空）
    print(f"正在读取查询文件：{args.a_file}")
    query_set = set()
    with open(args.a_file, "r", encoding="utf-8") as f:
        for line in f:
            contig_id = line.strip()
            if contig_id:
                query_set.add(contig_id)

    match_count = 0
    header_written = False

    print(f"开始精准检索CSV：{args.b_csv}")
    print(f"匹配列：{args.contig_col}")

    # 2. 逐行读取大CSV，精准匹配contig（完全相等）
    with open(args.b_csv, "r", encoding="utf-8", newline="") as fin, \
         open(args.output, "w", encoding="utf-8", newline="") as fout:

        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()  # 写入表头

        for row in reader:
            # 取出contig，去除空白
            contig = row[args.contig_col].strip()

            # ===================== 精准匹配（完全一样才算）=====================
            if contig in query_set:
                writer.writerow(row)
                match_count += 1

    print("=" * 60)
    print(f"✅ 精准匹配完成！")
    print(f"📌 成功匹配行数：{match_count}")
    print(f"📄 结果已保存到：{args.output}")
    print("✅ 完全精准匹配，不会把 K10__928 匹配到 K10__9280")
    print("=" * 60)

if __name__ == "__main__":
    main()