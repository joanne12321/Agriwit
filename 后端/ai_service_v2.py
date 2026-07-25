# ai_service_v2.py - LangChain/LangGraph 重构版
"""
与原 ai_service.py 的所有 7 个 API 端点兼容。
核心改动：自定义 BaseAgent/Orchestrator → LangGraph StateGraph
"""
import sys
import io
import json
import uuid
import re as _re
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

import config
from agents import get_workflow_app, workflow_store
from state import WorkflowState

# 兼容 Windows 控制台 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# DeepSeek 直调客户端（用于热点/直播等非工作流接口）
llm_client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

NEED_NEO4J = True
# ===== 映射表 =====
PLATFORM_MAP = {"xiaohongshu": "小红书", "douyin": "抖音", "taobao": "淘宝", "weibo": "微博", "toutiao": "头条"}

# ═══════════════════════════════════════════════════════
#  端点 1：主生成接口（LangGraph 工作流）
# ═══════════════════════════════════════════════════════
@app.route('/api/ai/generate', methods=['POST'])
def generate_content():
    data = request.json
    if isinstance(data.get("platform"), list):
        data["platform"] = data["platform"][0] if data["platform"] else "小红书"

    workflow_id = str(uuid.uuid4())
    user_id = str(data.get("user_id", "default_user"))
    platform = data.get("platform", "小红书")
    user_input = data.get("product_name", "").strip()
    supplemental_info = data.get("supplemental_info", "")
    template = data.get("template", "")

    # 提取字数要求
    word_match = _re.search(r"(\d+)\s*字", user_input or "")
    word_count_target = int(word_match.group(1)) if word_match else data.get("word_count_target", 120)
    word_count_hint = f"{word_count_target}字左右" if word_match else data.get("word_count_hint", "100～120字")

    # 初始化 workflow_store（兼容前端轮询）
    workflow_store[workflow_id] = {
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "agents": {}
    }

    # 构建初始状态
    initial_state: WorkflowState = {
        "user_id": user_id,
        "platform": platform,
        "user_input": user_input,
        "custom_tags": data.get("custom_tags", []),
        "festival_hint": data.get("festival_hint", ""),
        "target_user": data.get("target_user_hint", ""),
        "template": template,
        "supplemental_info": supplemental_info,
        "word_count_target": word_count_target,
        "word_count_hint": word_count_hint,
        "workflow_id": workflow_id,
        "product_name": "",
        "region_raw": "",
        "origin": "",
        "traits": [],
        "company": "",
        "user_type": "",
        "extra_info": [],
        "culture": "",
        "style_guide": "",
        "emotions": [],
        "region_keywords": [],
        "forbidden_words": [],
        "platform_tags": [],
        "culture_tags": [],
        "product_attributes": [],
        "category": "",
        "content": "",
        "content_draft": "",
        "qa_feedback": "",
        "qa_passed": False,
        "qa_rounds": 0,
        "recommended_tags": [],
        "agent_statuses": {},
    }

    try:
        print(f"\n{'='*60}")
        print(f" [LangGraph] 工作流启动 [{workflow_id[:8]}] user:{user_id} platform:{platform}")
        print(f"{'='*60}")

        graph = get_workflow_app()
        final_state = graph.invoke(initial_state)

        workflow_store[workflow_id]["status"] = "done"

        # 保存历史
        _save_history(
            user_id=user_id,
            product=final_state.get("product_name", ""),
            platform=platform,
            region=final_state.get("culture", ""),
            content=final_state.get("content", ""),
            tags=final_state.get("recommended_tags", []),
            workflow_id=workflow_id,
        )

        result = {
            "content": final_state.get("content", ""),
            "type": "content",
            "workflow_id": workflow_id,
            "session_id": workflow_id,
            "product_name": final_state.get("product_name", ""),
            "region": final_state.get("culture", ""),
            "recommended_tags": final_state.get("recommended_tags", []),
            "all_traits": final_state.get("traits", []),
            "qa_rounds": final_state.get("qa_rounds", 0),
            "agent_summary": {
                name: {"status": info["status"], "logs": info["logs"]}
                for name, info in workflow_store[workflow_id].get("agents", {}).items()
            }
        }

        print(f" [LangGraph] 工作流完成 [{workflow_id[:8]}] | "
              f"文案{len(result['content'])}字 | "
              f"标签{len(result['recommended_tags'])}个 | "
              f"QA轮次:{result['qa_rounds']}\n")
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        workflow_store[workflow_id]["status"] = "error"
        return jsonify({"error": str(e), "workflow_id": workflow_id}), 500


# ═══════════════════════════════════════════════════════
#  端点 2：文案修改（refine）
# ═══════════════════════════════════════════════════════
@app.route('/api/ai/refine', methods=['POST'])
def refine_content():
    data = request.json
    req_text = data.get("request", "")

    wm = _re.search(r"(\d+)\s*字", req_text)
    wc_target = int(wm.group(1)) if wm else data.get("word_count_target", 120)
    wc_hint = f"{wc_target}字左右" if wm else data.get("word_count_hint", "100～120字")

    # 加载禁用词
    forbidden = []
    try:
        driver = config.get_neo4j_driver()
        with driver.session() as sess:
            rec = sess.run("MATCH (fw:ForbiddenWord) RETURN collect(fw.word) as words").single()
            forbidden = [w for w in (rec["words"] if rec else []) if w]
    except Exception:
        pass

    platform = data.get("platform", "小红书")

    # 构建简化状态，跳过信息收集，直接走文案+质检
    wid = str(uuid.uuid4())
    workflow_store[wid] = {"status": "running", "started_at": datetime.now().isoformat(), "agents": {}}

    refine_state: WorkflowState = {
        "user_id": "refine",
        "platform": platform,
        "user_input": req_text,
        "product_name": data.get("product_name", "农产品"),
        "traits": [],
        "culture": "通用",
        "style_guide": "根据用户要求调整",
        "forbidden_words": forbidden,
        "custom_tags": [],
        "festival_hint": "",
        "target_user": "",
        "supplemental_info": "",
        "template": "",
        "extra_info": [],
        "word_count_hint": wc_hint,
        "word_count_target": wc_target,
        "qa_feedback": f"原文案：{data.get('original_content', '')}；修改要求：{req_text}",
        "qa_passed": False,
        "qa_rounds": 0,
        "content": "",
        "content_draft": "",
        "workflow_id": wid,
        "origin": "",
        "emotions": [],
        "platform_tags": [],
        "culture_tags": [],
        "product_attributes": [],
        "region_keywords": [],
        "recommended_tags": [],
        "agent_statuses": {},
        "region_raw": "",
        "company": "",
        "user_type": "",
        "category": "",
    }

    try:
        from agents import copywriter_node, qa_node

        # Round 1
        cw_result = copywriter_node(refine_state)
        refine_state.update(cw_result)
        qa_result = qa_node(refine_state)
        refine_state.update(qa_result)

        # Round 2（如果需要）
        if not refine_state.get("qa_passed", False):
            refine_state["qa_feedback"] = refine_state.get("qa_feedback", "")
            cw_result2 = copywriter_node(refine_state)
            refine_state.update(cw_result2)

        workflow_store[wid]["status"] = "done"
        return jsonify({"content": refine_state.get("content", ""), "type": "refined"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"content": "", "type": "refined", "error": str(e)}), 500


# ═══════════════════════════════════════════════════════
#  端点 3：工作流状态查询（前端轮询）
# ═══════════════════════════════════════════════════════
@app.route('/api/workflow/status/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    wf = workflow_store.get(workflow_id)
    if not wf:
        return jsonify({"error": "workflow not found"}), 404
    return jsonify(wf)


# ═══════════════════════════════════════════════════════
#  端点 4：热点推荐
# ═══════════════════════════════════════════════════════
@app.route('/api/hotspot', methods=['POST'])
def get_hotspot():
    data = request.json or {}
    product = data.get("product_name", "")
    platform = data.get("platform", "小红书")

    if product:
        prompt = f"""你是资深的农产品新媒体运营专家。
现在是2026年春季，请为销售【{product}】的农户生成{platform}平台上的热点内容方向。
输出JSON格式，包含：
- hotspots: 5条当前热门话题，每条包含 title(标题)、angle(内容角度)、heat(热度:高/中/低)
- tips: 3条针对{product}的运营小技巧
只输出JSON，不要任何解释：
{{
  "hotspots": [
    {{"title": "话题标题", "angle": "适合的内容角度", "heat": "高"}}
  ],
  "tips": ["技巧1", "技巧2", "技巧3"]
}}"""
    else:
        prompt = f"""你是资深的农产品新媒体运营专家。
请生成{platform}平台当前热门的农产品运营话题和技巧。
输出JSON格式：
{{
  "hotspots": [
    {{"title": "话题标题", "angle": "适合的内容角度", "heat": "高/中/低"}}
  ],
  "tips": ["运营技巧1", "运营技巧2", "运营技巧3"]
}}
要求：hotspots 5条，贴近当前时节和平台热点，tips 3条实用且针对新手农户。
只输出JSON："""

    try:
        resp = llm_client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=800
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return jsonify({"success": True, "product": product or "农产品通用", **result})
    except Exception:
        return jsonify({
            "success": True, "product": product or "农产品通用",
            "hotspots": [
                {"title": "产地直播带货新玩法", "angle": "展示真实采摘/生产过程", "heat": "高"},
                {"title": "农产品溯源故事", "angle": "讲述种植背后的人情味", "heat": "高"},
                {"title": "节气饮食搭配指南", "angle": "结合时令推荐食用方法", "heat": "中"},
                {"title": "乡村振兴好物推荐", "angle": "强调助农和地域文化", "heat": "中"},
                {"title": "原产地探店vlog", "angle": "带用户云逛农场", "heat": "中"},
            ],
            "tips": [
                "发布时间选早上7-9点或晚上8-10点，这两个时段用户活跃度最高",
                "图片首图用高饱和度的产品特写，点击率比风景图高40%",
                "评论区第一条自己置顶问题，引导互动可以显著提升推荐量"
            ]
        })


# ═══════════════════════════════════════════════════════
#  端点 5：历史记录查询
# ═══════════════════════════════════════════════════════
@app.route('/api/history', methods=['GET'])
def get_history():
    limit = request.args.get('limit', 20, type=int)
    user_id = request.args.get('user_id')

    # 优先读本地 JSON
    if user_id:
        import os as _os
        history_file = f"./history_{user_id}.json"
        if _os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify({"history": data[:limit], "total": len(data), "source": "local"})
            except Exception as e:
                print(f"读本地 JSON 失败，降级到 Neo4j: {e}")

    # 降级：读 Neo4j
    try:
        driver = config.get_neo4j_driver()
        with driver.session() as sess:
            result = sess.run("""
                MATCH (conv:Conversation)
                WHERE $uid IS NULL OR conv.user_id = $uid
                RETURN conv.timestamp as time,
                       conv.product_name as product,
                       conv.platform as platform,
                       conv.region as region,
                       conv.ai_response as content,
                       conv.recommended_tags as tags,
                       conv.poster_versions as poster_versions,
                       conv.workflow_id as workflow_id
                ORDER BY conv.timestamp DESC LIMIT $limit
            """, uid=str(user_id) if user_id else None, limit=limit)
            history = []
            for r in result:
                poster_raw = r.get("poster_versions") or "{}"
                try:
                    posters = json.loads(poster_raw) if isinstance(poster_raw, str) else poster_raw
                except Exception:
                    posters = {}
                history.append({
                    "timestamp": str(r["time"]),
                    "product": r["product"],
                    "platform": r["platform"],
                    "region": r.get("region", ""),
                    "content": r["content"],
                    "tags": r.get("tags") or [],
                    "poster_versions": posters,
                    "workflow_id": r.get("workflow_id", "")
                })
            return jsonify({"history": history, "total": len(history), "source": "neo4j"})
    except Exception as e:
        return jsonify({"history": [], "total": 0})


# ═══════════════════════════════════════════════════════
#  端点 6：历史记录 — 更新海报数据
# ═══════════════════════════════════════════════════════
@app.route('/api/history/update-poster', methods=['POST'])
def update_history_poster():
    data = request.json
    workflow_id = data.get('workflow_id')
    user_id = data.get('user_id')
    poster_versions = data.get('poster_versions', {})
    if not workflow_id:
        return jsonify({"error": "workflow_id 必填"}), 400

    updated = False
    # 更新本地 JSON
    if user_id:
        import os as _os
        history_file = f"./history_{user_id}.json"
        if _os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                for rec in records:
                    if rec.get("workflow_id") == workflow_id:
                        rec["poster_versions"] = poster_versions
                        updated = True
                        break
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"本地 JSON 更新失败: {e}")

    # 更新 Neo4j
    try:
        driver = config.get_neo4j_driver()
        with driver.session() as sess:
            result = sess.run("""
                MATCH (conv:Conversation {workflow_id: $wid})
                SET conv.poster_versions = $posters
                RETURN count(conv) as updated_count
            """, wid=workflow_id, posters=json.dumps(poster_versions))
            record = result.single()
            if record and record["updated_count"] > 0:
                updated = True
    except Exception as e:
        print(f"Neo4j poster 更新失败: {e}")

    return jsonify({"success": updated, "workflow_id": workflow_id})


# ═══════════════════════════════════════════════════════
#  端点 7：直播脚本生成
# ═══════════════════════════════════════════════════════
@app.route('/api/ai/generate-live-script', methods=['POST'])
def generate_live_script():
    data = request.json
    product_name = data.get("product_name", "农产品")
    platform = data.get("platform", "抖音")
    duration = data.get("duration", 60)
    style = data.get("style", "fresh")
    ai_content = data.get("ai_content", "")
    user_id = data.get("user_id", "")

    style_map = {'fresh': '清新自然、亲切温暖', 'humorous': '幽默搞笑、轻松活泼', 'professional': '专业权威、信息量大'}
    style_hint = style_map.get(style, '自然亲切')
    duration_label = f"{duration}秒" if duration < 60 else f"{duration // 60}分钟"

    prompt = f"""你是一位资深的农产品直播运营专家。请为【{product_name}】设计一份{platform}平台的直播脚本。

要求：
- 时长约 {duration_label}
- 语气风格：{style_hint}
- 平台：{platform}（符合该平台直播间风格和互动习惯）
- 结构清晰，分段标注时间节点和动作提示

请按以下结构输出（Markdown 格式）：

## 🎬 直播脚本 · {product_name}
**平台**：{platform} | **时长**：{duration_label} | **风格**：{style_hint}

### 🎤 开场（0:00 - ...）
（打招呼、暖场、预告今天内容）

### 📦 产品介绍（... - ...）
（展示产品、讲解卖点、产地故事）

### 💬 互动环节（... - ...）
（提问、评论互动、抽奖等）

### 🎁 福利时间（... - ...）
（报价、优惠、限时折扣）

### 🛒 引导下单（... - ...）
（催促下单、倒计时、结束语）

每个段落要包含：具体台词 + [动作/表情提示]"""

    if ai_content:
        prompt += f"\n\n参考文案（保持卖点一致）：\n{ai_content[:500]}"

    # 获取用户产品特征
    if user_id:
        try:
            import requests as http_req
            res = http_req.get(f"{config.MAIN_API}/api/user/{user_id}/profile", timeout=3)
            if res.status_code == 200:
                profile = res.json()
                traits = profile.get("traits", [])
                if traits:
                    trait_values = [t.get("trait_value", "") for t in traits[:5] if t.get("trait_value")]
                    if trait_values:
                        prompt += f"\n\n产品特征（融入脚本）：{'、'.join(trait_values)}"
        except Exception:
            pass

    try:
        resp = llm_client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的农产品直播运营专家，擅长写接地气、有感染力的直播脚本。直接输出脚本内容，不要额外解释。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.75, max_tokens=2000
        )
        script = resp.choices[0].message.content.strip()
        return jsonify({"success": True, "script": script})
    except Exception:
        # 兜底脚本
        fallback = f"""## 🎬 直播脚本 · {product_name}
**平台**：{platform} | **时长**：约{duration_label}

### 🎤 开场
[微笑，挥手] 哈喽家人们！欢迎来到我的直播间！
今天给大家带来一款超级棒的{product_name}！

### 📦 产品介绍
[展示产品] 大家看看这个品质！
🌱 纯天然种植，零污染
🥬 新鲜采摘，从田间到餐桌不超过24小时
💚 口感绝佳，营养满满

### 💬 互动环节
有没有宝宝想知道我们的{product_name}是怎么种出来的？扣 1 告诉我！

### 🎁 福利时间
今天直播间专属福利来啦！原价XX元，直播间只要XX元！

### 🛒 引导下单
宝宝们赶紧点击下方购物车！库存有限，冲冲冲！"""
        return jsonify({"success": True, "script": fallback})


# ═══════════════════════════════════════════════════════
#  历史保存（内部函数）
# ═══════════════════════════════════════════════════════
def _save_history(user_id, product, platform, region, content, tags, workflow_id):
    # Neo4j
    try:
        driver = config.get_neo4j_driver()
        with driver.session() as sess:
            sess.run("""
                CREATE (conv:Conversation {
                    timestamp: datetime(),
                    user_id: $uid,
                    product_name: $product,
                    platform: $platform,
                    region: $region,
                    ai_response: $content,
                    recommended_tags: $tags,
                    poster_versions: $poster_versions,
                    workflow_id: $wid
                })
            """, uid=str(user_id), product=product, platform=platform,
                region=region, content=content, tags=tags or [],
                poster_versions=json.dumps({}), wid=workflow_id)
    except Exception as e:
        print(f"Neo4j 保存失败: {e}")

    # 本地 JSON 备份
    try:
        import os as _os
        history_file = f"./history_{user_id}.json"
        record = {
            "timestamp": datetime.now().isoformat(),
            "product": product,
            "platform": platform,
            "region": region,
            "content": content,
            "tags": tags or [],
            "workflow_id": workflow_id,
            "poster_versions": {}
        }
        existing = []
        if _os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing.insert(0, record)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(existing[:50], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"本地 JSON 备份失败: {e}")


# ═══════════════════════════════════════════════════════
#  启动
# ═══════════════════════════════════════════════════════
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(" 云稼集 AgriWit - LangChain Multi-Agent Service")
    print("=" * 60)
    print(" http://localhost:5001")
    print()
    print(" LangGraph Workflow:")
    print(" START → [Parallel: Profile | Region | TagPool]")
    print("      → Copywriter → QA (up to 3 rounds)")
    print("      → TagSelector → END")
    print()
    print(" API Endpoints:")
    print(" POST /api/ai/generate           - 文案生成（LangGraph）")
    print(" POST /api/ai/refine             - 文案修改")
    print(" POST /api/ai/generate-live-script - 直播脚本")
    print(" POST /api/hotspot               - 热点推荐")
    print(" GET  /api/workflow/status/{id}   - 工作流状态")
    print(" GET  /api/history               - 历史记录")
    print(" POST /api/history/update-poster  - 更新海报")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5001, host='0.0.0.0')
