#!/usr/bin/env python3
# coding=utf-8

import os
import sys
import json
import argparse
import time
from typing import Dict, List, Tuple, Optional

import requests
import pandas as pd
import subprocess

WORKSPACE_ROOT = "/root/code/docs_llm"
DEFAULT_OUT_DIR = os.path.join(WORKSPACE_ROOT, "test_input_0825")
DEFAULT_EXCEL = os.path.join(WORKSPACE_ROOT, "results_RAG/业务反馈结果.xls")

# Two candidate host bases to try in order
HOST_BASES = [
    "http://121.36.32.255",
    "https://ci.openharmony.cn",
]
REQUEST_TIMEOUT = 60


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sanitize_filename(name: str) -> str:
    keep = [c for c in name if c.isalnum() or c in ("-", "_", ".")]
    s = "".join(keep).strip(" .")
    return s or "file"


def infer_filename_from_headers(resp: requests.Response, fallback: str) -> str:
    cd = resp.headers.get("Content-Disposition") or resp.headers.get("content-disposition")
    if cd:
        # naive parse of filename=
        parts = cd.split(";")
        for p in parts:
            p = p.strip()
            if p.lower().startswith("filename="):
                fn = p.split("=", 1)[1].strip('"')
                return sanitize_filename(fn)
    # fallback
    return sanitize_filename(fallback)


def try_download_file(file_id: str, out_dir: str) -> Tuple[str, bytes, str]:
    last_err: Optional[Exception] = None
    best: Optional[Tuple[str, bytes, str]] = None  # (url, content, filename)

    for base in HOST_BASES:
        url = f"{base}/api/aiService/noticeboard/file/export/{file_id}"
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT, verify=False)
            if resp.status_code == 200 and resp.content:
                guessed_name = infer_filename_from_headers(resp, f"{file_id}.md")
                if not guessed_name.lower().endswith(".md"):
                    guessed_name = f"{guessed_name}.md"
                content = resp.content
                # Keep the longer content
                if best is None or len(content) > len(best[1]):
                    best = (url, content, guessed_name)
            else:
                last_err = RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            last_err = e
        time.sleep(0.2)

    if best is not None:
        return best
    if last_err is None:
        last_err = RuntimeError("Unknown download error")
    raise last_err


def save_bytes(path: str, content: bytes) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "wb") as f:
        f.write(content)


def load_excel_rows(excel_path: str) -> pd.DataFrame:
    # Read as-is; let pandas infer engine (xlrd for .xls, openpyxl for .xlsx)
    df = pd.read_excel(excel_path)
    # Normalize column names by stripping spaces
    df.columns = [str(c).strip() for c in df.columns]
    return df


def validate_required_columns(df: pd.DataFrame, required: List[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Excel is missing required columns: {missing}. Available: {list(df.columns)}")


def run_llm_on_dir(input_dir: str, predictions_out: str, report_out: str) -> None:
    script_path = os.path.join(WORKSPACE_ROOT, "actual_using/run_lint_eval.py")
    cmd = [
        sys.executable,
        script_path,
        "--input_dir", input_dir,
        "--save_predictions", predictions_out,
        "--report_out", report_out,
        # Keep defaults: model/rules/temperature
    ]
    print(f"[INFO] Running LLM evaluator: {' '.join(cmd)}")
    # Run in the workspace root to keep relative paths stable
    proc = subprocess.run(cmd, cwd=WORKSPACE_ROOT)
    if proc.returncode != 0:
        raise RuntimeError(f"LLM evaluation script failed with code {proc.returncode}")


def compute_false_positive_rate(
    predictions_path: str,
    file_id_to_local: Dict[str, str],
    file_id_to_fp_lines: Dict[str, set],
) -> Dict[str, object]:
    # Invert local path to file_id for quick lookup
    local_to_file_id: Dict[str, str] = {os.path.abspath(v): k for k, v in file_id_to_local.items()}

    with open(predictions_path, "r", encoding="utf-8") as f:
        preds = json.load(f)

    total_preds = 0
    total_fp = 0
    per_file: Dict[str, Dict[str, int]] = {}

    for p in preds:
        abs_file = os.path.abspath(p.get("file", ""))
        line_number = p.get("line_number")
        if not abs_file or not isinstance(line_number, int):
            continue
        file_id = local_to_file_id.get(abs_file)
        if not file_id:
            # If exact path key missing, try normalized
            for k_abs, k_id in local_to_file_id.items():
                try:
                    if os.path.samefile(k_abs, abs_file):
                        file_id = k_id
                        break
                except Exception:
                    continue
        if not file_id:
            # Skip if we cannot map
            continue

        total_preds += 1
        per = per_file.setdefault(file_id, {"pred": 0, "fp": 0})
        per["pred"] += 1

        fp_lines = file_id_to_fp_lines.get(file_id, set())
        if line_number in fp_lines:
            total_fp += 1
            per["fp"] += 1

    fp_rate = (total_fp / total_preds) if total_preds > 0 else 0.0
    # Convert per-file to include rate
    per_file_rates = {
        fid: {"pred": v["pred"], "fp": v["fp"], "fp_rate": (v["fp"] / v["pred"]) if v["pred"] > 0 else 0.0}
        for fid, v in per_file.items()
    }

    return {
        "total_predictions": total_preds,
        "total_false_positives": total_fp,
        "false_positive_rate": fp_rate,
        "per_file": per_file_rates,
    }


def main():
    parser = argparse.ArgumentParser(description="Process Excel, download files by file_id, run LLM for rule 9, and compute false positive rate.")
    parser.add_argument("--excel", default=DEFAULT_EXCEL, help="Path to the Excel containing file_id, rule_id, feed_back_status, problematic_line_num")
    parser.add_argument("--out_dir", default=DEFAULT_OUT_DIR, help="Output directory to store downloaded files and results")
    parser.add_argument("--only_rule_id", type=int, default=9, help="Process only this rule id (default: 9 for colloquial expression)")
    parser.add_argument("--save_mapping", default=None, help="Optional path to save file_id-to-local mapping JSON")
    parser.add_argument("--predictions_out", default=None, help="Optional explicit path for predictions JSON")
    parser.add_argument("--report_out", default=None, help="Optional explicit path for evaluator report JSON")
    parser.add_argument("--fp_summary_out", default=None, help="Optional path to save FP summary JSON")
    args = parser.parse_args()

    ensure_dir(args.out_dir)

    print(f"[INFO] Reading Excel: {args.excel}")
    df = load_excel_rows(args.excel)
    required_cols = ["file_id", "rule_id", "feed_back_status", "problematic_line_num"]
    validate_required_columns(df, required_cols)

    # Keep only rule 9 rows
    df_rule = df[df["rule_id"] == args.only_rule_id].copy()
    if df_rule.empty:
        print(f"[WARN] No rows found for rule_id={args.only_rule_id}. Nothing to do.")
        return

    # Build FP lines per file_id: those with feed_back_status == 2
    file_id_to_fp_lines: Dict[str, set] = {}
    for _, row in df_rule.iterrows():
        fid = str(row["file_id"]).strip()
        try:
            ln = int(row["problematic_line_num"]) if pd.notna(row["problematic_line_num"]) else None
        except Exception:
            ln = None
        status = int(row["feed_back_status"]) if pd.notna(row["feed_back_status"]) else None
        if not fid or ln is None or status is None:
            continue
        if status == 2:
            file_id_to_fp_lines.setdefault(fid, set()).add(ln)

    # Download files for all unique file_ids in df_rule
    unique_file_ids = sorted(set(str(x).strip() for x in df_rule["file_id"].tolist() if pd.notna(x)))
    print(f"[INFO] Unique file_ids for rule {args.only_rule_id}: {len(unique_file_ids)}")

    file_id_to_local: Dict[str, str] = {}
    for idx, fid in enumerate(unique_file_ids, start=1):
        try:
            url, content, fname = try_download_file(fid, args.out_dir)
            local_path = os.path.join(args.out_dir, fname)
            save_bytes(local_path, content)
            file_id_to_local[fid] = os.path.abspath(local_path)
            print(f"  - [{idx}/{len(unique_file_ids)}] {fid} -> {fname} (from {url})")
        except Exception as e:
            print(f"  ! [{idx}/{len(unique_file_ids)}] {fid} -> download failed: {e}")

    # Save mapping if requested
    if args.save_mapping:
        ensure_dir(os.path.dirname(args.save_mapping))
        with open(args.save_mapping, "w", encoding="utf-8") as f:
            json.dump(file_id_to_local, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Saved mapping to {args.save_mapping}")

    # Run evaluator for rule 9 over out_dir
    predictions_out = args.predictions_out or os.path.join(args.out_dir, "predictions_rule9.json")
    report_out = args.report_out or os.path.join(args.out_dir, "report_rule9.json")
    run_llm_on_dir(args.out_dir, predictions_out, report_out)

    # Compute FP rate per Excel definition (feed_back_status == 2)
    fp_summary = compute_false_positive_rate(predictions_out, file_id_to_local, file_id_to_fp_lines)
    fp_summary_out = args.fp_summary_out or os.path.join(args.out_dir, "fp_summary_rule9.json")
    with open(fp_summary_out, "w", encoding="utf-8") as f:
        json.dump(fp_summary, f, ensure_ascii=False, indent=2)

    print("\n[RESULT]")
    print(json.dumps(fp_summary, ensure_ascii=False, indent=2))
    print(f"Saved FP summary to: {fp_summary_out}")


if __name__ == "__main__":
    main() 