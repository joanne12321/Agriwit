"""
Build and audit the project copywriting dataset.

Usage:
    python dataset_tools.py --input "../数据集_Sheet1 (1)(1).xlsx"

Outputs:
    dataset_corpus.json
    dataset_quality_report.json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from dataset_rag import normalize_platform, normalize_text, split_tags


BASE_DIR = Path(__file__).resolve().parent


FIELD_MAP = {
    "平台": "platform",
    "标题": "title",
    "正文": "body",
    "商品类别": "category",
    "商品名": "product_name",
    "价格区间": "price_tier",
    "目标受众": "audiences",
    "适用节日": "festivals",
    "宣传角度": "angles",
    "备注": "notes",
    "父记录": "parent_id",
}

REQUIRED_FIELDS = ["platform", "title", "body", "category", "product_name", "angles"]


def _load_xlsx_rows(path: Path) -> list[dict[str, Any]]:
    try:
        import pandas as pd

        df = pd.read_excel(path).fillna("")
        return df.to_dict(orient="records")
    except ImportError:
        pass
    except Exception:
        pass

    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("缺少 pandas/openpyxl，请先安装 requirements.txt 中的数据集依赖。") from exc

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [normalize_text(h) for h in rows[0]]
    result = []
    for raw in rows[1:]:
        item = {}
        for header, value in zip(headers, raw):
            if header:
                item[header] = value
        if any(normalize_text(v) for v in item.values()):
            result.append(item)
    return result


def normalize_record(raw: dict[str, Any], index: int) -> dict[str, Any]:
    record = {"id": f"copy_{index:04d}"}
    for cn, en in FIELD_MAP.items():
        value = raw.get(cn, "")
        if en in {"audiences", "festivals", "angles"}:
            record[en] = split_tags(value)
        elif en == "platform":
            record[en] = normalize_platform(value)
        else:
            record[en] = normalize_text(value)

    record["body_length"] = len(record.get("body", ""))
    record["title_length"] = len(record.get("title", ""))
    record["quality_flags"] = quality_flags(record)
    record["created_at"] = datetime.now().date().isoformat()
    return record


def quality_flags(record: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    for field in REQUIRED_FIELDS:
        if not record.get(field):
            flags.append(f"missing_{field}")
    body = record.get("body", "")
    if len(body) < 50:
        flags.append("body_too_short")
    if len(body) > 800:
        flags.append("body_too_long_for_single_chunk")
    if not record.get("audiences"):
        flags.append("missing_audience")
    if not record.get("festivals"):
        flags.append("missing_festival")
    if re.search(r"(最|第一|唯一|绝对|100%)", body):
        flags.append("possible_ad_law_risk")
    return flags


def build_quality_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    platform_counts = Counter(r.get("platform", "") for r in records)
    category_counts = Counter(r.get("category", "") for r in records)
    price_counts = Counter(r.get("price_tier", "") for r in records)
    festival_counts = Counter(f for r in records for f in r.get("festivals", []))
    flag_counts = Counter(flag for r in records for flag in r.get("quality_flags", []))

    body_lengths = sorted(r.get("body_length", 0) for r in records)
    median_body = body_lengths[len(body_lengths) // 2] if body_lengths else 0

    duplicate_bodies = len(records) - len({r.get("body", "") for r in records})
    ready_records = sum(1 for r in records if not r.get("quality_flags"))

    recommendations = []
    if len(records) < 300:
        recommendations.append("数据量不足：建议暑期先完成300-500条高质量样本，再扩展到1000+。")
    if platform_counts and max(platform_counts.values()) / max(1, len(records)) > 0.6:
        recommendations.append("平台分布过于集中：至少覆盖小红书、抖音/快手、电商详情页、百科/产地介绍。")
    if category_counts and max(category_counts.values()) / max(1, len(records)) > 0.45:
        recommendations.append("品类分布过于集中：单一品类建议不超过总量30%-35%。")
    if flag_counts.get("missing_audience", 0):
        recommendations.append("目标受众需要拆分为身份、地域、圈层，避免混在一个字段里。")
    if duplicate_bodies:
        recommendations.append("存在正文重复，需要去重或保留父记录关系。")
    if not recommendations:
        recommendations.append("当前数据可作为RAG语料继续扩展，并建议补充独立评价集。")

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_records": len(records),
        "ready_records": ready_records,
        "median_body_length": median_body,
        "duplicate_bodies": duplicate_bodies,
        "platform_counts": dict(platform_counts),
        "category_counts": dict(category_counts),
        "price_counts": dict(price_counts),
        "festival_counts": dict(festival_counts),
        "quality_flag_counts": dict(flag_counts),
        "recommendations": recommendations,
    }


def build_dataset(input_path: Path, output_dir: Path) -> tuple[Path, Path]:
    raw_rows = _load_xlsx_rows(input_path)
    records = [normalize_record(row, idx + 1) for idx, row in enumerate(raw_rows)]
    report = build_quality_report(records)

    corpus_path = output_dir / "dataset_corpus.json"
    report_path = output_dir / "dataset_quality_report.json"

    corpus = {
        "schema_version": "agriwit-copywriting-v1",
        "source_file": str(input_path),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "records": records,
    }
    corpus_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return corpus_path, report_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="../数据集_Sheet1 (1)(1).xlsx")
    parser.add_argument("--output-dir", default=str(BASE_DIR))
    args = parser.parse_args()

    corpus_path, report_path = build_dataset(Path(args.input), Path(args.output_dir))
    print(f"dataset_corpus={corpus_path}")
    print(f"quality_report={report_path}")


if __name__ == "__main__":
    main()
