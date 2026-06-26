"""文本向量化: 远程 embedding API(硅基流动 bge-m3, OpenAI 兼容接口)。

设计成可切换: 换模型/换 provider 只改 config 里的 base_url + model + key。
不依赖 openai SDK, 直接 httpx POST /v1/embeddings。
"""
import math

import httpx

from .config import settings


class EmbeddingError(RuntimeError):
    """embedding 调用失败(未配置 key / 接口报错 / 超时)。"""


class Embedder:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 30.0):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_settings(cls) -> "Embedder":
        return cls(settings.embed_base_url, settings.embed_api_key, settings.embed_model)

    def embed(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """批量向量化。返回顺序与输入一致。"""
        if not texts:
            return []
        if not self.api_key:
            raise EmbeddingError("未配置 SILICONFLOW_API_KEY，无法调用 embedding 接口")
        results: list[list[float] | None] = [None] * len(texts)
        with httpx.Client(timeout=self.timeout) as client:
            for start in range(0, len(texts), batch_size):
                chunk = texts[start : start + batch_size]
                resp = client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"model": self.model, "input": chunk},
                )
                if resp.status_code != 200:
                    raise EmbeddingError(
                        f"embedding API 返回 {resp.status_code}: {resp.text[:300]}"
                    )
                # OpenAI 兼容: data 是 [{embedding, index}, ...], index 指向原批次内位置
                payload = resp.json()
                for item in payload["data"]:
                    idx = item.get("index", 0)
                    results[start + idx] = item["embedding"]
        missing = [i for i, r in enumerate(results) if r is None]
        if missing:
            raise EmbeddingError(f"部分文本未返回向量, 缺失位置: {missing[:5]}")
        return results  # type: ignore[return-value]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


def cosine(a: list[float], b: list[float]) -> float:
    """余弦相似度。纯 Python 实现(278×1024 量级足够快, 免引入 numpy)。"""
    if not a or not b:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))
