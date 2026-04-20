#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCRIPTS="${SCRIPTS:-/media/jjz/hdd/lpy/meige/SCUT-zou/scripts}"
MICRO_SCRIPTS="${MICRO_SCRIPTS:-${SCRIPTS}/micro_scripts}"
MERGE_SCRIPTS="${MERGE_SCRIPTS:-${SCRIPTS}/merge}"
VFDB_SCRIPTS="${VFDB_SCRIPTS:-${SCRIPTS}/vfdb_script}"

OUTPUT="${OUTPUT:-/media/jjz/hdd/lpy/meige/SCUT-zou/results}"
RED="${RED:-/media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy}"
TAXONKIT_DB="${TAXONKIT_DB:-/media/jjz/hdd/lpy/DB/taxid}"
SAMPLE_LIST="${SAMPLE_LIST:-${OUTPUT}/fve/missing_quant_current.txt}"
PHABOX_DB="${PHABOX_DB:-/media/jjz/hdd/lpy/DB/phabox_db_v2}"
VFDB_FASTA="${VFDB_FASTA:-/media/jjz/hdd/lpy/DB/vfdb/VFDB_setA_pro.fas.gz}"
VFDB_DB_PREFIX="${VFDB_DB_PREFIX:-/media/jjz/hdd/lpy/DB/vfdb/vfdb_setA_pro}"

THREADS="${THREADS:-64}"
PIPELINE_MODE="full"
RUN_REDUNDANCY="false"
RUN_DRAM_DB_SETUP="false"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/main.sh [options]

Options:
  --mode <core|full|downstream>   core: 步骤1-3, downstream: 下游分析, full: core+downstream
  --with-redundancy               追加执行冗余分析区块（MGE/VFDB/CARD/DRAM-V）
  --with-dram-db-setup            执行 DRAM 数据库准备命令
  --scripts <path>                脚本根目录（含 micro_scripts/ merge/ vfdb_script/）
  --output <path>                 结果目录
  --red <path>                    冗余目录
  --taxonkit-db <path>            taxonkit 数据库目录
  --sample-list <path>            run_fve_workflow.sh 所需 sample list
  --threads <int>                 并行线程数，默认 64
  --help                          显示帮助

Environment variables can also be used:
  SCRIPTS, MICRO_SCRIPTS, MERGE_SCRIPTS, VFDB_SCRIPTS, OUTPUT, RED,
  TAXONKIT_DB, SAMPLE_LIST, THREADS, PHABOX_DB, VFDB_FASTA, VFDB_DB_PREFIX.
EOF
}

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

run() {
  log "RUN: $*"
  "$@"
}

run_to_file() {
  local output_file="$1"
  shift
  log "RUN: $* > ${output_file}"
  "$@" > "$output_file"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    log "ERROR: missing command: $1"
    exit 1
  }
}

require_file() {
  [[ -f "$1" ]] || {
    log "ERROR: missing file: $1"
    exit 1
  }
}

ensure_dirs() {
  run mkdir -p "${RED}/data" "${RED}/merge" "${OUTPUT}/merge" "${OUTPUT}/gene"
}

concat_from_find() {
  local search_dir="$1"
  local pattern="$2"
  local output_file="$3"
  local -a files=()

  mapfile -d '' files < <(find "$search_dir" -type f -name "$pattern" -print0 2>/dev/null)
  if (( ${#files[@]} == 0 )); then
    log "WARN: no file matched ${search_dir} / ${pattern}"
    : > "$output_file"
    return 0
  fi

  cat "${files[@]}" > "$output_file"
}

filter_virus_lines() {
  local input_file="$1"
  local output_file="$2"
  if ! grep -i 'Virus' "$input_file" > "$output_file"; then
    : > "$output_file"
    log "WARN: no Virus lines in ${input_file}"
  fi
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode)
        PIPELINE_MODE="$2"
        shift 2
        ;;
      --with-redundancy)
        RUN_REDUNDANCY="true"
        shift
        ;;
      --with-dram-db-setup)
        RUN_DRAM_DB_SETUP="true"
        shift
        ;;
      --scripts)
        SCRIPTS="$2"
        MICRO_SCRIPTS="${SCRIPTS}/micro_scripts"
        MERGE_SCRIPTS="${SCRIPTS}/merge"
        VFDB_SCRIPTS="${SCRIPTS}/vfdb_script"
        shift 2
        ;;
      --output)
        OUTPUT="$2"
        SAMPLE_LIST="${OUTPUT}/fve/missing_quant_current.txt"
        shift 2
        ;;
      --red)
        RED="$2"
        shift 2
        ;;
      --taxonkit-db)
        TAXONKIT_DB="$2"
        shift 2
        ;;
      --sample-list)
        SAMPLE_LIST="$2"
        shift 2
        ;;
      --threads)
        THREADS="$2"
        shift 2
        ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        log "ERROR: unknown argument: $1"
        usage
        exit 1
        ;;
    esac
  done

  case "$PIPELINE_MODE" in
    core|full|downstream) ;;
    *)
      log "ERROR: --mode only supports core|full|downstream"
      exit 1
      ;;
  esac
}

check_prerequisites() {
  require_cmd bash
  require_cmd python3
  require_cmd awk
  require_cmd grep
  require_cmd seqkit
  require_cmd taxonkit

  require_file "${MICRO_SCRIPTS}/diamond_head_only_one.sh"
  require_file "${MICRO_SCRIPTS}/fve.sh"
  require_file "${MICRO_SCRIPTS}/run_fve_workflow.sh"
  require_file "${MICRO_SCRIPTS}/pandas_list_one.py"
  require_file "${MERGE_SCRIPTS}/done_合并所有信息_checkv_1.py"
  require_file "${MERGE_SCRIPTS}/done_合并所有信息_genomad_2.py"
  require_file "${MERGE_SCRIPTS}/done_合并所有信息_kraken2_3.py"
  require_file "${MERGE_SCRIPTS}/done_合并所有信息_diamond_4.py"
  require_file "${MERGE_SCRIPTS}/done_合并所有信息_mapping_5.py"
}

step_collect_software_results() {
  log 'Step 1: 汇总四个软件结果并筛病毒'

  run bash "${MICRO_SCRIPTS}/diamond_head_only_one.sh"
  concat_from_find "${OUTPUT}/diamond_only-one" '*.tab' "${RED}/data/diamond.tab"
  run taxonkit lineage -i 13 "${RED}/data/diamond.tab" -j "${THREADS}" --data-dir "${TAXONKIT_DB}" -o "${RED}/data/diamond_1.tab"
  filter_virus_lines "${RED}/data/diamond_1.tab" "${RED}/data/diamond_results.tsv"

  concat_from_find "${OUTPUT}/checkv" 'quality_summary.tsv' "${RED}/data/checkv_all.tsv"
  run_to_file "${RED}/data/checkv_results.tsv" awk -F '\t' 'NR==1 || ($6 > $7 && !($6 == 0 && $7 == 0))' "${RED}/data/checkv_all.tsv"

  concat_from_find "${OUTPUT}/kraken2" 'kraken2_output.txt' "${RED}/data/kraken2.txt"
  run sort -t $'\t' -k3,3 "${RED}/data/kraken2.txt" -o "${RED}/data/kraken2_1.tsv"
  run taxonkit lineage -i 3 "${RED}/data/kraken2_1.tsv" -j "${THREADS}" --data-dir "${TAXONKIT_DB}" -o "${RED}/data/kraken2_2.tsv"
  filter_virus_lines "${RED}/data/kraken2_2.tsv" "${RED}/data/kraken2_results.tsv"

  concat_from_find "${OUTPUT}/genomad" '*.contig.ok_virus_summary.tsv' "${RED}/data/genomad_results.tsv"
}

step_extract_and_mapping() {
  log 'Step 2: 提取病毒序列并执行 mapping'

  require_file "${OUTPUT}/all.ok.fa"
  run python3 "${MICRO_SCRIPTS}/pandas_list_one.py"
  run_to_file "${OUTPUT}/mapping.fa" seqkit grep -j "${THREADS}" -f "${RED}/data/one.tsv" "${OUTPUT}/all.ok.fa"

  run bash "${MICRO_SCRIPTS}/fve.sh"
  require_file "${SAMPLE_LIST}"
  run bash "${MICRO_SCRIPTS}/run_fve_workflow.sh" --sample-list "${SAMPLE_LIST}"
}

step_merge_results() {
  log 'Step 3: 合并 checkv/genomad/kraken2/diamond/mapping 结果'

  run python3 "${MERGE_SCRIPTS}/done_合并所有信息_checkv_1.py"
  run python3 "${MERGE_SCRIPTS}/done_合并所有信息_genomad_2.py"
  run python3 "${MERGE_SCRIPTS}/done_合并所有信息_kraken2_3.py"
  run python3 "${MERGE_SCRIPTS}/done_合并所有信息_diamond_4.py"
  run python3 "${MERGE_SCRIPTS}/done_合并所有信息_mapping_5.py"

  require_file "${RED}/merge/results_diamond.tsv"
  run cp "${RED}/merge/results_diamond.tsv" "${OUTPUT}/merge/results.tsv"
}

step_downstream() {
  log 'Step 4: 下游分析（过滤、聚类、二次mapping、功能注释、生活史）'

  require_cmd cd-hit-est
  require_cmd phabox2
  require_file "${OUTPUT}/mapping.fa"

  run_to_file "${OUTPUT}/mapping_1000.fa" seqkit seq -m 1000 "${OUTPUT}/mapping.fa"
  run cd-hit-est -i "${OUTPUT}/mapping_1000.fa" -o "${OUTPUT}/mapping_1000_95.fa" -c 0.95 -aS 0.5 -n 10 -g 1 -G 0 -d 0 -p 1 -M 0 -T 0

  run_to_file "${OUTPUT}/mapping_1000_95.id" seqkit seq -n "${OUTPUT}/mapping_1000_95.fa"
  run python3 "${MICRO_SCRIPTS}/id提取tpm文件.py" -a "${OUTPUT}/mapping_1000_95.id" -b "${OUTPUT}/merge/results.tsv" -o "${OUTPUT}/merge/mapping_no_mapping.tsv"

  run bash "${MICRO_SCRIPTS}/fve.sh"
  run bash "${MICRO_SCRIPTS}/run_fve_workflow.sh" --sample-list "${SAMPLE_LIST}"
  run python3 "${MERGE_SCRIPTS}/done_合并所有信息_mapping_5.py"

  run python3 "${MICRO_SCRIPTS}/毒力基因.py" -a "${OUTPUT}/mapping_1000_95.id" -b "${OUTPUT}/gene/毒力基因.tsv" -o "${OUTPUT}/gene/毒力基因_1.tsv"
  run python3 "${MICRO_SCRIPTS}/辅助代谢.py" -a "${OUTPUT}/mapping_1000_95.id" -b "${OUTPUT}/gene/辅助代谢基因.tsv" -o "${OUTPUT}/gene/辅助代谢基因_1.tsv"
  run python3 "${MICRO_SCRIPTS}/可移动遗传元件.py" -a "${OUTPUT}/mapping_1000_95.id" -b "${OUTPUT}/gene/可移动遗传元件.csv" -o "${OUTPUT}/gene/可移动遗传元件_1.csv" -c contig
  run python3 "${MICRO_SCRIPTS}/耐药基因.py" -a "${OUTPUT}/mapping_1000_95.id" -b "${OUTPUT}/gene/耐药基因.tsv" -o "${OUTPUT}/gene/耐药基因_1.tsv"

  run phabox2 --task end_to_end --contigs "${OUTPUT}/mapping_1000_95.fa" --dbdir "${PHABOX_DB}" --outpth "${RED}/phabox" --len 1000
}

step_redundancy() {
  log 'Step 5: 冗余分析（MGE/VFDB/CARD/DRAM-V）'

  require_cmd mefinder
  require_cmd diamond
  require_cmd prodigal
  require_cmd rgi
  require_cmd virsorter
  require_cmd DRAM-v.py

  run mkdir -p "${RED}/megs" "${RED}/vfdb" "${RED}/card" "${RED}/fuzhu/dram"
  run mefinder find -g -t "${THREADS}" --contig "${OUTPUT}/mapping_1000.fa" "${RED}/megs"

  run diamond makedb --in "${VFDB_FASTA}" --db "${VFDB_DB_PREFIX}"
  run prodigal -i "${OUTPUT}/mapping_1000.fa" -a "${OUTPUT}/mapping_1000_protein.fa" -f gff -p meta
  run diamond blastp -d "${VFDB_DB_PREFIX}" -q "${OUTPUT}/mapping_1000_protein.fa" -f 0 -k 5 -e 1e-5 -p "${THREADS}" -o "${RED}/vfdb/vfdb_results.tsv"
  run_to_file "${RED}/vfdb/vfdb_results_1.tsv" perl "${VFDB_SCRIPTS}/parse_blastp_1hits_VFDB.pl" "${RED}/vfdb/vfdb_results.tsv"

  require_file "card.json"
  run rgi load --card_json card.json --local
  run rgi main -a DIAMOND --input_sequence "${OUTPUT}/mapping_1000.fa" --output_file "${RED}/card/card.card" --input_type contig -n "${THREADS}" --include_loose --clean

  run virsorter run --viral-gene-enrich-off --prep-for-dramv -i "${OUTPUT}/mapping_1000.fa" -w "${RED}/fuzhu/virsort_3" --include-groups dsDNAphage,NCLDV,RNA,ssDNA,lavidaviridae --min-length 1000 --min-score 0.5 -j "${THREADS}" all
  run DRAM-v.py annotate -i "${RED}/fuzhu/virsort/for-dramv/final-viral-combined-for-dramv.fa" -v "${RED}/fuzhu/virsort/for-dramv/viral-affi-contigs-for-dramv.tab" -o "${RED}/fuzhu/dram" --threads "${THREADS}"
  run DRAM-v.py distill -i "${RED}/fuzhu/dram/annotations.tsv" -o "${RED}/fuzhu/dram/subset"
}

step_dram_db_setup() {
  log 'Optional: DRAM 数据库准备'
  require_cmd DRAM-setup.py
  run DRAM-setup.py prepare_databases --output_dir DRAM_data --skip_uniref --threads "${THREADS}"
}

main() {
  parse_args "$@"
  ensure_dirs
  check_prerequisites

  log "Pipeline mode: ${PIPELINE_MODE}, redundancy: ${RUN_REDUNDANCY}, dram-db-setup: ${RUN_DRAM_DB_SETUP}"

  if [[ "${PIPELINE_MODE}" == "core" || "${PIPELINE_MODE}" == "full" ]]; then
    step_collect_software_results
    step_extract_and_mapping
    step_merge_results
  fi

  if [[ "${PIPELINE_MODE}" == "downstream" || "${PIPELINE_MODE}" == "full" ]]; then
    step_downstream
  fi

  if [[ "${RUN_REDUNDANCY}" == "true" ]]; then
    step_redundancy
  fi

  if [[ "${RUN_DRAM_DB_SETUP}" == "true" ]]; then
    step_dram_db_setup
  fi

  log 'Pipeline finished successfully.'
}

main "$@"