# ai_service.py - 真正的多Agent⼯作流版本
"""
架构说明：
═══════════════════════════════════════════════════════════════
 Orchestrator Agent（调度员）
 ├── 信息收集层（并⾏）
 │ ├── ProfileAgent 读取⽤户档案 + 特征
 │ ├── RegionAgent 查 Neo4j 地域⻛格
 │ └── TagPoolAgent 查 Neo4j 标签库 + 禁⽤词
 │
 ├── 创作层
 │ └── CopywriterAgent ⽣成文案（携带完整上下文）
 │
 ├── 质检层（可打回重做，最多3轮）
 │ └── QAAgent 检查禁⽤词 / 字数 / 文⻛
 │
 └── 推荐层
     └── TagSelectorAgent 从 Neo4j 池⾥选最优标签
每个 Agent 都有：
 - 明确的 role（⻆⾊）
 - 独⽴的 system_prompt
 - ⾃⼰的 run() ⽅法
 - 可观测的 log（思考过程），供前端展示
调⽤⼊⼝：
 POST /api/ai/generate → Orchestrator.run()
 POST /api/ai/refine → CopywriterAgent 单独修改
 GET /api/workflow/status → 返回当前各Agent状态（SSE 流式）
═══════════════════════════════════════════════════════════════
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from openai import OpenAI
from neo4j import GraphDatabase
import requests as http_req
import json, uuid, time, threading, os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# ─────────────────────── 基础配置 ───────────────────────
# LLM 服务使用 OpenAI 兼容协议，便于在 DeepSeek、vLLM、LM Studio、
# Ollama 等服务之间切换，而不改变上层 Agent 业务代码。
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or os.getenv("DEEPSEEK_BASE_URL")
    or "https://api.deepseek.com"
)
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
llm = OpenAI(
    api_key=LLM_API_KEY or "missing-key",
    base_url=LLM_BASE_URL,
)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "")
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

MAIN_API = "http://localhost:5000"
TAG_API = "http://localhost:5002"

# 运⾏中的⼯作流状态，供前端轮询
workflow_store: dict[str, dict] = {}

REGION_MAP = {
    # ⼴东 - 客家文化区
    '梅州': '客家文化区', '河源': '客家文化区', '惠州': '客家文化区', '韶关': '客家文化区', '清远': '客家文化区',
    # ⼴东 - ⼴府文化区
    '⼴州': '⼴府文化区', '佛⼭': '⼴府文化区', '肇庆': '⼴府文化区', '江⻔': '⼴府文化区',
    '中⼭': '⼴府文化区', '珠海': '⼴府文化区', '东莞': '⼴府文化区', '深圳': '⼴府文化区',
    # ⼴东 - 潮汕文化区
    '潮州': '潮汕文化区', '汕头': '潮汕文化区', '揭阳': '潮汕文化区', '汕尾': '潮汕文化区',
    # ⼴东 - 粤⻄/滨海区
    '湛江': '粤⻄/滨海区', '茂名': '粤⻄/滨海区', '阳江': '粤⻄/滨海区', '云浮': '粤⻄/滨海区',
    # 华东
    '⼭东': '华东地区', '济南': '华东地区', '⻘岛': '华东地区',
    '江苏': '华东地区', '南京': '华东地区', '苏州': '华东地区',
    '浙江': '华东地区', '杭州': '华东地区', '宁波': '华东地区',
    '上海': '华东地区', '安徽': '华东地区', '福建': '华东地区', '厦⻔': '华东地区',
    # 华中
    '湖南': '华中地区', '⻓沙': '华中地区', '湖北': '华中地区', '武汉': '华中地区',
    '河南': '华中地区', '郑州': '华中地区', '江⻄': '华中地区', '南昌': '华中地区',
    # ⻄南
    '四川': '⻄南地区', '成都': '⻄南地区', '重庆': '⻄南地区',
    '云南': '⻄南地区', '昆明': '⻄南地区', '贵州': '⻄南地区', '贵阳': '⻄南地区',
    # ⻄北
    '陕⻄': '⻄北地区', '⻄安': '⻄北地区', '⽢肃': '⻄北地区', '宁夏': '⻄北地区',
    '⻘海': '⻄北地区', '新疆': '⻄北地区', '乌鲁⽊⻬': '⻄北地区',
    # 东北
    '辽宁': '东北地区', '沈阳': '东北地区', '⼤连': '东北地区',
    '吉林': '东北地区', '⻓春': '东北地区', '⿊⻰江': '东北地区', '哈尔滨': '东北地区', '东北': '东北地区',
    # 华北
    '北京': '华北地区', '天津': '华北地区', '河北': '华北地区', '⽯家庄': '华北地区',
    '⼭⻄': '华北地区', '太原': '华北地区', '内蒙古': '华北地区',
}

REGION_STYLES = {
    '客家文化区': '强调"纯净""原⽣态""⼤⼭的馈赠"，语⽓朴实有温度',
    '⼴府文化区': '强调"讲究""精细""⽼字号"，注重品质感',
    '潮汕文化区': '强调"极度新鲜""⼯匠精神"，重视传统⼯艺',
    '粤⻄/滨海区': '强调"阳光充⾜""滨海⻛味"，语⽓热情',
    '华东地区': '强调"精致""品质""江南⻛味"，语⽓细腻',
    '⻄南地区': '强调"⼭珍""⽣态好物"，语⽓神秘有吸引⼒',
    '东北地区': '强调"实在量⼤""东北特⾊"，语⽓豪爽直接',
}

# ═══════════════════════════════════════════════════════════
# 基类：BaseAgent
# ═══════════════════════════════════════════════════════════
class BaseAgent:
    """所有Agent继承此基类，统⼀⽇志、LLM调⽤、状态上报"""
    def __init__(self, name: str, workflow_id: str):
        self.name = name
        self.workflow_id = workflow_id
        self.status = "idle"  # idle → running → done / error
        self.result = None
        self.logs = []  # 可⻅的思考过程
        self._start_time = None

    # ── 状态管理 ──
    def _set_status(self, status: str):
        self.status = status
        self._push_to_store()

    def _log(self, msg: str):
        entry = {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg}
        self.logs.append(entry)
        print(f" [{self.name}] {msg}")
        self._push_to_store()

    def _push_to_store(self):
        """把⾃⼰的状态写⼊全局 workflow_store，前端可轮询"""
        if self.workflow_id not in workflow_store:
            workflow_store[self.workflow_id] = {"agents": {}}
        workflow_store[self.workflow_id]["agents"][self.name] = {
            "status": self.status,
            "logs": self.logs[-5:],  # 只保留最近5条
        }

    # ── LLM 调⽤（统⼀封装，⽅便以后换模型）──
    def _chat(self, system: str, user: str,
              temperature: float = 0.7, max_tokens: int = 500) -> str:
        resp = llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()

    def run(self, context: dict) -> dict:
        raise NotImplementedError


# ═══════════════════════════════════════════════════════════
# Agent 1 — ProfileAgent（⽤户档案 + 特征收集）
# ═══════════════════════════════════════════════════════════
class ProfileAgent(BaseAgent):
    """
    职责：从 main.py 拉取⽤户完整档案，
    解析产品名、产地、注册关键词、历史特征，
    如果当前输⼊有新特征则提取并保存。
    """
    def run(self, context: dict) -> dict:
        self._set_status("running")
        self._log("读取⽤户档案…")

        user_id = context.get("user_id", "default_user")
        user_input = context.get("user_input", "")
        profile = {}

        try:
            res = http_req.get(f"{MAIN_API}/api/user/{user_id}/profile", timeout=5)
            if res.status_code == 200:
                profile = res.json()
                self._log(f"档案加载成功：{profile.get('username', '⽤户')}")
        except Exception as e:
            self._log(f"档案服务未响应，使⽤空档案（{e}）")

        primary = profile.get("primary_product") or {}
        product_name = primary.get("name") or ""
        origin = primary.get("origin") or ""

        # 汇总所有已知特征
        trait_values = list({
            t["trait_value"]
            for t in profile.get("traits", [])
            if not t.get("product_name") or t.get("product_name") == product_name
        })

        # 加上注册关键词
        for kw in primary.get("keywords", []):
            if kw not in trait_values:
                trait_values.append(kw)
        if primary.get("description"):
            trait_values.append(primary["description"])

        self._log(f"已知特征：{len(trait_values)} 条")

        # 从当前输⼊提取新特征
        new_traits = []
        if user_input and len(user_input) > 3:
            new_traits = self._extract_traits(user_input, product_name or "农产品")
            for t in new_traits:
                val = t.get("value", "")
                if val and val not in trait_values:
                    trait_values.append(val)
                    self._save_trait(user_id, product_name, t.get("type", "other"), val)
                    self._log(f"新特征学习：{t['type']}={val}")

        self._set_status("done")
        return {
            "product_name": product_name,
            "region_raw": profile.get("region", ""),
            "origin": origin,
            "traits": trait_values,
       
            "company": profile.get("company_name", ""),
            "user_type": profile.get("user_type", "individual"),
            "new_traits_count": 0,
        }

    def _extract_traits(self, text: str, product: str) -> list:
        try:
            raw = self._chat(
                system="提取产品特征，只输出JSON，不要任何其他内容。",
                user=f'从"{text}"中提取关于【{product}】的特征。输出格式：{{"traits":[{{"type":"texture/taste/appearance/usage/story/other","value":"具体描述"}}]}}',
                temperature=0.1, max_tokens=300
            )
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw).get("traits", [])
        except:
            return []

    def _save_trait(self, user_id, product_name, trait_type, trait_value):
        try:
            http_req.post(f"{MAIN_API}/api/user/trait", json={
                "user_id": user_id, "product_name": product_name,
                "trait_type": trait_type, "trait_value": trait_value,
                "source": "conversation"
            }, timeout=3)
        except:
            pass


# ═══════════════════════════════════════════════════════════
# Agent 2 — RegionAgent（地域文化⻛格分析）
# ═══════════════════════════════════════════════════════════
class RegionAgent(BaseAgent):
    """
    职责：根据⽤户注册地区（或输⼊中识别到的地名）
    确定文化圈，从 Neo4j 读取地域⻛格指南，
    返回文案⻛格指令给 CopywriterAgent。
    """
    def run(self, context: dict) -> dict:
        self._set_status("running")
        region_raw = context.get("region_raw", "")
        user_input = context.get("user_input", "")
        self._log(f"分析地域：{region_raw or '未填写'}")

        # 识别文化圈
        culture = self._detect_culture(region_raw) or self._detect_culture(user_input)

        # 从 Neo4j 读详细⻛格
        style_guide = ""
        emotions = []
        keywords = []
        if culture:
            style_guide, emotions, keywords = self._query_neo4j_style(culture)

        # fallback：⽤内置字典
        if not style_guide:
            style_guide = REGION_STYLES.get(culture, "真诚接地⽓，突出产品天然品质")

        self._log(f"识别文化圈：{culture or '未知'} → ⻛格：{style_guide[:30]}…")
        self._set_status("done")
        return {
            "culture": culture or "通⽤",
            "style_guide": style_guide,
            "emotions": emotions,
            "keywords": keywords,
        }

    def _detect_culture(self, text: str) -> str:
        if not text:
            return ""
        for kw, culture in REGION_MAP.items():
            if kw in text:
                return culture
        return ""

    def _query_neo4j_style(self, region_name: str):
        try:
            with neo4j_driver.session() as sess:
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
            self._log(f"Neo4j查询失败：{e}")
        return "", [], []


# ═══════════════════════════════════════════════════════════
# Agent 3 — TagPoolAgent（标签库 + 禁⽤词加载）
# ═══════════════════════════════════════════════════════════
class TagPoolAgent(BaseAgent):
    """
    职责：并⾏从 Neo4j 加载：
    - 禁⽤词列表
    - 平台标签库
    - 地域文化标签
    - 产品属性标签
    为后续 CopywriterAgent 和 TagSelectorAgent 提供素材池。
    """
    def run(self, context: dict) -> dict:
        self._set_status("running")
        platform = context.get("platform", "⼩红书")
        culture = context.get("culture", "")
        category = context.get("category", "")
        self._log(f"加载标签池：{platform} / {culture} / {category}")

        forbidden = self._load_forbidden_words()
        self._log(f"禁⽤词：{len(forbidden)} 个")

        tags_data = self._load_tags(platform, culture, category)
        total = sum(
            len(cat.get("tags", [])) for cat in tags_data.get("platform_tags", [])
        )
        self._log(f"平台标签：{total} 个，产品属性：{len(tags_data.get('product_attributes',[]))} 个")

        self._set_status("done")
        return {
            "forbidden_words": forbidden,
            "platform_tags": tags_data.get("platform_tags", []),
            "region_keywords": tags_data.get("region_info", {}).get("keywords", []) if tags_data.get("region_info") else [],
            "culture_tags": tags_data.get("culture_tags", []),
            "product_attributes": tags_data.get("product_attributes", []),
        }

    def _load_forbidden_words(self) -> list:
        try:
            with neo4j_driver.session() as sess:
                rec = sess.run("MATCH (fw:ForbiddenWord) RETURN collect(fw.word) as words").single()
                return [w for w in (rec["words"] if rec else []) if w]
        except Exception as e:
            self._log(f"禁⽤词加载失败：{e}")
            return []

    def _load_tags(self, platform, region, category) -> dict:
        try:
            res = http_req.get(f"{TAG_API}/api/tags/all",
                               params={"platform": platform, "region": region, "product_category": category},
                               timeout=5)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            self._log(f"标签服务未响应：{e}")
        return {}


# ═══════════════════════════════════════════════════════════
# Agent 4 — DatasetRAGAgent（本地数据集检索）
# ═══════════════════════════════════════════════════════════
class DatasetRAGAgent(BaseAgent):
    """
    职责：从清洗后的农业文案数据集中召回相似案例。
    这是挑战杯展示里最关键的“可解释 RAG 证据链”：生成结果不只是调用大模型，
    而是能说明参考了哪些真实平台文案、匹配了哪些卖点与受众。
    """
    def run(self, context: dict) -> dict:
        self._set_status("running")
        self._log("检索本地农业文案数据集…")

        try:
            from dataset_rag import get_dataset_retriever
            retriever = get_dataset_retriever()
            query = " ".join([
                context.get("product_name", ""),
                context.get("user_input", ""),
                context.get("target_user", ""),
                context.get("festival_hint", ""),
                " ".join(context.get("traits", [])[:8]),
            ])
            examples = retriever.search_as_context(
                query=query,
                platform=context.get("platform", ""),
                category=context.get("category", ""),
                target_user=context.get("target_user", ""),
                top_k=5,
            )
            self._log(f"召回参考案例：{len(examples)} 条")
            self._set_status("done")
            return {"rag_examples": examples}
        except Exception as e:
            self._log(f"数据集检索跳过：{e}")
            self._set_status("done")
            return {"rag_examples": []}


# ═══════════════════════════════════════════════════════════
# Agent 5 — CopywriterAgent（文案创作，核⼼Agent）
# ═══════════════════════════════════════════════════════════
class CopywriterAgent(BaseAgent):
    """
    职责：汇总前三个Agent的输出，构建完整上下文Prompt，
    ⽣成营销文案。
    接受 QAAgent 的打回意⻅，最多重试3次。
    """
    def run(self, context: dict) -> dict:
        self._set_status("running")
        self._log("开始创作文案…")

        product_name = context["product_name"]
        traits = context.get("traits", [])
        culture = context.get("culture", "通⽤")
        style_guide = context.get("style_guide", "真诚接地⽓")
        platform = context.get("platform", "⼩红书")
        forbidden = context.get("forbidden_words", [])
        custom_tags = context.get("custom_tags", [])
        festival_hint = context.get("festival_hint", "")
        target_user = context.get("target_user", "")
        user_input = context.get("user_input", "")
        qa_feedback = context.get("qa_feedback", "")  # QA打回时附带的意⻅

        traits_str = "、".join(traits[:8]) if traits else "优质天然"
        forbidden_str = "、".join(forbidden[:30]) if forbidden else "⽆"
        tags_str = "、".join(custom_tags[:6]) if custom_tags else ""
        
        # ==================== 新增：平台适配提示（关键修改） ====================
        if platform == "抖音":
            platform_hint = "文案要口语化、短平快，适合短视频，适当添加话题标签，控制在100字左右，语气活泼亲切"
        elif platform == "淘宝":
            platform_hint = "突出卖点，关键信息前置，使用✅等符号增强可读性，结构清晰，便于用户快速决策"
        elif platform == "小红书":
            platform_hint = "故事性强，情感丰富，分段清晰，增加生活场景描述，适合种草和分享"
        elif platform == "微博":
            platform_hint = "短小精悍，适合快速传播，添加热点元素，增强互动性"
        elif platform == "头条":
            platform_hint = "资讯风格，标题吸引人，正文分段清晰，突出实用信息"
        else:
            platform_hint = "根据平台特点调整文案格式和语气"


        system_prompt = (
            f"你是专业的农产品营销文案专家，深谙{culture}的文化风格。"
            "你的任务是为真实的农产品写宣传文案，吸引买家购买这个产品。"
            "请根据不同平台的用户习惯和算法特点，调整文案的语气、长度和结构。"
            "直接输出文案正文，不加标题，不解释，不提问。"
            "严禁介绍任何软件、工具、网站、平台或APP。"
            "严禁提到'这个工具'、'这个平台'、'一键生成'等与农产品无关的词语。"
         )

        # 如果产品名太泛（"农产品"），给出更明确的写作⽅向提示
        product_hint = ""
        if product_name in ("农产品", "", None):
            product_hint = "（根据产品特点推断具体品类，写出有针对性的内容）"
            
                # ==================== 多平台适配提示（核心修改） ====================
        platform = context.get("platform", "小红书")

        # 根据不同平台生成针对性适配要求
        platform_hints = {
            "抖音": "文案要口语化、短平快，像朋友聊天一样自然，适合短视频，适当添加#话题标签，控制在80-120字，语气活泼亲切，增加情感共鸣和呼吁行动",
            "淘宝": "突出卖点，关键信息前置，使用✅等符号增强可读性，结构清晰（优点+特点+保障），便于用户快速决策，增加信任感和购买欲望",
            "小红书": "故事性强，情感丰富，分段清晰，增加生活场景描述、个人感受和真实体验，语气温柔有温度，适合种草和分享",
            "微博": "短小精悍，适合快速传播，添加热点元素，增强互动性，语言简洁有力",
            "头条": "资讯风格，标题吸引人，正文分段清晰，突出实用信息和干货，逻辑性强"
        }

        # 获取当前平台的适配要求（默认小红书）
        platform_hint = platform_hints.get(platform, "根据平台特点调整文案格式和语气")

        # ==================== 提示词构建 ====================
        prompt_parts = [
            f"任务：为农户销售的【{product_name}】写一段{platform}宣传文案，目标是吸引消费者购买这个农产品。",
            "",
            f"平台适配要求：{platform_hint}",
            "",
            "═══ 产品信息（必须围绕这些内容写）═══",
            f"产品名称：{product_name}{product_hint}",
            f"产品特点：{traits_str}",
        ]

        if context.get("origin"):
            prompt_parts.append(f"产品产地：{context['origin']}")

        prompt_parts += [
            "",
            f"═══ 文案风格 ═══",
            f"地域文化：{culture}",
            f"风格要求：{style_guide}",
        ]

        if festival_hint:
            prompt_parts += ["", f"节⽇氛围：{festival_hint}（文案要体现节⽇特⾊）"]

        if target_user:
            prompt_parts += ["", f"⽬标受众：{target_user}（语⽓和内容针对该群体）"]

        if user_input and user_input != product_name:
            prompt_parts += ["", f"⽤户补充要求：{user_input}"]

        rag_examples = context.get("rag_examples", [])
        if rag_examples:
            example_lines = []
            for idx, ex in enumerate(rag_examples[:4], 1):
                body = (ex.get("body") or "")[:180]
                angles = "、".join(ex.get("angles") or [])
                audiences = "、".join(ex.get("audiences") or [])
                example_lines.append(
                    f"{idx}. [{ex.get('platform','')}] {ex.get('title','')}｜"
                    f"产品:{ex.get('product_name','')}｜角度:{angles}｜受众:{audiences}\n"
                    f"   参考表达:{body}"
                )
            prompt_parts += [
                "",
                "════ 本地数据集RAG参考案例（学习结构和卖点表达，禁止逐句照抄）════",
                "\n".join(example_lines),
                "请优先借鉴这些案例的宣传角度、平台语气和可信卖点组织方式，同时为当前产品重新创作。",
            ]

        # ★ 向量检索到的相关补充信息
        # ★ 工具箱向量记忆（强化版，原来是"可适当融入"，改为必须使用）
        extra_info = context.get("extra_info", [])
        if extra_info:
            extra_lines = "\n".join([f"• {item}" for item in extra_info])
            prompt_parts += [
                "",
                "════ 【用户真实背景信息·必须融入文案】 ════",
                extra_lines,
                "⚠️ 以上是用户提供的真实卖点，获奖/认证/年限/古法工艺等亮点必须明确写进文案，不能遗漏或模糊处理。",
            ]

        # ★ 素材库模板（新增）
        template = context.get("template", "")
        if template:
            prompt_parts += [
                "",
                "════ 参考模板风格 ════",
                "请严格参考以下模板的结构、节奏和语气来创作（内容替换为本产品，不要复制原文）：",
                template,
            ]

        # ★ 对话补充信息（新增）
        supplemental_info = context.get("supplemental_info", "")
        if supplemental_info and supplemental_info != context.get("user_input", ""):
            prompt_parts += ["", f"用户补充说明（请体现在文案中）：{supplemental_info}"]

        # max_tokens 根据字数要求动态调整，避免⻓文案被截断
        target_chars = context.get("word_count_target", 120)
        max_tok = max(800, int(target_chars * 2.5))
        content = self._chat(system_prompt, "\n".join(prompt_parts),
                             temperature=0.75, max_tokens=max_tok)
        self._log(f"文案⽣成完毕（{len(content)}字）")
        self._set_status("done")
        return {"content": content}


# ═══════════════════════════════════════════════════════════
# Agent 5 — QAAgent（质检 + 打回机制）
# ═══════════════════════════════════════════════════════════
class QAAgent(BaseAgent):
    """
    职责：检查 CopywriterAgent 输出的文案：
    1. 是否包含禁⽤词 → 有则打回
    2. 字数是否在 80-140 字之间 → 不符打回
    3. 让 AI 判断文⻛是否与地域/平台/⽬标⽤户匹配
    打回时附带具体修改建议，最多允许3轮重试。
    """
    def run(self, context: dict) -> dict:
        self._set_status("running")
        content = context.get("content", "")
        forbidden = context.get("forbidden_words", [])
        platform = context.get("platform", "⼩红书")
        culture = context.get("culture", "通⽤")
        target_user = context.get("target_user", "")
        self._log("质检开始…")

        issues = []

        # ── 检查0：是否跑题（介绍⼯具/网站⽽不是产品）──
        off_topic_words = ["这个⼯具", "这个平台", "这个软件", "这个APP", "操作简单", "⼀键⽣成",
                           "⼀学就会", "专为农产品设计", "帮助农户", "我们的系统"]
        found_off = [w for w in off_topic_words if w in content]
        if found_off:
            issues.append(f"文案跑题，出现了与产品⽆关的内容「{'、'.join(found_off)}」，"
                          f"必须重写：文案应该宣传【{context.get('product_name','农产品')}】本身，"
                          f"不能介绍任何⼯具或网站")
            self._log(f" 跑题：{found_off}")
        else:
            self._log(" 内容聚焦于产品本身")

        found = [w for w in forbidden if w and w in content]
        if found:
            issues.append(f"包含禁⽤词「{'、'.join(found)}」，必须替换")
            self._log(f" 禁⽤词：{found}")
        else:
            self._log(" ⽆禁⽤词")

        # ── 检查2：字数 ──
        char_count = len(content.replace(" ", "").replace("\n", ""))
        target = context.get("word_count_target", 120)
        low, high = max(40, int(target * 0.6)), int(target * 1.5)
        if char_count < low:
            issues.append(f"字数过少（{char_count}字），要求约{target}字")
            self._log(f" 字数不⾜：{char_count}（⽬标{target}）")
        elif char_count > high:
            issues.append(f"字数过多（{char_count}字），要求约{target}字")
            self._log(f" 字数超限：{char_count}（⽬标{target}）")
        else:
            self._log(f" 字数合格：{char_count}字（⽬标{target}）")

        # ── 检查3：AI 文⻛评判 ──
        if not issues:
            style_ok, style_comment = self._check_style(content, platform, culture, target_user)
            if not style_ok:
                issues.append(style_comment)
                self._log(f" 文⻛问题：{style_comment}")
            else:
                self._log(f" 文⻛合格：{style_comment}")

        passed = len(issues) == 0
        feedback = "；".join(issues) if issues else ""
        self._set_status("done")
        self._log("质检通过 " if passed else f"质检不通过，打回重写：{feedback}")
        return {"passed": passed, "feedback": feedback}

    def _check_style(self, content, platform, culture, target_user):
        prompt = f"""请评判以下农产品文案是否符合要求：
文案：{content}
要求：
- 平台：{platform}（符合该平台⽤户阅读习惯）
- 地域文化：{culture}
- ⽬标受众：{target_user or '⼤众'}
只回答：PASS 或 FAIL: <具体问题>
（如：FAIL: 语⽓太正式，不符合⼩红书年轻⽤户⻛格）"""
        result = self._chat(
            "你是文案质检专家，判断文案是否符合平台和受众要求。",
            prompt, temperature=0.2, max_tokens=100
        )
        if result.startswith("PASS"):
            return True, "语⽓与平台⻛格匹配"
        return False, result.replace("FAIL:", "").strip()


# ═══════════════════════════════════════════════════════════
# Agent 6 — TagSelectorAgent（智能标签推荐）
# ═══════════════════════════════════════════════════════════
class TagSelectorAgent(BaseAgent):
    """
    职责：从 Neo4j 提供的标签池中（由 TagPoolAgent 加载），
    结合最终文案内容，⽤ AI 精选出 8-10 个最适合的标签。
    确保标签"来⾃库"⽽不是凭空创造，保证准确性。
    """
    def run(self, context: dict) -> dict:
        self._set_status("running")
        content = context.get("content", "")
        product_name = context.get("product_name", "农产品")
        platform = context.get("platform", "⼩红书")
        culture = context.get("culture", "")
        platform_tags = context.get("platform_tags", [])
        region_kw = context.get("region_keywords", [])
        culture_tags = context.get("culture_tags", [])
        product_attrs = context.get("product_attributes", [])
        self._log("从 Neo4j 标签库精选推荐标签…")

        # 汇总候选标签
        candidates = []
        for cat in platform_tags:
            candidates.extend(cat.get("tags", []))
        candidates.extend(region_kw)
        candidates.extend(product_attrs)
        for cat in culture_tags:
            candidates.extend(cat.get("tags", []))
        candidates = list(set(candidates))[:60]

        if not candidates:
            self._log("标签库为空，跳过推荐")
            self._set_status("done")
            return {"recommended_tags": []}

        prompt = f"""已⽣成的文案：
{content}

为上述文案在【{platform}】平台精选8-10个标签，必须从以下候选列表中选取：
{chr(10).join(candidates)}

选择标准：
1. 与文案内容⾼度相关
2. 符合{platform}的搜索习惯，有实际搜索量
3. 体现{culture}地域特⾊（如有）

只输出标签列表，英文逗号分隔，例如：#标签A,#标签B,#标签C
不输出其他内容："""

        raw = self._chat(
            f"你是{platform}标签运营专家，只从给定候选列表中选标签，不⾃创。",
            prompt, temperature=0.3, max_tokens=200
        )
        tags = [t.strip() for t in raw.replace("，", ",").split(",") if t.strip()][:10]
        self._log(f"推荐标签：{len(tags)} 个")
        self._set_status("done")
        return {"recommended_tags": tags}


# ═══════════════════════════════════════════════════════════
# Orchestrator：调度所有Agent，管理⼯作流
# ═══════════════════════════════════════════════════════════
class Orchestrator:
    """
    调度员：
    1. 并⾏执⾏信息收集层（ProfileAgent / RegionAgent / TagPoolAgent）
    2. 汇总结果 → 交给 CopywriterAgent
    3. QAAgent 质检，不通过则打回 CopywriterAgent 重写（最多3轮）
    4. TagSelectorAgent 最终推荐标签
    5. 全程记录到 workflow_store
    """
    MAX_QA_ROUNDS = 3

    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id

    def _new_agent(self, cls):
        return cls(name=cls.__name__, workflow_id=self.workflow_id)

    def run(self, request_data: dict) -> dict:
        wid = self.workflow_id
        user_id = request_data.get("user_id", "default_user")
        platform = request_data.get("platform", "⼩红书")
        explicit_product_name = request_data.get("product_name", "").strip()
        user_input = (request_data.get("user_request") or explicit_product_name).strip()
        custom_tags = request_data.get("custom_tags", [])
        festival_hint = request_data.get("festival_hint", "")
        target_user = request_data.get("target_user_hint", "")
        template = request_data.get("template", "")
        supplemental_info = request_data.get("supplemental_info", "") 

        workflow_store[wid] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "agents": {}
        }

        print(f"\n{'═'*60}")
        print(f" ⼯作流启动 [{wid[:8]}] user:{user_id} platform:{platform}")
        print(f"{'═'*60}")

        # ── 阶段1：并⾏信息收集 ──────────────────────────────
        print("\n [阶段1] 并⾏信息收集")
        profile_agent = self._new_agent(ProfileAgent)
        region_agent = self._new_agent(RegionAgent)
        tag_pool_agent = self._new_agent(TagPoolAgent)

        collect_ctx = {"user_id": user_id, "user_input": user_input, "region_raw": ""}

        # 先⽤空 region_raw 启动，ProfileAgent 会填充
        with ThreadPoolExecutor(max_workers=3) as pool:
            f_profile = pool.submit(profile_agent.run, collect_ctx)
            # RegionAgent 和 TagPoolAgent 也可以先跑，拿到 profile 结果后不影响
            f_region_prelim = pool.submit(region_agent.run, {**collect_ctx})
            f_tagpool_prelim = pool.submit(tag_pool_agent.run, {
                "platform": platform, "culture": "", "category": ""
            })

            profile_result = f_profile.result()
            region_prelim = f_region_prelim.result()
            tagpool_result = f_tagpool_prelim.result()

        # ⽤ Profile 的 region_raw 重新跑⼀次 RegionAgent（更准确）
        if profile_result.get("region_raw") and not region_prelim.get("culture"):
            region_result = self._new_agent(RegionAgent).run(
                {**collect_ctx, "region_raw": profile_result["region_raw"]}
            )
        else:
            region_result = region_prelim

        print(f"\n 档案：product={profile_result.get('product_name')} traits={len(profile_result.get('traits',[]))}条")
        print(f" 地域：culture={region_result.get('culture')} style={region_result.get('style_guide','')[:30]}")
        print(f" 标签池：forbidden={len(tagpool_result.get('forbidden_words',[]))} platform_cats={len(tagpool_result.get('platform_tags',[]))}")

        # ── 阶段2：文案创作 + 质检循环 ──────────────────────
        print("\n [阶段2] 文案创作 + 质检")

        # 汇总完整上下文
        request_like_words = ["生成", "海报", "文案", "帮我", "给我", "带字", "修改", "做一张", "来一张"]
        looks_like_request = any(w in explicit_product_name for w in request_like_words)
        final_product_name = profile_result.get("product_name") or ("" if looks_like_request else explicit_product_name) or "农产品"
        extra_info = []
        try:
            from vector_memory import get_vector_memory
            vm = get_vector_memory()
            uid_int = int(user_id) if str(user_id).isdigit() else 0
            query = f"{final_product_name} {supplemental_info or user_input}"
            extra_info = vm.search_relevant(user_id=uid_int, query=query, top_k=6)
            if extra_info:
                print(f" 向量记忆召回 {len(extra_info)} 条用户信息")
        except Exception as e:
            print(f"⚠️ 向量记忆检索跳过：{e}")
        if not final_product_name:
            print(" 警告：未找到产品名称！⽤户可能未完成注册第⼆步（产品信息登记）")
            print(" 将使⽤⽤户输⼊作为补充，但建议引导⽤户完成产品登记")
            final_product_name = "农产品"

        rag_result = self._new_agent(DatasetRAGAgent).run({
            "product_name": final_product_name,
            "user_input": user_input,
            "platform": platform,
            "target_user": target_user,
            "festival_hint": festival_hint,
            "traits": profile_result.get("traits", []),
        })
        rag_examples = rag_result.get("rag_examples", [])

        full_ctx = {
            # Profile
            "user_id": user_id,
            "product_name": final_product_name,
            "traits": profile_result.get("traits", []),
            "origin": profile_result.get("origin", ""),
            "extra_info": extra_info,           # ★ 向量召回的工具箱/追问补充信息（GLM Embedding）
            "rag_examples": rag_examples,       # ★ 本地农业文案数据集召回案例
            # Region
            "culture": region_result.get("culture", "通⽤"),
            "style_guide": region_result.get("style_guide", "真诚接地⽓"),
            "emotions": region_result.get("emotions", []),
            # TagPool
            "forbidden_words": tagpool_result.get("forbidden_words", []),
            "platform_tags": tagpool_result.get("platform_tags", []),
            "region_keywords": tagpool_result.get("region_keywords", []),
            "culture_tags": tagpool_result.get("culture_tags", []),
            "product_attributes": tagpool_result.get("product_attributes", []),
            "template": template,               # ★ 素材库模板
            "supplemental_info": supplemental_info,  # ★ 对话中补充的信息
            "user_input": f"{user_input}\n{supplemental_info}".strip() if supplemental_info else user_input,
            # Request params
            "platform": platform,
            "custom_tags": custom_tags,
            "festival_hint": festival_hint,
            "target_user": target_user,
            "user_input": user_input,
            "word_count_hint": request_data.get("word_count_hint", "100～120字"),
            "word_count_target": request_data.get("word_count_target", 120),
            "qa_feedback": "",  # 初始⽆反馈
        }

        final_content = ""
        qa_rounds = 0
        
        while qa_rounds < self.MAX_QA_ROUNDS:
            # 写作
            copywriter = self._new_agent(CopywriterAgent)
            copy_result = copywriter.run(full_ctx)
            draft = copy_result["content"]

            # 质检
            qa_agent = self._new_agent(QAAgent)
            # 给每轮 QA 不同名字，前端可⻅多次
            qa_agent.name = f"QAAgent_round{qa_rounds+1}"
            qa_result = qa_agent.run({**full_ctx, "content": draft})
            qa_rounds += 1
            print(f" 轮次{qa_rounds}：QA={'通过' if qa_result['passed'] else '打回'}")

            if qa_result["passed"]:
                final_content = draft
                break
            else:
                # 打回：把质检意⻅写回上下文，下⼀轮 CopywriterAgent 参考
                full_ctx["qa_feedback"] = qa_result["feedback"]
                full_ctx["content_draft"] = draft  # 保留草稿供参考

        if not final_content:
            # 三轮后取最后⼀稿
            final_content = draft
            print(f" 已达最⼤重试轮次，使⽤最后⼀稿")

        # ── 阶段3：标签推荐 ─────────────────────────────────
        print("\n [阶段3] 标签推荐")
        tag_selector = self._new_agent(TagSelectorAgent)
        tag_result = tag_selector.run({**full_ctx, "content": final_content})

        # ── 保存历史 ─────────────────────────────────────────
                # ── 保存历史记录（包含图片 + 推荐标签） ─────────────────────
        self._save_history(
            user_id=user_id,
            product=full_ctx["product_name"],
            platform=platform,
            region=region_result.get("culture", ""),
            content=final_content,
            tags=tag_result.get("recommended_tags", []),
            poster_versions=None   # 目前前端还没传图片，先保存 tag
        )


        # ── 汇总返回 ─────────────────────────────────────────
        workflow_store[wid]["status"] = "done"
        print(f"\n{'═'*60}")
        print(f" ⼯作流完成 [{wid[:8]}] | 文案{len(final_content)}字 | 推荐标签{len(tag_result['recommended_tags'])}个 | QA轮次:{qa_rounds}")
        print(f"{'═'*60}\n")

        return {
            "content": final_content,
            "type": "content",
            "workflow_id": wid,
            "session_id": wid,
            "product_name": full_ctx["product_name"],
            "region": region_result.get("culture", ""),
            "recommended_tags": tag_result.get("recommended_tags", []),
            "all_traits": full_ctx["traits"],
            "rag_examples": rag_examples,
            "qa_rounds": qa_rounds,
            # 每个 Agent 的状态摘要（前端可展示⼯作流过程）
            "agent_summary": {
                name: {"status": info["status"], "logs": info["logs"]}
                for name, info in workflow_store[wid].get("agents", {}).items()
            }
        }

    # ─── _save_history 方法 ───
    def _save_history(self, user_id, product, platform, region, content, tags, poster_versions=None):
        """保存历史记录到 Neo4j + 本地 JSON"""
        # 第一步：存 Neo4j
        try:
            with neo4j_driver.session() as sess:
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
                """,
                    uid=str(user_id),
                    product=product,
                    platform=platform,
                    region=region,
                    content=content,
                    tags=tags or [],
                    poster_versions=json.dumps(poster_versions or {}),
                    wid=self.workflow_id
                )
                print(f"✅ Neo4j 历史保存成功 [user:{user_id}]")
        except Exception as e:
            print(f"❌ Neo4j 保存失败: {e}")

        # 第二步：同时存本地 JSON（作为备份，前端也可直接读）
        try:
            import os
            history_file = f"./history_{user_id}.json"
            record = {
                "timestamp": datetime.now().isoformat(),
                "product": product,
                "platform": platform,
                "region": region,
                "content": content,
                "tags": tags or [],
                "workflow_id": self.workflow_id,
                "poster_versions": {}  # 图片此时还没生成，留空，等 update-poster 接口来填
            }
            existing = []
            if os.path.exists(history_file):
                with open(history_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            existing.insert(0, record)
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(existing[:50], f, ensure_ascii=False, indent=2)
            print(f"✅ 本地 JSON 备份成功 ({history_file})")
        except Exception as e:
            print(f"⚠️ 本地 JSON 备份失败: {e}")



# ═══════════════════════════════════════════════════════════
# Flask 接⼝
# ═══════════════════════════════════════════════════════════
@app.route('/api/ai/generate', methods=['POST'])
def generate_content():
    """主⽣成接⼝，内部⾛多Agent⼯作流"""
    data = request.json
    if isinstance(data.get("platform"), list):
        data["platform"] = data["platform"][0] if data["platform"] else "⼩红书"

    workflow_id = str(uuid.uuid4())
    orchestrator = Orchestrator(workflow_id=workflow_id)

    try:
        result = orchestrator.run(data)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "workflow_id": workflow_id}), 500


@app.route('/api/ai/refine', methods=['POST'])
def refine_content():
    """文案修改接⼝：单独调⽤ CopywriterAgent + QAAgent"""
    data = request.json
    wid = str(uuid.uuid4())

    forbidden = []
    try:
        with neo4j_driver.session() as sess:
            rec = sess.run("MATCH (fw:ForbiddenWord) RETURN collect(fw.word) as words").single()
            forbidden = [w for w in (rec["words"] if rec else []) if w]
    except:
        pass

    # ★ 从修改请求中提取字数要求
    req_text = data.get("request", "")
    import re as _re
    wm = _re.search(r"(\d+)\s*字", req_text)
    wc_target = int(wm.group(1)) if wm else data.get("word_count_target", 120)
    wc_hint = f"{wc_target}字左右" if wm else data.get("word_count_hint", "100～120字")

    ctx = {
        "product_name": data.get("product_name", "农产品"),
        "traits": [],
        "culture": "通⽤",
        "style_guide": "根据⽤户要求调整",
        "platform": data.get("platform", "⼩红书"),
        "forbidden_words": forbidden,
        "custom_tags": [],
        "festival_hint": "",
        "target_user": "",
        "user_input": req_text,
        "word_count_hint": wc_hint,
        "word_count_target": wc_target,
        "qa_feedback": f"原文案：{data.get('original_content','')}；修改要求：{req_text}",
    }

    copywriter = CopywriterAgent(name="CopywriterAgent", workflow_id=wid)
    copy_result = copywriter.run(ctx)
    content = copy_result["content"]

    qa = QAAgent(name="QAAgent", workflow_id=wid)
    qa_result = qa.run({**ctx, "content": content})

    if not qa_result["passed"]:
        ctx["qa_feedback"] = qa_result["feedback"]
        content = CopywriterAgent(name="CopywriterAgent_retry", workflow_id=wid).run(ctx)["content"]

    return jsonify({"content": content, "type": "refined"})


@app.route('/api/workflow/status/<workflow_id>', methods=['GET'])
def get_workflow_status(workflow_id):
    """
    前端轮询此接⼝，可实时展示⼯作流中每个Agent的状态和⽇志。
    适合做"多Agent⼯作流可视化"展示⾯板。
    """
    wf = workflow_store.get(workflow_id)
    if not wf:
        return jsonify({"error": "workflow not found"}), 404
    return jsonify(wf)


@app.route('/api/dataset/report', methods=['GET'])
def get_dataset_report():
    """返回数据集质量报告，供参赛展示和迭代治理使用。"""
    report_path = os.path.join(os.path.dirname(__file__), "dataset_quality_report.json")
    if not os.path.exists(report_path):
        return jsonify({
            "success": False,
            "message": "尚未生成数据集报告，请先运行 python dataset_tools.py",
        }), 404
    with open(report_path, "r", encoding="utf-8") as f:
        return jsonify({"success": True, "report": json.load(f)})


@app.route('/api/dataset/search', methods=['POST'])
def search_dataset_examples():
    """调试/展示用：查询本地农业文案数据集召回结果。"""
    data = request.json or {}
    try:
        from dataset_rag import get_dataset_retriever
        examples = get_dataset_retriever().search_as_context(
            query=data.get("query", ""),
            platform=data.get("platform", ""),
            category=data.get("category", ""),
            target_user=data.get("target_user", ""),
            top_k=int(data.get("top_k", 5)),
        )
        return jsonify({"success": True, "examples": examples, "count": len(examples)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "examples": []}), 500


# ════════════════════════════════════════════════
# 热点推荐接⼝（素材库使⽤）
# ════════════════════════════════════════════════
@app.route('/api/hotspot', methods=['POST'])
def get_hotspot():
    """
    根据⽤户主推产品⽣成个性化热点话题。
    如果没有产品信息则返回泛⽤农产品运营内容。
    """
    data = request.json or {}
    product = data.get("product_name", "")
    platform = data.get("platform", "⼩红书")
    category = data.get("category", "")

    if product:
        # 个性化：针对具体产品
        prompt = f"""你是⼀位资深的农产品新媒体运营专家。
现在是2026年春季，请为销售【{product}】的农户⽣成{platform}平台上的热点内容⽅向。
输出JSON格式，包含：
- hotspots: 5条当前热⻔话题，每条包含 title(标题)、angle(内容⻆度)、heat(热度:⾼/中/低)
- tips: 3条针对{product}的运营⼩技巧
只输出JSON，不要任何解释：
{{
  "hotspots": [
    {{"title": "话题标题", "angle": "适合的内容⻆度", "heat": "⾼"}}
  ],
  "tips": ["技巧1", "技巧2", "技巧3"]
}}"""
    else:
        # 泛⽤：农产品运营通⽤内容
        prompt = f"""你是⼀位资深的农产品新媒体运营专家。
请⽣成{platform}平台当前热⻔的农产品运营话题和技巧。
输出JSON格式：
{{
  "hotspots": [
    {{"title": "话题标题", "angle": "适合的内容⻆度", "heat": "⾼/中/低"}}
  ],
  "tips": ["运营技巧1", "运营技巧2", "运营技巧3"]
}}
要求：
- hotspots 5条，贴近当前时节和平台热点
- tips 3条，实⽤且针对新⼿农户
只输出JSON："""

    try:
        resp = llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        return jsonify({"success": True, "product": product or "农产品通⽤", **result})
    except Exception as e:
        # fallback 数据，避免接⼝报错
        return jsonify({
            "success": True,
            "product": product or "农产品通⽤",
            "hotspots": [
                {"title": "产地直播带货新玩法", "angle": "展示真实采摘/⽣产过程", "heat": "⾼"},
                {"title": "农产品溯源故事", "angle": "讲述种植背后的⼈情味", "heat": "⾼"},
                {"title": "节⽓饮⻝搭配指南", "angle": "结合时令推荐⻝⽤⽅法", "heat": "中"},
                {"title": "乡村振兴好物推荐", "angle": "强调助农和地域文化", "heat": "中"},
                {"title": "原产地探店vlog", "angle": "带⽤户云逛农场", "heat": "中"},
            ],
            "tips": [
                "发布时间选早上7-9点或晚上8-10点，这两个时段⽤户活跃度最⾼",
                "图⽚⾸图⽤⾼饱和度的产品特写，点击率⽐⻛景图⾼40%",
                "评论区第⼀条⾃⼰置顶问题，引导互动可以显著提升推荐量"
            ]
        })


# ─── 替换原来的 get_history 接口，补上 poster_versions 字段 ───
@app.route('/api/history', methods=['GET'])
def get_history():
    limit = request.args.get('limit', 20, type=int)
    user_id = request.args.get('user_id')

    # 优先读本地 JSON（速度快，且包含最新数据）
    if user_id:
        import os
        history_file = f"./history_{user_id}.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify({"history": data[:limit], "total": len(data), "source": "local"})
            except Exception as e:
                print(f"读本地 JSON 失败，降级到 Neo4j: {e}")

    # 降级：读 Neo4j
    try:
        with neo4j_driver.session() as sess:
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
                except:
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

# ─── 新增接口：图片处理完后更新历史记录 ───
@app.route('/api/history/update-poster', methods=['POST'])
def update_history_poster():
    """
    前端图片处理完成后调用，把 poster_versions 补充到历史记录里。
    前端传：{ workflow_id: "xxx", user_id: "5", poster_versions: {...} }
    """
    data = request.json
    workflow_id = data.get('workflow_id')
    user_id = data.get('user_id')
    poster_versions = data.get('poster_versions', {})

    if not workflow_id:
        return jsonify({"error": "workflow_id 必填"}), 400

    updated = False

    # 1. 更新本地 JSON
    if user_id:
        import os
        history_file = f"./history_{user_id}.json"
        if os.path.exists(history_file):
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
                print(f"✅ 本地 JSON poster 更新成功 [workflow:{workflow_id[:8]}]")
            except Exception as e:
                print(f"⚠️ 本地 JSON 更新失败: {e}")

    # 2. 更新 Neo4j
    try:
        with neo4j_driver.session() as sess:
            result = sess.run("""
                MATCH (conv:Conversation {workflow_id: $wid})
                SET conv.poster_versions = $posters
                RETURN count(conv) as updated_count
            """, wid=workflow_id, posters=json.dumps(poster_versions))
            record = result.single()
            if record and record["updated_count"] > 0:
                updated = True
                print(f"✅ Neo4j poster 更新成功 [workflow:{workflow_id[:8]}]")
    except Exception as e:
        print(f"⚠️ Neo4j poster 更新失败: {e}")

    return jsonify({"success": updated, "workflow_id": workflow_id})


# ════════════════════════════════════════════════
# 直播脚本生成接口（DeepSeek AI 增强版）
# ════════════════════════════════════════════════
@app.route('/api/ai/generate-live-script', methods=['POST'])
def generate_live_script():
    """
    使用 DeepSeek AI 生成高质量直播脚本

    请求参数：
        product_name: 产品名称
        platform: 平台（抖音、快手、视频号等）
        user_id: 用户ID
        duration: 时长（秒）—— 30 / 60 / 180 / 300
        style: 风格（fresh/humorous/professional）
        ai_content: 关联文案内容（可选，用于保持一致性）
    返回：
        script: 生成的直播脚本文本
    """
    try:
        data = request.json
        product_name = data.get("product_name", "农产品")
        platform = data.get("platform", "抖音")
        duration = data.get("duration", 60)
        style = data.get("style", "fresh")
        ai_content = data.get("ai_content", "")
        user_id = data.get("user_id", "")

        # ── 用 DeepSeek 生成 ──
        style_map = {
            'fresh': '清新自然、亲切温暖',
            'humorous': '幽默搞笑、轻松活泼',
            'professional': '专业权威、信息量大',
        }
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

        # 获取用户产品特征（如果有）
        if user_id:
            try:
                res = http_req.get(f"{MAIN_API}/api/user/{user_id}/profile", timeout=3)
                if res.status_code == 200:
                    profile = res.json()
                    traits = profile.get("traits", [])
                    if traits:
                        trait_values = [t.get("trait_value", "") for t in traits[:5] if t.get("trait_value")]
                        if trait_values:
                            prompt += f"\n\n产品特征（融入脚本）：{'、'.join(trait_values)}"
            except Exception:
                pass

        print(f"  🎬 生成直播脚本: {product_name} / {platform} / {duration_label}")

        try:
            resp = llm.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是专业的农产品直播运营专家，擅长写接地气、有感染力的直播脚本。直接输出脚本内容，不要额外解释。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.75,
                max_tokens=2000
            )
            script = resp.choices[0].message.content.strip()
            print(f"  ✅ 直播脚本生成完毕（{len(script)}字）")

            return jsonify({
                "success": True,
                "script": script
            })

        except Exception as e:
            print(f"  ⚠️ DeepSeek 调用失败，使用模板: {e}")
            return jsonify({
                "success": True,
                "script": _generate_fallback_script(product_name, platform, duration)
            })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "script": _generate_fallback_script(
                data.get("product_name", "农产品") if 'data' in dir() else "农产品",
                data.get("platform", "抖音") if 'data' in dir() else "抖音",
                60
            )
        })


def _generate_fallback_script(product_name, platform, duration):
    """兜底脚本模板"""
    return f"""## 🎬 直播脚本 · {product_name}
**平台**：{platform} | **时长**：约{duration}秒

### 🎤 开场
[微笑，挥手] 哈喽家人们！欢迎来到我的直播间！
今天给大家带来一款超级棒的{product_name}！

### 📦 产品介绍
[展示产品] 大家看看这个品质！
🌱 纯天然种植，零污染
🥬 新鲜采摘，从田间到餐桌不超过24小时
💚 口感绝佳，营养满满

### 💬 互动环节
有没有宝宝想知道我们的{product_name}是怎么种出来的？
扣 1 告诉我！
[回复评论] 这位宝宝问得好，我来详细说说...

### 🎁 福利时间
今天直播间专属福利来啦！
原价XX元，直播间只要XX元！
前100名下单还送精美礼品一份！

### 🛒 引导下单
宝宝们赶紧点击下方购物车！
[指向下方] 就是这个链接！手慢无！
库存有限，冲冲冲！

感谢宝宝们的支持，明天同一时间再见！"""


# ─────────────── 启动 ───────────────
if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("\n" + "="*60)
    print(" Xiangyin Zhichuan - Multi-Agent Workflow Service")
    print("="*60)
    print(" http://localhost:5001")
    print()
    print("Agent Architecture:")
    print(" Orchestrator")
    print(" ├─ [Parallel] ProfileAgent -> User Profile + Memory")
    print(" ├─ [Parallel] RegionAgent -> Regional Style (Neo4j)")
    print(" ├─ [Parallel] TagPoolAgent -> Tag Library (Neo4j)")
    print(" ├─ CopywriterAgent -> Content Creation")
    print(" ├─ QAAgent -> Quality Assurance")
    print(" └─ TagSelectorAgent -> Tag Selection")
    print()
    print("API Endpoints:")
    print(" POST /api/ai/generate - Main generation")
    print(" POST /api/ai/refine - Refine content")
    print(" POST /api/ai/generate-live-script - Live script generation")
    print(" GET /api/workflow/status/{id} - Workflow status")
    print("="*60 + "\n")
    app.run(debug=True, port=5001, host='0.0.0.0')
