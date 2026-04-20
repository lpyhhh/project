#!/usr/bin/env bash

set -euo pipefail

# 配置（请检查/修改）
DIAMOND_DIR="/media/jjz/hdd/lpy/meige/SCUT-zou/results/test"
OUTPUT_DIR="${DIAMOND_DIR}/tax_results"
ACC2TAX_FILE="/media/jjz/hdd/lpy/DB/diamond/prot.accession2taxid"  # 支持 .gz 或纯文本
TAXDUMP_DIR="/media/jjz/hdd/lpy/DB/taxid"
DUCKDB_DB_FILE="${DIAMOND_DIR}/tax_results/duckdb_tax.db"  # 持久化到当前目录或 /fast/ssd/path/duckdb_tax.db
THREADS=96  # 留点给系统，别全占 96

mkdir -p "${OUTPUT_DIR}"

# DuckDB 命令 + 优化设置
DUCKDB="duckdb ${DUCKDB_DB_FILE}"

# 第一步：一次性建大表 + 优化设置（只跑一次！）
# echo "=== 首次建 acc2tax 表（如果已存在会跳过或覆盖） ==="
# ${DUCKDB} <<EOF
# SET memory_limit = '400GB';
# SET threads TO ${THREADS};
# SET preserve_insertion_order = false;
# SET temp_directory = '/tmp/duckdb_tmp';  -- 改成你的 SSD 快路径，如果 /tmp 是 ramdisk 更好

# -- 如果表已存在，可先 DROP TABLE acc2tax; 但首次建时注释掉
# CREATE OR REPLACE TABLE acc2tax AS
# SELECT * FROM read_csv_auto(
#     '${ACC2TAX_FILE}',
#     delim='\t',
#     header=True,
#     columns={
#         'accession': 'VARCHAR',
#         'accession.version': 'VARCHAR',
#         'taxid': 'UBIGINT',
#         'gi': 'UBIGINT'
#     }
# );

# -- 可选：建索引加速重复查询（accession.version 是常用匹配列）
# CREATE INDEX idx_acc_ver ON acc2tax("accession.version");
# CREATE INDEX idx_acc ON acc2tax(accession);
# EOF

# echo "大表构建完成！后续每个文件只需查询。"

# 第二步：循环处理每个 .tab 文件
for tab_file in "${DIAMOND_DIR}"/*.tab; do
    base=$(basename "${tab_file}" .tab)
    echo "处理: ${base}.tab"

    uniq_acc="${OUTPUT_DIR}/${base}.unique_acc.txt"
    acc_tax_tsv="${OUTPUT_DIR}/${base}.acc_to_taxid.tsv"
    taxids_txt="${OUTPUT_DIR}/${base}.taxids.txt"
    lineage_txt="${OUTPUT_DIR}/${base}.lineage.txt"
    final_out="${OUTPUT_DIR}/${base}.diamond_with_tax.tsv"

    # 1. 提取 unique accession（如果已存在可跳过，但建议每次重提防更新）
    awk '{print $2}' "${tab_file}" | sort | uniq > "${uniq_acc}"

    # 2. duckdb 查询 taxid（利用已建表，极快）
    ${DUCKDB} <<EOF
    CREATE OR REPLACE TABLE queries AS
    SELECT column0 AS accession FROM read_csv_auto('${uniq_acc}', header=False);

    COPY (
        SELECT 
            q.accession AS query_acc,
            COALESCE(a."accession.version", a.accession) AS matched_acc,
            a.taxid
        FROM queries q
        LEFT JOIN acc2tax a 
            ON q.accession = a."accession.version" 
            OR q.accession = a.accession
    ) TO '${acc_tax_tsv}' (FORMAT CSV, HEADER, DELIMITER '\t');
EOF

    # 3. 提取 taxids 并用 taxonkit 加 lineage
    if [ -s "${acc_tax_tsv}" ]; then
        cut -f3 "${acc_tax_tsv}" | grep -v '^$' | sort -u > "${taxids_txt}"

        taxonkit lineage "${taxids_txt}" \
            --data-dir "${TAXDUMP_DIR}" \
            --show-lineage-ranks \
        | taxonkit reformat -P \
            -f "{k}\t{p}\t{c}\t{o}\t{f}\t{g}\t{s}" \
            -o "${lineage_txt}"

        # 合并回原表：用 join（taxid 作为 key）
        # 先准备 acc_tax + lineage
        join -t $'\t' -1 3 -2 1 \
            <(sort -k3 "${acc_tax_tsv}") \
            <(sort -k1 "${lineage_txt}") \
        | awk -F'\t' 'BEGIN {OFS="\t"} {print $2,$1,$3,$4,$5,$6,$7,$8,$9,$10}' \
        > "${final_out}"  # 调整列顺序：query_acc, matched_acc, taxid, k, p, c, o, f, g, s

        echo "完成: ${final_out} （包含 accession + taxid + 域 门 纲 目 科 属 种）"
    else
        echo "警告: ${acc_tax_tsv} 为空，跳过 lineage"
    fi
done

echo "全部处理完毕。结果在 ${OUTPUT_DIR}"
echo "DuckDB 数据库文件: ${DUCKDB_DB_FILE} （下次直接用，无需重读大文件）"