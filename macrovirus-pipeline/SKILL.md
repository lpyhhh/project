---
name: macrovirus-pipeline
description: "Use when running or maintaining the 宏病毒组 workflow: aggregate diamond/checkv/kraken2/genomad outputs, build mapping sequences, merge results, run downstream vOTU and gene analysis, or execute redundancy analysis via scripts/main.sh."
---

# 宏病毒组 Pipeline Skill

用于调用和维护 `scripts/main.sh` 的完整流程化执行。

## When To Use

- 用户提到“跑宏病毒组流程 / 跑 main.sh / 一键执行流程”。
- 用户要执行以下任一阶段：
  - core（四软件汇总 + mapping + merge）
  - downstream（长度过滤、聚类、功能注释、phabox2）
  - redundancy（MGE/VFDB/CARD/DRAM-V）
- 用户要修改目录参数（`OUTPUT`、`RED`、`TAXONKIT_DB`、`SAMPLE_LIST`）。

## Quick Start Commands

1. 执行核心流程（步骤 1-3）：

```bash
bash scripts/main.sh --mode core \
  --scripts /media/jjz/hdd/lpy/meige/SCUT-zou/scripts \
  --output /media/jjz/hdd/lpy/meige/SCUT-zou/results \
  --red /media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy \
  --taxonkit-db /media/jjz/hdd/lpy/DB/taxid \
  --threads 64
```

2. 执行完整流程（core + downstream）：

```bash
bash scripts/main.sh --mode full \
  --scripts /media/jjz/hdd/lpy/meige/SCUT-zou/scripts \
  --output /media/jjz/hdd/lpy/meige/SCUT-zou/results \
  --red /media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy \
  --taxonkit-db /media/jjz/hdd/lpy/DB/taxid \
  --sample-list /media/jjz/hdd/lpy/meige/SCUT-zou/results/fve/missing_quant_current.txt \
  --threads 64
```

3. 只跑下游步骤：

```bash
bash scripts/main.sh --mode downstream \
  --scripts /media/jjz/hdd/lpy/meige/SCUT-zou/scripts \
  --output /media/jjz/hdd/lpy/meige/SCUT-zou/results \
  --red /media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy
```

4. 完整流程 + 冗余分析：

```bash
bash scripts/main.sh --mode full --with-redundancy \
  --scripts /media/jjz/hdd/lpy/meige/SCUT-zou/scripts \
  --output /media/jjz/hdd/lpy/meige/SCUT-zou/results \
  --red /media/jjz/hdd/lpy/meige/SCUT-zou/3-redundancy \
  --taxonkit-db /media/jjz/hdd/lpy/DB/taxid \
  --threads 64
```

## Expected Outputs

- `${RED}/data/*_results.tsv`
- `${OUTPUT}/mapping.fa`
- `${OUTPUT}/merge/results.tsv`
- `${OUTPUT}/mapping_1000_95.fa`
- `${OUTPUT}/gene/*.tsv` 与 `${OUTPUT}/gene/*.csv`
- `${RED}/phabox/`

## Notes For Safe Execution

- 先确认 `scripts/micro_scripts` 与 `scripts/merge` 中脚本完整。
- `--with-redundancy` 依赖 `mefinder`, `diamond`, `prodigal`, `rgi`, `virsorter`, `DRAM-v.py`。
- 若使用默认路径，确保 `/media/jjz/hdd/lpy/meige/SCUT-zou/` 在当前机器可访问。
- 可通过 `bash scripts/main.sh --help` 查看全部参数。