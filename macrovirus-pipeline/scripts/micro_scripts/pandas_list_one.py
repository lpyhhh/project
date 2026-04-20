import pandas as pd

files = [
    '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/checkv_results.tsv',
    '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/diamond_results.tsv',
    '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/genomad_results.tsv',
    '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/kraken2_results.tsv'   # 改成你的实际文件名
]

# 只读取第一列（accession，通常是第2列在 Diamond 输出，但你说第一列）
dfs = [pd.read_csv(f, sep='\t', usecols=[0], header=None, names=['id']) for f in files]

# 合并 + 去重
unique_ids = pd.concat(dfs)['id'].dropna().drop_duplicates().sort_values()

# 输出
unique_ids.to_csv('/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/one.tsv', index=False, header=False)
print(f"去重后唯一 ID 数量: {len(unique_ids)}")
print(unique_ids.head(20))