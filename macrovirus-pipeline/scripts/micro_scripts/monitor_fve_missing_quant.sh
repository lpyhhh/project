#!/usr/bin/env bash
set -euo pipefail

RUN_PID="${1:?Usage: monitor_fve_missing_quant.sh <run_pid> <sample_list_file> <output_base> <log_dir>}"
SAMPLE_LIST_FILE="${2:?Usage: monitor_fve_missing_quant.sh <run_pid> <sample_list_file> <output_base> <log_dir>}"
OUTPUT_BASE="${3:?Usage: monitor_fve_missing_quant.sh <run_pid> <sample_list_file> <output_base> <log_dir>}"
LOG_DIR="${4:?Usage: monitor_fve_missing_quant.sh <run_pid> <sample_list_file> <output_base> <log_dir>}"

mkdir -p "${LOG_DIR}"
monitor_log="${LOG_DIR}/monitor_missing_quant.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] monitor start: pid=${RUN_PID}" >> "${monitor_log}"

while kill -0 "${RUN_PID}" 2>/dev/null; do
    sleep 300
done

timestamp="$(date '+%Y%m%d_%H%M%S')"
final_list="${LOG_DIR}/final_missing_quant_${timestamp}.txt"

: > "${final_list}"
while IFS= read -r sample || [[ -n "${sample}" ]]; do
    [[ -z "${sample// }" ]] && continue
    if [[ ! -s "${OUTPUT_BASE}/${sample}/quant.sf" ]]; then
        echo "${sample}" >> "${final_list}"
    fi
done < "${SAMPLE_LIST_FILE}"

count=$(wc -l < "${final_list}" | tr -d ' ')
echo "[$(date '+%Y-%m-%d %H:%M:%S')] monitor done: final_missing=${count}, file=${final_list}" >> "${monitor_log}"
