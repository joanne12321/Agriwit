from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import json

SOURCE = Path(r"D:/桌面/半修改版内有修改指示(1).docx")
OUT = Path(r"D:/桌面/云稼集Agriwit/outputs/doc_review_20261023")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

def node_text(node):
    parts = []
    for child in node.iter():
        # Reconstruct the version visible after accepting tracked changes.
        if child.tag == W + "t" and child.text:
            parts.append(child.text)
        elif child.tag == W + "tab":
            parts.append("\t")
        elif child.tag in (W + "br", W + "cr"):
            parts.append("\n")
    return "".join(parts).strip()

with ZipFile(SOURCE) as archive:
    document = ET.fromstring(archive.read("word/document.xml"))
    styles = ET.fromstring(archive.read("word/styles.xml"))
    style_names = {}
    for style in styles.findall(W + "style"):
        sid = style.get(W + "styleId", "")
        name = style.find(W + "name")
        style_names[sid] = name.get(W + "val", sid) if name is not None else sid
    body = document.find(W + "body")
    records, tables = [], []
    paragraph_index = 0
    for child in body:
        if child.tag == W + "p":
            paragraph_index += 1
            value = node_text(child)
            ppr = child.find(W + "pPr")
            pstyle = ppr.find(W + "pStyle") if ppr is not None else None
            sid = pstyle.get(W + "val", "") if pstyle is not None else ""
            if value:
                records.append({"index": paragraph_index, "style_id": sid, "style": style_names.get(sid, sid), "text": value})
        elif child.tag == W + "tbl":
            rows = [[node_text(tc) for tc in tr.findall(W + "tc")] for tr in child.findall(W + "tr")]
            tables.append({"table": len(tables) + 1, "rows": rows})
    changes = {
        "insertions": len(document.findall(".//" + W + "ins")),
        "deletions": len(document.findall(".//" + W + "del")),
        "moves_from": len(document.findall(".//" + W + "moveFrom")),
        "moves_to": len(document.findall(".//" + W + "moveTo")),
    }
    media = [name for name in archive.namelist() if name.startswith("word/media/")]

keywords = ["修改", "待填", "待补", "注意", "数据集", "数据库", "知识库", "知识图谱", "Chroma", "Neo4j", "创意简报", "共享简报", "需求简报", "多智能体", "多Agent", "Agent", "LangChain", "LangGraph", "创新"]
matches = {key: [row for row in records if key.lower() in row["text"].lower()] for key in keywords}
summary = {"paragraph_count": paragraph_index, "nonempty_paragraphs": len(records), "table_count": len(tables), "changes": changes, "media_count": len(media), "media": media}
(OUT / "document_structure.json").write_text(json.dumps({"summary": summary, "paragraphs": records, "tables": tables, "matches": matches}, ensure_ascii=False, indent=2), encoding="utf-8")
with (OUT / "document_text.txt").open("w", encoding="utf-8") as stream:
    for row in records:
        stream.write(f'{row["index"]:04d}\t[{row["style"]}]\t{row["text"]}\n')
    for table in tables:
        stream.write(f'\n=== TABLE {table["table"]} ===\n')
        for row in table["rows"]:
            stream.write(" | ".join(row) + "\n")
print(json.dumps(summary, ensure_ascii=False, indent=2))
