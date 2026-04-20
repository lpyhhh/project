import os
import pandas as pd

# 定义文件路径
bam_dir = "/media/jjz/hdd/lpy/meige/SCUT-zou/results/fve_95"
tsv_file = "/media/jjz/hdd/lpy/meige/SCUT-zou/results/merge/mapping_no_mapping.tsv"
backup_file = "/media/jjz/hdd/lpy/meige/SCUT-zou/results/merge/results_95.tsv"  # 备份文件路径

# 备份原始 TSV 文件
try:
    if os.path.exists(tsv_file):
        import shutil
        shutil.copy(tsv_file, backup_file)
        print(f"Backed up TSV file to {backup_file}")
except Exception as e:
    print(f"Error during backup: {e}")
    exit(1)

# 检查 bam_dir 是否存在
if not os.path.exists(bam_dir):
    print(f"Error: Directory {bam_dir} does not exist")
    exit(1)

# 获取所有变量名（从文件夹名提取）
variables = [
    folder for folder in os.listdir(bam_dir)
    if os.path.isdir(os.path.join(bam_dir, folder)) and os.path.exists(os.path.join(bam_dir, folder, "quant.sf"))
]

# 读取原始 TSV 文件，保留 #NA 值
try:
    df = pd.read_csv(tsv_file, sep='\t', keep_default_na=False, na_values=[], low_memory=False)
except FileNotFoundError:
    print(f"Error: TSV file {tsv_file} not found")
    exit(1)
except pd.errors.ParserError:
    print(f"Error: Failed to parse TSV file {tsv_file}. Check file format and delimiter")
    exit(1)

# 获取当前表头
metadata_anchor = 'taxname_diamond'
if metadata_anchor in df.columns:
    base_end = df.columns.get_loc(metadata_anchor) + 1
    df = df.iloc[:, :base_end].copy()

current_headers = df.columns.tolist()
print(f"Base headers ({len(current_headers)}): {current_headers}")

# 确保用于匹配的 contig_id 是字符串
df['contig_id'] = df['contig_id'].astype(str)

# 追加样本列（每次重建，不重复累加）
for var in sorted(variables):
    df[var] = pd.Series([pd.NA] * len(df), dtype='Float64')

new_headers = df.columns.tolist()

# 遍历每个变量（文件夹），匹配并插入 TPM 值
for var in variables:
    quant_sf_path = os.path.join(bam_dir, var, "quant.sf")
    try:
        # 读取 quant.sf 文件
        quant_df = pd.read_csv(quant_sf_path, sep='\t', keep_default_na=False, na_values=[])
        quant_df['Name'] = quant_df['Name'].astype(str)
        quant_df['TPM'] = pd.to_numeric(quant_df['TPM'], errors='coerce')
        # 创建 Name 到 TPM 的映射
        tpm_map = dict(zip(quant_df['Name'], quant_df['TPM']))

        # 匹配 TSV 的 contig_id 和 quant.sf 的 Name，插入 TPM 值
        df[var] = df['contig_id'].map(tpm_map).astype('Float64')
        print(f"Processed {quant_sf_path}: matched {df[var].notna().sum()} contig IDs")
    except Exception as e:
        print(f"Error processing {quant_sf_path}: {e}")
        continue

# 保存修改后的 TSV 文件
try:
    df.to_csv(tsv_file, sep='\t', index=False, na_rep='')
    print(f"Updated TSV file with {len(variables)} new headers and TPM values. New headers: {new_headers}")
except PermissionError:
    print(f"Error: Permission denied when writing to {tsv_file}")
    exit(1)

print("Processing completed successfully")