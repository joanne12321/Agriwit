from pathlib import Path
from zipfile import ZipFile
from lxml import etree

SOURCE = Path(r"D:/桌面/云稼集Agriwit/outputs/关键技术修改稿.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

with ZipFile(SOURCE) as archive:
    root = etree.fromstring(archive.read("word/document.xml"))
    rels_root = etree.fromstring(archive.read("word/_rels/document.xml.rels"))
    rels = {r.get("Id"): r.get("Target") for r in rels_root.findall(REL + "Relationship")}

for i, p in enumerate(root.findall(".//" + W + "p"), 1):
    values = [t.text or "" for t in p.findall(".//" + W + "t")]
    ids = [b.get(R + "embed") for b in p.findall(".//" + A + "blip")]
    if ids:
        print(i, "|", "".join(values)[:80], "|", [(rid, rels.get(rid)) for rid in ids])
