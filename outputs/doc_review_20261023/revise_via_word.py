from pathlib import Path
import ast
import shutil
import time

import pythoncom
import win32com.client

ROOT = Path(r"D:/桌面/云稼集Agriwit")
SOURCE = Path(r"D:/桌面/半修改版内有修改指示(1).docx")
OUTPUT = ROOT / "outputs" / "关键技术修改稿.docx"
TEXT_SOURCE = ROOT / "outputs" / "doc_review_20261023" / "revise_key_technology.py"
MODEL_FIGURE = ROOT / "outputs" / "doc_review_20261023" / "image5.png"
WORKFLOW_FIGURE = ROOT / "outputs" / "doc_review_20261023" / "image6.jpeg"
PRODUCT_UI = ROOT / "outputs" / "doc_review_20261023" / "image7.png"
REQUIREMENT_UI = ROOT / "outputs" / "doc_review_20261023" / "image8.png"


def load_section():
    tree = ast.parse(TEXT_SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "SECTION" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("SECTION text not found")


def find_text(doc, value, start=0):
    rng = doc.Range(start, doc.Content.End)
    finder = rng.Find
    finder.ClearFormatting()
    finder.Text = value
    finder.Forward = True
    finder.Wrap = 0
    return rng if finder.Execute() else None


def insert_figure(doc, anchor_text, image_path, caption=None, width_points=430):
    anchor = find_text(doc, anchor_text)
    if anchor is None:
        raise RuntimeError(f"Figure anchor missing: {anchor_text}")
    pos = anchor.Paragraphs(1).Range.End
    rng = doc.Range(pos, pos)
    rng.InsertAfter("\r")
    pic_range = doc.Range(pos, pos)
    pic = doc.InlineShapes.AddPicture(str(image_path), False, True, pic_range)
    pic.LockAspectRatio = True
    if pic.Width > width_points:
        pic.Width = width_points
    pic.Range.ParagraphFormat.Alignment = 1
    if caption:
        tail = doc.Range(pic.Range.End, pic.Range.End)
        tail.InsertAfter("\r" + caption)
        cap = doc.Range(pic.Range.End + 1, pic.Range.End + 1 + len(caption))
        cap.ParagraphFormat.Alignment = 1
        cap.Font.NameFarEast = "宋体"
        cap.Font.Size = 9


def replace_after_page_16_terms(doc):
    replacements = [
        (
            "构建以广东特色农产品为重点的领域数据集",
            "构建面向农产品营销的领域知识库与训练数据集",
        ),
        (
            "项目构建了以广东地理标志农产品为重点的领域数据集，整理三千余条资料，涵盖茶叶、板栗、荔枝、龙眼等品类的产地背景、产品特点、地域文化和生产加工知识，并补充营销文案与宣传规范。数据经清洗、去重、分类及来源标注，为领域模型微调、知识检索和内容审核提供支持，也为后续类似应用的研究提供了宝贵的数据资源。",
            "项目完成10000条农业营销领域数据治理，形成企业及产品档案、营销素材、地方历史文化知识、广告法违禁词四类知识库；其中筛选8000条高质量指令样本用于Qwen3-8B监督微调。数据经清洗、去重、分类、实体关联及来源标注，为领域模型、RAG检索、内容审核和跨模态对齐提供统一的数据底座，也为后续扩展更多地域与品类保留标准化接口。",
        ),
        ("以共享创意简报连接文案、海报、视频和直播脚本", "以共享需求简报连接推文、海报、视频和直播脚本"),
        ("通过多Agent共享创意简报协调不同物料", "通过LangGraph组织多Agent共享需求简报并协调不同物料"),
        ("创意简报", "需求简报"),
    ]
    # Page 16 begins at this heading in the original document. Limit replacements to the remainder.
    boundary = find_text(doc, "创新点")
    start = boundary.Start if boundary is not None else 0
    for old, new in replacements:
        rng = doc.Range(start, doc.Content.End)
        finder = rng.Find
        finder.ClearFormatting()
        finder.Replacement.ClearFormatting()
        finder.Text = old
        finder.Replacement.Text = new
        finder.Forward = True
        finder.Wrap = 0
        finder.Format = False
        finder.Execute(Replace=2)


def format_inserted(range_obj):
    range_obj.Font.NameFarEast = "宋体"
    range_obj.Font.Name = "Times New Roman"
    range_obj.Font.Size = 10.5
    for p in range_obj.Paragraphs:
        text = p.Range.Text.strip("\r\x07 ")
        p.Range.ParagraphFormat.Alignment = 3
        p.Range.ParagraphFormat.SpaceAfter = 0
        p.Range.ParagraphFormat.LineSpacingRule = 0
        if text.startswith("5、") or text.startswith("6、"):
            p.Range.Font.Bold = True
            p.Range.Font.Size = 12
            p.Range.ParagraphFormat.FirstLineIndent = 0
        elif text.startswith(("5.1 ", "5.2 ", "5.3 ", "5.4 ", "5.5 ", "5.6 ", "5.7 ")):
            p.Range.Font.Bold = True
            p.Range.Font.Size = 11
            p.Range.ParagraphFormat.FirstLineIndent = 0
        elif text.startswith("（") and "）" in text[:5]:
            p.Range.Font.Bold = True
            p.Range.ParagraphFormat.FirstLineIndent = 0
        elif text.startswith(("表2 ", "图4 ")):
            p.Range.ParagraphFormat.Alignment = 1
            p.Range.Font.Size = 9
            p.Range.ParagraphFormat.FirstLineIndent = 0
        elif text.startswith("【此处保留"):
            p.Range.Font.Bold = True
            p.Range.Font.Color = 255
            p.Range.ParagraphFormat.Alignment = 1
            p.Range.ParagraphFormat.FirstLineIndent = 0
        else:
            p.Range.ParagraphFormat.FirstLineIndent = 21


def convert_agent_table(doc):
    header = find_text(doc, "Agent｜核心模型｜关键输入与输出｜主要Skill｜编排关系")
    last = find_text(doc, "交付决策Agent｜Qwen3-8B+规则评分｜合格候选→推荐版本及交付包｜候选排序、版本管理、打包交付｜终节点，保留人工确认")
    if header is None or last is None:
        raise RuntimeError("Agent table rows not found")
    table_range = doc.Range(header.Start, last.Paragraphs(1).Range.End - 1)
    table_range.Text = table_range.Text.replace("｜", "\t")
    table = table_range.ConvertToTable("\t", 9, 5)
    table.Borders.Enable = True
    table.Rows(1).Range.Font.Bold = True
    table.Rows(1).Shading.BackgroundPatternColor = 15189684
    table.Range.Font.NameFarEast = "宋体"
    table.Range.Font.Size = 8
    table.Range.ParagraphFormat.FirstLineIndent = 0
    table.Range.ParagraphFormat.SpaceAfter = 0
    table.AutoFitBehavior(2)


def main():
    section = load_section()
    shutil.copyfile(SOURCE, OUTPUT)
    pythoncom.CoInitialize()
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    doc = None
    try:
        doc = word.Documents.Open(str(OUTPUT), False, False)
        tracking = doc.TrackRevisions
        doc.TrackRevisions = False

        target = None
        for table in doc.Tables:
            for cell in table.Range.Cells:
                if "5、技术关键" in cell.Range.Text and "5.1 农业营销数据集构建与处理" in cell.Range.Text:
                    target = cell
                    break
            if target is not None:
                break
        if target is None:
            raise RuntimeError("Technical section cell not found")

        cell_range = target.Range.Duplicate
        start_find = cell_range.Find
        start_find.Text = "5、技术关键"
        start_find.Forward = True
        start_find.Wrap = 0
        if not start_find.Execute():
            raise RuntimeError("Technical section heading not found")
        replace_start = cell_range.Start
        replace_end = target.Range.End - 1
        replacement = doc.Range(replace_start, replace_end)
        replacement.Text = section.replace("\n", "\r")
        inserted = doc.Range(replace_start, replace_start + len(section))
        format_inserted(inserted)
        convert_agent_table(doc)

        insert_figure(doc, "模型微调流程如下图所示。", MODEL_FIGURE, None, 440)
        insert_figure(
            doc,
            "多Agent围绕共享状态协同执行，资料补充、节点修订、人工确认和版本归档均通过LangGraph条件边连接，整体工作流程如图4所示。",
            WORKFLOW_FIGURE,
            None,
            440,
        )
        insert_figure(doc, "（1）产品资料与宣传需求的引导式输入", PRODUCT_UI, "图5 产品资料录入页面", 390)
        insert_figure(doc, "图5 产品资料录入页面", REQUIREMENT_UI, "图6 前端宣传需求页面", 390)

        replace_after_page_16_terms(doc)
        doc.TrackRevisions = tracking
        doc.Save()
        doc.ExportAsFixedFormat(str(ROOT / "outputs" / "关键技术修改稿.pdf"), 17)
        pages = doc.ComputeStatistics(2)
        print(f"Saved {OUTPUT} pages={pages}")
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
