# vector_memory_v2.py - LangChain Chroma 向量存储
"""
公共 API 与旧 vector_memory.py 完全一致：
  get_vector_memory() -> VectorMemoryV2 单例
  vm.add_memory(user_id, text, source)
  vm.search_relevant(user_id, query, top_k) -> List[str]
  vm.list_memories(user_id) -> List[dict]
  vm.clear_memories(user_id)
"""
import os
import json
import hashlib
import re
from datetime import datetime
from typing import Optional, List

from langchain_chroma import Chroma
from langchain_community.embeddings import ZhipuAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

import config

PERSIST_DIR = "./chroma_data"
MEMORY_DIR = "./memory_data"
os.makedirs(PERSIST_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)

_instance: Optional["VectorMemoryV2"] = None


def get_vector_memory() -> "VectorMemoryV2":
    global _instance
    if _instance is None:
        _instance = VectorMemoryV2()
    return _instance


class VectorMemoryV2:
    """Chroma 向量存储 + JSON 备份（兼容旧数据格式）"""

    def __init__(self):
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", "。", "，", " ", ""],
        )
        # 延迟初始化 embedding（避免 import 时的 API 调用）
        self._embeddings = None
        print("[VectorMemoryV2] 初始化完成（Chroma 后端）")

    @property
    def embeddings(self):
        if self._embeddings is None:
            try:
                api_key = config.ZHIPU_API_KEY
                if not api_key:
                    raise ValueError("ZHIPU_API_KEY 未配置")
                self._embeddings = ZhipuAIEmbeddings(
                    model=config.ZHIPU_EMBEDDING_MODEL,
                    api_key=api_key,
                )
                print(f"[VectorMemoryV2] 智谱 Embedding 已连接（{config.ZHIPU_EMBEDDING_MODEL}）")
            except Exception as e:
                print(f"[VectorMemoryV2] Embedding 初始化失败：{e}，降级到关键词模式")
                self._embeddings = None
        return self._embeddings

    @property
    def vector_mode(self) -> bool:
        return self.embeddings is not None

    # ═══════════════════════════════════════════
    # 公共 API
    # ═══════════════════════════════════════════

    def add_memory(self, user_id: int, text: str, source: str = "toolbox"):
        text = text.strip()
        if not text:
            return

        print(f"[VectorMemoryV2] 写入：user={user_id}, {text[:30]}…")

        # 1. 写 JSON 备份（确保数据不丢）
        self._json_backup_add(user_id, text, source)

        # 2. 写 Chroma（如果有向量能力）
        if self.vector_mode:
            try:
                docs = self._text_splitter.create_documents(
                    texts=[text],
                    metadatas=[{"source": source, "user_id": str(user_id)}],
                )
                store = self._get_store(user_id)
                store.add_documents(docs)
                print(f"[VectorMemoryV2] 已写入 {len(docs)} 个 chunk 到 Chroma")
            except Exception as e:
                print(f"[VectorMemoryV2] Chroma 写入失败（JSON 已保存）：{e}")

    def search_relevant(self, user_id: int, query: str, top_k: int = 6) -> List[str]:
        if not query:
            return []

        # 1. 尝试向量搜索
        if self.vector_mode:
            try:
                store = self._get_store(user_id)
                results = store.similarity_search(query, k=top_k)
                if results:
                    texts = [doc.page_content for doc in results]
                    print(f"[VectorMemoryV2] 向量召回 {len(texts)} 条")
                    return texts
            except Exception as e:
                print(f"[VectorMemoryV2] 向量搜索失败，降级：{e}")

        # 2. 降级：关键词搜索
        return self._keyword_search(user_id, query, top_k)

    def list_memories(self, user_id: int) -> List[dict]:
        return [
            {"text": r["text"], "has_vector": self.vector_mode}
            for r in self._json_load(user_id)
        ]

    def clear_memories(self, user_id: int):
        # 1. 先通过 Chroma API 删除集合
        if self.vector_mode:
            try:
                store = Chroma(
                    collection_name=f"user_{user_id}_memory",
                    embedding_function=self.embeddings,
                    persist_directory=os.path.join(PERSIST_DIR, f"user_{user_id}"),
                )
                store.delete_collection()
            except Exception as e:
                print(f"[VectorMemoryV2] Chroma 删除集合失败（将强制删目录）: {e}")

        # 2. 强制删 Chroma 目录（带重试，解决文件锁问题）
        persist_path = os.path.join(PERSIST_DIR, f"user_{user_id}")
        if os.path.exists(persist_path):
            import shutil, time
            for attempt in range(3):
                try:
                    shutil.rmtree(persist_path)
                    break
                except PermissionError:
                    if attempt < 2:
                        time.sleep(0.5)
                    else:
                        print(f"[VectorMemoryV2] 清理 {persist_path} 失败（文件被占用），跳过")

        # 3. 删 JSON 备份
        json_path = self._json_path(user_id)
        if os.path.exists(json_path):
            os.remove(json_path)
        print(f"[VectorMemoryV2] 已清空 user={user_id}")

    # ═══════════════════════════════════════════
    # 内部实现
    # ═══════════════════════════════════════════

    def _file_path(self, user_id: int) -> str:
        """兼容旧 API 别名"""
        return self._json_path(user_id)

    def _get_store(self, user_id: int) -> Chroma:
        """获取用户的 Chroma 向量集合"""
        return Chroma(
            collection_name=f"user_{user_id}_memory",
            embedding_function=self.embeddings,
            persist_directory=os.path.join(PERSIST_DIR, f"user_{user_id}"),
        )

    def _json_path(self, user_id: int) -> str:
        return os.path.join(MEMORY_DIR, f"user_{user_id}.json")

    def _json_load(self, user_id: int) -> list:
        path = self._json_path(user_id)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _json_dump(self, user_id: int, records: list):
        with open(self._json_path(user_id), "w", encoding="utf-8") as f:
            json.dump(records[-300:], f, ensure_ascii=False)

    def _json_backup_add(self, user_id: int, text: str, source: str):
        records = self._json_load(user_id)
        h = hashlib.md5(text.encode()).hexdigest()
        for r in records:
            if r.get("hash") == h:
                return  # 去重
        records.append({
            "hash": h,
            "text": text,
            "source": source,
            "created_at": datetime.now().isoformat(),
        })
        self._json_dump(user_id, records)

    def _keyword_search(self, user_id: int, query: str, top_k: int) -> List[str]:
        records = self._json_load(user_id)
        words = set(w for w in re.split(r'[\s，。！？、,.]', query) if len(w) >= 2)

        def score(r):
            return sum(1 for w in words if w in r["text"])

        ranked = sorted(records, key=score, reverse=True)
        results = [r["text"] for r in ranked[:top_k] if r["text"]]
        print(f"[VectorMemoryV2] 关键词召回 {len(results)} 条")
        return results


# ============================================================
# 数据迁移脚本（从旧 JSON 迁移到 Chroma）
# ============================================================
def migrate_all():
    """将 memory_data/ 下所有旧 JSON 数据重新嵌入并写入 Chroma"""
    import glob
    vm = get_vector_memory()
    if not vm.vector_mode:
        print("[migrate] 向量模式不可用，跳过迁移")
        return

    json_files = glob.glob(os.path.join(MEMORY_DIR, "user_*.json"))
    for filepath in json_files:
        filename = os.path.basename(filepath)
        user_id = int(filename.replace("user_", "").replace(".json", ""))
        records = vm._json_load(user_id)
        for r in records:
            vm.add_memory(user_id, r["text"], r.get("source", "toolbox"))
        print(f"[migrate] user_{user_id}: {len(records)} 条已迁移")


if __name__ == "__main__":
    migrate_all()
