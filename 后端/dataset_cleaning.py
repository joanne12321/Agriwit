"""
Create a conservative, reviewable cleaned copy of the copywriting corpus.

This script never overwrites dataset_corpus.json. It removes or softens
obvious absolute claims and fills only safe metadata defaults. It does not
invent product facts; short, vague, or still-risky records remain excluded
from SFT and are listed in dataset_cleaning_report.json.

Usage:
    python dataset_cleaning.py
    python dataset_cleaning.py --input dataset_corpus.json --output-dir .
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent

# Longer phrases must be replaced before shorter tokens.
REPLACEMENTS = [
    ("一百倍", "更有新鲜感"),
    ("100%", "足量"),
    ("百分之百", "足量"),
    ("顶级", "品质突出"),
    ("极品", "特色鲜明"),
    ("天花板", "品质突出"),
    ("独一无二", "特色鲜明"),
    ("世界第一", "具有代表性"),
    ("中国第一", "具有代表性"),
    ("全网第一", "具有代表性"),
    ("销量第一", "销量表现较好"),
    ("第一", "具有代表性"),
    ("唯一", "少见的"),
    ("最甜", "甜度突出"),
    ("最好吃", "口感较好"),
    ("最好", "较好"),
    ("最便宜", "价格友好"),
    ("最受欢迎", "受到不少消费者关注"),
    ("最优", "较优"),
    ("最", "较为"),
    ("绝对", "比较"),
    ("无敌", "很有特色"),
    ("封神", "表现亮眼"),
    ("神仙味道", "独特风味"),
    ("一定会回来", "不少人会再次考虑"),
    ("一定会回购", "有机会再次购买"),
    ("放心吃", "适合日常食用"),
    ("孕妇放心吃", "孕产家庭可结合自身情况选择"),
    ("孕妈放心吃", "孕产家庭可结合自身情况选择"),
    ("减肥", "体重管理期间"),
    ("降血压", "日常饮食"),
    ("抗癌", "营养"),
    ("治疗", "日常食用"),
    ("根治", "日常调理"),
    ("药效", "食用体验"),
    ("特效", "特色"),
    ("纯天然", "自然风味"),
    ("绝不磨磨蹭蹭", "及时处理"),
    ("坏果肯定赔", "坏果按售后规则处理"),
]

RISK_PATTERNS = [
    r"最(?:佳|好|甜|便宜|受欢迎|优|大|高|低|新)??",
    r"第一|唯一|独家|顶级|极品|天花板|无敌|封神|100%|百分之百",
    r"抗癌|降血压|治疗|根治|特效|药效|减肥|壮阳|排毒",
    r"纯天然|绝对|世界级|国家级|全网首发",
]


def clean_text(value: Any) -> tuple[str, list[str]]:
    text = "" if value is None else str(value)
    actions: list[str] = []
    for old, new in REPLACEMENTS:
        if old in text:
            text = text.replace(old, new)
            actions.append(f"{old}->{new}")
    text = re.sub(r"\s+", " ", text).strip()
    return text, actions


def infer_angles(record: dict[str, Any]) -> list[str]:
    text = " ".join(
        str(record.get(key, ""))
        for key in ("title", "body", "notes")
    )
    mapping = [
        ("采摘", "新鲜采摘"),
        ("现摘", "新鲜采摘"),
        ("产地", "产地特色"),
        ("家乡", "家乡风味"),
        ("口感", "口感特点"),
        ("甜", "甜味口感"),
        ("脆", "脆爽口感"),
        ("糯", "软糯口感"),
        ("送礼", "送礼场景"),
        ("冷链", "冷链配送"),
        ("手工", "手工工艺"),
        ("低盐", "低盐制作"),
    ]
    result: list[str] = []
    for needle, angle in mapping:
        if needle in text and angle not in result:
            result.append(angle)
    return result[:5] or ["产品特色"]


def has_risk(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in RISK_PATTERNS)


def clean_record(raw: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    record = dict(raw)
    actions: list[str] = []
    for key in ("title", "body", "notes"):
        record[key], changed = clean_text(record.get(key, ""))
        if changed:
            actions.extend([f"{key}:{item}" for item in changed])

    if not record.get("audiences"):
        record["audiences"] = ["日常采购消费者"]
        actions.append("补充默认受众：日常采购消费者")
    if not record.get("festivals"):
        record["festivals"] = ["日常"]
        actions.append("补充默认场景：日常")
    if not record.get("angles"):
        record["angles"] = infer_angles(record)
        actions.append("根据原文关键词补充宣传角度")

    record["body_length"] = len(record.get("body", ""))
    record["title_length"] = len(record.get("title", ""))
    original_flags = list(record.get("quality_flags") or [])
    record["original_quality_flags"] = original_flags
    record["cleaning_actions"] = actions

    remaining_flags: list[str] = []
    if not record.get("platform"):
        remaining_flags.append("missing_platform")
    if not record.get("title"):
        remaining_flags.append("missing_title")
    if not record.get("body"):
        remaining_flags.append("missing_body")
    if not record.get("product_name"):
        remaining_flags.append("missing_product_name")
    if not record.get("category"):
        remaining_flags.append("missing_category")
    if record["body_length"] < 50:
        remaining_flags.append("body_too_short")
    if record["body_length"] > 800:
        remaining_flags.append("body_too_long_for_single_chunk")
    if has_risk(f"{record.get('title', '')} {record.get('body', '')}"):
        remaining_flags.append("needs_claim_review")

    record["quality_flags"] = remaining_flags
    record["cleaning_status"] = "ready_for_sft" if not remaining_flags else "needs_review"
    return record, actions


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(BASE_DIR / "dataset_corpus.json"))
    parser.add_argument("--output-dir", default=str(BASE_DIR))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    corpus = json.loads(input_path.read_text(encoding="utf-8"))
    raw_records = corpus.get("records", []) if isinstance(corpus, dict) else corpus

    cleaned_records: list[dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    for raw in raw_records:
        cleaned, actions = clean_record(raw)
        cleaned_records.append(cleaned)
        for action in actions:
            action_counts[action.split(":", 1)[-1]] += 1

    # Exact duplicate bodies should not be repeated in SFT.
    seen_bodies: set[str] = set()
    duplicate_count = 0
    for record in cleaned_records:
        body = record.get("body", "")
        if body and body in seen_bodies:
            record["quality_flags"].append("duplicate_body")
            record["cleaning_status"] = "needs_review"
            duplicate_count += 1
        elif body:
            seen_bodies.add(body)

    ready = sum(r.get("cleaning_status") == "ready_for_sft" for r in cleaned_records)
    report = {
        "source_file": str(input_path),
        "total_records": len(cleaned_records),
        "ready_for_sft": ready,
        "needs_review": len(cleaned_records) - ready,
        "duplicate_after_cleaning": duplicate_count,
        "action_counts": dict(action_counts.most_common()),
        "remaining_flag_counts": dict(
            Counter(flag for r in cleaned_records for flag in r.get("quality_flags", []))
        ),
        "policy": "自动修正明确风险；不补写未经来源支持的产品事实；短文案和长文案需人工决定是否拆分或扩写。",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned_corpus = {
        "schema_version": "agriwit-copywriting-v1-cleaned",
        "source_file": str(input_path),
        "records": cleaned_records,
    }
    (output_dir / "dataset_corpus_cleaned.json").write_text(
        json.dumps(cleaned_corpus, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "dataset_cleaning_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
