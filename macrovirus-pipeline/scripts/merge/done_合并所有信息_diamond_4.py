import csv
import sys
from pathlib import Path

def merge_second_tsv(merged_file_path, blast_file_path, final_output_path):
    """
    将第一次合并结果与BLAST结果文件进行匹配，并将匹配的记录合并到新文件
    
    参数:
    merged_file_path (str): 第一次合并结果文件路径
    blast_file_path (str): BLAST结果文件路径
    final_output_path (str): 最终输出文件路径
    """
    try:
        # 读取第一次合并结果文件
        with open(merged_file_path, 'r', newline='') as merged_file:
            merged_reader = csv.reader(merged_file, delimiter='\t')
            merged_header = next(merged_reader)  # 获取合并文件的表头
            merged_rows = list(merged_reader)
        
        # 读取BLAST结果文件，构建ID到整行的映射
        blast_dict = {}
        with open(blast_file_path, 'r', newline='') as blast_file:
            blast_reader = csv.reader(blast_file, delimiter='\t')
            blast_header = next(blast_reader)  # 获取BLAST文件的表头
            for row in blast_reader:
                blast_dict[row[0]] = row
        
        # 统计匹配行数
        matched_count = 0
        total_count = len(merged_rows)
        
        # 写入最终合并结果
        with open(final_output_path, 'w', newline='') as output_file:
            writer = csv.writer(output_file, delimiter='\t')
            
            # 构建并写入新表头
            new_header = merged_header + blast_header[1:]  # 合并表头，跳过blast的第一个ID列
            writer.writerow(new_header)
            
            # 处理每个ID
            for row in merged_rows:
                id_value = row[0]  # 假设ID在第一列
                if id_value in blast_dict:
                    # 找到匹配的ID，合并行（跳过blast的第一个ID列）
                    merged_row = row + blast_dict[id_value][1:]
                    writer.writerow(merged_row)
                    matched_count += 1
                else:
                    # 没有匹配的ID，填充#NA
                    na_cols = ['#NA'] * (len(blast_header) - 1)
                    writer.writerow(row + na_cols)
        
        # 输出统计信息
        print(f"第二次合并完成，结果已保存到 {final_output_path}")
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
    merged_file = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/merge/results_kraken2.tsv'  # 第一次合并的结果文件
    blast_file = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/diamond_results.tsv'    # 新的BLAST结果文件
    final_output = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/merge/results_diamond.tsv'  # 最终输出文件
    
    # 执行第二次合并
    merge_second_tsv(merged_file, blast_file, final_output)