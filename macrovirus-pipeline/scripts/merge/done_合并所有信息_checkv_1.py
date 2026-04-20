import csv
import sys
from pathlib import Path

def merge_tsv_files(id_file_path, checkv_file_path, output_file_path):
    """
    读取两个TSV文件，根据第一列ID匹配，并将匹配的记录合并到新文件
    
    参数:
    id_file_path (str): ID文件路径
    checkv_file_path (str): 检查结果文件路径
    output_file_path (str): 输出文件路径
    """
    try:
        # 读取ID文件，提取ID列
        with open(id_file_path, 'r', newline='') as id_file:
            id_reader = csv.reader(id_file, delimiter='\t')
            id_header = next(id_reader)  # 获取ID文件的表头
            id_list = [row[0] for row in id_reader]
        
        # 读取检查结果文件，构建ID到整行的映射
        checkv_dict = {}
        with open(checkv_file_path, 'r', newline='') as checkv_file:
            checkv_reader = csv.reader(checkv_file, delimiter='\t')
            checkv_header = next(checkv_reader)  # 获取检查结果文件的表头
            for row in checkv_reader:
                checkv_dict[row[0]] = row
        
        # 统计匹配行数
        matched_count = 0
        total_count = len(id_list)
        
        # 写入合并结果
        with open(output_file_path, 'w', newline='') as output_file:
            writer = csv.writer(output_file, delimiter='\t')
            
            # 构建并写入新表头
            new_header = id_header + checkv_header[1:]  # 合并表头，跳过checkv的第一个ID列
            writer.writerow(new_header)
            
            # 处理每个ID
            for id_value in id_list:
                if id_value in checkv_dict:
                    # 找到匹配的ID，合并行（跳过checkv的第一个ID列）
                    merged_row = [id_value] + checkv_dict[id_value][1:]
                    writer.writerow(merged_row)
                    matched_count += 1
                else:
                    # 没有匹配的ID，填充#NA
                    na_cols = ['#NA'] * (len(checkv_header) - 1)
                    writer.writerow([id_value] + na_cols)
        
        # 输出统计信息
        print(f"合并完成，结果已保存到 {output_file_path}")
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
    id_file = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/one.tsv'
    checkv_file = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/data/checkv_results.tsv'
    output_file = '/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy/merge/results_checkv.tsv'
    
    # 执行合并
    merge_tsv_files(id_file, checkv_file, output_file)