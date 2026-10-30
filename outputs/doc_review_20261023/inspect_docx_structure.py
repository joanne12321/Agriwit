from pathlib import Path
from zipfile import ZipFile
from lxml import etree

SOURCE = Path(r"D:/桌面/云稼集Agriwit/outputs/关键技术修改稿.docx")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def text(node):
    return "".join(node.itertext()).strip()


with ZipFile(SOURCE) as archive:
    root = etree.fromstring(archive.read("word/document.xml"))

for table_index, table in enumerate(root.findall(".//" + W + "tbl"), 1):
    print(f"TABLE {table_index}")
    for row_index, row in enumerate(table.findall("./" + W + "tr"), 1):
        for cell_index, cell in enumerate(row.findall("./" + W + "tc"), 1):
            value = text(cell)
            if "5.1 农业营销数据集" not in value:
                continue
            print(f"CELL {row_index},{cell_index}")
            for paragraph_index, paragraph in enumerate(cell.findall(".//" + W + "p"), 1):
                value = "".join(t.text or "" for t in paragraph.findall(".//" + W + "t"))
                drawings = len(paragraph.findall(".//" + W + "drawing"))
                print(f"{paragraph_index:04d}\tdrawings={drawings}\t{value[:240]}")
