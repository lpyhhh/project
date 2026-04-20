#!/usr/bin/env bash
#运行该程序要求：1 lpy-FastViromeExplorer 2 cd /media/jjz/hdd/lpy/src/FastViromeExplorer
set -euo pipefail

# ===================== 配置区 =====================
RAW_DATA="/media/jjz/hdd/lpy/meige/SCUT-zou/data/clean_data"
OUTPUT_BASE="/media/jjz/hdd/lpy/meige/SCUT-zou/results/fve_95"
DB="/media/jjz/hdd/lpy/meige/SCUT-zou/results/mapping_1000_95.fa"                  # 你的参考数据库 fasta
GENOME_LIST="${DB}-list.txt"                    # generateGenomeList.sh 生成的列表

# FastViromeExplorer 路径（根据你的安装调整）
FVE_JAR_DIR="/media/jjz/hdd/lpy/src/FastViromeExplorer"
FVE_CMD="java -cp ${FVE_JAR_DIR}/bin FastViromeExplorer"

# 并行任务数（根据机器调整，建议 8~16，避免 IO 瓶颈）
PARALLEL_JOBS=1

# 可选：只运行名单中的样本（每行一个样本名）
SAMPLE_LIST_FILE="${SAMPLE_LIST_FILE:-}"

# 日志目录
LOG_DIR="${OUTPUT_BASE}/logs"
mkdir -p "${OUTPUT_BASE}" "${LOG_DIR}"

cd "${FVE_JAR_DIR}" || { echo "cd 到 FastViromeExplorer 目录失败"; exit 1; }
# ===================== 生成 genome list（如果还没生成） =====================
if [[ ! -s "${GENOME_LIST}" ]]; then
    echo "生成 genome list ..."
    bash utility-scripts/generateGenomeList.sh "${DB}" "${GENOME_LIST}"
fi

# ===================== 提取样本 ID（适配你的文件名格式） =====================
# 从 *_R1_kneaddata_paired_1.fastq.gz 提取前缀，如 K1a、Z10c 等
mapfile -t SAMPLE_LIST < <( \
    ls "${RAW_DATA}"/*_R1_kneaddata_paired_1.fastq.gz 2>/dev/null \
    | xargs -n1 basename \
    | sed 's/_R1_kneaddata_paired_1\.fastq\.gz$//' \
    | sort -u
)

# 如果提供了样本名单文件，则按名单过滤
if [[ -n "${SAMPLE_LIST_FILE}" ]]; then
    if [[ ! -s "${SAMPLE_LIST_FILE}" ]]; then
        echo "错误：SAMPLE_LIST_FILE 不存在或为空：${SAMPLE_LIST_FILE}"
        exit 1
    fi

    mapfile -t TARGET_SAMPLES < <(grep -v '^\s*$' "${SAMPLE_LIST_FILE}" | sort -u)
    declare -A target_map
    for sample in "${TARGET_SAMPLES[@]}"; do
        target_map["${sample}"]=1
    done

    FILTERED_SAMPLES=()
    for sample in "${SAMPLE_LIST[@]}"; do
        if [[ -n "${target_map[${sample}]:-}" ]]; then
            FILTERED_SAMPLES+=("${sample}")
        fi
    done
    SAMPLE_LIST=("${FILTERED_SAMPLES[@]}")
fi

if [[ ${#SAMPLE_LIST[@]} -eq 0 ]]; then
    echo "错误：在 ${RAW_DATA} 中没有找到 *_R1_kneaddata_paired_1.fastq.gz 文件"
    exit 1
fi

echo "找到 ${#SAMPLE_LIST[@]} 个样本："
printf '  %s\n' "${SAMPLE_LIST[@]}"
echo

# ===================== 并行处理每个样本 =====================
process_sample() {
    local sample="$1"
    local out_dir="${OUTPUT_BASE}/${sample}"
    local log_file="${LOG_DIR}/${sample}.log"
    local err_file="${out_dir}/${sample}.err"

    mkdir -p "${out_dir}"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始处理 ${sample}" | tee -a "${log_file}"

    # 构建输入文件路径
    local r1="${RAW_DATA}/${sample}_R1_kneaddata_paired_1.fastq.gz"
    local r2="${RAW_DATA}/${sample}_R1_kneaddata_paired_2.fastq.gz"

    if [[ ! -f "${r1}" || ! -f "${r2}" ]]; then
        echo "错误：${sample} 的 fastq 文件缺失" | tee -a "${log_file}"
        return 1
    fi

    # 执行 FastViromeExplorer
    ${FVE_CMD} \
        -1 "${r1}" \
        -2 "${r2}" \
        -o "${out_dir}" \
        -salmon true \
        -cn 7 \
        -co 0.1 \
        -cr 0 \
        -db "${DB}" \
        -l "${GENOME_LIST}" \
        > "${err_file}" 2>&1

    local exit_code=$?
    if [[ ${exit_code} -eq 0 ]]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${sample} 完成成功" | tee -a "${log_file}"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${sample} 失败 (exit code ${exit_code})，详见 ${err_file}" | tee -a "${log_file}"
    fi

    return ${exit_code}
}

export -f process_sample
export OUTPUT_BASE LOG_DIR FVE_CMD DB GENOME_LIST RAW_DATA

# 使用 GNU parallel 并行运行（需先安装 parallel）
echo "开始并行处理（最多同时 ${PARALLEL_JOBS} 个任务）..."
set +e
parallel --eta --progress --jobs ${PARALLEL_JOBS} \
    process_sample {} \
    ::: "${SAMPLE_LIST[@]}"
parallel_exit_code=$?
set -e

# 输出未生成 quant.sf 的样本清单
timestamp="$(date '+%Y%m%d_%H%M%S')"
missing_quant_log="${LOG_DIR}/missing_quant_${timestamp}.txt"

missing_count=0
: > "${missing_quant_log}"
for sample in "${SAMPLE_LIST[@]}"; do
    if [[ ! -s "${OUTPUT_BASE}/${sample}/quant.sf" ]]; then
        echo "${sample}" >> "${missing_quant_log}"
        ((missing_count++))
    fi
done

echo
echo "全部任务提交完成。"
echo "日志汇总目录：${LOG_DIR}"
echo "每个样本输出目录：${OUTPUT_BASE}/<sample>"
echo "错误/标准输出：每个样本目录下的 <sample>.err"
echo "未生成 quant.sf 的样本清单：${missing_quant_log} (count=${missing_count})"
echo "完成时间：$(date '+%Y-%m-%d %H:%M:%S')"

if [[ ${parallel_exit_code} -ne 0 || ${missing_count} -ne 0 ]]; then
    exit 1
fi