#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.perf import run_and_profile
from utils.common import ensure_uncompressed, list_samples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run diamond for all samples")
    parser.add_argument("--results-megahit", help="Megahit results directory")
    parser.add_argument("--results-diamond", help="diamond output directory")
    parser.add_argument("--query", help="Input query FASTA (override results-megahit)")
    parser.add_argument("--out", help="Output tab file (required with --query)")
    parser.add_argument("--threads", type=int, required=True, help="Thread count")
    parser.add_argument("--db", required=True, help="Diamond database path")
    parser.add_argument("--log-dir", required=True, help="Log directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.query:
        if not args.out:
            raise SystemExit("--out is required when using --query")
        cmd: List[str] = [
            "diamond",
            "blastx",
            "--threads",
            str(args.threads),
            "-d",
            args.db,
            "-q",
            args.query,
            "-o",
            args.out,
            "--evalue",
            "0.00001",
            "--outfmt",
            "6",
            "qseqid",
            "sseqid",
            "pident",
            "length",
            "mismatch",
            "gapopen",
            "qstart",
            "qend",
            "sstart",
            "send",
            "evalue",
            "bitscore",
            "staxids",
        ]
        run_and_profile(cmd, Path(args.log_dir), "diamond:single")
        return

    if not args.results_megahit or not args.results_diamond:
        raise SystemExit("--results-megahit and --results-diamond are required when --query is not set")

    results_megahit = Path(args.results_megahit)
    results_diamond = Path(args.results_diamond)

    samples = list_samples(results_megahit)
    if not samples:
        raise SystemExit("No contigs found in results_megahit")

    for sample in samples:
        contig = ensure_uncompressed(results_megahit, sample)
        out = results_diamond / f"{sample}.tab"
        cmd = [
            "diamond",
            "blastx",
            "--threads",
            str(args.threads),
            "-d",
            args.db,
            "-q",
            str(contig),
            "-o",
            str(out),
            "--evalue",
            "0.00001",
            "--outfmt",
            "6",
            "qseqid",
            "sseqid",
            "pident",
            "length",
            "mismatch",
            "gapopen",
            "qstart",
            "qend",
            "sstart",
            "send",
            "evalue",
            "bitscore",
            "staxids",
        ]
        run_and_profile(cmd, Path(args.log_dir), f"diamond:{sample}")


if __name__ == "__main__":
    main()
