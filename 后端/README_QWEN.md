# Qwen 文案模型接入说明

## 1. 当前项目的模型切换

`ai_service.py` 使用 OpenAI 兼容协议。模型由环境变量控制：

```env
LLM_BASE_URL=http://127.0.0.1:8000/v1
LLM_API_KEY=EMPTY
LLM_MODEL=Qwen/Qwen3-4B-Instruct-2507
```

如果没有配置 `LLM_*`，代码仍会兼容旧的 `DEEPSEEK_API_KEY` 和
`DEEPSEEK_BASE_URL`。正式切换时建议在 `后端/.env` 中增加 `LLM_*`，
不要把模型名称写死在业务 Agent 里。

## 2. 启动 Qwen 服务

推荐在有 NVIDIA GPU 的 Linux 服务器使用 vLLM：

```bash
pip install vllm
vllm serve Qwen/Qwen3-4B-Instruct-2507 --host 0.0.0.0 --port 8000
```

本机演示也可以用 LM Studio 或 Ollama，但需要打开 OpenAI 兼容接口，
并把 `LLM_BASE_URL` 改成对应地址。先用未微调基座跑通，再加载 LoRA。

## 3. 从 Excel 导出微调数据

在 `后端` 目录执行：

```bash
python dataset_tools.py --input "../数据集_Sheet1 (1)(1).xlsx" --export-sft
```

输出：

- `dataset_corpus.json`：清洗后的文案案例库，供 `dataset_rag.py` 检索。
- `dataset_quality_report.json`：质量统计。
- `sft_train.jsonl`：训练集，默认约 90%。
- `sft_eval.jsonl`：验证集，默认约 10%。

只有标题、正文、平台、商品、品类和宣传角度完整且没有质量标记的记录
才会进入 SFT。被排除的记录仍保留在 `dataset_corpus.json`，不会丢失。

## 4. 三类数据分别放哪里

### 文案案例

```text
后端/dataset_corpus.json
```

存平台、标题、正文、商品、受众、节日、宣传角度等。它已经由
`dataset_rag.py` 做关键词检索，后续可以换成真正的 embedding 向量库。

### 农产品专业知识

建议新建：

```text
后端/knowledge/products.json
```

每个产品一个 `product_id`，字段包括产地、品种、上市季节、口感、
外观、种植/加工方式、保存方式、推荐吃法、认证、核心卖点、来源等。
知识切成较短的片段后，再生成 embedding 存到：

```text
后端/vector_store/product_knowledge/
```

原始 JSON 是可编辑的权威资料，向量文件只是检索索引，不要反过来把
向量当成原始知识。每个向量记录必须保存 `product_id`、`field`、`source`
和 `text`，这样召回后才能关联回产品。

### 用户私有信息

```text
后端/memory_data/user_<id>.json
```

这里适合放用户在注册、追问或工具箱中补充的真实卖点。它与公共产品知识
分开，避免一个用户的产地、认证或价格信息泄露给另一个用户。

## 5. Neo4j 应该放什么

当前 Neo4j 已经承担三类关系数据：

- `Platform`、`PlatformCategory`、`Tag`：平台和标签关系。
- `Region`、`CultureTag`：地域、文化和文案风格。
- `ProductCategory`、`AttributeTag`、`ForbiddenWord`：品类属性和禁用词。

建议继续把这些稳定的“关系和规则”放 Neo4j，不要把所有正文和 embedding
都塞进去。专业知识可以先放 JSON，再按需要建立图关系：

```text
(Product)-[:IN_CATEGORY]->(ProductCategory)
(Product)-[:PRODUCED_IN]->(Region)
(Product)-[:HAS_ATTRIBUTE]->(Attribute)
(Product)-[:AVAILABLE_IN]->(Season)
(Product)-[:SUITABLE_FOR]->(Audience)
(Product)-[:HAS_CERTIFICATION]->(Certification)
(Product)-[:HAS_KNOWLEDGE]->(KnowledgeChunk)
```

`KnowledgeChunk` 可以保存 `chunk_id`、`product_id`、`field`、`text`、
`source`，但向量检索仍建议由独立向量索引完成。生成文案时使用
`product_id` 先在 Neo4j 过滤真实关系，再从知识库召回文本，最后把结果
和文案案例一起交给 Qwen。

## 6. 最终生成链路

```text
用户输入
  -> Neo4j：平台规则、地域风格、标签和禁用词
  -> 文案案例库：相似平台/受众/宣传角度
  -> 产品知识库：该商品的事实和来源
  -> 用户记忆：该用户自己的真实卖点
  -> Qwen3-4B + LoRA：生成标题、正文、标签
  -> QAAgent：检查字数、禁用词和事实风险
```

