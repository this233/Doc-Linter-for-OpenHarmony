import os
import json
from typing import List, Dict, Optional

try:
	from tenacity import retry, stop_after_attempt, wait_exponential
except Exception:  # pragma: no cover
	def retry(*args, **kwargs):
		def wrapper(fn):
			return fn
		return wrapper
	def stop_after_attempt(n):  # type: ignore
		return None
	def wait_exponential(*args, **kwargs):  # type: ignore
		return None

try:
	from openai import OpenAI
except Exception:  # pragma: no cover
	OpenAI = None  # type: ignore

import requests


class LLMClient:
	def __init__(self, model: Optional[str] = None, temperature: float = 0.3):
		self.provider = os.getenv("LLM_PROVIDER", "maas")  # 'openai' or 'maas'
		self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
		self.temperature = float(os.getenv("LLM_TEMPERATURE", str(temperature)))

		# OpenAI compatible
		self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
		self.api_key = os.getenv("OPENAI_API_KEY", "")
		self.client = None
		if self.provider == "openai" and OpenAI is not None and self.api_key:
			self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

		# ModelArts MaaS
		self.maas_url = os.getenv("MAAS_URL", "https://api.modelarts-maas.com/v1/chat/completions")
		self.maas_api_key = os.getenv("MAAS_API_KEY", "mATSRxNA6sLbRzfYOU9St9y0OcaX37-47V0FK49XMySBn-T-olZ4SJM8C3lJXtwBJ3F4vEjMv2tUbZGKf7EEuQ")
		self.maas_model = os.getenv("MAAS_MODEL", "DeepSeek-V3")

	@property
	def available(self) -> bool:
		if self.provider == "maas":
			return bool(self.maas_api_key)
		return self.client is not None

	@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
	def chat(self, system: str, user: str) -> str:
		if self.provider == "maas":
			if not self.maas_api_key:
				raise RuntimeError("MAAS_API_KEY not set")
			headers = {
				"Content-Type": "application/json",
				"Authorization": f"Bearer {self.maas_api_key}",
			}
			payload = {
				"model": self.maas_model,
				"messages": [
					{"role": "system", "content": system},
					{"role": "user", "content": user},
				],
				"stream": False,
				"temperature": self.temperature,
			}
			resp = requests.post(self.maas_url, headers=headers, data=json.dumps(payload), verify=False, timeout=180)
			resp.raise_for_status()
			data = resp.json()
			# Expect OpenAI-like schema
			try:
				return data["choices"][0]["message"]["content"]
			except Exception:
				return json.dumps(data, ensure_ascii=False)

		if not self.available:
			raise RuntimeError("LLM client not available. Set OPENAI_API_KEY or configure MAAS_API_KEY.")
		resp = self.client.chat.completions.create(
			model=self.model,
			messages=[
				{"role": "system", "content": system},
				{"role": "user", "content": user},
			],
			temperature=self.temperature,
		)
		return resp.choices[0].message.content or ""

	@staticmethod
	def extract_json_array(text: str) -> List[Dict]:
		start = text.find("[")
		end = text.rfind("]")
		if start != -1 and end != -1 and end > start:
			candidate = text[start : end + 1]
			try:
				return json.loads(candidate)
			except Exception:
				pass
		try:
			obj = json.loads(text)
			if isinstance(obj, list):
				return obj
			if isinstance(obj, dict):
				for v in obj.values():
					if isinstance(v, list):
						return v
		except Exception:
			pass
		return [] 