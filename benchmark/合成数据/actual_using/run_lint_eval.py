# coding=utf-8

import os
import re
import json
import time
import argparse
from typing import List, Dict, Any, Tuple

import requests


API_URL = "https://api.modelarts-maas.com/v1/chat/completions"
DEFAULT_MODEL = "DeepSeek-V3"
DEFAULT_TEMPERATURE = 0.6

WORKSPACE_ROOT = "/root/code/docs_llm"
RULES_PATH = os.path.join(WORKSPACE_ROOT, "actual_using/DocLinter方案_origin/prompt/fluent_etc1.md")
INPUT_DIR = os.path.join(WORKSPACE_ROOT, "results_error_fluent/zh-cn-bad")
ANNOTATIONS_PATH = os.path.join(WORKSPACE_ROOT, "results_error_fluent/annotations.json")
PREDICTIONS_OUT = os.path.join(WORKSPACE_ROOT, "results_error_fluent/predictions_fluent_etc.json")
REPORT_OUT = os.path.join(WORKSPACE_ROOT, "results_error_fluent/eval_report_fluent_etc.json")


def load_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def list_markdown_files(root_dir: str) -> List[str]:
    md_files: List[str] = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".md"):
                md_files.append(os.path.join(dirpath, filename))
    return sorted(md_files)


def is_url_line(line: str) -> bool:
    if "http://" in line or "https://" in line or "chrome://" in line:
        return True
    # Match generic protocol URLs
    if re.search(r"[a-zA-Z]+://\S+", line):
        return True
    return False


def extract_non_code_lines_with_numbers(md_path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    in_code_block = False
    fence_re = re.compile(r"^\s*```")

    with open(md_path, "r", encoding="utf-8") as f:
        for idx, raw_line in enumerate(f, start=1):
            line = raw_line.rstrip("\n")
            # if fence_re.match(line):
            #     in_code_block = not in_code_block
            #     continue
            # if in_code_block:
            #     continue
            # if is_url_line(line):
            #     continue
            # # Keep markdown formatting intact, but skip empty lines to reduce token usage
            # if not line.strip():
            #     continue
            items.append({"lineNum": idx, "lineContent": line})
    return items


def chunk_items_by_chars(items: List[Dict[str, Any]], max_chars: int) -> List[List[Dict[str, Any]]]:
    chunks: List[List[Dict[str, Any]]] = []
    current: List[Dict[str, Any]] = []
    current_chars = 0

    for obj in items:
        # Rough size: json dump of the obj
        obj_text = json.dumps(obj, ensure_ascii=False)
        size = len(obj_text)
        if current and current_chars + size > max_chars:
            chunks.append(current)
            current = []
            current_chars = 0
        current.append(obj)
        current_chars += size
    if current:
        chunks.append(current)
    return chunks


def build_messages(system_prompt: str, lines_chunk: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    user_payload = json.dumps(lines_chunk, ensure_ascii=False, indent=2)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_payload},
    ]
    return messages


def call_llm(api_key: str, system_prompt: str, lines_chunk: List[Dict[str, Any]], model: str, temperature: float, retries: int = 3, timeout: int = 180) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    messages = build_messages(system_prompt, lines_chunk)
    body = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
    }

    last_err: Exception = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(API_URL, headers=headers, data=json.dumps(body, ensure_ascii=False).encode("utf-8"), verify=False, timeout=timeout)
            if resp.status_code != 200:
                raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")
            data = resp.json()
            # Expected structure: { choices: [ { message: { content: "..." } } ] }
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                raise RuntimeError(f"Empty content in response: {json.dumps(data)[:500]}")
            return content
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.5 * attempt)
            else:
                raise last_err
    raise RuntimeError("Unreachable")


def extract_json_array(text: str) -> Any:
    # Try fenced JSON first
    fenced = re.findall(r"```json\s*(\[.*?\])\s*```", text, flags=re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced[0])
        except Exception:
            pass
    # Try any fenced code
    fenced_any = re.findall(r"```[a-zA-Z]*\s*(\[.*?\])\s*```", text, flags=re.DOTALL)
    if fenced_any:
        for candidate in fenced_any:
            try:
                return json.loads(candidate)
            except Exception:
                continue
    # Try to find the first JSON array
    start = text.find("[")
    if start != -1:
        # Heuristic: scan to find matching bracket by counting
        depth = 0
        for i in range(start, len(text)):
            ch = text[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    candidate = text[start:i + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        break
    # Fallback: empty list
    return []


def normalize_predictions(pred_list: Any, file_path: str) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    if not isinstance(pred_list, list):
        return results
    for item in pred_list:
        if not isinstance(item, dict):
            continue
        line_number_raw = item.get("line_number")
        problematic_sentence = item.get("problematic sentence")
        reason = item.get("reason")
        fixed_sentence = item.get("fixed sentence")
        try:
            line_number = int(str(line_number_raw).strip()) if line_number_raw is not None else None
        except Exception:
            line_number = None
        if line_number is None or not problematic_sentence:
            continue
        results.append({
            "file": file_path,
            "line_number": line_number,
            "problematic_sentence": problematic_sentence,
            "reason": reason,
            "fixed_sentence": fixed_sentence,
        })
    return results


def load_ground_truth(path: str) -> Dict[str, List[int]]:
    with open(path, "r", encoding="utf-8") as f:
        arr = json.load(f)
    mapping: Dict[str, List[int]] = {}
    for obj in arr:
        if obj.get("rule") != "colloquial_expression":
            continue
        file_rel = obj.get("file")
        line_number = obj.get("line_number")
        if not isinstance(line_number, int):
            continue
        mapping.setdefault(file_rel, []).append(line_number)
    for k in list(mapping.keys()):
        mapping[k] = sorted(set(mapping[k]))
    return mapping


def rel_path_under_bad(abs_path: str) -> str:
    # Convert absolute path to relative path used by annotations.json
    # annotations use paths relative to zh-cn-bad root
    rel = os.path.relpath(abs_path, INPUT_DIR)
    return rel.replace(os.sep, "/")


def evaluate(predictions: List[Dict[str, Any]], gt: Dict[str, List[int]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    # Build per-file predicted line numbers
    pred_map: Dict[str, List[int]] = {}
    for p in predictions:
        rel_file = rel_path_under_bad(p["file"]) if os.path.isabs(p["file"]) else p["file"]
        pred_map.setdefault(rel_file, []).append(p["line_number"])
    for k in list(pred_map.keys()):
        pred_map[k] = sorted(set(pred_map[k]))

    files = sorted(set(list(pred_map.keys()) + list(gt.keys())))

    per_file_metrics: Dict[str, Any] = {}
    total_tp = total_fp = total_fn = 0

    for file_rel in files:
        gts = set(gt.get(file_rel, []))
        preds = set(pred_map.get(file_rel, []))
        tp = len(gts & preds)
        fp = len(preds - gts)
        fn = len(gts - preds)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        per_file_metrics[file_rel] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "num_gt": len(gts),
            "num_pred": len(preds),
        }
        total_tp += tp
        total_fp += fp
        total_fn += fn

    overall_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    overall_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    overall_f1 = 2 * overall_prec * overall_rec / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 0.0

    overall = {
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "precision": round(overall_prec, 4),
        "recall": round(overall_rec, 4),
        "f1": round(overall_f1, 4),
    }

    return per_file_metrics, overall


def ensure_api_key() -> str:
    api_key = os.environ.get("MAAS_API_KEY")
    if not api_key:
    #     raise RuntimeError("Environment variable MAAS_API_KEY is required to call the API.")
        api_key = "mATSRxNA6sLbRzfYOU9St9y0OcaX37-47V0FK49XMySBn-T-olZ4SJM8C3lJXtwBJ3F4vEjMv2tUbZGKf7EEuQ"
    return api_key


def load_gt_detail_map(path: str) -> Dict[Tuple[str, int], Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        arr = json.load(f)
    detail: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for obj in arr:
        if obj.get("rule") != "colloquial_expression":
            continue
        file_rel = obj.get("file")
        line_number = obj.get("line_number")
        if not isinstance(file_rel, str) or not isinstance(line_number, int):
            continue
        detail[(file_rel, line_number)] = obj
    return detail


def evaluate_grouped(predictions: List[Dict[str, Any]], gt: Dict[str, List[int]]) -> Dict[str, Dict[str, Any]]:
    # Build sets of (file_rel, line_number)
    def to_rel(file_path: str) -> str:
        return rel_path_under_bad(file_path) if os.path.isabs(file_path) else file_path

    pred_pairs_ref = set()
    pred_pairs_nonref = set()
    for p in predictions:
        file_rel = to_rel(p["file"]) 
        pair = (file_rel, int(p["line_number"]))
        if file_rel.startswith("reference/"):
            pred_pairs_ref.add(pair)
        else:
            pred_pairs_nonref.add(pair)

    gt_pairs_ref = set()
    gt_pairs_nonref = set()
    for file_rel, lines in gt.items():
        for ln in lines:
            pair = (file_rel, int(ln))
            if file_rel.startswith("reference/"):
                gt_pairs_ref.add(pair)
            else:
                gt_pairs_nonref.add(pair)

    def summarize(pred_pairs: set, gt_pairs: set) -> Dict[str, Any]:
        tp = len(pred_pairs & gt_pairs)
        fp = len(pred_pairs - gt_pairs)
        fn = len(gt_pairs - pred_pairs)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        return {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
        }

    return {
        "reference": summarize(pred_pairs_ref, gt_pairs_ref),
        "non_reference": summarize(pred_pairs_nonref, gt_pairs_nonref),
    }


def get_line_content(file_rel: str, line_number: int) -> str:
    abs_path = os.path.join(INPUT_DIR, file_rel)
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                if idx == line_number:
                    return line.rstrip("\n")
    except Exception:
        return ""
    return ""


def build_pair_sets(predictions: List[Dict[str, Any]], gt: Dict[str, List[int]]):
    def to_rel(file_path: str) -> str:
        return rel_path_under_bad(file_path) if os.path.isabs(file_path) else file_path

    # Map predicted pairs to details
    pred_pair_to_detail: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for p in predictions:
        rel_file = to_rel(p["file"])
        pair = (rel_file, int(p["line_number"]))
        pred_pair_to_detail[pair] = {
            "file": rel_file,
            "line_number": int(p["line_number"]),
            "problematic_sentence": p.get("problematic_sentence"),
            "reason": p.get("reason"),
            "fixed_sentence": p.get("fixed_sentence"),
        }

    pred_pairs = set(pred_pair_to_detail.keys())
    gt_pairs: set = set()
    for file_rel, lines in gt.items():
        for ln in lines:
            gt_pairs.add((file_rel, int(ln)))

    tp_pairs = pred_pairs & gt_pairs
    fp_pairs = pred_pairs - gt_pairs
    fn_pairs = gt_pairs - pred_pairs

    return pred_pair_to_detail, tp_pairs, fp_pairs, fn_pairs


def summarize_pairs_for_report(pred_detail_map: Dict[Tuple[str, int], Dict[str, Any]], gt_detail_map: Dict[Tuple[str, int], Dict[str, Any]], tp_pairs: set, fp_pairs: set, fn_pairs: set) -> Dict[str, List[Dict[str, Any]]]:
    tp_list: List[Dict[str, Any]] = []
    for pair in sorted(tp_pairs):
        base = pred_detail_map.get(pair, {"file": pair[0], "line_number": pair[1]})
        ann = gt_detail_map.get(pair)
        if ann is not None:
            base = dict(base)
            base["annotation"] = ann
        tp_list.append(base)

    fp_list: List[Dict[str, Any]] = []
    for pair in sorted(fp_pairs):
        fp_list.append(pred_detail_map.get(pair, {"file": pair[0], "line_number": pair[1]}))

    fn_list: List[Dict[str, Any]] = []
    for file_rel, ln in sorted(fn_pairs):
        item = {
            "file": file_rel,
            "line_number": int(ln),
            "line_content": get_line_content(file_rel, int(ln)),
        }
        ann = gt_detail_map.get((file_rel, int(ln)))
        if ann is not None:
            item["annotation"] = ann
        fn_list.append(item)

    return {"tp": tp_list, "fp": fp_list, "fn": fn_list}


def grouped_pairs_for_report(predictions: List[Dict[str, Any]], gt: Dict[str, List[int]], gt_detail_map: Dict[Tuple[str, int], Dict[str, Any]]):
    pred_detail_map, tp_pairs, fp_pairs, fn_pairs = build_pair_sets(predictions, gt)

    def starts_with_reference(pair: Tuple[str, int]) -> bool:
        return pair[0].startswith("reference/")

    tp_ref = {p for p in tp_pairs if starts_with_reference(p)}
    tp_non = tp_pairs - tp_ref
    fp_ref = {p for p in fp_pairs if starts_with_reference(p)}
    fp_non = fp_pairs - fp_ref
    fn_ref = {p for p in fn_pairs if starts_with_reference(p)}
    fn_non = fn_pairs - fn_ref

    overall_lists = summarize_pairs_for_report(pred_detail_map, gt_detail_map, tp_pairs, fp_pairs, fn_pairs)
    reference_lists = summarize_pairs_for_report(pred_detail_map, gt_detail_map, tp_ref, fp_ref, fn_ref)
    non_reference_lists = summarize_pairs_for_report(pred_detail_map, gt_detail_map, tp_non, fp_non, fn_non)

    return overall_lists, reference_lists, non_reference_lists


def main():
    parser = argparse.ArgumentParser(description="Detect colloquial expressions in markdown files via LLM and evaluate against ground truth.")
    parser.add_argument("--input_dir", default=INPUT_DIR, help="Directory containing zh-cn-bad markdown files")
    parser.add_argument("--annotations", default=ANNOTATIONS_PATH, help="Path to annotations.json ground truth")
    parser.add_argument("--rules_path", default=RULES_PATH, help="Path to colloquial_expression.md prompt rules")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--max_chars_per_chunk", type=int, default=6000)
    parser.add_argument("--sleep_between_calls", type=float, default=0.0)
    parser.add_argument("--save_predictions", default=PREDICTIONS_OUT)
    parser.add_argument("--eval_only", action="store_true", help="Skip inference and only evaluate from saved predictions")
    parser.add_argument("--load_predictions", default="", help="Path to previously saved predictions JSON to evaluate")
    parser.add_argument("--report_out", default=REPORT_OUT, help="Path to save evaluation report JSON including TP/FP/FN")
    args = parser.parse_args()

    predictions: List[Dict[str, Any]] = []

    if args.eval_only or (args.load_predictions and os.path.exists(args.load_predictions)):
        load_path = args.load_predictions or args.save_predictions
        with open(load_path, "r", encoding="utf-8") as f:
            predictions = json.load(f)
        print(f"Loaded predictions from {load_path}")
    else:
        api_key = ensure_api_key()
        system_prompt = load_text_file(args.rules_path)
        md_files = list_markdown_files(args.input_dir)
        print(f"Found {len(md_files)} markdown files. Starting analysis...")
        for idx, md_file in enumerate(md_files, start=1):
            try:
                items = extract_non_code_lines_with_numbers(md_file)
                if not items:
                    continue
                chunks = chunk_items_by_chars(items, args.max_chars_per_chunk)
                file_predictions: List[Dict[str, Any]] = []
                for c_idx, chunk in enumerate(chunks, start=1):
                    response_text = call_llm(api_key, system_prompt, chunk, args.model, args.temperature)
                    parsed = extract_json_array(response_text)
                    preds = normalize_predictions(parsed, md_file)
                    file_predictions.extend(preds)
                    if args.sleep_between_calls > 0:
                        time.sleep(args.sleep_between_calls)
                # Deduplicate by (line_number, problematic_sentence)
                unique: Dict[Tuple[int, str], Dict[str, Any]] = {}
                for p in file_predictions:
                    key = (p["line_number"], p["problematic_sentence"])
                    unique[key] = p
                deduped = list(unique.values())
                predictions.extend(deduped)
                print(f"[{idx}/{len(md_files)}] {rel_path_under_bad(md_file)} -> {len(deduped)} predictions")
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
        # Save predictions
        os.makedirs(os.path.dirname(args.save_predictions), exist_ok=True)
        with open(args.save_predictions, "w", encoding="utf-8") as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)
        print(f"Saved predictions to {args.save_predictions}")

    # Evaluate
    gt = load_ground_truth(args.annotations)
    gt_detail_map = load_gt_detail_map(args.annotations)
    per_file_metrics, overall = evaluate(predictions, gt)
    grouped = evaluate_grouped(predictions, gt)
    overall_lists, reference_lists, non_reference_lists = grouped_pairs_for_report(predictions, gt, gt_detail_map)

    # Print grouped summary first
    print("\nGrouped metrics:")
    print("- reference:")
    print(json.dumps(grouped["reference"], ensure_ascii=False, indent=2))
    print("- non-reference:")
    print(json.dumps(grouped["non_reference"], ensure_ascii=False, indent=2))

    # Print per-file report
    print("\nPer-file metrics (precision, recall, f1, num_gt, num_pred):")
    for file_rel in sorted(per_file_metrics.keys()):
        m = per_file_metrics[file_rel]
        print(f"- {file_rel}: P={m['precision']}, R={m['recall']}, F1={m['f1']} (gt={m['num_gt']}, pred={m['num_pred']})")

    print("\nOverall:")
    print(json.dumps(overall, ensure_ascii=False, indent=2))

    # Save report JSON
    report = {
        "meta": {
            "model": args.model,
            "temperature": args.temperature,
            "rules_path": args.rules_path,
            "input_dir": args.input_dir,
            "annotations": args.annotations,
            "predictions": args.load_predictions or args.save_predictions,
        },
        "metrics": {
            "overall": overall,
            "grouped": grouped,
            "per_file": per_file_metrics,
        },
        "pairs": {
            "overall": overall_lists,
            "reference": reference_lists,
            "non_reference": non_reference_lists,
        },
    }
    os.makedirs(os.path.dirname(args.report_out), exist_ok=True)
    with open(args.report_out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Saved evaluation report to {args.report_out}")


if __name__ == "__main__":
    main() 