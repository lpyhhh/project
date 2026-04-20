#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.perf import run_and_profile
from utils.common import ensure_uncompressed, list_samples, find_read_pair


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run FastViromeExplorer for all samples")
    parser.add_argument("--results-megahit", required=True, help="Megahit results directory")
    parser.add_argument("--results-fve", required=True, help="FVE output directory")
    parser.add_argument("--reads-dir", required=True, help="Reads directory")
    parser.add_argument("--reads-dir-alt", default="", help="Alternative reads directory")
    parser.add_argument("--reps", default="a,b,c", help="Replicates, comma-separated")
    parser.add_argument("--fve-root", required=True, help="FastViromeExplorer repo path")
    parser.add_argument("--log-dir", required=True, help="Log directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_megahit = Path(args.results_megahit)
    results_fve = Path(args.results_fve)
    reads_dir = Path(args.reads_dir)
    reads_dir_alt = Path(args.reads_dir_alt) if args.reads_dir_alt else None
    fve_root = Path(args.fve_root)
    log_dir = Path(args.log_dir)

    fve_root.mkdir(parents=True, exist_ok=True)
    results_fve.mkdir(parents=True, exist_ok=True)

    samples = list_samples(results_megahit)
    if not samples:
        raise SystemExit("No contigs found in results_megahit")

    reps = [r.strip() for r in args.reps.split(",") if r.strip()]
    for sample in samples:
        contig = ensure_uncompressed(results_megahit, sample)
        list_file = results_megahit / f"{sample}.txt"
        subprocess.run(
            [
                "bash",
                str(fve_root / "utility-scripts" / "generateGenomeList.sh"),
                str(contig),
                str(list_file),
            ],
            check=True,
            cwd=str(fve_root),
        )

        found_any = False
        for rep in reps:
            sample_rep = f"{sample}{rep}"
            pair = find_read_pair(reads_dir, reads_dir_alt, sample_rep)
            if not pair:
                continue
            found_any = True
            r1, r2 = pair
            outdir = results_fve / sample_rep
            outdir.mkdir(parents=True, exist_ok=True)

            cmd: List[str] = [
                "java",
                "-cp",
                "bin",
                "FastViromeExplorer",
                "-1",
                str(r1),
                "-2",
                str(r2),
                "-o",
                str(outdir),
                "-salmon",
                "true",
                "-cn",
                "7",
                "-co",
                "0.1",
                "-cr",
                "0",
                "-db",
                str(contig),
                "-l",
                str(list_file),
            ]
            run_and_profile(cmd, log_dir, f"FastViromeExplorer:{sample_rep}", work_dir=fve_root)

        if not found_any:
            print(f"[WARN] No read pairs found for {sample} ({','.join(reps)}), skip.")


if __name__ == "__main__":
    main()
