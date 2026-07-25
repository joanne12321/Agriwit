# config.py - LangChain 版中心化配置
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env（确保在项目根目录下运行）
load_dotenv(Path(__file__).parent / ".env", override=True)

# ===== DeepSeek LLM（通过 OpenAI 兼容接口）=====
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"

# ===== Neo4j =====
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "")

# ===== 内部服务 =====
MAIN_API = "http://localhost:5000"
TAG_API = "http://localhost:5002"

# ===== 智谱 AI（向量嵌入）=====
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", os.getenv("GLM_API_KEY", ""))
ZHIPU_EMBEDDING_MODEL = "embedding-3"

# ===== 地域映射（从原 ai_service.py 迁移）=====
REGION_MAP = {
    '梅州': '客家文化区', '河源': '客家文化区', '惠州': '客家文化区', '韶关': '客家文化区', '清远': '客家文化区',
    '广州': '广府文化区', '佛山': '广府文化区', '肇庆': '广府文化区', '江门': '广府文化区',
    '中山': '广府文化区', '珠海': '广府文化区', '东莞': '广府文化区', '深圳': '广府文化区',
    '潮州': '潮汕文化区', '汕头': '潮汕文化区', '揭阳': '潮汕文化区', '汕尾': '潮汕文化区',
    '湛江': '粤西/滨海区', '茂名': '粤西/滨海区', '阳江': '粤西/滨海区', '云浮': '粤西/滨海区',
    '山东': '华东地区', '济南': '华东地区', '青岛': '华东地区',
    '江苏': '华东地区', '南京': '华东地区', '苏州': '华东地区',
    '浙江': '华东地区', '杭州': '华东地区', '宁波': '华东地区',
    '上海': '华东地区', '安徽': '华东地区', '福建': '华东地区', '厦门': '华东地区',
    '湖南': '华中地区', '长沙': '华中地区', '湖北': '华中地区', '武汉': '华中地区',
    '河南': '华中地区', '郑州': '华中地区', '江西': '华中地区', '南昌': '华中地区',
    '四川': '西南地区', '成都': '西南地区', '重庆': '西南地区',
    '云南': '西南地区', '昆明': '西南地区', '贵州': '西南地区', '贵阳': '西南地区',
    '陕西': '西北地区', '西安': '西北地区', '甘肃': '西北地区', '宁夏': '西北地区',
    '青海': '西北地区', '新疆': '西北地区', '乌鲁木齐': '西北地区',
    '辽宁': '东北地区', '沈阳': '东北地区', '大连': '东北地区',
    '吉林': '东北地区', '长春': '东北地区', '黑龙江': '东北地区', '哈尔滨': '东北地区',
    '北京': '华北地区', '天津': '华北地区', '河北': '华北地区', '石家庄': '华北地区',
    '山西': '华北地区', '太原': '华北地区', '内蒙古': '华北地区',
}

REGION_STYLES = {
    '客家文化区': '强调"纯净""原生态""大山的馈赠"，语气朴实有温度',
    '广府文化区': '强调"讲究""精细""老字号"，注重品质感',
    '潮汕文化区': '强调"极度新鲜""工匠精神"，重视传统工艺',
    '粤西/滨海区': '强调"阳光充足""滨海风味"，语气热情',
    '华东地区': '强调"精致""品质""江南风味"，语气细腻',
    '西南地区': '强调"山珍""生态好物"，语气神秘有吸引力',
    '东北地区': '强调"实在量大""东北特色"，语气豪爽直接',
}

PLATFORM_HINTS = {
    "抖音": "文案要口语化、短平快，像朋友聊天一样自然，适合短视频，适当添加#话题标签，控制在80-120字，语气活泼亲切，增加情感共鸣和呼吁行动",
    "淘宝": "突出卖点，关键信息前置，使用✅等符号增强可读性，结构清晰（优点+特点+保障），便于用户快速决策，增加信任感和购买欲望",
    "小红书": "故事性强，情感丰富，分段清晰，增加生活场景描述、个人感受和真实体验，语气温柔有温度，适合种草和分享",
    "微博": "短小精悍，适合快速传播，添加热点元素，增强互动性，语言简洁有力",
    "头条": "资讯风格，标题吸引人，正文分段清晰，突出实用信息和干货，逻辑性强",
}

# ===== LLM 实例工厂 =====
from langchain_openai import ChatOpenAI

def get_llm(temperature: float = 0.7, max_tokens: int = 500) -> ChatOpenAI:
    """获取 DeepSeek LLM 实例（通过 OpenAI 兼容接口）"""
    return ChatOpenAI(
        model=DEEPSEEK_MODEL,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=temperature,
        max_tokens=max_tokens,
    )

# ===== Neo4j Driver（懒加载单例）=====
_neo4j_driver = None

def get_neo4j_driver():
    global _neo4j_driver
    if _neo4j_driver is None:
        from neo4j import GraphDatabase
        _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        print(f"[config] Neo4j 连接已初始化：{NEO4J_URI}")
    return _neo4j_driver

print(f"[config] 配置加载完成")
print(f"  DeepSeek: {'已配置' if DEEPSEEK_API_KEY else '未配置'}")
print(f"  Neo4j: {NEO4J_URI}")
print(f"  智谱AI: {'已配置' if ZHIPU_API_KEY else '未配置'}")
