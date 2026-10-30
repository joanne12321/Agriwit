"""Build the two replacement tables from the expanded batch, without model calls."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import html
import json
import math
import re

BASE = Path(__file__).resolve().parent
PAGE = BASE.parent / "论文表3表4_替换稿.html"

def load(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))

def save(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

def percentile(values, p):
    return sorted(values)[math.ceil(len(values) * p) - 1] if values else None

def decimal(value):
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

RISK = re.compile(r"产地直发|产地直供|现采|抽[^。！!？?\n]{0,40}送")
cases = load("cases.json")["cases"]
texts, scripts, images, errors = [load(name) for name in ["text_results.json", "script_results.json", "image_results.json", "error_results.json"]]
assert len(cases) == len(scripts) == len(images) == 30 and len(texts) == 90
assert len({(r["case_id"], r["variant"]) for r in texts}) == 90
groups = {name: [r for r in texts if r["variant"] == name] for name in ["writer_only", "writer_rag", "writer_rag_qa"]}
summary, flags = {}, []
for name, rows in {**groups, "live_script": scripts, "poster_text_render": images}.items():
    calls = [c for row in rows for c in row.get("calls", [])]
    times = [row["seconds"] for row in rows if row["ok"]]
    checks = [row["field_check"] for row in rows if "field_check" in row]
    tokens = sum((c.get("usage") or {}).get("total_tokens", 0) for c in calls)
    summary[name] = {
        "n": len(rows), "complete": sum(row["ok"] for row in rows),
        "p50": percentile(times, .5), "p95": percentile(times, .95),
        "covered_fields": sum(c["covered"] for c in checks), "total_fields": sum(c["total"] for c in checks),
        "field_pass": sum(c["strict_field_pass"] for c in checks),
        "risk_tasks": sum(bool(RISK.search(row.get("text", ""))) for row in rows),
        "calls": len(calls), "successful_calls": sum(c["ok"] for c in calls),
        "total_tokens": tokens, "mean_tokens": tokens / len(rows),
        "model_returned": sorted({c.get("model_returned") for c in calls if c.get("model_returned")}),
        "finish_reasons": sorted({c.get("finish_reason") for c in calls if c.get("finish_reason")}),
    }
    for row in rows:
        hits = [{"phrase": m.group(), "context": row["text"][max(0, m.start()-25):m.end()+25]} for m in RISK.finditer(row.get("text", ""))]
        if hits:
            flags.append({"group": name, "case_id": row["case_id"], "hits": hits})
qa = groups["writer_rag_qa"]
summary["audit"] = {
    "first_pass": sum(row["drafts"][0].get("qa", {}).get("passed", False) for row in qa),
    "final_pass": sum(row.get("final_qa_pass") is True for row in qa),
    "rounds": {row["case_id"]: len(row["drafts"]) for row in qa},
}
summary["errors"] = {
    "n": len(errors), "json_error_returned": sum(row["contract_pass"] for row in errors),
    "controlled_4xx": sum(row["contract_pass"] and 400 <= row["status"] < 500 for row in errors),
    "p50": percentile([row["seconds"] for row in errors], .5),
    "p95": percentile([row["seconds"] for row in errors], .95),
}
summary["risk_rule"] = RISK.pattern
summary["design"] = {"product_archetypes": 10, "information_conditions": 3, "tasks": 30, "repetitions": 1, "pilot_included": False}
save("verified_summary.json", summary)
save("risk_screening.json", flags)

def duration(s):
    return f'{s["p50"]:.3f} / {s["p95"]:.3f}' if s["p50"] is not None else "无成功记录"

def fraction(n, total):
    return f"{n}/{total}（{n/total*100:.1f}%）"

def fields(s):
    return fraction(s["covered_fields"], s["total_fields"])

def table(headers, rows, widths):
    cols = ''.join(f'<col style="width:{w}%">' for w in widths)
    head = ''.join(f'<th scope="col">{html.escape(h)}</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(c))}</td>' for c in row) + '</tr>' for row in rows)
    return f'<div class="table-scroll"><table><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

a, b, c = [summary[key] for key in groups]
script, image, err = [summary[key] for key in ["live_script", "poster_text_render", "errors"]]
table3 = table(
    ["测试任务与调用范围", "任务数", "P50 / P95（秒）", "技术完成／规范响应", "自动核对结果与边界"],
    [
        ["文案：创作＋案例检索＋现有审核", 30, duration(c), fraction(c["complete"], 30), f'指定字段：{fields(c)}；非人工可用率'],
        ["海报排版：本地HTTP文字渲染接口", 30, duration(image), fraction(image["complete"], 30), f'{image["complete"]}张可解码且为1080×1080；未核验OCR、实拍真实性'],
        ["直播脚本：Flask测试客户端＋真实模型", 30, duration(script), fraction(script["complete"], 30), f'指定字段：{fields(script)}；模板降级{sum(row["fallback"] for row in scripts)}次；未实测口播时长'],
        ["完整任务包：资料到多物料交付", "未测", "不适用", "未测", "未进行端到端验收，不从模块结果推算"],
        ["异常响应：缺参、未知任务、无效图像", err["n"], duration(err), "规范4xx：" + fraction(err["controlled_4xx"], err["n"]), f'JSON错误返回{err["json_error_returned"]}/{err["n"]}；不规范状态另行分析，未测试断点恢复'],
    ], [26, 7, 16, 22, 29])
labels = ["A：既有创作节点", "B：A＋案例检索", "C：B＋现有审核（最多3轮）"]
table4 = table(
    ["受控对比配置", "任务数", "指定字段保留率", "指定风险短语命中任务率", "P50 / P95（秒）", "模型调用总次数", "平均Token／任务"],
    [[label, s["n"], fields(s), fraction(s["risk_tasks"], s["n"]), duration(s), s["calls"], decimal(s["mean_tokens"])] for label, s in zip(labels, [a, b, c])],
    [22, 7, 15, 16, 17, 11, 12])

contents3 = f'''<p>为扩大初步测试的任务覆盖范围，本研究于2026年10月19日另行开展30项合成任务的模块评测，原8项探索性测试不并入本轮统计。测试覆盖熟制板栗、苹果、绿茶、鲜香菇、红薯干、大米、鲜玉米、蜂蜜、带壳核桃和脐橙10类产品；每类设置基本资料完整、价格缺失、加工包装与履约约束3种资料情形，共30份任务。抖音与小红书各15份，三种资料情形各10份。产地、规格与价格均为测试设定，不对应真实企业商品；同类任务共享产品原型，因此30项任务不代表30家独立企业或30类独立产品。结果见表3。</p>
<h3>表3 原型模块功能与响应测试结果（30项合成任务）</h3>{table3}
<p class="footnote">注：每项任务每个配置运行1次，顺序执行；文案三组按固定随机种子20261019打乱运行顺序。文案直接调用现有CopywriterAgent、DatasetRetriever和QAAgent；脚本通过Flask测试客户端调用现有路由函数，均为真实模型请求。排版通过本地HTTP接口，使用统一1080×1080合成测试底图替换文字，不涉及生成式背景、抠图或真实商品照片。各行调用和计时边界不同，不作模块间速度排名。</p>
<p>技术完成指模型调用成功且返回非空输出，脚本模板降级不算正常完成；排版须HTTP成功、图像可解码且尺寸符合要求。指定字段只检查产品名称、产地、净含量及已提供价格的原样保留；本轮共110个必查字段，10项未确认价格不要求补全。该检查不能发现所有新增陈述，故字段保留率不是事实正确率或业务可用率。时延只统计成功任务，P50与P95采用最近秩法；30项时P95为第29个顺序统计量。单次运行不足以评价生成稳定性或生产负载表现。</p>
<p>文案、排版、脚本分别完成{c["complete"]}/30、{image["complete"]}/30、{script["complete"]}/30项任务。异常响应另使用5种不同错误输入，而非将同一错误重复计为30种用例；其中{err["controlled_4xx"]}/5返回规范4xx状态，{err["json_error_returned"]}/5返回JSON错误。无效图像返回状态为{next(row["status"] for row in errors if row["name"] == "invalid_image_render")}，应改进为明确的输入校验错误；本结果不证明具备异常恢复能力。完整任务包、人工业务验收及真实企业应用效果未纳入本轮。</p>'''

contents4 = f'''<p>使用上述30项任务开展三组受控对比：A组为既有文案创作节点；B组加入本地营销案例检索；C组在B组基础上加入现有审核，最多进行3轮生成与审核。三组使用相同任务资料、平台要求和生成参数；B、C组使用相同的预先固定召回结果。三组共生成90份最终文案，按同一口径计算字段保留、指定风险短语命中、时延与Token开销，结果见表4。</p>
<h3>表4 现有文案模块受控对比结果（每组30项任务）</h3>{table4}
<p class="footnote">注：平均Token为接口报告的输入与输出Token总和除以30，包含该组的生成、重写和模型审核调用；不等于人民币费用。指定风险短语规则固定为“产地直发”“产地直供”“现采”及“抽……送”，按最终输出中至少命中一次的任务计数；这些履约或促销事实均未由任务提供。该指标仅为指定表达的风险筛查，不能替代逐条事实核验；未命中不代表没有事实风险。它与8项探索性测试使用同一筛查规则，未依据本轮结果增删词项。</p>
<p>A、B、C组三组技术完成分别为{a["complete"]}/30、{b["complete"]}/30、{c["complete"]}/30，指定字段保留分别为{a["covered_fields"]}/110、{b["covered_fields"]}/110、{c["covered_fields"]}/110；指定风险短语命中分别为{a["risk_tasks"]}/30、{b["risk_tasks"]}/30、{c["risk_tasks"]}/30。B组E06与C组E04未原样出现“红富士苹果”产品名称，构成两组各1个必查字段遗漏。C组{summary["audit"]["first_pass"]}/30项首轮通过审核，最终{summary["audit"]["final_pass"]}/30项通过；这说明审核通过状态不等于产品事实已核验：当前QA主要检查禁用表达、长度和文风，尚不具备完整证据比对能力。</p>
<p>与A组相比，C组P50由{a["p50"]:.3f}秒变为{c["p50"]:.3f}秒，约为{c["p50"]/a["p50"]:.2f}倍；平均Token由{decimal(a["mean_tokens"])}变为{decimal(c["mean_tokens"]) }，约为{c["mean_tokens"]/a["mean_tokens"]:.2f}倍。本轮只报告观测差异，不据单次合成任务结果宣称检索或多节点协作显著优于单节点。相同产品的三种资料情形存在关联，不能将90份输出当作90份独立产品样本；检索内容是营销案例而非经核验的产品事实库，因此也不构成产品知识RAG有效性的完整验证。</p>
<p>30项任务相较8项探索性测试扩大了品类和缺失信息覆盖，但仍是原型级评测。后续应引入取得授权的真实企业档案，按企业或产品系列划分独立测试任务，增加重复运行，并由独立审核人员盲评事实错误、编辑时间和业务可用性；完成共享简报与完整多物料链路后再进行相关消融。当前未测试的微调、多物料冲突率、生成式视频与LangChain/LangGraph迁移效果，不填写推测结果。</p>'''

env = load("environment.json")
total_calls = sum(summary[name]["calls"] for name in [*groups, "live_script"])
returned = sorted({model for name in [*groups, "live_script"] for model in summary[name]["model_returned"]})
examples = ''.join(f'<li>{html.escape(row["group"])}／{row["case_id"]}：{html.escape(row["hits"][0]["context"])}</li>' for row in flags[:6])
links = ''.join(f'<li><a href="paper_eval_30_20261019/{name}">{label}</a></li>' for name, label in [
    ("verified_summary.json", "离线复算汇总"), ("cases.json", "30份任务及条件"), ("text_results.json", "90份文案、审核和调用记录"),
    ("script_results.json", "30份脚本及调用记录"), ("image_results.json", "30次排版接口记录"), ("error_results.json", "5种异常记录"),
    ("risk_screening.json", "风险短语命中上下文"), ("environment.json", "环境、设计和源代码哈希"), ("run_expanded.py", "扩大评测运行脚本（付费）"),
    ("finalize_report.py", "离线复算脚本（不调用模型）")])
backup = BASE / "论文表3表4_8任务版.html"
if not backup.exists():
    backup.write_bytes(PAGE.read_bytes())
old = PAGE.read_text(encoding="utf-8")
style = old.split('<style>', 1)[1].split('</style>', 1)[0]
copy_script = old.split('<script>', 1)[1].split('</script>', 1)[0]
PAGE.write_text(f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>云稼集论文：表3与表4（30项实测）</title><style>{style}</style></head><body><main>
<h1>论文表3与表4：30项任务实测版</h1>
<p class="note">本页已更新为独立的30项合成任务评测，原8项探索性记录保留、不混入本轮。请将表格、表前后正文和注释一并复制；原Word未修改。实测是实际调用模型与接口，不代表资料来自真实企业，也不等于已完成业务验收。</p>
<p id="copy-status" role="status" aria-live="polite"></p>
<section><div class="toolbar"><h2>表3：功能与响应实测</h2><button type="button" data-copy="table3-content">复制表3及配套正文</button></div><div id="table3-content">{contents3}</div></section>
<section><div class="toolbar"><h2>表4：受控对比实测</h2><button type="button" data-copy="table4-content">复制表4及配套正文</button></div><div id="table4-content">{contents4}</div></section>
<aside class="editorial"><h2>实验条件与证据（核对用）</h2>
<p>环境：{html.escape(env["os"])}；Python {env["python"]}；OpenAI兼容客户端{env["openai_sdk"]}。请求模型名{html.escape(env["model"])}，保存的响应模型名为{html.escape('、'.join(returned))}。文案温度0.75、max_tokens=800；模型文风审核温度0.2、max_tokens=100；脚本温度0.75、max_tokens=2000。SDK重试关闭，单次模型超时60秒；本轮共{total_calls}次模型请求，另有30次本地排版调用与5种异常请求。实际费用缺少统一账单依据，不估算人民币数值。</p>
<p>本轮30项×3组文案＋30项脚本，每项每组运行1次。文案检索结果预先固定，耗时不含检索初始化与召回；脚本计时不含外部HTTP传输。未启动完整Orchestrator，不调用用户档案写入或历史保存，未修改生产代码。图片仅是合成底图上的产品文字排版，不是生成30张真实商品图片。不同资料条件涉及同一产品原型，不能推断企业总体表现。</p>
<p>以下为固定短语筛查截取的待核实输出，并非独立人工标注：</p><ul>{examples}</ul>
<details><summary>查看本轮原始记录与复算文件</summary><ul>{links}</ul></details>
<p><a href="paper_eval_30_20261019/论文表3表4_8任务版.html">查看保留的8项探索性测试页面</a></p>
</aside></main><script>{copy_script}</script></body></html>''', encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("Updated the existing HTML using the saved 30-task batch; no new model calls.")
