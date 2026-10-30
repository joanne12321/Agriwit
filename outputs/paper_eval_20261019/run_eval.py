"""Bounded prototype evaluation. Real LLM calls; no production history writes."""
from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "后端"
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
from dotenv import load_dotenv
load_dotenv(BACKEND / ".env")
import httpx
import requests
from openai import OpenAI
from PIL import Image, ImageDraw
with contextlib.redirect_stdout(io.StringIO()):
    import ai_service as service
from dataset_rag import get_dataset_retriever

CASES = [
    {"id": "C01", "product": "熟制板栗", "origin": "河北遵化", "weight": "100g", "price": "12.8元", "process": "熟制", "scene": "办公室加餐", "platform": "抖音"},
    {"id": "C02", "product": "生板栗", "origin": "河北迁西", "weight": "500g", "price": "18.6元", "process": "生鲜，必须加热后食用", "scene": "家庭烹饪", "platform": "抖音"},
    {"id": "C03", "product": "红富士苹果", "origin": "山东烟台", "weight": "1000g", "price": "26.8元", "process": "鲜果", "scene": "办公室水果", "platform": "小红书"},
    {"id": "C04", "product": "龙井绿茶", "origin": "浙江绍兴", "weight": "100g", "price": "认证未提供；价格未确认", "process": "散装干茶，需冲泡", "scene": "日常饮茶", "platform": "小红书"},
    {"id": "C05", "product": "鲜香菇", "origin": "湖北随州", "weight": "250g", "price": "9.8元", "process": "鲜菇，必须烹熟", "scene": "家庭做饭", "platform": "抖音"},
    {"id": "C06", "product": "烤红薯干", "origin": "福建连城", "weight": "200g", "price": "15.8元", "process": "熟制即食", "scene": "出游零食", "platform": "小红书"},
    {"id": "C07", "product": "散装大米", "origin": "黑龙江佳木斯", "weight": "1000g", "price": "11.8元", "process": "生米，需煮熟", "scene": "家庭主食", "platform": "抖音"},
    {"id": "C08", "product": "鲜玉米", "origin": "吉林四平", "weight": "500g", "price": "价格未确认", "process": "生鲜，需煮熟", "scene": "家庭备餐", "platform": "小红书"},
]


def save(name, value):
    (OUTPUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def requirement(case):
    return (
        f"测试用虚构产品档案：产品{case['product']}；产地{case['origin']}；净含量{case['weight']}；"
        f"价格{case['price']}；形态{case['process']}。写约120字宣传文案，场景为{case['scene']}。"
        "必须原样包含产品名称、产地和净含量；有已知价格时必须原样写出。"
        "未知价格和认证不得补全，不得编造有机认证、无添加、零农残、营养功效、具体优惠、库存或发货承诺。"
        "参考案例仅可借鉴表达，不得照搬其他产品的事实。对生鲜产品不得描述为开袋即食。"
    )


def context(case):
    return {
        "product_name": case["product"], "origin": case["origin"],
        "traits": [case["weight"], case["price"], case["process"]],
        "culture": "通用", "style_guide": "清晰、客观、亲切，不夸大事实", "platform": case["platform"],
        "target_user": "家庭消费者", "user_input": requirement(case),
        "word_count_target": 120, "forbidden_words": ["全网最低", "治疗", "降血糖", "减肥", "零农残"],
        "rag_examples": [], "extra_info": [], "qa_feedback": "",
    }


def field_check(text, case):
    # A narrow exact-field check, NOT a claim-level factual or business evaluation.
    required = {"product": case["product"], "origin": case["origin"], "weight": case["weight"]}
    if re.fullmatch(r"\d+(?:\.\d+)?元", case["price"]):
        required["price"] = case["price"]
    missing = [key for key, value in required.items() if value not in text]
    risky = [word for word in ["全网最低", "零农残", "降血糖", "减肥", "治疗"] if word in text]
    return {"required": required, "missing": missing, "covered": len(required) - len(missing),
            "total": len(required), "literal_risk_hits": risky,
            "strict_field_pass": bool(text) and not missing}


class Meter:
    def __init__(self, api):
        self.api = api
        self.records = []

    def create(self, **kwargs):
        # Bound every model request. Never retry a billable request automatically.
        start = time.perf_counter()
        record = {"model_requested": kwargs["model"], "max_tokens": kwargs.get("max_tokens"),
                  "temperature": kwargs.get("temperature"),
                  "prompt_sha256": hashlib.sha256(json.dumps(kwargs["messages"], ensure_ascii=False).encode()).hexdigest()}
        try:
            resp = self.api.create(**kwargs)
            record.update({"ok": True, "model_returned": resp.model, "usage": resp.usage.model_dump() if resp.usage else None,
                           "finish_reason": resp.choices[0].finish_reason})
            return resp
        except Exception as error:
            record.update({"ok": False, "error_type": type(error).__name__, "status_code": getattr(error, "status_code", None)})
            raise
        finally:
            record["seconds"] = round(time.perf_counter() - start, 4)
            self.records.append(record)


client = OpenAI(api_key=service.LLM_API_KEY or "missing-key", base_url=service.LLM_BASE_URL,
                max_retries=0, timeout=httpx.Timeout(60.0, connect=10.0))
meter = Meter(client.chat.completions)
service.llm = SimpleNamespace(chat=SimpleNamespace(completions=meter))


def quiet_call(fn):
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
        result = fn()
    return result


def model_smoke():
    try:
        resp = meter.create(model=service.LLM_MODEL, messages=[{"role": "user", "content": "只回答：连接正常"}], max_tokens=16, temperature=0)
        return {"ok": True, "content": resp.choices[0].message.content, "calls": meter.records}
    except Exception:
        return {"ok": False, "calls": meter.records}


def source_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_text():
    retriever = get_dataset_retriever()
    # Recall is fixed across the two RAG groups to isolate the audit module.
    evidence = {c["id"]: retriever.search_as_context(query=c["product"] + " " + c["scene"],
                platform=c["platform"], top_k=5) for c in CASES}
    save("retrieved_cases.json", evidence)
    jobs = [(case, variant) for case in CASES for variant in ["writer_only", "writer_rag", "writer_rag_qa"]]
    random.Random(20261019).shuffle(jobs)
    rows = []
    for case, variant in jobs:
        start = time.perf_counter()
        before = len(meter.records)
        ctx = context(case)
        if variant != "writer_only":
            ctx["rag_examples"] = evidence[case["id"]]
        wid = f"paper-eval-{case['id']}-{variant}"
        row = {"case_id": case["id"], "variant": variant, "scope": "original CopywriterAgent and QAAgent; isolated controlled-context benchmark", "drafts": []}
        try:
            rounds = 3 if variant == "writer_rag_qa" else 1
            text = ""
            for iteration in range(rounds):
                text = quiet_call(lambda: service.CopywriterAgent("CopywriterAgent", wid).run(ctx))["content"]
                draft = {"round": iteration + 1, "text": text}
                row["drafts"].append(draft)
                if variant == "writer_rag_qa":
                    qa = quiet_call(lambda: service.QAAgent("QAAgent", wid).run({**ctx, "content": text}))
                    draft["qa"] = qa
                    if qa["passed"]:
                        break
                    ctx["qa_feedback"] = qa["feedback"]
                    ctx["content_draft"] = text
            row.update({"ok": bool(text), "text": text, "field_check": field_check(text, case),
                        "final_qa_pass": row["drafts"][-1].get("qa", {}).get("passed")})
        except Exception as error:
            row.update({"ok": False, "error_type": type(error).__name__})
        row.update({"seconds": round(time.perf_counter() - start, 4), "calls": meter.records[before:]})
        rows.append(row)
        save("text_results.json", rows)
        print(json.dumps({"progress": len(rows), "total": len(jobs), "case": case["id"], "variant": variant, "ok": row["ok"], "seconds": row["seconds"]}), flush=True)
        if not row["ok"] and all(not r["ok"] for r in rows[-2:]) and len(rows) >= 2:
            print("Stopping after consecutive model failures.", flush=True)
            break
    return rows


def run_scripts():
    rows = []
    for case in CASES:
        start = time.perf_counter()
        before = len(meter.records)
        response = quiet_call(lambda: service.app.test_client().post("/api/ai/generate-live-script", json={
            "product_name": case["product"], "platform": case["platform"], "duration": 60,
            "ai_content": requirement(case), "user_id": "", "style": "fresh"}))
        data = response.get_json() or {}
        script = data.get("script", "")
        calls = meter.records[before:]
        fallback = script == service._generate_fallback_script(case["product"], case["platform"], 60)
        row = {"case_id": case["id"], "status": response.status_code, "seconds": round(time.perf_counter() - start, 4),
               "ok": response.status_code == 200 and bool(script) and not fallback and any(c["ok"] for c in calls),
               "fallback": fallback, "text": script, "field_check": field_check(script, case), "calls": calls}
        rows.append(row)
        save("script_results.json", rows)
        print(json.dumps({"script": case["id"], "ok": row["ok"], "seconds": row["seconds"]}), flush=True)
        if not row["ok"] and len(rows) >= 2 and not rows[-2]["ok"]:
            break
    return rows


def fixture_image():
    image = Image.new("RGB", (1080, 1080), "white")
    draw = ImageDraw.Draw(image)
    for i in range(8):
        for j in range(8):
            draw.rectangle((i * 135, j * 135, (i + 1) * 135, (j + 1) * 135), fill=(180 + i * 8, 180 + j * 8, 205))
    draw.rectangle((360, 300, 720, 780), fill=(47, 97, 62))
    draw.text((390, 520), "LAYOUT TEST ONLY", fill="white")
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    image.save(OUTPUT / "synthetic_layout_fixture.png")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def run_images_and_errors():
    session = requests.Session()
    session.trust_env = False
    image_b64 = fixture_image()
    rows = []
    for index, case in enumerate(CASES):
        start = time.perf_counter()
        response = session.post("http://127.0.0.1:5003/api/poster/render-text", json={
            "base_image": image_b64, "poster_text": {"headline": case["product"], "subhead": case["origin"],
            "badge": case["weight"], "footer": case["price"], "event": "排版测试", "brand": "合成测试资料",
            "disclaimer": "仅用于接口测试"}}, timeout=30)
        data = response.json()
        decoded = None
        if data.get("image"):
            decoded = Image.open(io.BytesIO(base64.b64decode(data["image"].split(",")[-1])))
            decoded.save(OUTPUT / f"poster_{case['id']}.jpg")
        rows.append({"case_id": case["id"], "seconds": round(time.perf_counter() - start, 4), "status": response.status_code,
                     "ok": response.status_code == 200 and bool(data.get("success")) and decoded is not None and decoded.size == (1080, 1080),
                     "dimensions": list(decoded.size) if decoded else None, "scope": "live HTTP text-render endpoint only; synthetic raster fixture; no background removal or image generation"})
    save("image_results.json", rows)
    errors = []
    checks = [
        ("missing_image_pipeline", "post", "http://127.0.0.1:5003/api/image/full-pipeline", {}, 400),
        ("missing_base_render", "post", "http://127.0.0.1:5003/api/poster/render-text", {}, 400),
        ("unknown_image_task", "get", "http://127.0.0.1:5003/api/task/paper-eval-unknown", None, 404),
        ("unknown_workflow", "get", "http://127.0.0.1:5001/api/workflow/status/paper-eval-unknown", None, 404),
        ("invalid_image_render", "post", "http://127.0.0.1:5003/api/poster/render-text", {"base_image": "not-base64"}, 500),
    ]
    for name, method, url, payload, expected in checks:
        start = time.perf_counter()
        response = session.request(method, url, json=payload, timeout=10)
        data = response.json()
        errors.append({"name": name, "status": response.status_code, "expected": expected,
                       "seconds": round(time.perf_counter() - start, 4),
                       "contract_pass": response.status_code == expected and bool(data.get("error"))})
    save("error_results.json", errors)
    return rows, errors


def percentile(values, p):
    if not values:
        return None
    # Nearest-rank quantile; P95 equals the maximum for n=8.
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(len(ordered) * p) - 1)], 3)


def summarize(rows):
    checks = [r["field_check"] for r in rows if r.get("ok") and "field_check" in r]
    calls = [c for r in rows for c in r.get("calls", [])]
    usages = [c["usage"] for c in calls if c.get("usage")]
    return {"n": len(rows), "technical_complete": sum(bool(r.get("ok")) for r in rows),
            "p50_seconds": percentile([r["seconds"] for r in rows if r.get("ok")], .5),
            "p95_seconds": percentile([r["seconds"] for r in rows if r.get("ok")], .95),
            "field_exact_pass": sum(c["strict_field_pass"] for c in checks),
            "covered_fields": sum(c["covered"] for c in checks), "total_fields": sum(c["total"] for c in checks),
            "calls": len(calls), "prompt_tokens": sum(u.get("prompt_tokens", 0) for u in usages),
            "completion_tokens": sum(u.get("completion_tokens", 0) for u in usages),
            "total_tokens": sum(u.get("total_tokens", 0) for u in usages),
            "qa_final_pass": sum(r.get("final_qa_pass") is True for r in rows)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.smoke:
        result = model_smoke()
        save("model_smoke.json", result)
        print(json.dumps(result, ensure_ascii=False))
        return
    if not args.run:
        parser.error("Choose --smoke or --run (billable model requests).")
    save("cases.json", {"type": "synthetic test fixtures, not real company facts", "cases": CASES})
    save("environment.json", {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "python": platform.python_version(),
        "os": platform.platform(), "model": service.LLM_MODEL, "openai_sdk": importlib.metadata.version("openai"),
        "source_hashes": {p.name: source_hash(p) for p in [BACKEND / "ai_service.py", BACKEND / "image_service.py", BACKEND / "dataset_rag.py", BACKEND / "dataset_corpus.json"]},
        "design": "8 synthetic tasks, 3 randomized controlled-context text variants; real model; unchanged production classes; persistence not called; one repetition; sequential; no claims of human usability or full-system performance",
        "network": "real model requests, zero SDK retries, 60-second per-call timeout", "pricing": "not available; token usage only"})
    images, errors = run_images_and_errors()
    text = run_text()
    scripts = run_scripts() if any(r["ok"] for r in text) else []
    summary = {variant: summarize([r for r in text if r["variant"] == variant]) for variant in ["writer_only", "writer_rag", "writer_rag_qa"]}
    summary.update({"live_script": summarize(scripts), "poster_text_render": summarize(images),
                    "error_contracts": {"n": len(errors), "passed": sum(r["contract_pass"] for r in errors)},
                    "scope_warning": "Not full-system end-to-end, not trained model, not generative poster, not video, not business usability; no independent human review"})
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    service.neo4j_driver.close()
    client.close()


if __name__ == "__main__":
    main()
