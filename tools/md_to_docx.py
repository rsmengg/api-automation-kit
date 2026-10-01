#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把项目里的 .md 文档转成可直接用 Word 编辑的 .docx。

零第三方依赖：直接拼 OOXML（docx 本质是一个 zip 里的 word/document.xml）。

用法:
    python3 tools/md_to_docx.py docs/首单需求确认书模板.md [更多.md ...]

支持：#/##/### 标题、普通段落、- 列表、> 引用、GFM 表格、``` 代码块、--- 分隔线
"""
import sys
import pathlib
import zipfile
from xml.sax.saxutils import escape

ACCENT = "1F4E79"   # 标题色
CN_HEAD = "微软雅黑"
CN_BODY = "宋体"
MONO = "Consolas"


def esc(text: str) -> str:
    return escape(text, {'"': "&quot;"})


def runs(text: str, size: float, bold=False, color=None, font=CN_BODY, italic=False):
    """生成一个 w:r 的 XML 字符串。"""
    color_xml = f'<w:color w:val="{color}"/>' if color else ""
    rpr = (
        f'<w:rPr>'
        f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}"/>'
        f'{color_xml}'
        f'<w:b/>' if bold else
        f'<w:rPr>'
        f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}"/>'
        f'{color_xml}'
    )
    rpr = rpr.replace("<w:b/>", "") if not bold and not italic else rpr
    italic_xml = "<w:i/>" if italic else ""
    rpr = (
        f'<w:rPr>'
        f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:eastAsia="{font}"/>'
        f'{color_xml}{italic_xml}'
        f'{"<w:b/>" if bold else ""}'
        f'</w:rPr>'
    )
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


def para(text="", size=10.5, bold=False, color=None, font=CN_BODY,
         before=0, after=4, indent=0, level=0, align=None):
    props = [f'<w:spacing w:before="{before}" w:after="{after}" w:line="276" w:lineRule="auto"/>']
    if indent:
        props.append(f'<w:ind w:left="{indent}"/>')
    if align:
        props.append(f'<w:jc w:val="{align}"/>')
    ppr = f'<w:pPr>{"".join(props)}</w:pPr>'
    body = runs(text, size, bold, color, font) if text else ""
    return f"<w:p>{ppr}{body}</w:p>"


def heading(text, level):
    size = {1: 18, 2: 15, 3: 13}.get(level, 12)
    return para(text, size=size, bold=True, color=ACCENT, font=CN_HEAD,
                before=200, after=80)


def code_line(text):
    return para(text or " ", size=9.5, font=MONO, after=0, indent=170)


def rich_para(text, size=10.5, after=4, indent=0, bold_all=False):
    """处理粗体 **x** 的简单行内解析。"""
    out = []
    i = 0
    parts = []
    while i < len(text):
        if text.startswith("**", i):
            j = text.find("**", i + 2)
            if j != -1:
                parts.append(("b", text[i + 2:j]))
                i = j + 2
                continue
        parts.append(("n", text[i]))
        i += 1
    # 合并同类型相邻片段，减少 run 数量
    merged = []
    for kind, val in parts:
        if merged and merged[-1][0] == kind:
            merged[-1] = (kind, merged[-1][1] + val)
        else:
            merged.append((kind, val))
    for kind, val in merged:
        if kind == "b":
            out.append(runs(val, size, bold=True, font=CN_BODY))
        else:
            out.append(runs(val, size, font=CN_BODY))
    ppr = (f'<w:pPr><w:spacing w:after="{after}" w:line="276" w:lineRule="auto"/>'
           f'<w:ind w:left="{indent}"/></w:pPr>')
    return f"<w:p>{ppr}{''.join(out)}</w:p>"


def table(rows):
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    xml = ['<w:tbl><w:tblPr>'
           '<w:tblStyle w:val="TableGrid"/>'
           '<w:tblW w:w="0" w:type="auto"/>'
           '<w:tblBorders>'
           '<w:top w:val="single" w:sz="4" w:color="B7C4D1"/>'
           '<w:left w:val="single" w:sz="4" w:color="B7C4D1"/>'
           '<w:bottom w:val="single" w:sz="4" w:color="B7C4D1"/>'
           '<w:right w:val="single" w:sz="4" w:color="B7C4D1"/>'
           '<w:insideH w:val="single" w:sz="4" w:color="B7C4D1"/>'
           '<w:insideV w:val="single" w:sz="4" w:color="B7C4D1"/>'
           '</w:tblBorders></w:tblPr>']
    for ri, row in enumerate(rows):
        tr_pr = '<w:trPr><w:tblHeader/></w:trPr>' if ri == 0 else ""
        xml.append(f"<w:tr>{tr_pr}")
        for ci in range(ncols):
            val = row[ci] if ci < len(row) else ""
            shade = f'<w:shd w:val="clear" w:color="auto" w:fill="F2F6FA"/>' if ri == 0 else ""
            cell = (f'<w:tc><w:tcPr><w:tcW w:w="2400" w:type="dxa"/>{shade}'
                    f'<w:vAlign w:val="center"/></w:tcPr>'
                    + para(val, size=9.5, bold=(ri == 0), color=(ACCENT if ri == 0 else None),
                           after=20)
                    + "</w:tc>")
            xml.append(cell)
        xml.append("</w:tr>")
    xml.append("</w:tbl>")
    xml.append(para(after=100))
    return "".join(xml)


def convert(md_path: pathlib.Path) -> bytes:
    text = md_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    body_parts = []
    i = 0
    code_buf = []

    def flush_code():
        if code_buf:
            body_parts.append(para(after=0))
            for ln in code_buf:
                body_parts.append(code_line(ln))
            body_parts.append(para(after=120))
            code_buf.clear()

    while i < len(lines):
        raw = lines[i]
        s = raw.strip()

        if s.startswith("```"):
            flush_code()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            code_buf = buf
            flush_code()
            continue

        if not s:
            flush_code()
            i += 1
            continue

        if s.startswith("|") and s.endswith("|"):
            flush_code()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= set("-: ") for c in cells):
                    rows.append(cells)
                i += 1
            for r in rows:
                body_parts.append(table([r]))
            if rows:
                body_parts.append(para(after=100))
            continue

        if s.startswith("#"):
            flush_code()
            lvl = min(len(s) - len(s.lstrip("#")), 3)
            body_parts.append(heading(s.lstrip("# ").strip(), lvl))
            i += 1
            continue

        if s == "---":
            flush_code()
            body_parts.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" '
                              'w:sz="6" w:space="1" w:color="D0D7DE"/></w:pBdr>'
                              '</w:pPr></w:p>')
            i += 1
            continue

        if s.startswith(">"):
            flush_code()
            if s.strip(">").strip():
                body_parts.append(rich_para(s.lstrip("> ").strip(), after=80, indent=240))
            i += 1
            continue

        if s.startswith("- ") or s.startswith("* "):
            flush_code()
            body_parts.append(rich_para("· " + s[2:].strip(), indent=170))
            i += 1
            continue

        if len(s) >= 3 and s[0].isdigit() and s[1:3] in (". ", "、"):
            flush_code()
            body_parts.append(rich_para(s, indent=170))
            i += 1
            continue

        flush_code()
        body_parts.append(rich_para(s))
        i += 1

    flush_code()

    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>" + "".join(body_parts) +
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="851" w:footer="992" w:gutter="0"/></w:sectPr>'
        "</w:body></w:document>"
    )

    styles = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr>'
        f'<w:rFonts w:ascii="{CN_BODY}" w:hAnsi="{CN_BODY}" w:eastAsia="{CN_BODY}"/>'
        '<w:sz w:val="21"/></w:rPr></w:rPrDefault>'
        '<w:pPrDefault><w:pPr><w:spacing w:after="80" w:line="276" w:lineRule="auto"/>'
        '</w:pPr></w:pPrDefault></w:docDefaults>'
        '<w:style w:type="table" w:styleId="TableGrid">'
        '<w:name w:val="Table Grid"/><w:tableBorders>'
        + "".join(f'<w:{t} w:val="single" w:sz="4" w:color="B7C4D1"/>'
                  for t in ("top", "left", "bottom", "right", "insideH", "insideV"))
        + "</w:tableBorders></w:style>"
        '<w:style w:type="paragraph" w:styleId="Quote"><w:name w:val="Quote"/></w:style>'
        "</w:styles>"
    )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )
    doc_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>'
        "</Relationships>"
    )
    numbering = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"/>'
    )
    core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<dc:title>{esc(md_path.stem)}</dc:title>"
        f"<dc:creator>api-automation-kit</dc:creator>"
        "</cp:coreProperties>"
    )
    app = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>WorkBuddy md_to_docx</Application>"
        "</Properties>"
    )

    buf = pathlib.Path(md_path).with_suffix(".docx")
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/styles.xml", styles)
        z.writestr("word/numbering.xml", numbering)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
    return buf


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        if not p.exists():
            print(f"skip (not found): {p}")
            continue
        print("ok ->", convert(p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
