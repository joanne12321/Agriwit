"""Recompute paper tables from saved records, without any new model requests."""
from pathlib import Path
import hashlib
import html
import json
import math
import re
import statistics
from decimal import Decimal, ROUND_HALF_UP

BASE = Path(__file__).resolve().parent
PAGE = BASE.parent / "论文表3表4_替换稿.html"

def load(name):
    return json.loads((BASE / name).read_text(encoding="utf-8"))

def quantile(values, p):
    return sorted(values)[math.ceil(len(values) * p) - 1]

# Screening is deliberately narrow and disclosed; a hit is not a claim-level verdict.
RISK = re.compile(r"产地直发|产地直供|现采|抽[^。！!？?\n]{0,40}送")
texts = load("text_results.json")
scripts = load("script_results.json")
images = load("image_results.json")
errors = load("error_results.json")
cases = load("cases.json")["cases"]
assert len(texts) == 24 and len(scripts) == len(images) == len(cases) == 8
assert len({(r["case_id"], r["variant"]) for r in texts}) == 24
groups = {name: [r for r in texts if r["variant"] == name] for name in ["writer_only", "writer_rag", "writer_rag_qa"]}
summary = {}
flags = []
for name, rows in {**groups, "live_script": scripts, "poster_text_render": images}.items():
    for row in rows:
        if row.get("text"):
            hits = [{"phrase": m.group(), "context": row["text"][max(0, m.start()-20):m.end()+20]} for m in RISK.finditer(row["text"])]
            if hits:
                flags.append({"group": name, "case_id": row["case_id"], "hits": hits})
    times = [r["seconds"] for r in rows if r["ok"]]
    calls = [c for r in rows for c in r.get("calls", [])]
    assert all(c["ok"] and c["finish_reason"] == "stop" for c in calls)
    checks = [r["field_check"] for r in rows if "field_check" in r]
    summary[name] = {
        "n": len(rows), "complete": sum(r["ok"] for r in rows),
        "p50": quantile(times, .5), "p95": quantile(times, .95),
        "field_pass": sum(c["strict_field_pass"] for c in checks),
        "covered_fields": sum(c["covered"] for c in checks), "total_fields": sum(c["total"] for c in checks),
        "risk_tasks": sum(bool(RISK.search(r.get("text", ""))) for r in rows),
        "calls": len(calls), "total_tokens": sum(c["usage"]["total_tokens"] for c in calls),
        "mean_tokens": statistics.mean([sum(c["usage"]["total_tokens"] for c in r.get("calls", [])) for r in rows]),
        "model_returned": sorted({c["model_returned"] for c in calls}),
    }
qa = groups["writer_rag_qa"]
summary["audit"] = {"first_pass": sum(r["drafts"][0]["qa"]["passed"] for r in qa),
                     "final_pass": sum(r["final_qa_pass"] for r in qa),
                     "rounds": {r["case_id"]: len(r["drafts"]) for r in qa}}
summary["errors"] = {"responses": len(errors), "json_error_returned": sum(r["contract_pass"] for r in errors),
                     "controlled_4xx": sum(r["contract_pass"] and 400 <= r["status"] < 500 for r in errors),
                     "p50": quantile([r["seconds"] for r in errors], .5), "p95": quantile([r["seconds"] for r in errors], .95)}
summary["risk_rule"] = RISK.pattern
(BASE / "verified_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
(BASE / "risk_screening.json").write_text(json.dumps(flags, ensure_ascii=False, indent=2), encoding="utf-8")

def duration(s):
    return f'{s["p50"]:.3f} / {s["p95"]:.3f}'

def mean_tokens(value):
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def table(headers, rows, widths):
    cols = ''.join(f'<col style="width:{w}%">' for w in widths)
    head = ''.join(f'<th scope="col">{html.escape(h)}</th>' for h in headers)
    body = ''.join('<tr>' + ''.join(f'<td>{html.escape(str(c))}</td>' for c in row) + '</tr>' for row in rows)
    return f'<div class="table-scroll"><table><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'

copy = summary["writer_rag_qa"]
script = summary["live_script"]
image = summary["poster_text_render"]
err = summary["errors"]
table3 = table(
    ["测试任务与范围", "样本数", "P50 / P95（秒）", "技术完成／规范响应", "字段保留／验收情况"],
    [
        ["文案生成：既有创作节点＋案例检索＋审核", "8", duration(copy), "8/8（100%）", "指定字段30/30；人工业务验收未开展"],
        ["海报文字排版：本地HTTP接口、合成测试底图", "8", duration(image), "8/8（100%）", "8张均可解码且为1080×1080；未做OCR与产品真实性验收"],
        ["直播脚本：现有接口函数、真实模型调用", "8", duration(script), "8/8（100%）；模板降级0次", "指定字段30/30；真实口播时长未核验"],
        ["完整任务包：从资料到多物料交付", "未测", "不适用", "未测", "未开展端到端验收，不由单模块结果推算"],
        ["异常响应：缺参、未知任务、无效图像", "5个用例", duration(err), "规范4xx：4/5（80%）", "5/5返回JSON错误；1项返回500，尚不规范；未测试断点恢复"],
    ], [27, 8, 16, 22, 27])

labels = {"writer_only": "A：既有创作节点", "writer_rag": "B：A＋案例检索", "writer_rag_qa": "C：B＋现有审核（最多3轮）"}
rows4 = []
for name, label in labels.items():
    s = summary[name]
    rows4.append([label, "8", f'{s["covered_fields"]}/{s["total_fields"]}（100%）',
                  f'{s["risk_tasks"]}/8（{s["risk_tasks"] / 8 * 100:g}%）', duration(s), str(s["calls"]),
                  mean_tokens(s["mean_tokens"])])
table4 = table(["受控对比配置", "样本数", "指定字段保留率", "指定风险短语命中任务率", "P50 / P95（秒）", "模型调用总次数", "平均Token／任务"], rows4, [22, 7, 15, 16, 17, 11, 12])

contents3 = f'''<p>为获得可复核的原型运行记录，本研究于2026年10月19日开展小样本模块测试。测试采用8份合成产品档案，覆盖熟制板栗、生板栗、苹果、绿茶、鲜香菇、红薯干、大米及鲜玉米，包含已知价格与价格缺失情形。档案中的产地、规格及价格仅为测试设定，不对应真实企业产品。各任务顺序执行、每个配置每项任务运行1次，结果见表3。</p>
<h3>表3 原型模块功能与响应测试结果（小样本）</h3>{table3}
<p class="footnote">注：本次不是完整系统负载测试。文案通过直接调用现有CopywriterAgent、DatasetRetriever及QAAgent测试；直播脚本通过Flask测试客户端调用现有路由函数，两者均使用真实模型。海报仅测试运行中服务的文字渲染HTTP接口，不包含生成式背景、抠图及产品实拍。各行计时边界不同，不宜横向比较快慢。技术完成不等于业务可用。</p>
<p>文案与脚本的技术完成定义为模型调用成功且返回非空结果，模板降级不计入正常完成；文字排版的技术完成定义为HTTP调用成功、返回图像可解码且尺寸符合设定。指定字段仅检查产品名、产地、净含量及已提供价格的原样保留情况；8份档案共30个必查字段，价格未确认的2项不要求补全。字段保留不核验其他新增陈述，也不能等同事实正确率。P50与P95采用最近秩法计算，样本数为8时P95即最大观测值，不代表稳定的生产环境尾时延。</p>
<p>本轮8次文案、8次脚本和8次排版均完成规定输出。5个异常用例均返回JSON错误信息，其中缺少图片、缺少底图、未知图像任务及未知工作流4项返回预期的400或404；无效Base64图像返回500，因此规范错误响应率为80%，不能据此宣称已实现异常恢复。尚未开展经营者盲评、OCR核验及完整任务包测试，原表中的业务可用率暂不报告，也不以自动字段检查代替人工业务验收。</p>'''

ratio_time = copy["p50"] / summary["writer_only"]["p50"]
ratio_tokens = copy["mean_tokens"] / summary["writer_only"]["mean_tokens"]
contents4 = f'''<p>为初步观察案例检索和现有审核带来的质量与开销变化，使用同一组8份合成产品档案开展三组受控对比。A组调用既有创作节点；B组在A组基础上加入本地案例检索；C组在B组基础上加入现有QA节点，最多执行3轮生成与审核。三组的基础产品资料、平台要求和生成温度一致；B、C组使用相同的检索结果。实验按固定随机顺序执行，结果见表4。</p>
<h3>表4 现有文案模块受控对比结果（小样本）</h3>{table4}
<p class="footnote">注：平均Token为接口报告的输入与输出Token之和，累计该任务的全部生成、重写与模型审核调用；不是人民币费用。无统一账单价格依据，故不估算费用。指定风险短语命中任务率采用固定规则扫描“产地直发”“产地直供”“现采”及“抽……送”表达，分母为每组8项任务；这些履约或促销信息均未包含在合成档案中。命中为待核实线索，不是逐条事实错误率；未命中也不表示没有其他事实风险。</p>
<p>三组技术完成率均为8/8，指定字段均保留30/30，但这一结果只说明给定字段未被遗漏，不能证明文案不存在编造。A、B、C组分别有0、1、3项任务命中上述指定风险短语。C组中7项首轮通过现有审核，另1项运行至第3轮后通过；尽管最终8项均通过，仍有3项新增了档案未提供的产地直发或直供表述，说明现有审核不能替代基于证据的事实核验。另有熟制板栗文案新增“不用剥壳”等未经提供的包装或加工细节，亦应列为后续事实审核重点。</p>
<p>与A组相比，C组P50由1.508秒增加至2.796秒，约为{ratio_time:.2f}倍；平均Token由{mean_tokens(summary["writer_only"]["mean_tokens"])}增加至{mean_tokens(copy["mean_tokens"]) }，约为{ratio_tokens:.2f}倍。本轮未观察到指定字段保留率的进一步改善，不能据此宣称检索或多节点协作显著优于单节点。样本量仅8项、每项仅运行1次，也不足以检验统计显著性。当前检索内容为营销案例而非经过授权核验的产品事实库，本实验不构成产品知识RAG有效性的完整验证。</p>
<p>原计划中的完整多Agent架构、去除共享语义简报、跨物料冲突率及领域微调对比，因相关模块尚未形成可独立评估的完整链路，未纳入本轮结果。后续应完成框架与证据链联调，在独立企业或产品系列上扩展样本，增加重复运行和人工盲评，再报告逐条事实错误率、跨物料冲突率、业务可用率与实际账单费用。</p>'''

backup = BASE / "论文表3表4_原说明版.html"
if not backup.exists():
    backup.write_bytes(PAGE.read_bytes())
old = PAGE.read_text(encoding="utf-8")
style = old.split('<style>', 1)[1].split('</style>', 1)[0]
script_copy = old.split('<script>', 1)[1].split('</script>', 1)[0]
env = load("environment.json")
source_links = ''.join(f'<li><a href="paper_eval_20261019/{name}">{label}</a></li>' for name, label in [
    ("verified_summary.json", "离线复算汇总"), ("cases.json", "8份合成产品档案"),
    ("text_results.json", "24份文案、审核轮次与逐调用记录"), ("script_results.json", "8份脚本与逐调用记录"),
    ("image_results.json", "排版接口记录"), ("error_results.json", "异常响应记录"),
    ("risk_screening.json", "指定风险短语命中及上下文"), ("environment.json", "环境与代码哈希"),
    ("run_eval.py", "原始测试脚本（运行会调用付费模型）"), ("finalize_report.py", "离线复算与生成脚本（不调用模型）")])
page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>云稼集论文：表3与表4实测版</title><style>{style}</style></head>
<body><main><h1>论文表3与表4：真实小样本实测版</h1>
<p class="note">已由说明表改为实测结果表。数据来自2026年10月19日保存的真实调用记录，不是模拟成功率。请将表格与表前后文字、注释一并替换；原始Word未改动。当前证据只支持模块级小样本结论，不支持完整系统或业务验收结论。</p>
<p id="copy-status" role="status" aria-live="polite"></p>
<section><div class="toolbar"><h2>表3：功能与响应实测</h2><button type="button" data-copy="table3-content">复制表3及配套正文</button></div><div id="table3-content">{contents3}</div></section>
<section><div class="toolbar"><h2>表4：受控对比实测</h2><button type="button" data-copy="table4-content">复制表4及配套正文</button></div><div id="table4-content">{contents4}</div></section>
<aside class="editorial"><h2>实验条件与证据（核对用）</h2>
<p>环境：{html.escape(env['os'])}；Python {env['python']}；OpenAI兼容客户端{env['openai_sdk']}。请求模型名deepseek-chat，所有保存的模型响应名均为deepseek-flash，论文中应同时说明两者，不据别名推断其他版本。文案温度0.75、max_tokens=800；模型文风审核温度0.2、max_tokens=100；直播脚本温度0.75、max_tokens=2000；SDK自动重试关闭，单次调用超时60秒。共44次计入文案与脚本的成功模型请求，另有一次最小连通性检查，不计入表格。</p>
<p>本轮按8份档案×3组文案配置＋8份脚本执行；4种生鲜或需加工产品明确写明需加热。8次排版使用相同1080×1080合成图，逐次替换产品字段，不代表8张真实产品照片。没有启动完整Orchestrator、用户档案写入或历史保存，未修改生产代码。受控对比不包含档案读取、标签推荐、数据库持久化或线上HTTP传输等开销；文案检索结果预先固定，表中耗时不计检索索引初始化与召回耗时。</p>
<p>发现的具体风险：C01直播脚本新增“抽一位家人送一袋”，C04新增“抽一位宝子送小礼物”，C06新增抽赠承诺，均不在测试档案中；C01的C组文案新增“不用剥壳”。这些示例说明字段全部保留也不等于可直接发布。本次不是两名人工审核员的独立标注，不报告人工业务可用率。</p>
<p>原表的研究方向可以保留，但当前无法实测的行不能填预期数值冒充结果。后续完善后再扩展“完整方案、去共享简报、去审核、微调”等组；LangChain/LangGraph迁移未包含在本轮测试中。</p>
<details><summary>查看原始记录与复算文件</summary><ul>{source_links}</ul></details>
</aside></main><script>{script_copy}</script></body></html>'''
PAGE.write_text(page, encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("Updated paper HTML from saved records; no new model calls.")
