# Error Injection Tool

This tool injects rule-based errors into OpenHarmony docs under `docs/zh-cn` using rules in `DocLinter方案/prompt`.

Usage example:

```bash
python3 -m error_injection.inject \
  --docs_dir /root/code/docs_llm/docs/zh-cn \
  --repo_root /root/code/docs_llm\
  --out_dir /root/code/docs_llm/results_error/zh-cn-bad \
  --annotation_file /root/code/docs_llm/results_error/annotations.json \
  --max_errors_per_file 10 \
  --max_files 3
```

Set `OPENAI_API_KEY` (and optional `OPENAI_BASE_URL`, `LLM_MODEL`) to use an LLM. Without a key, a deterministic mock is used. 