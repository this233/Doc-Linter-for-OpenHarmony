import os
from typing import Dict, List, Tuple

RULE_FILES = {
	# "punctuation_check": "DocLinter方案/prompt/punctuation_check.md",
	# "spelling_errors": "DocLinter方案/prompt/spelling_errors.md",
	"chinese_misspelling": "DocLinter方案/prompt/chinese_misspelling_yz.md",
	# "inconsistent": "DocLinter方案/prompt/inconsistent.md",
	# "fluent_etc": "DocLinter方案/prompt/fluent_etc.md",
	# "colloquial_expression": "DocLinter方案/prompt/colloquial_expression.md",
	# "redundant_expression": "DocLinter方案/prompt/redundant_expression.md",
	# "repeat_words_blanks": "DocLinter方案/prompt/repeat_words_blanks.md",
	# "fuzz_words": "DocLinter方案/prompt/fuzz_words.md",
}


class RulesLoader:
	def __init__(self, repo_root: str):
		self.repo_root = repo_root

	def _read(self, relative_path: str) -> List[str]:
		path = os.path.join(self.repo_root, relative_path)
		if not os.path.exists(path):
			return []
		with open(path, "r", encoding="utf-8") as f:
			return f.readlines()

	def load_excerpts(self, max_lines: int = 80) -> Dict[str, str]:
		results: Dict[str, str] = {}
		for rule, relative_path in RULE_FILES.items():
			lines = self._read(relative_path)
			if not lines:
				continue
			trimmed = []
			for line in lines:
				if line.strip().startswith("# 输出要求") or line.strip().startswith("# 示例"):
					break
				trimmed.append(line)
			excerpt = "".join(trimmed[:max_lines]).strip()
			results[rule] = excerpt
		return results

	def load_details(self, max_lines: int = 120) -> Dict[str, Dict[str, object]]:
		"""Return per-rule details: excerpt and extracted subrules.

		Structure: { rule_name: { 'excerpt': str, 'subrules': [str, ...] } }
		"""
		details: Dict[str, Dict[str, object]] = {}
		for rule, relative_path in RULE_FILES.items():
			lines = self._read(relative_path)
			if not lines:
				continue
			# excerpt
			trimmed = []
			for line in lines:
				# if line.strip().startswith("# 输出要求") or line.strip().startswith("# 示例"):
				# 	break
				trimmed.append(line)
			excerpt = "".join(trimmed[:max_lines]).strip()
			# subrules: lines starting with 【规则】, strip prefix and trailing punctuation
			subrules: List[str] = []
			for raw in lines:
				s = raw.strip()
				if s.startswith("【规则】"):
					content = s.replace("【规则】", "", 1).strip()
					# Remove trailing punctuation
					content = content.rstrip("。，：；！？.,;!?")
                    
					if content:
						subrules.append(content)
			if not subrules and excerpt:
				# fallback: first 1-2 sentences as a generic rule hint
				subrules = [excerpt.split("\n")[0][:80]]
			details[rule] = {"excerpt": excerpt, "subrules": subrules}

			print("!!!", rule, details[rule])

		return details 