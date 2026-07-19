# vector_memory.py - 智谱AI embedding 版本
import os
import json
import hashlib
import numpy as np
from datetime import datetime
from typing import Optional, List
import re

# Prefer environment variables so keys do not leak into source code or slides.
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
MEMORY_DIR    = "./memory_data"
os.makedirs(MEMORY_DIR, exist_ok=True)

_instance: Optional["VectorMemory"] = None

def get_vector_memory() -> "VectorMemory":
    global _instance
    if _instance is None:
        _instance = VectorMemory()
    return _instance


class VectorMemory:

    def __init__(self):
        self.mode = "fallback"
        self.client = None
        self._try_init()

    def _try_init(self):
        if not ZHIPU_API_KEY or ZHIPU_API_KEY.strip() == "":
            print("[VectorMemory] ⚠️  未填写 API Key，使用关键词匹配模式")
            return
        try:
            from zhipuai import ZhipuAI
            self.client = ZhipuAI(api_key=ZHIPU_API_KEY)
            # 测试连通性
            test = self.client.embeddings.create(
                model="embedding-3",
                input=["测试"]
            )
            dim = len(test.data[0].embedding)
            self.mode = "zhipu"
            print(f"[VectorMemory] ✅ 智谱AI连接成功！向量维度：{dim}")
        except ImportError:
            print("[VectorMemory] ⚠️  未安装 SDK，请运行：pip install zhipuai --break-system-packages")
        except Exception as e:
            print(f"[VectorMemory] ⚠️  连接失败：{e}")

    # ════════════ 对外接口 ════════════

    def add_memory(self, user_id: int, text: str, source: str = "toolbox"):
        text = text.strip()
        if not text:
            return
        print(f"[VectorMemory] 写入：user={user_id}, {text[:30]}…")
        if self.mode == "zhipu":
            try:
                vector = self._get_embedding(text)
                self._save(user_id, text, vector, source)
                return
            except Exception as e:
                print(f"[VectorMemory] 写入失败降级：{e}")
        self._save(user_id, text, None, source)

    def search_relevant(self, user_id: int, query: str, top_k: int = 6) -> List[str]:
        if not query:
            return []
        if self.mode == "zhipu":
            try:
                return self._vector_search(user_id, query, top_k)
            except Exception as e:
                print(f"[VectorMemory] 向量搜索失败降级：{e}")
        return self._keyword_search(user_id, query, top_k)

    # ════════════ 内部实现 ════════════

    def _get_embedding(self, text: str) -> List[float]:
        resp = self.client.embeddings.create(
            model="embedding-3",
            input=[text[:500]]
        )
        return resp.data[0].embedding

    def _file_path(self, user_id: int) -> str:
        return os.path.join(MEMORY_DIR, f"user_{user_id}.json")

    def _load(self, user_id: int) -> list:
        path = self._file_path(user_id)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _dump(self, user_id: int, records: list):
        with open(self._file_path(user_id), "w", encoding="utf-8") as f:
            json.dump(records[-300:], f, ensure_ascii=False)

    def _save(self, user_id: int, text: str, vector, source: str):
        records = self._load(user_id)
        h = hashlib.md5(text.encode()).hexdigest()
        # 去重
        for r in records:
            if r.get("hash") == h:
                # 如果之前没向量，现在有了，就更新
                if vector and not r.get("vector"):
                    r["vector"] = vector
                    self._dump(user_id, records)
                return
        records.append({
            "hash":       h,
            "text":       text,
            "source":     source,
            "vector":     vector,
            "created_at": datetime.now().isoformat()
        })
        self._dump(user_id, records)
        print(f"[VectorMemory] ✅ 已保存（共 {len(records)} 条）")

    def _vector_search(self, user_id: int, query: str, top_k: int) -> List[str]:
        records = self._load(user_id)
        with_vec = [r for r in records if r.get("vector")]
        if not with_vec:
            return self._keyword_search(user_id, query, top_k)

        q_vec  = np.array(self._get_embedding(query))
        matrix = np.array([r["vector"] for r in with_vec])

        # 余弦相似度
        q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-8)
        m_norm = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
        scores = m_norm @ q_norm

        top_idx = np.argsort(scores)[::-1][:top_k]
        results = [with_vec[i]["text"] for i in top_idx if scores[i] > 0.3]
        print(f"[VectorMemory] ✅ 向量召回 {len(results)} 条")
        return results

    def _keyword_search(self, user_id: int, query: str, top_k: int) -> List[str]:
        records = self._load(user_id)
        words = set(w for w in re.split(r'[\s，。！？、,.]', query) if len(w) >= 2)

        def score(r):
            return sum(1 for w in words if w in r["text"])

        ranked = sorted(records, key=score, reverse=True)
        results = [r["text"] for r in ranked[:top_k] if r["text"]]
        print(f"[VectorMemory] 关键词召回 {len(results)} 条")
        return results

    # ════════════ 调试工具 ════════════

    def list_memories(self, user_id: int) -> List[dict]:
        return [{"text": r["text"], "has_vector": bool(r.get("vector"))}
                for r in self._load(user_id)]

    def clear_memories(self, user_id: int):
        path = self._file_path(user_id)
        if os.path.exists(path):
            os.remove(path)
            print(f"[VectorMemory] 已清空 user={user_id}")
