"""Lightweight client for calling multimodal LLMs (DashScope/Qwen)."""
from typing import Any, Dict, List
import requests


class DashScopeClient:
    """Simple HTTP client for DashScope multimodal generation."""

    def __init__(self, api_key: str, endpoint: str, model_name: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self.model_name = model_name

    def generate(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call DashScope multimodal generation."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "input": {
                "messages": messages
            }
        }
        response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            raise RuntimeError(f"DashScope error: status={response.status_code}, body={response.text}")
        data = response.json()
        return data
