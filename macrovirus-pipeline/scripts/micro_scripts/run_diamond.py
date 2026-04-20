#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

@dataclass
class ProcMetrics:
    name: str
    cmd: List[str]
    start_ts: float
    end_ts: float
    elapsed_sec: float
    user_time_sec: Optional[float] = None
    sys_time_sec: Optional[float] = None
    cpu_percent: Optional[float] = None
    max_rss_kb: Optional[int] = None
    exit_code: Optional[int] = None
    stdout_log: Optional[str] = None
    stderr_log: Optional[str] = None
    time_log: Optional[str] = None


def list_samples(results_megahit: Path) -> List[str]:
    names = set()
    for path in results_megahit.glob("*.contig.ok.fa.gz"):
        names.add(path.name.replace(".contig.ok.fa.gz", ""))
    for path in results_megahit.glob("*.contig.ok.fa"):
        names.add(path.name.replace(".contig.ok.fa", ""))
    return sorted(names)


def ensure_uncompressed(results_megahit: Path, sample: str) -> Path:
    contig_gz = results_megahit / f"{sample}.contig.ok.fa.gz"
    contig = results_megahit / f"{sample}.contig.ok.fa"
    if contig.exists():
        return contig
    if contig_gz.exists():
        if not contig.exists() or contig_gz.stat().st_mtime > contig.stat().st_mtime:
            with contig.open("wb") as fh:
                subprocess.run(["gunzip", "-c", str(contig_gz)], check=True, stdout=fh)
        return contig
    raise FileNotFoundError(f"Missing contig for {sample}")


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]+", "_", name)


def _parse_elapsed_to_seconds(s: str) -> float:
    s = s.strip()
    if not s:
        return 0.0
    parts = s.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            m = int(parts[0])
            sec = float(parts[1])
            return m * 60 + sec
        if len(parts) == 3:
            h = int(parts[0])
            m = int(parts[1])
            sec = float(parts[2])
            return h * 3600 + m * 60 + sec
    except ValueError:
        pass
    return 0.0


def _find_gnu_time() -> Optional[str]:
    for cand in ("/usr/bin/time", "/opt/homebrew/bin/gtime", "/usr/local/bin/gtime"):
        if Path(cand).exists():
            return cand
    return shutil.which("time")


def run_and_profile(
    cmd: Sequence[str],
    log_dir: Path,
    name: str,
    work_dir: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
) -> ProcMetrics:
    log_dir.mkdir(parents=True, exist_ok=True)
    safe = _safe_name(name)
    out_log = log_dir / f"{safe}.out"
    err_log = log_dir / f"{safe}.err"
    time_log = log_dir / f"{safe}.time.txt"

    gnu_time = _find_gnu_time()
    start_ts = time.time()
    full_cmd = [gnu_time, "-v", "-o", str(time_log), "--", *cmd] if gnu_time else list(cmd)

    rc = None
    try:
        with open(out_log, "wb") as fo, open(err_log, "wb") as fe:
            p = subprocess.Popen(
                full_cmd,
                cwd=str(work_dir) if work_dir else None,
                stdout=fo,
                stderr=fe if gnu_time else subprocess.PIPE,
                env={**os.environ, **(env or {})},
            )
            _, pipe_err = p.communicate()
            rc = p.returncode
            if not gnu_time and pipe_err:
                with open(err_log, "ab") as fe2:
                    fe2.write(pipe_err)
    finally:
        end_ts = time.time()

    elapsed = end_ts - start_ts
    user_t = sys_t = cpu_pct = None
    max_rss = None
    if gnu_time and time_log.exists():
        stats = {}
        with open(time_log, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    stats[k.strip()] = v.strip()
        if "User time (seconds)" in stats:
            try:
                user_t = float(stats["User time (seconds)"])
            except ValueError:
                pass
        if "System time (seconds)" in stats:
            try:
                sys_t = float(stats["System time (seconds)"])
            except ValueError:
                pass
        if "Elapsed (wall clock) time (h:mm:ss or m:ss)" in stats:
            elapsed = _parse_elapsed_to_seconds(stats["Elapsed (wall clock) time (h:mm:ss or m:ss)"])
        if "Percent of CPU this job got" in stats:
            try:
                cpu_pct = float(stats["Percent of CPU this job got"].rstrip("%"))
            except ValueError:
                pass
        if "Maximum resident set size (kbytes)" in stats:
            try:
                max_rss = int(stats["Maximum resident set size (kbytes)"])
            except ValueError:
                pass

    metrics = ProcMetrics(
        name=name,
        cmd=list(cmd),
        start_ts=start_ts,
        end_ts=end_ts,
        elapsed_sec=elapsed,
        user_time_sec=user_t,
        sys_time_sec=sys_t,
        cpu_percent=cpu_pct,
        max_rss_kb=max_rss,
        exit_code=rc,
        stdout_log=str(out_log),
        stderr_log=str(err_log),
        time_log=str(time_log) if time_log.exists() else None,
    )

    with open(log_dir / "metrics.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(metrics), ensure_ascii=False) + "\n")

    if rc != 0:
        raise subprocess.CalledProcessError(rc, cmd)
    return metrics

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single-file Diamond runner")
    parser.add_argument("--results-megahit", help="Megahit results directory")
    parser.add_argument("--results-diamond", help="Diamond output directory")
    parser.add_argument("--query", help="Input query FASTA (override batch mode)")
    parser.add_argument("--out", help="Output tab file (required with --query)")
    parser.add_argument("--threads", type=int, required=True, help="Thread count")
    parser.add_argument("--db", required=True, help="Diamond database path")
    parser.add_argument("--log-dir", required=True, help="Log directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    log_dir = Path(args.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    base_cmd = [
        "diamond",
        "blastx",
        "--threads",
        str(args.threads),
        "-d",
        args.db,
    ]

    if args.query:
        if not args.out:
            raise SystemExit("--out is required when using --query")
        single_cmd = [
            *base_cmd,
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
        run_and_profile(single_cmd, log_dir, "diamond:single")
        print("[INFO] Diamond single query done")
        return

    if not args.results_megahit or not args.results_diamond:
        raise SystemExit("--results-megahit and --results-diamond are required when --query is not set")

    results_megahit = Path(args.results_megahit)
    results_diamond = Path(args.results_diamond)
    results_diamond.mkdir(parents=True, exist_ok=True)

    samples = list_samples(results_megahit)
    if not samples:
        raise SystemExit("No contigs found in results_megahit")

    print("[INFO] Samples:")
    for s in samples:
        print(s)

    for sample in samples:
        contig = ensure_uncompressed(results_megahit, sample)
        out = results_diamond / f"{sample}.tab"
        cmd = [
            *base_cmd,
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
        print(f"[INFO] Running Diamond for {sample}")
        run_and_profile(cmd, log_dir, f"diamond:{sample}")
    print("[INFO] Diamond batch done")


if __name__ == "__main__":
    main()
