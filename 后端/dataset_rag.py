"""
Dataset-backed retrieval for agricultural copywriting examples.

This module is deliberately lightweight: the runtime search path only depends on
the Python standard library, so the demo can keep working even without Chroma or
an embedding provider. It gives the project an auditable RAG baseline now, and
can later be replaced by a vector database behind the same interface.
"""
from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CORPUS_PATH = BASE_DIR / "dataset_corpus.json"

PLATFORM_ALIASES = {
    "xiaohongshu": "小红书",
    "douyin": "抖音",
    "kuaishou": "快手",
    "taobao": "淘宝",
    "tmall": "天猫",
    "jd": "京东",
    "pinduoduo": "拼多多",
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", "\n")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_platform(value: Any) -> str:
    text = normalize_text(value)
    return PLATFORM_ALIASES.get(text, text)


def split_tags(value: Any) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    parts = re.split(r"[,，、/|；;]+", text)
    return [p.strip() for p in parts if p.strip()]


def tokenize(text: str) -> set[str]:
    """Simple Chinese-friendly tokenization for a no-dependency BM25-ish search."""
    text = normalize_text(text).lower()
    tokens = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]{2,}", text))
    chinese = re.findall(r"[\u4e00-\u9fff]+", text)
    for block in chinese:
        if len(block) <= 2:
            tokens.add(block)
        else:
            tokens.update(block[i : i + 2] for i in range(len(block) - 1))
            tokens.update(block[i : i + 3] for i in range(len(block) - 2))
    return {t for t in tokens if t}


@dataclass
class RetrievalResult:
    score: float
    record: dict[str, Any]
    matched_terms: list[str]


class DatasetRetriever:
    def __init__(self, corpus_path: str | os.PathLike[str] = DEFAULT_CORPUS_PATH):
        self.corpus_path = Path(corpus_path)
        self.records = self._load_records()
        self._doc_tokens = [tokenize(self._record_text(r)) for r in self.records]
        self._idf = self._build_idf(self._doc_tokens)

    def _load_records(self) -> list[dict[str, Any]]:
        if not self.corpus_path.exists():
            return []
        with self.corpus_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = data.get("records", [])
        return [r for r in data if isinstance(r, dict)]

    def _build_idf(self, docs: list[set[str]]) -> dict[str, float]:
        if not docs:
            return {}
        df: dict[str, int] = {}
        for terms in docs:
            for term in terms:
                df[term] = df.get(term, 0) + 1
        total = len(docs)
        return {term: math.log((total + 1) / (count + 0.5)) + 1 for term, count in df.items()}

    def _record_text(self, record: dict[str, Any]) -> str:
        fields: Iterable[Any] = (
            record.get("title"),
            record.get("body"),
            record.get("category"),
            record.get("product_name"),
            record.get("price_tier"),
            " ".join(record.get("audiences") or []),
            " ".join(record.get("angles") or []),
            record.get("notes"),
        )
        return " ".join(normalize_text(f) for f in fields if f)

    def search(
        self,
        query: str,
        *,
        platform: str = "",
        category: str = "",
        target_user: str = "",
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        if not self.records:
            return []

        query_text = " ".join([query, category, target_user])
        query_terms = tokenize(query_text)
        platform = normalize_platform(platform)
        category = normalize_text(category)
        target_tags = set(split_tags(target_user))

        scored: list[RetrievalResult] = []
        for idx, record in enumerate(self.records):
            doc_terms = self._doc_tokens[idx]
            matched = query_terms & doc_terms
            score = sum(self._idf.get(term, 1.0) for term in matched)

            if platform and normalize_platform(record.get("platform")) == platform:
                score += 3.0
            if category and category in normalize_text(record.get("category")):
                score += 2.0
            audiences = set(record.get("audiences") or [])
            if target_tags:
                score += 1.5 * len(audiences & target_tags)

            product = normalize_text(record.get("product_name"))
            if product and product in normalize_text(query):
                score += 2.0

            if score > 0:
                scored.append(RetrievalResult(round(score, 4), record, sorted(matched)[:12]))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:top_k]

    def search_as_context(self, **kwargs: Any) -> list[dict[str, Any]]:
        items = self.search(**kwargs)
        context = []
        for item in items:
            r = item.record
            context.append(
                {
                    "score": item.score,
                    "platform": r.get("platform", ""),
                    "title": r.get("title", ""),
                    "product_name": r.get("product_name", ""),
                    "category": r.get("category", ""),
                    "body": r.get("body", ""),
                    "angles": r.get("angles", []),
                    "audiences": r.get("audiences", []),
                    "matched_terms": item.matched_terms,
                }
            )
        return context


_instance: DatasetRetriever | None = None


def get_dataset_retriever() -> DatasetRetriever:
    global _instance
    if _instance is None:
        _instance = DatasetRetriever()
    return _instance

