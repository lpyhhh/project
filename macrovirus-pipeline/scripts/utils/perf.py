from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
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
    bin_time = shutil.which("time")
    return bin_time


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
    if gnu_time:
        full_cmd = [gnu_time, "-v", "-o", str(time_log), "--", *cmd]
    else:
        full_cmd = list(cmd)

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

    summary_file = log_dir / "metrics.jsonl"
    with open(summary_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(metrics), ensure_ascii=False) + "\n")

    return metrics


class Timer:
    def __init__(self, name: str = "timer") -> None:
        self.name = name
        self.start_ts: float = 0.0
        self.end_ts: float = 0.0
        self.elapsed_sec: float = 0.0

    def __enter__(self):
        self.start_ts = time.time()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.end_ts = time.time()
        self.elapsed_sec = self.end_ts - self.start_ts
        return False


__all__ = ["ProcMetrics", "run_and_profile", "Timer"]
