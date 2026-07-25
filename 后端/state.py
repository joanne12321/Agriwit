# state.py - LangGraph WorkflowState 定义
from typing import TypedDict, List, Optional, Annotated, Dict, Any
from langgraph.graph.message import add_messages


class WorkflowState(TypedDict, total=False):
    """多 Agent 营销文案生成工作流的状态"""

    # ── 请求输入 ──
    user_id: str
    platform: str
    user_input: str
    custom_tags: List[str]
    festival_hint: str
    target_user: str
    template: str
    supplemental_info: str
    word_count_target: int
    word_count_hint: str

    # ── Phase 1：并行信息收集 ──
    # ProfileAgent 输出
    product_name: str
    region_raw: str
    origin: str
    traits: List[str]
    company: str
    user_type: str
    extra_info: List[str]

    # RegionAgent 输出
    culture: str
    style_guide: str
    emotions: List[str]
    region_keywords: List[str]

    # TagPoolAgent 输出
    forbidden_words: List[str]
    platform_tags: List[dict]
    culture_tags: List[dict]
    product_attributes: List[str]
    category: str  # 产品类别

    # ── Phase 2：文案创作 + QA 循环 ──
    content: str
    content_draft: str
    qa_feedback: str
    qa_passed: bool
    qa_rounds: int

    # ── Phase 3：标签推荐 ──
    recommended_tags: List[str]

    # ── 元数据 ──
    workflow_id: str
    agent_statuses: Dict[str, Any]


# 用于 QA 路由的常量
MAX_QA_ROUNDS = 3

# 跑题检测词列表（从原 QAAgent 迁移）
OFF_TOPIC_WORDS = [
    "这个工具", "这个平台", "这个软件", "这个APP", "操作简单", "一键生成",
    "一学就会", "专为农产品设计", "帮助农户", "我们的系统"
]
