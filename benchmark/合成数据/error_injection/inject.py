import os
import re
import json
import random
import argparse
from typing import List, Dict, Tuple, Optional

from .llm_client import LLMClient
from .rules_loader import RulesLoader, RULE_FILES


FENCED_CODE_BLOCK_RE = re.compile(r"^\s*```")
URL_RE = re.compile(r"https?://|\b[a-zA-Z0-9_.-]+\.[a-zA-Z]{2,}\b")
HEADER_RE = re.compile(r"^\s*#+")


def is_code_or_url_line(line: str, in_code_block: bool) -> Tuple[bool, bool]:
	if FENCED_CODE_BLOCK_RE.search(line):
		return True, not in_code_block  # toggle
	if in_code_block:
		return True, in_code_block
	if URL_RE.search(line):
		return True, in_code_block
	return False, in_code_block


def choose_candidate_lines(lines: List[str], max_candidates: int) -> List[int]:
	indices: List[int] = []
	in_code = False
	for idx, line in enumerate(lines):
		flag, in_code = is_code_or_url_line(line, in_code)
		# if flag:
		# 	continue
		text = line.strip()
		# if not text:
		# 	continue
		# if HEADER_RE.match(text):
		# 	continue
		# Prefer lines with Chinese punctuation or longer length
		if any(p in text for p in ["。", "，", "：", "；"]) or len(text) >= 20:
			indices.append(idx)
	if len(indices) > max_candidates:
		indices = random.sample(indices, max_candidates)
	return sorted(indices)


def build_batch_prompt(rule_name: str, rule_excerpt: str, items: List[Tuple[int, str]], subrules: List[str]) -> Tuple[str, str]:
	sub = "；".join(subrules[:]) if subrules else ""
    
	system = (
		"你是一个错误注入助手。目标：基于指定的文档规范规则，反向生成包含该规则常见错误的改写句子，"
		"尽量保持语义接近，不引入新事实，不改变数字/代码/URL。对每一行仅做最小必要改写。"
	)
	user_obj = {
		"rule": rule_name,
		# "subrules": sub,
		"rule_excerpt": rule_excerpt[:2000],
		"instruction": (
			"请对下列每一行各生成一个包含此规则错误的改写。保持原有markdown内联格式（如反引号、链接）不破坏；"
			"保留行首缩进；不要合并/拆分行；不要新增或删除词汇太多；每项只返回一个改写。严格输出JSON数组。"
		),
		"items": [
			{"lineNum": ln + 1, "lineContent": text} for (ln, text) in items
		],
		"output_format": [
			{
				"line_number": "与输入相同的行号",
				"original": "原句(与输入一致)",
				"injected": "注入错误后的句子(单行)",
				"reason": "简要说明违反了该规则的哪个点"
			}
		],
	}
	user = json.dumps(user_obj, ensure_ascii=False)
	print(sub, system, user)
	# print("--------------------------------")
	return system, user


def apply_injections_to_lines(lines: List[str], injections: List[Dict]) -> Tuple[List[str], List[Dict]]:
	line_map: Dict[int, Dict] = {item["line_number"]: item for item in injections if isinstance(item, dict) and "line_number" in item}
	new_lines = list(lines)
	applied: List[Dict] = []
	for zero_idx, line in enumerate(lines):
		line_no = zero_idx + 1
		if line_no in line_map:
			inj = line_map[line_no]
			original = line
			injected = inj.get("injected", "").rstrip("\n")
			# Preserve leading whitespace
			leading = len(original) - len(original.lstrip(" \t"))
			prefix = original[:leading]
			new_lines[zero_idx] = prefix + injected.lstrip(" \t") + ("\n" if original.endswith("\n") else "")
			applied.append({
				"line_number": line_no,
				"original": original.rstrip("\n"),
				"injected": (prefix + injected.lstrip(" \t")).rstrip("\n"),
				"reason": inj.get("reason", ""),
			})
	return new_lines, applied


# Mock injectors for offline mode

def mock_inject(rule: str, text: str) -> str:
	if rule == "punctuation_check":
		return text.replace("，", "。", 1) if "，" in text else (text + "。" if not text.endswith("。") else text[:-1] + "，，")
	if rule == "spelling_errors":
		return re.sub(r"[参数能用作请设置配置登录点击账号账户图象外型阀值]", "讠", text, count=1)
	if rule == "inconsistent":
		pairs = {"登录": "登陆", "帐号": "账号", "帐户": "账户", "单击": "点击", "图像": "图象", "计费": "记费", "阈值": "阀值", "命令": "指令", "外形": "外型"}
		for k, v in pairs.items():
			if k in text:
				return text.replace(k, v, 1)
			if v in text:
				return text.replace(v, k, 1)
		return text + "（参数）"
	if rule == "colloquial_expression":
		return "我们" + text if not text.startswith("我们") else ("你" + text)
	if rule == "redundant_expression":
		return text.replace("进行", "进行进行", 1) if "进行" in text else text.replace("配置", "进行配置", 1)
	if rule == "repeat_words_blanks":
		return re.sub(r"(\S)(\s)", r"\1  ", text, count=1) if "  " not in text else re.sub(r"(\w+)", r"\1 \1", text, count=1)
	if rule == "fuzz_words":
		return text + " 等等"
	if rule == "fluent_etc":
		return text.replace("支持", "被支持", 1) if "支持" in text else ("可以被" + text)
	return text


def mock_batch(items: List[Tuple[int, str]], rule: str) -> List[Dict]:
	results = []
	for ln, t in items:
		inj = mock_inject(rule, t)
		if inj == t:
			inj = t + "（示例）"
		results.append({
			"line_number": ln + 1,
			"original": t,
			"injected": inj,
			"reason": f"违反{rule}规则的示例",
		})
	return results


def process_file(file_path: str, out_root: str, rules_detail: Dict[str, Dict[str, object]], client: Optional[LLMClient], max_errors_per_file: int, rng: random.Random, docs_dir: str) -> List[Dict]:
	with open(file_path, "r", encoding="utf-8") as f:
		lines = f.readlines()

	candidates = choose_candidate_lines(lines, max_errors_per_file)
	if not candidates:
		rel = os.path.relpath(file_path, start=docs_dir)
		out_path = os.path.join(out_root, rel)
		os.makedirs(os.path.dirname(out_path), exist_ok=True)
		with open(out_path, "w", encoding="utf-8") as wf:
			wf.writelines(lines)
		return []

	selected_rules = list(rules_detail.keys())
	if not selected_rules:
		selected_rules = list(RULE_FILES.keys())

	used_items: List[Tuple[int, str]] = [(idx, lines[idx].rstrip("\n")) for idx in candidates]
	rule = rng.choice(selected_rules)
	detail = rules_detail.get(rule, {"excerpt": "", "subrules": []})
	excerpt = str(detail.get("excerpt", ""))
	subrules: List[str] = list(detail.get("subrules", []))

	if client and client.available:
		system, user = build_batch_prompt(rule, excerpt, used_items, subrules)
		resp = client.chat(system, user)
		parsed = client.extract_json_array(resp)
		if not parsed:
			parsed = mock_batch(used_items, rule)
	else:
		parsed = mock_batch(used_items, rule)

	new_lines, applied = apply_injections_to_lines(lines, parsed)

	rel = os.path.relpath(file_path, start=docs_dir)
	out_path = os.path.join(out_root, rel)
	os.makedirs(os.path.dirname(out_path), exist_ok=True)
	with open(out_path, "w", encoding="utf-8") as wf:
		wf.writelines(new_lines)

	annotations: List[Dict] = []
	for a in applied:
		annotations.append({
			"file": rel,
			"rule": rule,
			"line_number": a["line_number"],
			"original": a["original"],
			"injected": a["injected"],
			"reason": a.get("reason", ""),
		})
	return annotations


def iter_markdown_files(root: str) -> List[str]:
	paths: List[str] = [[],[]]
	for dirpath, _dirnames, filenames in os.walk(root):
		for fn in filenames:
			if fn.lower().endswith((".md", ".mdx")):
				file_path = os.path.join(dirpath, fn)
				# Get relative path from root
				rel_path = os.path.relpath(file_path, root)
				# Check if first level directory is 'reference'
				path_parts = rel_path.split(os.sep)
				
				if 'reference' in path_parts:
					paths[1].append(file_path)
				else:
					paths[0].append(file_path)
	return paths


def main():
	parser = argparse.ArgumentParser(description="Inject rule-based errors into OpenHarmony docs")
	parser.add_argument("--docs_dir", default="/root/code/docs_llm/docs/zh-cn/application-dev")
	parser.add_argument("--repo_root", default="/root/code/docs_llm")
	parser.add_argument("--out_dir", default="/root/code/docs_llm/results_error_fluent/zh-cn-bad")
	parser.add_argument("--annotation_file", default="/root/code/docs_llm/results_error_fluent/annotations.json")
	parser.add_argument("--max_errors_per_file", type=int, default=16)
	parser.add_argument("--max_files", type=int, default=25)
	parser.add_argument("--seed", type=int, default=42)
	args = parser.parse_args()

	rng = random.Random(args.seed)
	loader = RulesLoader(args.repo_root)
	details = loader.load_details()
	client = LLMClient()

	os.makedirs(args.out_dir, exist_ok=True)
	all_annotations: List[Dict] = []
	files = iter_markdown_files(args.docs_dir)
	files[0] = rng.sample(files[0], min(args.max_files, len(files[0]))) if args.max_files and args.max_files > 0 else files[0]
	files[1] = rng.sample(files[1], min(args.max_files, len(files[1]))) if args.max_files and args.max_files > 0 else files[1]
	files = files[0] + files[1]
	print(files)
	for path in files:
		ann = process_file(path, args.out_dir, details, client if client.available else None, args.max_errors_per_file, rng, args.docs_dir)
		all_annotations.extend(ann)

	with open(args.annotation_file, "w", encoding="utf-8") as jf:
		json.dump(all_annotations, jf, ensure_ascii=False, indent=2)

	print(f"Injected errors into {len(files)} files; annotations: {len(all_annotations)} entries")


if __name__ == "__main__":
	main() 