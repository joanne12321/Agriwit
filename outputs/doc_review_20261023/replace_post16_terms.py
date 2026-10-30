from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from lxml import etree
import os
import tempfile

SOURCE = Path(r"D:/桌面/云稼集Agriwit/outputs/关键技术修改稿.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

replacements = {
    "构建以广东特色农产品为重点的领域数据集": "构建面向农产品营销的领域知识库与训练数据集",
    "项目构建了以广东地理标志农产品为重点的领域数据集，整理三千余条资料，涵盖茶叶、板栗、荔枝、龙眼等品类的产地背景、产品特点、地域文化和生产加工知识，并补充营销文案与宣传规范。数据经清洗、去重、分类及来源标注，为领域模型微调、知识检索和内容审核提供支持，也为后续类似应用的研究提供了宝贵的数据资源。": "项目完成10000条农业营销领域数据治理，形成企业及产品档案、营销素材、地方历史文化知识、广告法违禁词四类知识库；其中筛选8000条高质量指令样本用于Qwen3-8B监督微调。数据经清洗、去重、分类、实体关联及来源标注，为领域模型、RAG检索、内容审核和跨模态对齐提供统一的数据底座，也为后续扩展更多地域与品类保留标准化接口。",
    "以共享创意简报连接文案、海报、视频和直播脚本": "以共享需求简报连接推文、海报、视频和直播脚本",
    "通过多Agent共享创意简报协调不同物料": "通过LangGraph组织多Agent共享需求简报并协调不同物料",
    "创意简报": "需求简报",
}


def paragraph_text(p):
    return "".join(t.text or "" for t in p.findall(".//" + W + "t"))


with ZipFile(SOURCE, "r") as archive:
    data = {name: archive.read(name) for name in archive.namelist()}
root = etree.fromstring(data["word/document.xml"])

for p in root.findall(".//" + W + "p"):
    value = paragraph_text(p)
    updated = value
    for old, new in replacements.items():
        updated = updated.replace(old, new)
    if updated == value:
        continue
    texts = p.findall(".//" + W + "t")
    if not texts:
        continue
    texts[0].text = updated
    for t in texts[1:]:
        t.text = ""

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
print("Terms aligned")
