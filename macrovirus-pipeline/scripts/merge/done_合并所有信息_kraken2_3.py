import csv
import sys
from pathlib import Path

def merge_fourth_tsv(third_merged_file_path, tax_file_path, final_output_path):
    """
    将第三次合并结果与分类文件进行匹配，并将匹配的记录合并到新文件
    
    参数:
    third_merged_file_path (str): 第三次合并结果文件路径
    tax_file_path (str): 分类文件路径
    final_output_path (str): 最终输出文件路径
    """
    try:
        # 读取第三次合并结果文件
        with open(third_merged_file_path, 'r', newline='') as merged_file:
            merged_reader = csv.reader(merged_file, delimiter='\t')
            merged_header = next(merged_reader)  # 获取合并文件的表头
            merged_rows = list(merged_reader)
        
        # 读取分类文件，构建contig_id(第二列)到整行的映射
        tax_dict = {}
        with open(tax_file_path, 'r', newline='') as tax_file:
            tax_reader = csv.reader(tax_file, delimiter='\t')
            tax_header = next(tax_reader)  # 获取分类文件的表头
            for row in tax_reader:
                contig_id = row[1]  # 第二列是contig_id
                tax_dict[contig_id] = row
        
        # 统计匹配行数
        matched_count = 0
        total_count = len(merged_rows)
        
        # 写入最终合并结果
        with open(final_output_path, 'w', newline='') as output_file:
            writer = csv.writer(output_file, delimiter='\t')
            
            # 构建并写入新表头
            # 跳过分类文件的第二列(contig_id)，避免重复
            new_header = merged_header + tax_header[:1] + tax_header[2:]
            writer.writerow(new_header)
            
            # 处理每个ID
            for row in merged_rows:
                id_value = row[0]  # 假设ID在第一列
                if id_value in tax_dict:
                    # 找到匹配的ID，合并行(跳过分类文件的第二列)
                    tax_row = tax_dict[id_value]
                    merged_row = row + tax_row[:1] + tax_row[2:]
                    writer.writerow(merged_row)
                    matched_count += 1
                else:
                    # 没有匹配的ID，填充#NA
                    # 计算需要填充的列数(分类文件列数减1，跳过contig_id列)
                    na_cols = ['#NA'] * (len(tax_header) - 1)
                    writer.writerow(row + na_cols)
        
        # 输出统计信息
        print(f"第四次合并完成，结果已保存到 {final_output_path}")
        print(f"总共处理 {total_count} 条记录")
        print(f"成功匹配 {matched_count} 条记录")
        print(f"未匹配 {total_count - matched_count} 条记录")
        
    except FileNotFoundError as e:
        print(f"错误：找不到文件 - {e.filename}")
        sys.exit(1)
    except Exception as e:
        print(f"发生未知错误：{e}")
        sys.exit(1)

if __name__ == "__main__":
    # 设置文件路径
    third_merged_file = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/merge/results_genomad.tsv'  # 第三次合并的结果文件
    tax_file = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/kraken2_results.tsv'             # 分类文件
    final_output = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/merge/results_kraken2.tsv'    # 最终输出文件
    
    # 执行第四次合并
    merge_fourth_tsv(third_merged_file, tax_file, final_output)    