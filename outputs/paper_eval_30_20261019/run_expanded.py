"""Run a fresh 30-task synthetic benchmark; do not overwrite the pilot records."""
from pathlib import Path
import importlib.util
import json
import time

BASE = Path(__file__).resolve().parent
PILOT = BASE.parent / "paper_eval_20261019" / "run_eval.py"
spec = importlib.util.spec_from_file_location("pilot_evaluator", PILOT)
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
evaluation.OUTPUT = BASE

PRODUCTS = [
    ("熟制板栗", "河北遵化", "熟制带壳，独立袋装", "办公室加餐", "100g", "12.8元"),
    ("红富士苹果", "山东烟台", "鲜果，食用前清洗", "家庭水果", "1000g", "26.8元"),
    ("龙井绿茶", "浙江绍兴", "散装干茶，需冲泡", "日常饮茶", "100g", "38.8元"),
    ("鲜香菇", "湖北随州", "鲜菇，必须烹熟", "家庭做饭", "250g", "9.8元"),
    ("烤红薯干", "福建连城", "熟制即食，袋装", "出游零食", "200g", "15.8元"),
    ("散装大米", "黑龙江佳木斯", "生米，需煮熟", "家庭主食", "1000g", "11.8元"),
    ("鲜玉米", "吉林四平", "生鲜，必须加热后食用", "家庭备餐", "500g", "8.8元"),
    ("百花蜂蜜", "湖北神农架", "瓶装液态蜂蜜，不含功效或认证资料", "日常冲饮", "250g", "29.8元"),
    ("带壳核桃", "新疆阿克苏", "生制带硬壳，需去壳取仁后按需加工", "家庭备料", "500g", "22.8元"),
    ("脐橙", "江西赣州", "鲜果，需清洗剥皮", "家庭水果", "1500g", "32.8元"),
]
CASES = []
for product_index, (product, origin, process, scene, weight, price) in enumerate(PRODUCTS):
    for condition in range(3):
        index = len(CASES) + 1
        CASES.append({
            "id": f"E{index:02d}", "product": product, "origin": origin,
            "weight": weight if condition != 2 else {"100g": "200g", "1000g": "2000g", "250g": "500g", "200g": "400g", "500g": "1000g", "1500g": "3000g"}[weight],
            "price": "价格未确认" if condition == 1 else price,
            "process": process, "scene": scene if condition != 2 else "家庭日常采购",
            "platform": "抖音" if (product_index + condition) % 2 == 0 else "小红书",
            "condition": ["基本资料完整", "价格缺失", "加工包装与履约约束"][condition],
            "constraints": "认证、营养功效、保质期、促销和物流信息均未提供。" + (
                "本任务明确没有抽奖、赠品或优惠；发货地点和时效未确认；不得推断去壳、即食、独立包装等未提供属性。"
                if condition == 2 else "不得将产地推断为发货地，不得自行安排抽奖赠品。"),
        })
assert len(CASES) == 30 and sum(c["platform"] == "抖音" for c in CASES) == 15
evaluation.CASES = CASES
original_requirement = evaluation.requirement
evaluation.requirement = lambda case: original_requirement(case) + case["constraints"]

# A hard ceiling prevents an unexpected QA loop from causing unbounded charges.
original_create = evaluation.meter.create
def bounded_create(**kwargs):
    if len(evaluation.meter.records) >= 210:
        raise RuntimeError("Evaluation model request budget of 210 exhausted")
    return original_create(**kwargs)
evaluation.meter.create = bounded_create

def main():
    if (BASE / "text_results.json").exists():
        raise RuntimeError("Records already exist; refusing to repeat billable requests")
    evaluation.save("cases.json", {"type": "synthetic test fixtures, not real company facts", "cases": CASES})
    evaluation.save("environment.json", {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "python": evaluation.platform.python_version(), "os": evaluation.platform.platform(),
        "model": evaluation.service.LLM_MODEL, "openai_sdk": evaluation.importlib.metadata.version("openai"),
        "source_hashes": {p.name: evaluation.source_hash(p) for p in [evaluation.BACKEND / "ai_service.py", evaluation.BACKEND / "image_service.py", evaluation.BACKEND / "dataset_rag.py", evaluation.BACKEND / "dataset_corpus.json"]},
        "design": "30 synthetic tasks: 10 product archetypes x 3 information conditions; 15 tasks per platform; 3 shuffled text variants; one repetition; controlled module calls, not full workflow or human acceptance",
        "network": "real model requests; zero SDK retries; 60 seconds per request; hard limit 210 model calls",
        "pricing": "not available; token usage only", "pilot": "separate 8-task pilot excluded from this batch",
        "runner_sha256": evaluation.source_hash(Path(__file__)),
    })
    try:
        evaluation.run_text()
        evaluation.run_scripts()
        evaluation.run_images_and_errors()
        evaluation.save("completed.json", {"completed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "model_requests": len(evaluation.meter.records)})
        print("Expanded evaluation completed.", flush=True)
    finally:
        evaluation.service.neo4j_driver.close()
        evaluation.client.close()

if __name__ == "__main__":
    main()
