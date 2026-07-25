# agents.py - LangGraph 多 Agent 工作流
"""
6 个节点函数 + LangGraph StateGraph 构建
逻辑与旧 ai_service.py 中的 Agent/Orchestrator 完全一致
"""
import json
import requests as http_req
from datetime import datetime
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage

import config
from state import WorkflowState, MAX_QA_ROUNDS, OFF_TOPIC_WORDS
from prompts import (
    TRAIT_EXTRACTION_PROMPT, COPYWRITER_PROMPT,
    QA_STYLE_CHECK_PROMPT, TAG_SELECTION_PROMPT,
)

# ─── 全局 workflow_store（兼容前端轮询）───
workflow_store: Dict[str, dict] = {}


def _log(workflow_id: str, agent_name: str, msg: str, status: str = "running"):
    """写日志到 workflow_store（与原 _push_to_store 一致）"""
    if workflow_id not in workflow_store:
        workflow_store[workflow_id] = {"agents": {}}
    if agent_name not in workflow_store[workflow_id]["agents"]:
        workflow_store[workflow_id]["agents"][agent_name] = {"logs": [], "status": "idle"}
    entry = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg}
    wf_agent = workflow_store[workflow_id]["agents"][agent_name]
    wf_agent["status"] = status
    wf_agent["logs"].append(entry)
    wf_agent["logs"] = wf_agent["logs"][-5:]  # 只保留最近5条
    print(f" [{agent_name}] {msg}")


# ═══════════════════════════════════════════════════════════
#  节点 1：profile_node（用户档案 + 特征提取）
# ═══════════════════════════════════════════════════════════
def profile_node(state: WorkflowState) -> dict:
    wid = state.get("workflow_id", "")
    _log(wid, "ProfileAgent", "读取用户档案…")

    user_id = state.get("user_id", "default_user")
    user_input = state.get("user_input", "")
    profile = {}

    # 1. 从 main API 获取用户档案
    try:
        res = http_req.get(f"{config.MAIN_API}/api/user/{user_id}/profile", timeout=5)
        if res.status_code == 200:
            profile = res.json()
            _log(wid, "ProfileAgent", f"档案加载成功：{profile.get('username', '用户')}")
    except Exception as e:
        _log(wid, "ProfileAgent", f"档案服务未响应，使用空档案（{e}）")

    primary = profile.get("primary_product") or {}
    product_name = primary.get("name") or ""
    origin = primary.get("origin", "")

    # 2. 汇总已知特征
    trait_values = list({
        t["trait_value"]
        for t in profile.get("traits", [])
        if not t.get("product_name") or t.get("product_name") == product_name
    })
    for kw in primary.get("keywords", []):
        if kw not in trait_values:
            trait_values.append(kw)
    if primary.get("description"):
        trait_values.append(primary["description"])

    _log(wid, "ProfileAgent", f"已知特征：{len(trait_values)} 条")

    # 3. 从输入中提取新特征
    new_traits = []
    if user_input and len(user_input) > 3:
        new_traits = _extract_traits(user_input, product_name or "农产品")
        for t in new_traits:
            val = t.get("value", "")
            if val and val not in trait_values:
                trait_values.append(val)
                _save_trait(user_id, product_name, t.get("type", "other"), val)
                _log(wid, "ProfileAgent", f"新特征学习：{t['type']}={val}")

    # 4. 向量记忆检索
    extra_info = []
    try:
        from vector_memory_v2 import get_vector_memory
        vm = get_vector_memory()
        uid_int = int(user_id) if str(user_id).isdigit() else 0
        supplemental = state.get("supplemental_info", "")
        query = f"{product_name} {supplemental or user_input}"
        extra_info = vm.search_relevant(user_id=uid_int, query=query, top_k=6)
        if extra_info:
            _log(wid, "ProfileAgent", f"向量记忆召回 {len(extra_info)} 条")
    except Exception as e:
        _log(wid, "ProfileAgent", f"向量检索跳过：{e}")

    _log(wid, "ProfileAgent", "档案读取完成", "done")
    return {
        "product_name": product_name or user_input or "农产品",
        "region_raw": profile.get("region", ""),
        "origin": origin,
        "traits": trait_values,
        "company": profile.get("company_name", ""),
        "user_type": profile.get("user_type", "individual"),
        "extra_info": extra_info,
        "category": primary.get("category", ""),
    }


def _extract_traits(text: str, product: str) -> list:
    try:
        llm = config.get_llm(temperature=0.1, max_tokens=300)
        messages = TRAIT_EXTRACTION_PROMPT.format_messages(
            user_input=text, product_name=product
        )
        resp = llm.invoke(messages)
        raw = resp.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw).get("traits", [])
    except Exception:
        return []


def _save_trait(user_id, product_name, trait_type, trait_value):
    try:
        http_req.post(f"{config.MAIN_API}/api/user/trait", json={
            "user_id": user_id, "product_name": product_name,
            "trait_type": trait_type, "trait_value": trait_value,
            "source": "conversation"
        }, timeout=3)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
#  节点 2：region_node（地域文化风格分析）
# ═══════════════════════════════════════════════════════════
def region_node(state: WorkflowState) -> dict:
    wid = state.get("workflow_id", "")
    region_raw = state.get("region_raw", "")
    user_input = state.get("user_input", "")
    _log(wid, "RegionAgent", f"分析地域：{region_raw or '未填写'}")

    culture = _detect_culture(region_raw) or _detect_culture(user_input)
    style_guide = ""
    emotions = []
    keywords = []

    if culture:
        style_guide, emotions, keywords = _query_neo4j_style(culture, wid)

    if not style_guide:
        style_guide = config.REGION_STYLES.get(culture, "真诚接地气，突出产品天然品质")

    _log(wid, "RegionAgent", f"识别文化圈：{culture or '未知'}", "done")
    return {
        "culture": culture or "通用",
        "style_guide": style_guide,
        "emotions": emotions,
        "region_keywords": keywords,
    }


def _detect_culture(text: str) -> str:
    if not text:
        return ""
    for kw, culture in config.REGION_MAP.items():
        if kw in text:
            return culture
    return ""


def _query_neo4j_style(region_name: str, wid: str):
    try:
        driver = config.get_neo4j_driver()
        with driver.session() as sess:
            rec = sess.run("""
                MATCH (r:Region {name: $name})
                OPTIONAL MATCH (r)-[:HAS_KEYWORD]->(t:CultureTag)
                RETURN r.style_guide as style,
                       r.emotions as emotions,
                       collect(t.name) as keywords
            """, name=region_name).single()
            if rec:
                emotions = rec.get("emotions", "")
                emo_list = emotions.split(",") if emotions else []
                return rec.get("style", ""), emo_list, rec.get("keywords", [])
    except Exception as e:
        _log(wid, "RegionAgent", f"Neo4j查询失败：{e}")
    return "", [], []


# ═══════════════════════════════════════════════════════════
#  节点 3：tagpool_node（标签库 + 禁用词加载）
# ═══════════════════════════════════════════════════════════
def tagpool_node(state: WorkflowState) -> dict:
    wid = state.get("workflow_id", "")
    platform = state.get("platform", "小红书")
    culture = state.get("culture", "")
    category = state.get("category", "")
    _log(wid, "TagPoolAgent", f"加载标签池：{platform} / {culture} / {category}")

    forbidden = _load_forbidden_words(wid)
    _log(wid, "TagPoolAgent", f"禁用词：{len(forbidden)} 个")

    tags_data = _load_tags(platform, culture, category, wid)
    total = sum(len(cat.get("tags", [])) for cat in tags_data.get("platform_tags", []))
    _log(wid, "TagPoolAgent", f"平台标签：{total} 个", "done")

    return {
        "forbidden_words": forbidden,
        "platform_tags": tags_data.get("platform_tags", []),
        "region_keywords": tags_data.get("region_info", {}).get("keywords", []) if tags_data.get("region_info") else [],
        "culture_tags": tags_data.get("culture_tags", []),
        "product_attributes": tags_data.get("product_attributes", []),
    }


def _load_forbidden_words(wid: str) -> list:
    try:
        driver = config.get_neo4j_driver()
        with driver.session() as sess:
            rec = sess.run("MATCH (fw:ForbiddenWord) RETURN collect(fw.word) as words").single()
            return [w for w in (rec["words"] if rec else []) if w]
    except Exception as e:
        _log(wid, "TagPoolAgent", f"禁用词加载失败：{e}")
        return []


def _load_tags(platform, region, category, wid) -> dict:
    try:
        res = http_req.get(f"{config.TAG_API}/api/tags/all",
                           params={"platform": platform, "region": region, "product_category": category},
                           timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        _log(wid, "TagPoolAgent", f"标签服务未响应：{e}")
    return {}


# ═══════════════════════════════════════════════════════════
#  节点 4：copywriter_node（文案创作）
# ═══════════════════════════════════════════════════════════
def copywriter_node(state: WorkflowState) -> dict:
    wid = state.get("workflow_id", "")
    _log(wid, "CopywriterAgent", "开始创作文案…")

    product_name = state.get("product_name", "农产品")
    traits = state.get("traits", [])
    culture = state.get("culture", "通用")
    style_guide = state.get("style_guide", "真诚接地气")
    platform = state.get("platform", "小红书")
    origin = state.get("origin", "")
    qa_feedback = state.get("qa_feedback", "")
    target_user = state.get("target_user", "")
    word_count_target = state.get("word_count_target", 120)

    platform_hint = config.PLATFORM_HINTS.get(platform, config.PLATFORM_HINTS["小红书"])
    traits_str = "、".join(traits[:8]) if traits else "优质天然"

    product_hint = ""
    if product_name in ("农产品", "", None):
        product_hint = "（根据产品特点推断具体品类，写出有针对性的内容）"

    # 构建各可选段落
    festival_hint = state.get("festival_hint", "")
    festival_section = f"\n节日氛围：{festival_hint}（文案要体现节日特色）" if festival_hint else ""

    target_user_section = f"\n目标受众：{target_user}（语气和内容针对该群体）" if target_user else ""

    user_input = state.get("user_input", "")
    user_input_section = ""
    if user_input and user_input != product_name:
        user_input_section = f"\n用户补充要求：{user_input}"

    extra_info = state.get("extra_info", [])
    extra_info_section = ""
    if extra_info:
        extra_lines = "\n".join([f"• {item}" for item in extra_info])
        extra_info_section = (
            f"\n\n════ 【用户真实背景信息·必须融入文案】 ════\n{extra_lines}\n"
            "⚠️ 以上是用户提供的真实卖点，获奖/认证/年限/古法工艺等亮点必须明确写进文案。"
        )

    template = state.get("template", "")
    template_section = ""
    if template:
        template_section = (
            f"\n\n════ 参考模板风格 ════\n"
            "请严格参考以下模板的结构、节奏和语气来创作（内容替换为本产品，不要复制原文）：\n"
            f"{template}"
        )

    supplemental_info = state.get("supplemental_info", "")
    supplemental_section = ""
    if supplemental_info and supplemental_info != state.get("user_input", ""):
        supplemental_section = f"\n用户补充说明（请体现在文案中）：{supplemental_info}"

    # 用 ChatPromptTemplate 构建消息
    messages = COPYWRITER_PROMPT.format_messages(
        culture=culture,
        product_name=product_name,
        platform=platform,
        platform_hint=platform_hint,
        product_hint=product_hint,
        traits_str=traits_str,
        origin=origin,
        style_guide=style_guide,
        festival_section=festival_section,
        target_user_section=target_user_section,
        user_input_section=user_input_section,
        extra_info_section=extra_info_section,
        template_section=template_section,
        supplemental_section=supplemental_section,
    )

    # 如果有 QA 反馈，追加到消息中
    if qa_feedback:
        messages.append(HumanMessage(
            content=f"⚠️ 上一版文案存在以下问题，请根据反馈重新创作：\n{qa_feedback}\n"
                    f"上一版文案（供参考，请修正上述问题后重新输出）：\n{state.get('content_draft', '')}"
        ))

    max_tok = max(800, int(word_count_target * 2.5))
    llm = config.get_llm(temperature=0.75, max_tokens=max_tok)
    resp = llm.invoke(messages)
    content = resp.content.strip()

    _log(wid, "CopywriterAgent", f"文案生成完毕（{len(content)}字）", "done")
    return {"content": content, "content_draft": content}


# ═══════════════════════════════════════════════════════════
#  节点 5：qa_node（质检）
# ═══════════════════════════════════════════════════════════
def qa_node(state: WorkflowState) -> dict:
    wid = state.get("workflow_id", "")
    round_num = state.get("qa_rounds", 0) + 1
    agent_name = f"QAAgent_round{round_num}"
    _log(wid, agent_name, "质检开始…")

    content = state.get("content", "")
    forbidden = state.get("forbidden_words", [])
    platform = state.get("platform", "小红书")
    culture = state.get("culture", "通用")
    target_user = state.get("target_user", "")
    product_name = state.get("product_name", "农产品")
    word_count_target = state.get("word_count_target", 120)
    issues = []

    # 检查 0：跑题检测
    found_off = [w for w in OFF_TOPIC_WORDS if w in content]
    if found_off:
        issues.append(f"文案跑题，出现了与产品无关的内容「{'、'.join(found_off)}」，"
                      f"必须重写：文案应该宣传【{product_name}】本身，不能介绍任何工具或网站")
        _log(wid, agent_name, f"跑题：{found_off}")
    else:
        _log(wid, agent_name, "内容聚焦于产品本身")

    # 检查 1：禁用词
    found = [w for w in forbidden if w and w in content]
    if found:
        issues.append(f"包含禁用词「{'、'.join(found)}」，必须替换")
        _log(wid, agent_name, f"禁用词：{found}")
    else:
        _log(wid, agent_name, "无禁用词")

    # 检查 2：字数
    char_count = len(content.replace(" ", "").replace("\n", ""))
    low, high = max(40, int(word_count_target * 0.6)), int(word_count_target * 1.5)
    if char_count < low:
        issues.append(f"字数过少（{char_count}字），要求约{word_count_target}字")
        _log(wid, agent_name, f"字数不足：{char_count}（目标{word_count_target}）")
    elif char_count > high:
        issues.append(f"字数过多（{char_count}字），要求约{word_count_target}字")
        _log(wid, agent_name, f"字数超限：{char_count}（目标{word_count_target}）")
    else:
        _log(wid, agent_name, f"字数合格：{char_count}字（目标{word_count_target}）")

    # 检查 3：AI 风格评判（仅当前面都通过时）
    if not issues:
        style_ok, style_comment = _check_style(content, platform, culture, target_user)
        if not style_ok:
            issues.append(style_comment)
            _log(wid, agent_name, f"文风问题：{style_comment}")
        else:
            _log(wid, agent_name, f"文风合格：{style_comment}")

    passed = len(issues) == 0
    feedback = "；".join(issues) if issues else ""
    _log(wid, agent_name, "质检通过" if passed else f"质检不通过，打回重写：{feedback}", "done")
    return {"qa_passed": passed, "qa_feedback": feedback, "qa_rounds": round_num}


def _check_style(content, platform, culture, target_user):
    prompt = f"""请评判以下农产品文案是否符合要求：
文案：{content}
要求：
- 平台：{platform}（符合该平台用户阅读习惯）
- 地域文化：{culture}
- 目标受众：{target_user or '大众'}
只回答：PASS 或 FAIL: <具体问题>
（如：FAIL: 语气太正式，不符合小红书年轻用户风格）"""
    try:
        llm = config.get_llm(temperature=0.2, max_tokens=100)
        messages = QA_STYLE_CHECK_PROMPT.format_messages(
            content=content, platform=platform, culture=culture, target_user=target_user or "大众"
        )
        result = llm.invoke(messages)
        result_text = result.content.strip()
        if result_text.startswith("PASS"):
            return True, "语气与平台风格匹配"
        return False, result_text.replace("FAIL:", "").strip()
    except Exception:
        return True, "跳过风格检查"


# ═══════════════════════════════════════════════════════════
#  节点 6：tag_selector_node（标签精选）
# ═══════════════════════════════════════════════════════════
def tag_selector_node(state: WorkflowState) -> dict:
    wid = state.get("workflow_id", "")
    _log(wid, "TagSelectorAgent", "从 Neo4j 标签库精选推荐标签…")

    content = state.get("content", "")
    product_name = state.get("product_name", "农产品")
    platform = state.get("platform", "小红书")
    culture = state.get("culture", "")

    # 汇总候选标签
    candidates = []
    for cat in state.get("platform_tags", []):
        candidates.extend(cat.get("tags", []))
    candidates.extend(state.get("region_keywords", []))
    candidates.extend(state.get("product_attributes", []))
    for cat in state.get("culture_tags", []):
        candidates.extend(cat.get("tags", []))
    candidates = list(set(candidates))[:60]

    if not candidates:
        _log(wid, "TagSelectorAgent", "标签库为空，跳过推荐", "done")
        return {"recommended_tags": []}

    try:
        messages = TAG_SELECTION_PROMPT.format_messages(
            platform=platform, content=content, culture=culture,
            candidates="\n".join(candidates),
        )
        llm = config.get_llm(temperature=0.3, max_tokens=200)
        resp = llm.invoke(messages)
        raw = resp.content.strip()
        tags = [t.strip() for t in raw.replace("，", ",").split(",") if t.strip()][:10]
        _log(wid, "TagSelectorAgent", f"推荐标签：{len(tags)} 个", "done")
        return {"recommended_tags": tags}
    except Exception as e:
        _log(wid, "TagSelectorAgent", f"标签选择失败：{e}", "done")
        return {"recommended_tags": []}


# ═══════════════════════════════════════════════════════════
#  Phase 1 并行汇聚节点
# ═══════════════════════════════════════════════════════════
def collectors_node(state: WorkflowState) -> dict:
    """并行执行 profile + region + tagpool 三个节点，合并结果"""
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(profile_node, state): "profile",
            pool.submit(region_node, state): "region",
            pool.submit(tagpool_node, state): "tagpool",
        }
        for future in as_completed(futures):
            try:
                results.update(future.result())
            except Exception as e:
                name = futures[future]
                print(f" [collectors] {name} 执行失败: {e}")
    return results


# ═══════════════════════════════════════════════════════════
#  QA 路由函数
# ═══════════════════════════════════════════════════════════
def route_after_qa(state: WorkflowState) -> str:
    """判断 QA 后走哪条路"""
    if state.get("qa_passed", False):
        return "tag_selector_node"
    if state.get("qa_rounds", 0) >= MAX_QA_ROUNDS:
        return "tag_selector_node"  # 兜底：达到最大轮次，强制通过
    return "copywriter_node"  # 打回重写


# ═══════════════════════════════════════════════════════════
#  StateGraph 构建
# ═══════════════════════════════════════════════════════════
def build_workflow() -> StateGraph:
    """构建并返回编译好的 LangGraph 工作流"""
    workflow = StateGraph(WorkflowState)

    # 添加节点
    workflow.add_node("collectors_node", collectors_node)
    workflow.add_node("copywriter_node", copywriter_node)
    workflow.add_node("qa_node", qa_node)
    workflow.add_node("tag_selector_node", tag_selector_node)

    # 边
    workflow.set_entry_point("collectors_node")
    workflow.add_edge("collectors_node", "copywriter_node")
    workflow.add_edge("copywriter_node", "qa_node")

    # QA 条件路由
    workflow.add_conditional_edges(
        "qa_node",
        route_after_qa,
        {
            "copywriter_node": "copywriter_node",
            "tag_selector_node": "tag_selector_node",
        }
    )

    workflow.add_edge("tag_selector_node", END)

    return workflow.compile()


# ═══════════════════════════════════════════════════════════
#  单例
# ═══════════════════════════════════════════════════════════
_workflow_app = None


def get_workflow_app():
    global _workflow_app
    if _workflow_app is None:
        _workflow_app = build_workflow()
        print("[agents] LangGraph 工作流已编译")
    return _workflow_app
