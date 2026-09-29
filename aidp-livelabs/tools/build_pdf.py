"""Build the portable, screenshot-embedded learner handbook from current Markdown."""
import html
import json
import os
import re
import subprocess
import textwrap
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, KeepTogether, Preformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / "output/pdf/AIDP_Lab1_and_Lab2_Learner_Guide.pdf"
DOCS = [
    ("00-setup.md", "1", "Before you begin"),
    ("01-lab1.md", "2", "Lab 1 | Bronze, Silver and Gold"),
    ("02-lab2.md", "3", "Lab 2 | Train, compare and predict"),
    ("knowledge-base.md", "4", "Optional PDF knowledge-base extension"),
    ("workflow.md", "5", "Run the four-notebook workflow"),
    ("reruns.md", "6", "Reruns, recovery and cleanup"),
    ("learner-evidence.md", "7", "Workshop checkpoints"),
    ("images/README.md", "A", "Screenshot provenance"),
]
FONT_DIR = Path(os.environ.get("AIDP_GUIDE_FONT_DIR", "/usr/share/fonts/truetype/dejavu"))
for name, filename in [
    ("Guide", "DejaVuSans.ttf"), ("Guide-Bold", "DejaVuSans-Bold.ttf"),
    ("Guide-Italic", "DejaVuSans-Oblique.ttf"), ("GuideMono", "DejaVuSansMono.ttf"),
]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="Guide-Bold", italic="Guide-Italic", boldItalic="Guide-Bold")
INK = colors.HexColor("#233638")
TEAL = colors.HexColor("#175f66")
MUTED = colors.HexColor("#586a6d")
WIDTH, HEIGHT = 612, 792
MARGIN = 42
CONTENT = WIDTH - MARGIN * 2
styles = {
    "body": ParagraphStyle("Body", fontName="Guide", fontSize=9.2, leading=13.5,
        textColor=INK, spaceAfter=7, splitLongWords=True, allowWidows=0, allowOrphans=0),
    "h1": ParagraphStyle("Chapter", fontName="Guide-Bold", fontSize=23, leading=29,
        textColor=TEAL, spaceAfter=18, keepWithNext=True),
    "h2": ParagraphStyle("Section", fontName="Guide-Bold", fontSize=13.5, leading=18,
        textColor=TEAL, spaceBefore=15, spaceAfter=8, keepWithNext=True),
    "h3": ParagraphStyle("Subsection", fontName="Guide-Bold", fontSize=10.5, leading=15,
        textColor=INK, spaceBefore=10, spaceAfter=6, keepWithNext=True),
    "table": ParagraphStyle("TableText", fontName="Guide", fontSize=8, leading=11.3,
        textColor=INK, splitLongWords=True, spaceAfter=0),
    "caption": ParagraphStyle("Caption", fontName="Guide-Italic", fontSize=8, leading=11.5,
        textColor=MUTED, spaceAfter=12),
    "code": ParagraphStyle("Code", fontName="GuideMono", fontSize=7.5, leading=10.5,
        textColor=INK, backColor=colors.HexColor("#eef3f1"), borderPadding=9,
        spaceBefore=5, spaceAfter=12),
}
SOURCE = None
LINKS = {}
IMAGE_COUNT = 0


def normalize(value):
    return value.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", " - ")


def plain(nodes):
    result = []
    for node in nodes:
        kind, c = node["t"], node.get("c")
        if kind == "Str":
            result.append(c)
        elif kind in ("Space", "SoftBreak", "LineBreak"):
            result.append(" ")
        elif kind in ("Code", "Math"):
            result.append(c[1])
        elif kind in ("Link", "Image", "Span"):
            result.append(plain(c[1]))
        elif kind in ("Strong", "Emph", "Strikeout", "SmallCaps"):
            result.append(plain(c))
        elif kind == "Quoted":
            result.append(plain(c[1]))
    return normalize("".join(result))


def inline(nodes, code_size=8):
    result = []
    for node in nodes:
        kind, c = node["t"], node.get("c")
        if kind == "Str":
            result.append(html.escape(normalize(c)))
        elif kind in ("Space", "SoftBreak"):
            result.append(" ")
        elif kind == "LineBreak":
            result.append("<br/>")
        elif kind == "Code":
            result.append('<font name="GuideMono" size="%s">%s</font>' % (code_size, html.escape(normalize(c[1]))))
        elif kind in ("Strong", "Emph"):
            tag = "b" if kind == "Strong" else "i"
            result.append("<%s>%s</%s>" % (tag, inline(c, code_size), tag))
        elif kind in ("Link", "Image"):
            label = inline(c[1], code_size)
            target = c[2][0]
            if kind == "Image":
                result.append(label)
            elif target.startswith(("https://", "http://")):
                result.append('<link href="%s" color="#175f66">%s</link>' % (html.escape(target, quote=True), label))
            else:
                path, _, fragment = target.partition("#")
                dest = (SOURCE.parent / path).resolve() if path else SOURCE.resolve()
                key = LINKS.get((str(dest), fragment)) or LINKS.get((str(dest), ""))
                if key:
                    result.append('<link href="#%s" color="#175f66">%s</link>' % (key, label))
                else:
                    result.append(label + ' <font size="7" color="#586a6d">(workshop package)</font>')
        elif kind == "Quoted":
            result.append('"' + inline(c[1], code_size) + '"')
        elif kind == "Span":
            result.append(inline(c[1], code_size))
        else:
            result.append(html.escape(plain([node])))
    return "".join(result)


def para(text, style="body", **kwargs):
    return Paragraph(text, styles[style], **kwargs)


def cell_content(cell):
    blocks = cell[-1]
    values = []
    for block in blocks:
        if block["t"] in ("Plain", "Para"):
            values.append(inline(block["c"], 7.2))
        elif block["t"] == "BulletList":
            values.extend("- " + inline(b[0]["c"], 7.2) for b in block["c"])
    return para("<br/>".join(values), "table")


def table_flow(c):
    rows = c[3][1]
    for body in c[4]:
        rows += body[2] + body[3]
    rows += c[5][1]
    data = [[cell_content(cell) for cell in row[1]] for row in rows]
    count = len(c[2])
    fractions = {2: [.32, .68], 3: [.27, .36, .37], 4: [.25] * 4}.get(count, [1/count] * count)
    table = Table(data, colWidths=[CONTENT * f for f in fractions], repeatRows=1,
                  hAlign="LEFT", spaceBefore=6, spaceAfter=12)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0ece8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9f8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#cad7d2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def render(blocks, indent=0):
    global IMAGE_COUNT
    result = []
    skip_caption = False
    for block_index, block in enumerate(blocks):
        if skip_caption:
            skip_caption = False
            continue
        kind, c = block["t"], block.get("c")
        if kind == "Header":
            level, attr, content = c
            if level == 1:
                continue
            p = para(inline(content), "h2" if level == 2 else "h3")
            p.bookmark = LINKS[(str(SOURCE.resolve()), attr[0])]
            p.outline_level = min(level - 1, 2)
            result.append(p)
        elif kind in ("Para", "Plain"):
            if any(n["t"] == "Image" for n in c):
                for n in c:
                    if n["t"] != "Image":
                        continue
                    image_path = (SOURCE.parent / n["c"][2][0]).resolve()
                    with PILImage.open(image_path) as image:
                        w, h = image.size
                    size = min(CONTENT/w, 310/h)
                    figure = Image(str(image_path), width=w*size, height=h*size)
                    figure.hAlign = "LEFT"
                    IMAGE_COUNT += 1
                    caption = inline(n["c"][1])
                    if block_index + 1 < len(blocks):
                        following = blocks[block_index + 1]
                        if following["t"] in ("Para", "Plain"):
                            note = plain(following["c"])
                            if re.match(r"^Figure \d+\.", note):
                                caption += " " + html.escape(re.sub(r"^Figure \d+\.\s*", "", note))
                                skip_caption = True
                    figure_parts = [Spacer(1, 7), figure, Spacer(1, 5),
                        para("Figure %d. %s" % (IMAGE_COUNT, caption), "caption")]
                    if result and isinstance(result[-1], Paragraph) and hasattr(result[-1], "bookmark"):
                        figure_parts.insert(0, result.pop())
                    result.append(KeepTogether(figure_parts))
            elif not plain(c).startswith(("Workshop home", "Back to Lab", "Back to Lab 1", "Workshop home")):
                result.append(para(inline(c)))
        elif kind in ("BulletList", "OrderedList"):
            items = c if kind == "BulletList" else c[1]
            start = 1 if kind == "BulletList" else c[0][0]
            for index, item in enumerate(items, start):
                first = True
                for flow in render(item, indent+12):
                    if isinstance(flow, Paragraph):
                        flow.style = ParagraphStyle("ListItem", parent=flow.style,
                            leftIndent=indent+14, firstLineIndent=0, bulletIndent=indent,
                            spaceAfter=5)
                        if first:
                            flow.bulletText = "-" if kind == "BulletList" else str(index)+"."
                    result.append(flow)
                    first = False
            result.append(Spacer(1, 3))
        elif kind == "CodeBlock":
            lines = []
            for line in normalize(c[1]).splitlines():
                lines.extend(textwrap.wrap(line, width=91, subsequent_indent="    ",
                    replace_whitespace=False, drop_whitespace=False) or [""])
            result.append(Preformatted("\n".join(lines), styles["code"]))
        elif kind == "Table":
            result.append(table_flow(c))
        elif kind == "BlockQuote":
            for flow in render(c):
                if isinstance(flow, Paragraph):
                    flow.style = ParagraphStyle("Notice", parent=flow.style,
                        backColor=colors.HexColor("#f7f0df"), borderPadding=8,
                        leftIndent=10, rightIndent=10, spaceBefore=8, spaceAfter=12)
                result.append(flow)
        elif kind == "Div":
            result.extend(render(c[1]))
        elif kind == "HorizontalRule":
            result.append(Spacer(1, 8))
        elif kind not in ("Null",):
            raise ValueError("Unhandled block " + kind)
    return result


class Handbook(BaseDocTemplate):
    def afterFlowable(self, flow):
        if hasattr(flow, "bookmark"):
            self.canv.bookmarkPage(flow.bookmark)
            level = flow.outline_level
            title = flow.getPlainText()
            self.canv.addOutlineEntry(title, flow.bookmark, level, False)
            if level == 0:
                self.notify("TOCEntry", (0, title, self.page, flow.bookmark))


def footer(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#d0dcda"))
        canvas.line(MARGIN, HEIGHT-29, WIDTH-MARGIN, HEIGHT-29)
        canvas.setFont("Guide", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, HEIGHT-22, "ORACLE AI DATA PLATFORM  |  LAB 1 + LAB 2")
        canvas.drawString(MARGIN, 23, "Learner guide  |  September 2026  |  Synthetic-data workshop")
        canvas.drawRightString(WIDTH-MARGIN, 23, str(doc.page))
    canvas.restoreState()


def main():
    global SOURCE
    parsed = []
    for idx, (file, number, title) in enumerate(DOCS):
        path = ROOT / "docs" / file
        ast = json.loads(subprocess.check_output(["pandoc", "-f", "gfm", "-t", "json", str(path)]))
        key = "chapter-%s" % idx
        LINKS[(str(path.resolve()), "")] = key
        for b in ast["blocks"]:
            if b["t"] == "Header":
                level, attr, _ = b["c"]
                LINKS[(str(path.resolve()), attr[0])] = key if level == 1 else key+"-"+attr[0]
        parsed.append((path, number, title, ast["blocks"], key))
    # Links to the standalone reset note lead to its comprehensive replacement.
    LINKS[(str((ROOT/"docs/lab1-table-reset.md").resolve()), "")] = "chapter-5"
    story = [Spacer(1, 65), para("SEER CONSTRUCTION", "h2"),
        Paragraph("Oracle AI Data Platform", ParagraphStyle("Cover", parent=styles["h1"], fontSize=30, leading=37)),
        para("Lab 1 + Lab 2", "h1"),
        para("Lakehouse foundations and MLOps", "h2"),
        Spacer(1, 25),
        para("Portable learner handbook", "h3"),
        para("September 29, 2026 | Lab 2 streamlined to Tasks 1-11"),
        Spacer(1, 20),
        para("Includes setup, all three Lab 1 notebooks, the Lab 2 experiment-to-inference walkthrough, separate optional PDF knowledge-base and workflow guides, and safe reruns. The public edition is text-only."),
        para("This PDF is the instructions, not an executable notebook. Use the accompanying workshop ZIP and original CSV/PDF assets to run the labs in your authorized AIDP environment."),
        para("Training and evaluation use synthetic teaching history. Predictions and registration do not establish production readiness."),
        Spacer(1, 28),
        para("Create the example resource names in your own environment or replace them consistently. No live resource identifiers or account-specific screenshots are included.", "caption"),
        PageBreak(), para("Contents", "h1")]
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("TOC", fontName="Guide", fontSize=11, leading=17,
                                     spaceBefore=12, textColor=INK)]
    story += [toc, Spacer(1, 24),
        para("How to use this PDF", "h2"),
        para("Click a chapter in the contents or use your PDF reader's bookmarks to jump to individual tasks. Internal guide links work within this file. Official documentation links require internet access; references labeled 'workshop package' refer to files supplied separately in the ZIP."),
        para("Run Lab 1A, then 1B, then 1C, then Lab 2. On a repeat exercise, read Chapter 6 before executing. No prior experiment or model deletion is required; Lab 1 recreates its target tables, while Lab 2 retains model history and overwrites predictions.")]
    for path, number, title, blocks, key in parsed:
        SOURCE = path
        story.append(PageBreak())
        story.append(para("CHAPTER " + number if number.isdigit() else "APPENDIX " + number, "caption"))
        p = para(html.escape(title), "h1")
        p.bookmark, p.outline_level = key, 0
        story.append(p)
        story.extend(render(blocks))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = Handbook(str(OUT), pagesize=(WIDTH, HEIGHT), leftMargin=MARGIN,
        rightMargin=MARGIN, topMargin=43, bottomMargin=42,
        title="Oracle AI Data Platform - Lab 1 and Lab 2 Learner Guide",
        author="Seer Construction workshop", subject="Portable lab instructions")
    frame = Frame(MARGIN, 42, CONTENT, HEIGHT-85, leftPadding=0,
                  bottomPadding=0, rightPadding=0, topPadding=0)
    doc.addPageTemplates(PageTemplate(id="Guide", frames=[frame], onPage=footer))
    doc.multiBuild(story)
    reader = PdfReader(OUT)
    text = "\n".join(p.extract_text() for p in reader.pages)
    normalized_text = " ".join(text.split())
    for marker in ["Task 11", "SESSION_ID", "Lab 1A", "milestone_delay_classifier", "No prior deletion is required"]:
        assert marker in normalized_text, marker
    assert not any(a.get_object().get("/A", {}).get("/URI", "").startswith("file:")
                   for p in reader.pages for a in p.get("/Annots", []))
    print(json.dumps({"pdf": str(OUT), "pages": len(reader.pages),
        "embedded_figures": IMAGE_COUNT, "bytes": OUT.stat().st_size,
        "chapters": len(DOCS)}, indent=2))


if __name__ == "__main__":
    main()
