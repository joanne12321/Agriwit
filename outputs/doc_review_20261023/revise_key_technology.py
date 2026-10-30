from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from lxml import etree
import os
import tempfile

SOURCE = Path(r"D:/桌面/云稼集Agriwit/outputs/关键技术修改稿.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

SECTION = """5、技术关键
本作品围绕农业经营主体“资料分散、内容生产链条长、多物料口径难统一”的痛点，形成“知识库治理—领域模型适配—检索增强—多Agent协同—跨模态对齐—审核交付”的技术闭环。系统以企业及产品档案、营销素材、地方历史文化知识和广告法违禁词四类知识为事实底座，以Qwen3-8B领域模型承担农业营销语言理解与推文生成，以LangChain完成模型、提示模板和Skill封装，以LangGraph维护共享状态、任务依赖和审核回退，使同一营销任务中的推文、海报、视频及直播脚本能够共享事实依据、协同生产并统一核验。
5.1 农业营销知识库与训练数据构建
（1）四类知识的统一治理
项目围绕农业营销场景完成10000条领域数据的清洗、去重、分类、标注和版本化管理，并按照用途纳入企业及产品档案、营销素材、地方历史文化知识、广告法违禁词四类知识库。企业及产品档案保存企业文化、品牌故事、资质荣誉、产品名称、产地、规格、生产工艺及授权实拍素材；营销素材保存经筛选的推文结构、海报样式、镜头范式和平台表达规则；地方历史文化知识记录产区历史、传统技艺、民俗节庆和地理标志背景；广告法违禁词知识保存禁限用表述、适用平台、风险等级及替换建议。每条知识均配置knowledge_id、tenant_id、product_id、source_id、更新时间、适用范围和审核状态，实现来源可追溯、企业间隔离和内容可更新。
（2）8000条训练样本构建
从知识库中筛选8000条高质量样本用于领域模型训练，覆盖产品事实抽取、卖点提炼、平台推文生成、直播脚本生成、约束遵循和错误纠正六类任务。样本统一组织为“任务指令—输入资料—约束条件—目标输出—来源编号”结构，并由人工完成事实校验、表达审校与敏感表述检查。训练集、验证集和测试集按照企业或产品系列划分，防止同一产品的近似改写跨集合造成数据泄漏；测试集保留未见企业及资料不完整任务，用于检验模型对缺失证据、冲突信息和禁限用表达的处理能力。
（3）知识加工与索引
文本资料按语义边界切分为可检索知识块，保留标题、正文、来源、适用产品及有效状态等元数据；企业、产品、规格、产地、认证和素材等实体建立关系映射；图片与视频素材记录产品编号、拍摄时间、授权范围、可编辑范围和视觉特征。清洗阶段依次执行编码统一、重复检测、字段规范化、实体消歧、敏感信息处理和人工复核，使训练数据、检索知识和审核依据共享同一数据口径。
5.2 基于Qwen3-8B的农业营销领域模型微调
项目统一选用Qwen3-8B作为文本基座模型，采用监督微调（SFT）与LoRA低秩适配构建农业营销领域模型。微调重点不是记忆价格、库存等易变事实，而是学习农业产品信息的组织方式、卖点提炼逻辑、不同平台的内容结构、营销语言风格以及缺少证据时的拒绝与提示策略。
LoRA冻结Qwen3-8B基座权重，仅在注意力投影层注入低秩可训练矩阵，其参数更新公式为：
【此处保留原3.1中的LoRA公式，由你粘贴公式】
其中，r为低秩维度，A、B为可训练矩阵，α为缩放系数。训练配置以r=16、α=32、dropout=0.05、学习率2×10⁻⁴、最大序列长度4096为基础，通过验证集选择训练轮次与最优检查点。训练过程中使用混合精度和梯度累积控制显存占用，并仅对目标输出部分计算损失，使模型集中学习营销任务的回答格式与约束遵循。
训练流程包括数据与样本准备、LoRA监督微调、验证与独立测试、适配器导出四个阶段。模型版本同时绑定基座版本、数据版本、提示模板版本及训练参数；完成训练后保存LoRA适配器并接入推文Agent。推理时，Qwen3-8B领域模型负责卖点组织和文本表达，具体产品事实则由知识库检索动态注入，实现“领域表达能力”和“企业实时事实”的分离，避免将流畅表达等同于事实依据。
模型效果从关键字段保留率、指令遵循率、违禁词命中率、无依据表述率、平台结构完整度和人工修改量六个维度进行评价，并与未微调Qwen3-8B进行同任务对照。该设计使模型形成稳定的农产品营销表达能力，同时能够配合知识库完成企业级个性化生成。
模型微调流程如下图所示。
5.3 知识库管理与RAG检索增强
（1）企业与产品定位
系统接收product_id、tenant_id及任务类型后，首先校验资料归属和访问权限，读取对应企业及产品档案、已授权素材和当前有效字段。名称、产地、规格、价格、库存、认证有效期等可核验信息由结构化档案直接提供，不依赖语义相似度推断，从入口处避免不同企业、不同规格和不同包装资料混用。
（2）混合检索与证据融合
LangChain将检索能力封装为KnowledgeRetrievalSkill。ChromaDB保存企业资料、地方文化知识、营销案例和平台规则的向量索引，Neo4j保存“企业—销售—产品”“产品—具有—规格”“认证—适用于—产品”“素材—展示—产品”等关系。执行时先按tenant_id、product_id、有效状态和授权范围过滤，再并行获取语义候选与图谱关联证据；候选经去重、相关性排序和长度控制后形成evidence_list，每条证据携带source_id、claim_id和置信状态。
（3）冲突检测与增强生成
EvidenceOrganizerSkill对企业档案、结构化字段及检索结果进行交叉核对：企业确认资料作为第一事实来源，行业常识仅用于补充背景；资料冲突或关键字段缺失时触发补充确认节点，不允许模型自行选择。整理后的证据被注入Qwen3-8B生成上下文，同时将forbidden_claims、平台规则和引用编号写入约束区，生成结果中的关键卖点能够追溯到具体证据。该流程形成“产品与任务定位—ChromaDB/Neo4j混合检索—证据整理与确认—增强生成与审核”的闭环。
5.4 基于LangChain与LangGraph的多Agent Skill编排
系统基于LangChain封装大模型、提示模板、结构化输出解析器及工具调用接口，基于LangGraph构建有向状态图。共享状态统一保存task_id、需求简报、证据列表、素材清单、各Agent产物、审核问题、执行次数和成本信息。Orchestrator按照依赖关系调度节点：需求解析与知识检索先行，推文和脚本在需求简报确认后并行执行，海报依赖关键文案字段和产品实拍素材，视频依赖分镜脚本及授权素材；审核Agent对所有分支汇总检查，问题只回退至对应节点，单节点最多自动修订两轮，仍存在冲突时转人工确认。
（1）需求解析Agent
需求解析Agent以用户表单、自然语言补充和所选产品为输入，调用Qwen3-8B通用指令能力及RequirementParsingSkill，将目标平台、目标人群、营销场景、内容类型、视觉风格、时长和成本偏好解析为结构化字段。随后调用SchemaValidationSkill检查必填项、字段类型和枚举值，并把产品标识、任务标识和权限范围写入LangGraph共享状态。信息不完整时，该Agent生成最小补充问题；字段完整后输出统一需求简报，作为全部生产Agent的唯一任务入口。
（2）知识检索Agent
知识检索Agent读取需求简报中的tenant_id、product_id和任务意图，通过ChromaDBRetrieverSkill执行语义检索，通过Neo4jQuerySkill查询企业、产品、规格、认证、文化和素材之间的关系，再调用EvidenceOrganizerSkill完成去重、冲突检测、时效校验和证据排序。该Agent不直接撰写营销内容，而是输出verified_claims、forbidden_claims、evidence_list和asset_manifest，确保后续Agent使用相同事实依据。
（3）推文Agent
推文Agent加载经8000条样本LoRA微调后的Qwen3-8B农业营销领域模型，是领域模型的核心应用节点。其输入为需求简报、已核验卖点、平台规则及参考营销素材，依次调用PlatformTemplateSkill确定小红书、微信公众号、微博等平台结构，调用CopyGenerationSkill生成标题、正文、行动引导和标签，再调用CopyRewriteSkill根据用户反馈局部改写。输出通过JSON Schema固定为title、body、tags、claim_refs和platform_version，关键表达与证据编号绑定，既保持品牌差异化，也防止生成无依据的认证、功效和产地信息。
（4）海报Agent
海报Agent使用具备图文理解能力的多模态大模型分析产品实拍、包装形态和参考版式，并通过ImageGenerationSkill调用可控图像生成模型完成背景与辅助场景，通过AssetMatchingSkill锁定与product_id一致的授权主体素材，通过LayoutCompositionSkill完成画布比例、主体位置、留白和信息层级设计。产品名称、规格、价格及活动字段不交由图像模型绘制，而由确定性排版工具叠加，以避免中文错字和数字失真。该Agent输出海报图、layout_json、素材引用和字段坐标，为OCR审核和多平台裁切提供依据。
（5）脚本Agent
脚本Agent调用Qwen3-8B，根据需求简报、推文核心卖点、产品素材清单和目标时长规划视频与直播叙事。StoryboardGenerationSkill将脚本拆分为镜头编号、时长、画面描述、素材编号、口播、字幕和转场；DurationValidationSkill累计镜头时长并校验口播字数；AssetCoverageSkill检查每个关键画面是否有可用素材。视频脚本强调开场吸引、产品展示、工艺或场景说明和收束行动，直播脚本进一步生成开场、卖点讲解、互动问答、节奏提示与收尾话术，并保持所有事实字段与证据一致。
（6）视频Agent
视频Agent依据结构化分镜调用AssetProcessingSkill完成授权素材裁切、比例适配、清晰度处理和镜头排序，调用SpeechSynthesisSkill生成与品牌风格一致的口播，调用SubtitleCompositionSkill生成字幕时间轴，并通过VideoCompositionSkill完成配音、字幕、转场和背景音乐合成。当素材不足时，调用ShotListSkill返回具体补拍清单；需要生成式镜头时，通过AsyncVideoGenerationSkill提交参考图、动作、长度、画幅和产品约束，保存job_id并异步轮询任务状态。成片输出同时携带素材溯源、字幕文件和分镜映射，保证视频可以继续编辑和审核。
（7）审核Agent
审核Agent采用规则引擎、Qwen3-8B和视觉语言模型协同审核。FactCheckSkill将推文、脚本、OCR文本和口播转写中的名称、产地、规格、认证、价格等字段与知识库逐项比对；ComplianceCheckSkill匹配广告法违禁词及平台规则；OCRValidationSkill校验海报和视频关键帧文字；VisualConsistencySkill检查产品形态、包装、主体图与档案是否一致。审核结果以issue_id、severity、target_node、evidence_id和repair_instruction输出，LangGraph据此路由至推文、海报、脚本或视频节点局部修订，避免整套内容重复生成。
（8）交付决策Agent
交付决策Agent只接收审核通过的候选版本，通过CandidateRankingSkill综合平台适配度、品牌一致性、预计编辑工作量、生产成本和用户历史偏好进行透明排序，输出推荐版本及可解释理由。随后调用PackageDeliverySkill核对推文、海报、视频、直播脚本、字幕和来源清单是否齐全，生成统一命名的交付包并写入版本库。用户修改与最终采纳结果回写任务状态，为后续同类任务的模板选择和排序提供依据。
（9）Skill契约与运行控制
每个Skill均采用统一契约描述name、input_schema、output_schema、timeout、retry_policy、cost_estimate和error_code。Agent提出工具调用后，执行器依次完成JSON Schema校验、身份与资料范围校验、预算校验和幂等性检查，再将结果写回LangGraph状态。模型版本、提示模板哈希、检索证据、工具输入输出、重试次数和审核原因均写入任务日志；资料中的文字仅作为数据，不被解释为工具调用指令。该机制将多Agent协作从简单串联提升为可追踪、可回退、可复用的工程化生产流程。
各Agent的具体职责与Skill配置见表2。
表2 多Agent职责与技能分配
Agent｜核心模型｜关键输入与输出｜主要Skill｜编排关系
需求解析Agent｜Qwen3-8B｜用户需求→需求简报｜需求解析、结构校验｜首节点，缺项转人工补充
知识检索Agent｜Qwen3-8B+RAG｜需求简报→证据与素材清单｜ChromaDB检索、Neo4j查询、证据整理｜先于所有生成节点
推文Agent｜LoRA微调Qwen3-8B｜证据化简报→标题、正文、标签｜平台模板、推文生成、局部改写｜与脚本Agent并行
海报Agent｜多模态大模型+图像生成模型｜简报与实拍→海报及版式描述｜素材匹配、背景生成、确定性排版｜依赖关键文案字段
脚本Agent｜Qwen3-8B｜简报与素材→分镜、字幕、口播｜分镜生成、素材覆盖、时长校验｜与推文Agent并行
视频Agent｜视频生成模型+语音模型｜分镜与素材→成片及字幕文件｜素材处理、语音合成、异步视频、剪辑合成｜依赖脚本及授权素材
审核Agent｜Qwen3-8B+视觉语言模型｜全部物料与证据→问题清单及状态｜字段比对、合规检查、OCR、视觉一致性｜失败定向回退对应节点
交付决策Agent｜Qwen3-8B+规则评分｜合格候选→推荐版本及交付包｜候选排序、版本管理、打包交付｜终节点，保留人工确认
多Agent围绕共享状态协同执行，资料补充、节点修订、人工确认和版本归档均通过LangGraph条件边连接，整体工作流程如图4所示。
图4 多Agent与Skill协同生产工作流
5.5 基于需求简报的多模态生成与跨模态对齐
同一营销任务需要同时生成推文、海报、视频和直播脚本。若各Agent分别理解原始需求，容易出现卖点变化、规格不一致、包装错用和视觉风格分裂。系统因此将“需求简报”设计为跨模态协同的中间表示，并把对齐过程落实到输入、生成、审核三个阶段。
（1）统一需求简报
需求解析Agent将用户输入与知识检索结果合并为版本化JSON需求简报，核心字段包括brief_id、product_identity、verified_claims、evidence_refs、audience、platform、scene、content_goals、visual_constraints、asset_refs、forbidden_claims和brand_style。产品名称、产地、规格、加工形态、认证和包装属于硬约束；色调、构图、镜头节奏和叙事顺序属于软约束。所有Agent只读取同一brief_id，简报更新后由LangGraph使受影响节点失效并按依赖重新执行，防止不同版本资料同时进入生产链。
（2）文本与视觉条件映射
推文Agent将verified_claims映射为标题、正文与标签；海报Agent将product_identity、visual_constraints和asset_refs转换为主体参考、场景提示和版式参数；脚本Agent将content_goals、scene和素材清单展开为结构化分镜；视频Agent再将每个镜头映射到具体素材、口播、字幕和时长。每项可核验内容均保留claim_id与evidence_id，每个视觉元素保留asset_id，使“文案中的卖点—海报中的文字与主体—视频中的镜头与口播”形成可追踪关系。
（3）产品身份与视觉风格对齐
海报和视频优先复用同一组产品实拍与品牌视觉参数，通过参考图约束产品外观、包装颜色、Logo位置和产品形态；生成模型主要负责背景、辅助场景与转场镜头。标题、规格和价格由确定性工具排版，视频字幕从已确认文案和分镜自动生成。系统在需求简报中统一色板、字体层级、构图关键词、镜头节奏和禁用视觉元素，使静态海报与动态视频既保持品牌风格一致，又不改变产品真实外观。
（4）跨模态一致性审核与定向修订
生成完成后，审核Agent抽取推文、海报OCR文本、视频字幕和口播中的实体与字段，同知识库档案逐项比对；视觉语言模型辅助识别产品主体、包装和画面动作，语义模型检查不同物料是否围绕同一受众、场景与核心卖点。事实硬约束失败时直接退回对应Agent，风格评分不能抵消事实错误；审核通过后才进入候选排序与交付。以生板栗为例，若档案没有熟制或即食证据，推文、海报和视频均不得呈现“开袋即食”场景。该机制实现“同一需求简报、同一事实来源、分支专业生成、跨模态交叉核验”的完整对齐闭环。
5.6 前端交互与多平台预览
（1）产品资料与宣传需求的引导式输入
系统将产品登记与宣传任务设置分为两个环节。产品登记页面引导用户录入名称、品类、产地、规格、特点、资质及授权素材，保存后形成可重复调用的产品档案。宣传需求页面通过平台、风格、节日、产品类型、目标用户和宣传场景等选项收集任务条件，并允许补充自然语言、图片和语音。前端将这些信息与product_id组合提交给需求解析Agent，形成结构化需求简报，降低农业经营者编写复杂提示词的门槛。
（2）生成、编辑与预览状态同步
前端依据LangGraph任务状态分别展示推文、海报、脚本和视频的排队、执行、审核、退回和完成状态，并通过task_id订阅长耗时任务进度。用户对标题、画面或镜头提出修改时，系统只更新对应节点及其下游依赖，已通过审核且不受影响的成果继续保留。多平台预览按照各平台尺寸和内容结构展示文字截断、图片裁切和视频画幅效果，确保页面预览、在线修改与最终导出使用同一成果版本。
5.7 后端存储、异步处理与成果交付
（1）企业档案与媒体素材的关联存储
后端以tenant_id、product_id、asset_id和version_id建立知识、产品、素材与成果之间的关联。结构化字段存入业务数据库，长文本与向量索引写入ChromaDB，实体关系写入Neo4j，图片、音频和视频写入对象存储；元数据统一记录归属、来源、授权范围、校验状态和更新时间。四类知识库通过统一接口向检索Agent和审核Agent提供查询服务，并利用租户隔离保证企业资料只在授权任务范围内使用。
（2）LangGraph任务调度与异步处理
后端将多Agent生产流程实现为LangGraph状态图，以条件边表达依赖、并行、审核回退和人工确认。推文与脚本节点并行执行，海报等待关键文案字段确认，视频等待脚本和素材就绪；图像、语音和视频等长耗时调用进入异步队列，返回job_id并通过状态查询更新共享状态。每个节点使用task_id与node_id组成幂等键，重试时复用已完成成果，避免重复扣费和整组任务重新生成。
（3）权限、预算与可观测性控制
LangChain工具执行器在调用前校验用户身份、租户范围、Skill白名单、参数Schema和任务预算，模型服务密钥仅保存在服务端。日志记录请求链路、模型版本、提示模板哈希、知识证据、工具耗时、费用估算、重试和审核原因，支持从最终物料追溯到需求简报、证据和Agent节点。对外部生成服务设置超时、熔断和降级策略，单节点超过自动修订次数后转入人工处理。
（4）成果版本管理与打包交付
后端以task_id关联推文、海报、脚本、视频、字幕、版式描述和审核报告，保存候选版本、父版本及用户确认状态。交付决策Agent选定候选后，系统核对物料完整性和审核状态，按“企业—产品—平台—任务日期—版本”统一命名并打包，同时生成成果清单与证据索引。用户的最终选择和修改反馈写回版本库，用于下一轮需求简报生成、模板推荐和候选排序。
6、主要技术指标
（1）领域知识与训练数据规模
系统完成10000条农业营销领域数据的统一治理，形成企业及产品档案、营销素材、地方历史文化知识、广告法违禁词四类知识库；其中筛选8000条高质量指令样本用于Qwen3-8B领域模型训练。
（2）领域模型能力
采用监督微调与LoRA低秩适配，形成面向产品事实理解、卖点提炼、平台推文、直播脚本和约束纠错的农业营销领域模型，并实现基座、适配器、数据及提示模板的版本关联。
（3）多Agent协同生产
基于LangChain与LangGraph完成需求解析、知识检索、推文、海报、脚本、视频、审核和交付决策八类Agent编排，支持并行执行、依赖调度、定向回退、人工确认和幂等重试。
（4）多模态对齐与审核
通过版本化需求简报统一产品身份、已核验卖点、品牌风格和素材引用；结合字段比对、广告合规检查、OCR与视觉语言模型，审核推文、海报、视频和直播脚本的事实与表达一致性。
（5）知识与成果管理
支持企业资料隔离、知识版本更新、ChromaDB/Neo4j混合检索、异步任务状态查询、多平台预览、成果版本管理和一键打包交付，形成从资料录入到成套物料交付的完整生产链路。"""


def visible_text(p):
    return "".join(t.text or "" for t in p.findall(".//" + W + "t"))


def set_paragraph_text(p, value):
    ppr = p.find(W + "pPr")
    keep_ppr = deepcopy(ppr) if ppr is not None else None
    first_rpr = p.find(".//" + W + "rPr")
    keep_rpr = deepcopy(first_rpr) if first_rpr is not None else None
    for child in list(p):
        p.remove(child)
    if keep_ppr is not None:
        p.append(keep_ppr)
    run = etree.SubElement(p, W + "r")
    if keep_rpr is not None:
        run.append(keep_rpr)
    text = etree.SubElement(run, W + "t")
    text.text = value


def make_paragraph(template, value):
    p = deepcopy(template)
    set_paragraph_text(p, value)
    return p


with ZipFile(SOURCE, "r") as archive:
    data = {name: archive.read(name) for name in archive.namelist()}

root = etree.fromstring(data["word/document.xml"])
target_cell = None
for cell in root.findall(".//" + W + "tc"):
    if any(visible_text(p).startswith("5.1 农业营销数据集构建与处理") for p in cell.findall(".//" + W + "p")):
        target_cell = cell
        break
if target_cell is None:
    raise RuntimeError("Target technical section not found")

paragraphs = target_cell.findall(".//" + W + "p")
start = next(i for i, p in enumerate(paragraphs) if visible_text(p).startswith("5.1 农业营销数据集构建与处理"))
end = len(paragraphs)

# Keep the existing model workflow and system UI figures by moving their drawing paragraphs
# into the revised section at the corresponding captions.
model_drawings = []
for p in paragraphs[start:end]:
    ids = [b.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed") for b in p.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip")]
    if "rId9" in ids:
        model_drawings.append(deepcopy(p))
workflow_drawing = next((deepcopy(p) for p in paragraphs[start:end] if p.find(".//" + W + "drawing") is not None and any(b.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed") == "rId10" for b in p.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip"))), None)
ui_drawings = []
for p in paragraphs[start:end]:
    ids = [b.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed") for b in p.findall(".//{http://schemas.openxmlformats.org/drawingml/2006/main}blip")]
    if any(rid in {"rId11", "rId12"} for rid in ids):
        ui_drawings.append(deepcopy(p))

template = paragraphs[start]
parent = paragraphs[start].getparent()
insert_at = parent.index(paragraphs[start])
for p in paragraphs[start:end]:
    p.getparent().remove(p)

new_nodes = []
for line in SECTION.splitlines():
    new_nodes.append(make_paragraph(template, line))
    if line == "模型微调流程如下图所示。":
        new_nodes.extend(deepcopy(x) for x in model_drawings)
    if line == "多Agent围绕共享状态协同执行，资料补充、节点修订、人工确认和版本归档均通过LangGraph条件边连接，整体工作流程如图4所示。" and workflow_drawing is not None:
        new_nodes.append(deepcopy(workflow_drawing))
    if line == "（2）生成、编辑与预览状态同步":
        new_nodes.extend(deepcopy(x) for x in ui_drawings)

for offset, node in enumerate(new_nodes):
    parent.insert(insert_at + offset, node)

# The same figures are referenced only once in the replacement section.
data["word/document.xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")

fd, tmp_name = tempfile.mkstemp(suffix=".docx", dir=str(SOURCE.parent))
os.close(fd)
try:
    with ZipFile(tmp_name, "w", ZIP_DEFLATED) as archive:
        for name, payload in data.items():
            archive.writestr(name, payload)
    os.replace(tmp_name, SOURCE)
finally:
    if os.path.exists(tmp_name):
        os.unlink(tmp_name)

print(f"Revised: {SOURCE}")
