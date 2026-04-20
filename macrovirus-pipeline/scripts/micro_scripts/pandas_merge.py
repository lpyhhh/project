import pandas as pd
import glob
### 合并同一类型的文件，但不要表头
# 读取所有文件，跳过第一个以外的表头
df_list = []
for i, f in enumerate(glob.glob("/media/jjz/hdd/lpy/meige/SCUT-zou/results/checkv/*/quality_summary.tsv")):
    if i == 0:
        df = pd.read_csv(f, sep="\t")
    else:
        # 直接跳过表头，只读数据
        df = pd.read_csv(f, sep="\t", header=0, skiprows=1)
    df_list.append(df)

# 合并
final_df = pd.concat(df_list, ignore_index=True)
final_df.to_csv("/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/checkv.tsv", sep="\t", index=False)