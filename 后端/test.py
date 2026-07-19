# test_zhipu.py
from zhipuai import ZhipuAI

API_KEY = "f81a67e2edcd40bb987a71d40ac1f97d.zPRsMirvx9pHRWJF"

client = ZhipuAI(api_key=API_KEY)
response = client.embeddings.create(
    model="embedding-3",
    input="梅州客家板栗，软糯香甜"
)
vec = response.data[0].embedding
print(f"✅ 成功！向量维度：{len(vec)}")
