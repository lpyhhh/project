#!/usr/bin/env bash
set -euo pipefail

# 用法：
# 1) 全量运行：
#    bash run_fve_workflow.sh
# 2) 仅重跑缺少 quant.sf 的样本：
#    bash run_fve_workflow.sh --missing-only
# 3) 指定样本名单文件运行：
#    bash run_fve_workflow.sh --sample-list /path/to/sample_list.txt

PROJECT_ROOT="/media/jjz/hdd/lpy/meige/SCUT-zou"
FVE_SCRIPT="${PROJECT_ROOT}/scripts/micro_scripts/fve.sh"
FVE_OUTPUT_BASE="${PROJECT_ROOT}/results/fve"
FVE_LOG_DIR="${FVE_OUTPUT_BASE}/logs"
CONDA_ENV="lpy-FastViromeExplorer"

MODE="all"
SAMPLE_LIST_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --missing-only)
            MODE="missing"
            shift
            ;;
        --sample-list)
            MODE="list"
            SAMPLE_LIST_FILE="${2:-}"
            if [[ -z "${SAMPLE_LIST_FILE}" ]]; then
                echo "错误：--sample-list 需要提供文件路径"
                exit 1
            fi
            shift 2
            ;;
        *)
            echo "未知参数：$1"
            exit 1
            ;;
    esac
done

mkdir -p "${FVE_LOG_DIR}"

if ! command -v conda >/dev/null 2>&1; then
    echo "错误：未找到 conda，请先安装并配置 conda"
    exit 1
fi

if [[ ! -f "${FVE_SCRIPT}" ]]; then
    echo "错误：未找到脚本 ${FVE_SCRIPT}"
    exit 1
fi

if [[ "${MODE}" == "missing" ]]; then
    SAMPLE_LIST_FILE="${FVE_LOG_DIR}/missing_quant_rerun_input.txt"
    python - <<'PY'
import os
base='/media/jjz/hdd/lpy/meige/SCUT-zou/results/fve'
out='/media/jjz/hdd/lpy/meige/SCUT-zou/results/fve/logs/missing_quant_rerun_input.txt'
subs=sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base,d)) and d!='logs'])
missing=[d for d in subs if not os.path.isfile(os.path.join(base,d,'quant.sf'))]
with open(out,'w',encoding='utf-8') as f:
    for d in missing:
        f.write(d+'\n')
print(f"missing_count={len(missing)}")
print(f"sample_list={out}")
PY
fi

if [[ "${MODE}" == "list" || "${MODE}" == "missing" ]]; then
    if [[ ! -s "${SAMPLE_LIST_FILE}" ]]; then
        echo "错误：样本名单不存在或为空：${SAMPLE_LIST_FILE}"
        exit 1
    fi
fi

ts="$(date '+%Y%m%d_%H%M%S')"
run_log="${FVE_LOG_DIR}/run_fve_workflow_${ts}.log"

echo "开始运行时间：$(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${run_log}"
echo "模式：${MODE}" | tee -a "${run_log}"
[[ -n "${SAMPLE_LIST_FILE}" ]] && echo "样本名单：${SAMPLE_LIST_FILE}" | tee -a "${run_log}"

if [[ -n "${SAMPLE_LIST_FILE}" ]]; then
    SAMPLE_LIST_FILE="${SAMPLE_LIST_FILE}" conda run -n "${CONDA_ENV}" bash "${FVE_SCRIPT}" | tee -a "${run_log}"
else
    conda run -n "${CONDA_ENV}" bash "${FVE_SCRIPT}" | tee -a "${run_log}"
fi

final_missing="${FVE_LOG_DIR}/missing_quant_after_run_${ts}.txt"
python - <<PY
import os
base='${FVE_OUTPUT_BASE}'
out='${final_missing}'
subs=sorted([d for d in os.listdir(base) if os.path.isdir(os.path.join(base,d)) and d!='logs'])
missing=[d for d in subs if not os.path.isfile(os.path.join(base,d,'quant.sf'))]
with open(out,'w',encoding='utf-8') as f:
    for d in missing:
        f.write(d+'\n')
print(f'final_missing_count={len(missing)}')
print(f'final_missing_file={out}')
PY

echo "运行结束时间：$(date '+%Y-%m-%d %H:%M:%S')" | tee -a "${run_log}"
echo "总日志：${run_log}" | tee -a "${run_log}"
echo "未生成 quant.sf 清单：${final_missing}" | tee -a "${run_log}"
