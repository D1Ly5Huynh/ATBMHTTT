#!/usr/bin/env python3
"""Sinh slide bảo vệ ATBMHTTT — 10 trang, số chốt từ lab.

Chạy:
  python3 huong_dan/_gen_slides.py

Ra: huong_dan/Slide_Bao_ve_ATBMHTTT.pptx
Điền Họ tên / MSSV / GVHD trên slide 1 trước khi chiếu.
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

OUT = Path(__file__).resolve().parent / "Slide_Bao_ve_ATBMHTTT.pptx"

NAVY = RGBColor(0x0E, 0x27, 0x44)
NAVY2 = RGBColor(0x16, 0x3A, 0x5F)
AMBER = RGBColor(0xC4, 0x7E, 0x12)
RED = RGBColor(0x9B, 0x2C, 0x2C)
GREEN = RGBColor(0x1F, 0x6B, 0x4A)
INK = RGBColor(0x1A, 0x1F, 0x26)
MUTED = RGBColor(0x5A, 0x65, 0x70)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PAPER = RGBColor(0xF6, 0xF3, 0xEC)
LINE = RGBColor(0xD4, 0xD0, 0xC8)
ROW = RGBColor(0xEE, 0xF2, 0xF6)
HEAD = RGBColor(0x0E, 0x27, 0x44)

FONT = "Calibri"


def _set_typeface(run, name: str) -> None:
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    for tag in ("latin", "ea", "cs"):
        el = rPr.find(qn(f"a:{tag}"))
        if el is None:
            el = etree.SubElement(rPr, qn(f"a:{tag}"))
        el.set("typeface", name)


def _run(p, text, size=18, bold=False, color=INK, font=FONT, italic=False):
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    _set_typeface(r, font)
    return r


def _tf(shape, margin=0.08):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    inset = Inches(margin)
    tf._txBody.bodyPr.set("lIns", str(inset))
    tf._txBody.bodyPr.set("rIns", str(inset))
    tf._txBody.bodyPr.set("tIns", str(int(inset * 0.7)))
    tf._txBody.bodyPr.set("bIns", str(int(inset * 0.5)))
    return tf


def box(slide, l, t, w, h, fill=None, line=None, line_w=Pt(1)):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.adjustments[0] = 0.06
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill or WHITE
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = line_w
    return sh


def rect(slide, l, t, w, h, fill, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(1)
    return sh


def txt(slide, l, t, w, h, text, size=18, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT):
    sh = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = _tf(sh, 0.04)
    tf.paragraphs[0].alignment = align
    try:
        tf._txBody.bodyPr.set("anchor", {MSO_ANCHOR.TOP: "t", MSO_ANCHOR.MIDDLE: "ctr", MSO_ANCHOR.BOTTOM: "b"}[anchor])
    except Exception:
        pass
    p = tf.paragraphs[0]
    p.space_before = Pt(0)
    p.space_after = Pt(0)
    _run(p, text, size=size, bold=bold, color=color, font=font)
    return sh


def multiline(slide, l, t, w, h, lines, size=16, color=INK, gap=6, bold_first=False):
    """lines: list[str] or list[tuple]."""
    sh = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = _tf(sh, 0.06)
    for i, item in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_before = Pt(0 if i == 0 else gap)
        p.space_after = Pt(0)
        p.level = 0
        if isinstance(item, tuple):
            text, kw = item[0], item[1] if len(item) > 1 else {}
            _run(p, text, size=kw.get("size", size), bold=kw.get("bold", False), color=kw.get("color", color), italic=kw.get("italic", False))
        else:
            _run(p, item, size=size, bold=(bold_first and i == 0), color=color)
    return sh


def notes(slide, text: str) -> None:
    tf = slide.notes_slide.notes_text_frame
    tf.text = text


def footer(slide, page: int, total: int = 10) -> None:
    rect(slide, 0, 7.18, 13.333, 0.32, NAVY)
    txt(slide, 0.4, 7.18, 9.5, 0.32, "ATBMHTTT  ·  Không trộn nhánh A (~99%) với nhánh B (~1%)  ·  TASR = HTTP 200 VÀ JS chạy", size=11, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    txt(slide, 11.5, 7.18, 1.5, 0.32, f"{page} / {total}", size=11, color=WHITE, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)


def header(slide, kicker: str, title: str) -> None:
    rect(slide, 0, 0, 13.333, 0.12, AMBER)
    rect(slide, 0, 0.12, 13.333, 0.92, NAVY)
    txt(slide, 0.45, 0.16, 12.4, 0.28, kicker.upper(), size=11, color=AMBER, anchor=MSO_ANCHOR.MIDDLE)
    txt(slide, 0.45, 0.42, 12.4, 0.52, title, size=26, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)


def table(slide, l, t, w, h, rows, col_w=None, header=True, font_size=13):
    n_row, n_col = len(rows), len(rows[0])
    sh = slide.shapes.add_table(n_row, n_col, Inches(l), Inches(t), Inches(w), Inches(h))
    tbl = sh.table
    if col_w:
        total = sum(col_w)
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Inches(w * cw / total)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.text = ""
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.text_frame.word_wrap = True
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j else PP_ALIGN.LEFT
            p.space_before = Pt(0)
            p.space_after = Pt(0)
            is_head = header and i == 0
            _run(
                p,
                str(val),
                size=font_size if not is_head else font_size,
                bold=is_head or (j == 0),
                color=WHITE if is_head else INK,
            )
            fill = HEAD if is_head else (ROW if i % 2 == 0 else WHITE)
            cell.fill.solid()
            cell.fill.fore_color.rgb = fill
    return sh


def callout(slide, l, t, w, h, label, value, sub, fill=NAVY):
    sh = box(slide, l, t, w, h, fill=fill)
    tf = _tf(sh, 0.1)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    _run(p, label, size=11, color=RGBColor(0xE8, 0xD7, 0xA8), bold=True)
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(4)
    _run(p2, value, size=26, bold=True, color=WHITE)
    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(2)
    _run(p3, sub, size=11, color=RGBColor(0xD0, 0xDC, 0xE8))
    return sh


def new_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # ------------------------------------------------------------------ 1
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, NAVY)
    rect(s, 0, 0, 0.16, 7.5, AMBER)
    txt(s, 0.55, 0.35, 12.2, 0.28, "HỌC PHẦN AN TOÀN BẢO MẬT HỆ THỐNG THÔNG TIN  ·  ATBMHTTT", size=13, color=AMBER)
    txt(s, 0.55, 0.85, 12.2, 1.55,
        "Sinh mẫu thử tấn công XSS bằng kỹ thuật sinh dữ liệu đối kháng để kiểm tra bộ lọc",
        size=30, bold=True, color=WHITE)
    txt(s, 0.55, 2.50, 12.2, 0.55,
        "PPO + 27 đột biến Table 2  →  kiểm tra detector học sâu, OWASP CRS 4 và DOMPurify (localhost)",
        size=16, color=RGBColor(0xD0, 0xDC, 0xE8))

    box(s, 0.55, 3.25, 12.2, 1.55, fill=NAVY2, line=RGBColor(0x2A, 0x55, 0x80))
    multiline(s, 0.7, 3.35, 11.9, 1.4, [
        ("Khung đánh giá: Pasini, Maragliano, Kim, Tonella  ·  JSS 2026  ·  arXiv 2502.19095v2", {"size": 14, "color": WHITE}),
        ("Artifact GitHub GianlucaMaragliano/Adversarial_RL_XSS  ·  commit a299bb6", {"size": 14, "color": RGBColor(0xC5, 0xD4, 0xE4)}),
        ("Phạm vi lab: Mereani / data/10  ·  không WAF cloud  ·  không LLM sinh payload", {"size": 14, "color": RGBColor(0xC5, 0xD4, 0xE4)}),
    ], gap=8)

    txt(s, 0.55, 5.05, 4.0, 0.28, "Sinh viên", size=12, color=AMBER)
    txt(s, 0.55, 5.32, 4.0, 0.35, "________________________", size=16, color=WHITE)
    txt(s, 5.0, 5.05, 3.5, 0.28, "MSSV", size=12, color=AMBER)
    txt(s, 5.0, 5.32, 3.5, 0.35, "________________", size=16, color=WHITE)
    txt(s, 9.0, 5.05, 3.7, 0.28, "Giảng viên hướng dẫn", size=12, color=AMBER)
    txt(s, 9.0, 5.32, 3.7, 0.35, "________________________", size=16, color=WHITE)
    txt(s, 0.55, 6.15, 12.2, 0.35, "Tháng 9 năm 2026  ·  10 slide  ·  số đo trên máy lab, không bịa", size=13, color=RGBColor(0x9A, 0xB0, 0xC4))
    txt(s, 0.55, 6.85, 12.2, 0.28, "1 / 10", size=12, color=RGBColor(0x9A, 0xB0, 0xC4))
    notes(s,
          "20 giây: Chen báo Escape Rate khoảng 99% mà không kiểm tra XSS còn chạy. "
          "Pasini thêm Oracle DOM. Em bám khung đó, siết Oracle thành JavaScript chạy thật, "
          "rồi dùng PPO sinh mẫu để kiểm tra detector, CRS và DOMPurify. "
          "Giữ bug encode thì ER khoảng 99% lặp lại được; khép bug thì còn khoảng 1%. "
          "Trên CRS lab, catalog Table 2 có TASR bằng 0.")

    # ------------------------------------------------------------------ 2
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Vấn đề", "ER ~99% không chứng minh XSS còn chạy")
    multiline(s, 0.45, 1.25, 12.4, 1.3, [
        ("Chen et al. (2022) huấn luyện RL để payload XSS “lọt” detector học sâu, báo Escape Rate ~99%.", {"size": 17}),
        ("Họ không kiểm tra payload còn thực thi được trong trình duyệt.", {"size": 17, "bold": True}),
        ("Pasini et al. (JSS 2026) thêm Oracle DOM và chỉ ra phần lớn “lọt” đến từ tiền xử lý / token None (TH2).", {"size": 17}),
    ], gap=6)

    callout(s, 0.45, 2.75, 4.0, 1.55, "W1  ·  ORACLE DOM", "23,4%", "Mereani “độc” chỉ đổi cây HTML, JS không chạy  (3.542 / 15.149)")
    callout(s, 4.65, 2.75, 4.0, 1.55, "W4  ·  TABLE 4", "1 bộ số", "MLP = LSTM = CNN  ·  P 99,67  R 100  Acc 99,83")
    callout(s, 8.85, 2.75, 4.0, 1.55, "TH2  ·  OOV / NONE", "~48%", "token None trên mẫu lọt  ·  detector “mù”")

    box(s, 0.45, 4.50, 12.4, 2.40, fill=WHITE, line=LINE)
    multiline(s, 0.6, 4.58, 12.1, 2.25, [
        ("Ba câu hỏi đồ án", {"size": 15, "bold": True, "color": NAVY}),
        ("(i) Protocol Pasini có lặp lại được trên đúng artifact data/10 không?", {"size": 16}),
        ("(ii) Khi khép token-id và siết Oracle thành thực thi JS, ER 99% còn không?", {"size": 16}),
        ("(iii) Catalog 27 action có tạo được payload vừa lọt CRS lab vừa còn execute không?", {"size": 16}),
    ], gap=5)
    footer(s, 2)
    notes(s,
          "Nhấn: ER là detector gọi nhầm độc thành lành — không phải XSS chạy. "
          "div hello trên Oracle paper cũng bị gọi độc vì thêm nút DOM. "
          "23,4% nhãn Mereani lab đo được là parser-only.")

    # ------------------------------------------------------------------ 3
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Đề tài", "Sinh mẫu đối kháng  →  kiểm tra bộ lọc")

    steps = [
        ("1", "Payload độc", "Oracle JS chạy"),
        ("2", "PPO chọn action", "1 trong 27 Table 2"),
        ("3", "Mẫu thử", "chuỗi sau đột biến"),
        ("4", "Ba bộ lọc", "detector · CRS · Purify"),
    ]
    for i, (n, a, b) in enumerate(steps):
        x = 0.45 + i * 3.22
        box(s, x, 1.28, 2.95, 1.55, fill=WHITE, line=NAVY, line_w=Pt(1.5))
        txt(s, x + 0.12, 1.35, 0.4, 0.35, n, size=16, bold=True, color=AMBER)
        txt(s, x + 0.15, 1.70, 2.65, 0.45, a, size=16, bold=True, color=NAVY)
        txt(s, x + 0.15, 2.15, 2.65, 0.5, b, size=13, color=MUTED)
        if i < 3:
            txt(s, x + 2.85, 1.75, 0.4, 0.5, "→", size=22, bold=True, color=AMBER, align=PP_ALIGN.CENTER)

    table(
        s, 0.45, 3.10, 12.4, 2.35,
        [
            ["Bộ lọc", "Mẫu đưa vào", "Chỉ số thành công", "Kết quả lab"],
            ["Detector DL (nhánh A)", "PPO 250k, data/10", "ER = độc bị gọi lành", "~99%  — do OOV/None"],
            ["Detector DL (nhánh B)", "cùng 27 action, vocab cố định", "ER / TASR (JS chạy)", "0,75% → 0,25%"],
            ["OWASP CRS 4 PL1/PL2", "catalog + mẫu PPO transfer", "TASR = 200 VÀ execute", "0"],
            ["DOMPurify", "84 mẫu Table 2", "TASR ;  Δ = Escape − TASR", "TASR 0  ·  Δ = 1"],
        ],
        col_w=[2.6, 3.4, 3.4, 3.0],
        font_size=13,
    )
    txt(s, 0.45, 5.60, 12.4, 0.7,
        "TASR mới được viết là tấn công thành công trên bộ lọc web.  HTTP 200 một mình = Escape, không tính.  Không train RL trên CRS: catalog chưa có primitive BYPASS_EXEC.",
        size=15, color=NAVY)
    footer(s, 3)
    notes(s,
          "Đây là slide khớp đề. Kỹ thuật sinh = PPO + 27 action, không GAN không LLM. "
          "Ba bộ lọc. Thuộc công thức TASR. App không WAF TASR 84,5% — chỗ này để đối chiếu, không phải bypass WAF.")

    # ------------------------------------------------------------------ 4
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Pasini 2026  ·  PDF v2", "Ba RQ — TH2 là thủ phạm, không phải mutation")

    cards = [
        (NAVY, "RQ1  /  TH1", "Mutation có phá XSS?", "RR(E) ≈ 6–7%", "Tập E = mẫu đã lọt detector.\nPaper: hầu hết vẫn độc trên DOM."),
        (RGBColor(0x8A, 0x4B, 0x12), "RQ2  /  TH2", "Preprocess / OOV phá XSS?", "RR(V) ≈ 93–98%", "V = E sau tokenize, OOV → None.\nOR(V) ≈ 44–48% token None."),
        (GREEN, "RQ3", "Oracle vào reward thì sao?", "ER vẫn > 96%", "RR ≈ 0 theo Oracle DOM.\nER cao không có nghĩa JS còn chạy."),
    ]
    for i, (fill, k, q, v, sub) in enumerate(cards):
        x = 0.45 + i * 4.22
        box(s, x, 1.28, 4.02, 3.55, fill=WHITE, line=LINE)
        rect(s, x, 1.28, 4.02, 0.12, fill)
        txt(s, x + 0.18, 1.50, 3.7, 0.32, k, size=13, bold=True, color=fill)
        txt(s, x + 0.18, 1.88, 3.7, 0.70, q, size=18, bold=True, color=NAVY)
        txt(s, x + 0.18, 2.62, 3.7, 0.55, v, size=26, bold=True, color=fill)
        multiline(s, x + 0.18, 3.30, 3.7, 1.3, [(ln, {"size": 14, "color": MUTED}) for ln in sub.split("\n")], gap=4)

    box(s, 0.45, 5.05, 12.4, 1.85, fill=WHITE, line=LINE)
    multiline(s, 0.6, 5.15, 12.1, 1.7, [
        ("Công thức (thuộc 4 dòng này)", {"size": 15, "bold": True, "color": NAVY}),
        ("ER = (# độc detector gọi lành) / |adversarial|     ·     O(p)=1 nếu Oracle = còn độc", {"size": 15}),
        ("RR(M) = 1 − trung bình O trên tập M     ·     OR(V) = (# token None) / |V|", {"size": 15}),
        ("TASR = (# BYPASS_EXEC) / N     ·     Δ = Escape − TASR", {"size": 15}),
    ], gap=4)
    footer(s, 4)
    notes(s,
          "RQ1 mutation nhẹ. RQ2 preprocess nặng. RQ3 nhét Oracle DOM vào train, ER vẫn trên 96%. "
          "Đồ án bám khung này, không bám ER 99% như mục tiêu thành công.")

    # ------------------------------------------------------------------ 5
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Phương pháp", "Hai nhánh, cùng 27 action — không trộn số")
    table(
        s, 0.45, 1.25, 12.4, 3.55,
        [
            ["", "Chen 2022", "Pasini 2026", "Đồ án"],
            ["Dataset", "XSSed+Alexa ~90k (không public)", "Mereani, Oracle DOM, data/10", "A: data/10   B: Mereani lọc JSDOM"],
            ["Agent", "SAC", "PPO (SB3)", "PPO; P4 thêm Dueling DQN"],
            ["Oracle", "không", "DOM-diff vs \"abc\"", "A: DOM   B: JSDOM + Playwright"],
            ["Encode", "Word2Vec / token", "LabelEncoder từng mẫu", "A: giữ bug   B: vocab cố định"],
            ["Bộ lọc web", "SafeDog / XSSChop", "không", "CRS 4 PL1/PL2 + DOMPurify"],
            ["Chỉ số", "ER", "ER + RR + OR", "A: ER/RR/OR   B: TASR + Δ"],
        ],
        col_w=[1.8, 3.3, 3.5, 3.8],
        font_size=12,
    )
    callout(s, 0.45, 5.00, 6.05, 1.85, "NHÁNH A  ·  SÁT PAPER", "ER ~ 99%", "artifact data/10  ·  LabelEncoder từng mẫu  ·  Oracle DOM")
    callout(s, 6.75, 5.00, 6.10, 1.85, "NHÁNH B  ·  KHÉP TH2", "ER ~ 1%", "JSDOM execute  ·  token-id cố định  ·  CRS / Purify", fill=GREEN)
    footer(s, 5)
    notes(s,
          "Cùng 27 action. Khác encode và Oracle. "
          "Nhánh A để nói protocol lặp lại được. Nhánh B để nói khi khép OOV thì 99% biến mất. "
          "Không SAC. Không dataset 90k của Chen.")

    # ------------------------------------------------------------------ 6
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Nhánh A  ·  seed 42  ·  data/10", "Protocol lặp lại được — ER ~99% là TH2")

    table(
        s, 0.45, 1.22, 6.15, 2.05,
        [
            ["Table 4", "Precision", "Recall", "Acc / F1"],
            ["Paper 3 mạng", "99,67%", "100%", "99,83%"],
            ["Lab MLP/LSTM/CNN", "99,67%", "100%", "99,83%"],
        ],
        col_w=[2.1, 1.35, 1.2, 1.5],
        font_size=13,
    )
    txt(s, 0.45, 3.35, 6.15, 0.4, "Test n = 1.802  ·  TP 901  FP 3  TN 898  FN 0  ·  cả ba mạng một bộ số", size=12, color=MUTED)

    table(
        s, 6.80, 1.22, 6.05, 2.55,
        [
            ["PPO không Oracle", "ER lab", "Paper (10 seed)"],
            ["LSTM", "98,78%", "98,62%"],
            ["MLP", "98,67%", "99,73%"],
            ["CNN", "98,89%", "98,25%"],
        ],
        col_w=[2.2, 1.8, 2.05],
        font_size=13,
    )

    table(
        s, 0.45, 3.85, 12.4, 2.05,
        [
            ["RQ3 Oracle-in-loop (code −5, 250k, seed 42)", "ER lab", "ER paper", "RR(V) lab"],
            ["LSTM", "98,34%", "98,13%", "0"],
            ["MLP", "97,89%", "97,37%", "0"],
            ["CNN", "96,00%", "96,89%", "0,12%"],
        ],
        col_w=[5.2, 2.2, 2.4, 2.6],
        font_size=13,
    )
    txt(s, 0.45, 6.05, 12.4, 0.85,
        "LSTM: RR(E)=8,99%  ·  RR(V)=98,54%  ·  OR(V)=48,54%  →  lọt vì None, không vì XSS mạnh.  "
        "LSTM không Oracle 10 seed: 98,48% ± 0,31 (đủ bảng paper).  RQ3 trên 1 seed, cả 3 mạng >96%.",
        size=14, color=NAVY)
    footer(s, 6)
    notes(s,
          "Câu được: trên đúng artifact data/10, tái lập ER khoảng 99% và RQ3 ER lớn hơn 96% với RR gần 0 theo Oracle DOM. "
          "Câu cấm: coi 99% sau Oracle DOM là XSS còn chạy JavaScript. "
          "CNN seed 42 ER vẫn 99% nhưng RR(V) thấp — phương sai 1 seed, agent spam script.")

    # ------------------------------------------------------------------ 7
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Nhánh B  ·  JSDOM  ·  vocab cố định", "Cùng 27 action — ER 99% biến mất")

    callout(s, 0.45, 1.25, 4.05, 1.70, "P1  ·  LỌC MEREANI", "10.824", "giữ execute  ·  loại 3.542 parser-only  ·  RR gốc = 0")
    callout(s, 4.65, 1.25, 4.05, 1.70, "P3  ·  PPO 3×20k", "0,75%", "ER trung bình  ·  LSTM acc 99,1%", fill=NAVY2)
    callout(s, 8.85, 1.25, 4.00, 1.70, "P4  ·  R_exec", "0,25%", "PPO = sàn false-negative  ·  RR = 0", fill=GREEN)

    table(
        s, 0.45, 3.20, 12.4, 2.55,
        [
            ["Agent (LSTM đã khép OOV)", "Oracle trong train", "ER / TASR", "RR(E)"],
            ["P3 PPO  ·  tb 3 seed × 20k", "không", "0,75%", "0–0,33"],
            ["P4 PPO + R_exec  ·  tb 3 seed", "+10 chỉ khi lọt VÀ execute", "0,25%  = sàn FN", "0"],
            ["P4 Dueling DQN  ·  tb 3 seed", "như P4", "1,08%", "0"],
        ],
        col_w=[4.4, 3.6, 2.6, 1.8],
        font_size=14,
    )
    txt(s, 0.45, 5.90, 12.4, 0.95,
        "A18/A21 lab viết lại (artifact no-op / (1)(1)).  Wilcoxon P3 vs P4: n=2, p=0,5 — chỉ mô tả, không pretent ý nghĩa.  "
        "Không viết “DQN mạnh hơn Chen”.  Không viết replication ER 99% trên nhánh B.",
        size=14, color=NAVY)
    footer(s, 7)
    notes(s,
          "Khi khép LabelEncoder, PPO Table 2 không còn ER 99%. "
          "0,25% đúng bằng 1/400 — sàn FN detector, không phải tấn công mạnh. "
          "Mọi escape P4 vẫn execute (RR=0).")

    # ------------------------------------------------------------------ 8
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Kiểm tra bộ lọc  ·  P5", "CRS lab TASR = 0  ·  DOMPurify Δ = 1")

    table(
        s, 0.45, 1.22, 12.4, 2.55,
        [
            ["Đích (84 mẫu, /html)", "BLOCK", "NOEXEC", "EXEC", "Escape", "TASR", "Δ"],
            ["App không WAF  :13000", "0", "13", "71", "100%", "84,5%", "0,16"],
            ["CRS PL1  :18080", "84", "0", "0", "0", "0", "0"],
            ["CRS PL2  :18081", "84", "0", "0", "0", "0", "0"],
            ["DOMPurify", "0", "84", "0", "100%", "0", "1,00"],
        ],
        col_w=[3.2, 1.4, 1.5, 1.4, 1.5, 1.5, 1.5],
        font_size=13,
    )
    table(
        s, 0.45, 3.95, 12.4, 1.70,
        [
            ["Mở rộng trên CRS PL1", "n", "TASR"],
            ["Mereani × (gốc+27 action)  ·  chuỗi 2–3 action  ·  /attr /js", "1120+686+672+168", "0"],
            ["Transfer PPO P3 / P4  →  CRS (80 mẫu)", "80 + 80", "0"],
        ],
        col_w=[7.4, 3.2, 1.8],
        font_size=13,
    )
    txt(s, 0.45, 5.80, 12.4, 1.05,
        "WAF không dính token None.  Lọt HTTP ≠ còn độc (Purify).  Gate BYPASS_EXEC trên PL1 không đạt → không huấn luyện RL trên CRS.  "
        "Playwright Chromium hold-out 4 seed khớp JSDOM.  Không claim bypass WAF cloud.",
        size=15, color=NAVY)
    footer(s, 8)
    notes(s,
          "Demo curl: app 200, CRS 403, hello 200. "
          "TASR bằng 0 là kết quả kiểm tra bộ lọc, không phải thất bại đồ án. "
          "Purify: trình duyệt nhận 200 nhưng script bị tẩy.")

    # ------------------------------------------------------------------ 9
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Kết luận", "Sinh mẫu PPO đủ để kiểm tra — không cần lọt WAF")

    findings = [
        ("1", "Protocol Pasini lặp lại được trên data/10: Table 4 trùng, ER ~99%, RQ3 >96%, RR≈0 (Oracle DOM)."),
        ("2", "99% là TH2 (OOV/None + LabelEncoder từng mẫu), không phải XSS còn chạy JavaScript."),
        ("3", "Khép token-id + Oracle JS: PPO 0,75% → 0,25% (sàn FN); Dueling DQN 1,08%; RR=0."),
        ("4", "Mẫu PPO / catalog Table 2 trên CRS 4 lab: TASR=0. DOMPurify: Δ=1 (lọt HTTP, hết độc)."),
        ("5", "23,4% nhãn Malicious Mereani chỉ đổi DOM — Oracle paper ≠ XSS thực thi."),
    ]
    y = 1.22
    for n, line in findings:
        box(s, 0.45, y, 12.4, 0.72, fill=WHITE, line=LINE)
        txt(s, 0.58, y + 0.08, 0.45, 0.55, n, size=20, bold=True, color=AMBER, anchor=MSO_ANCHOR.MIDDLE)
        txt(s, 1.15, y + 0.08, 11.5, 0.55, line, size=15, color=INK, anchor=MSO_ANCHOR.MIDDLE)
        y += 0.80

    txt(s, 0.45, 5.35, 12.4, 0.35, "Hạn chế (nói trước khi bị hỏi)", size=13, bold=True, color=NAVY)
    multiline(s, 0.45, 5.70, 12.4, 1.2, [
        ("JSDOM ≠ mọi trình duyệt (có Playwright hold-out 4 seed).  RQ3 10 seed chưa đủ 3 mạng — seed 42 đủ Table 4 + RQ3.  Mereani 2018, chủ yếu alert/<script>.  CRS lab ≠ WAF thương mại.  Wilcoxon n=2 không pretent p.",
         {"size": 14, "color": MUTED}),
    ])
    footer(s, 9)
    notes(s,
          "Năm gạch này là slide chốt. Hướng phát triển: primitive BYPASS_EXEC trước khi train RL trên CRS; "
          "state nhìn payload; 10 seed RQ3 nếu hội đồng đòi số trung bình.")

    # ------------------------------------------------------------------ 10
    s = new_slide(prs)
    rect(s, 0, 0, 13.333, 7.5, PAPER)
    header(s, "Hỏi đáp", "Câu được nói  ·  câu không nói")

    table(
        s, 0.45, 1.22, 12.4, 2.85,
        [
            ["Họ hỏi", "Trả lời"],
            ["Sao không 99%?", "Nhánh B khép LabelEncoder. Nhánh A vẫn ~99% trên data/10."],
            ["Replication Chen?", "Protocol replication, PPO không SAC, Mereani không 90k."],
            ["Bypass CRS / WAF?", "Không. TASR lab = 0. Không đánh cloud."],
            ["10 seed?", "Paper 10. Seed 42 đủ Table 4 + RQ3 3 mạng. LSTM không Oracle đã 10 seed."],
            ["HTTP 200 là thành công?", "Không. Cần BYPASS_EXEC (200 và JS chạy) mới ra TASR."],
        ],
        col_w=[3.3, 9.1],
        font_size=13,
    )

    box(s, 0.45, 4.25, 6.05, 2.55, fill=RGBColor(0xE7, 0xF2, 0xEA), line=GREEN)
    multiline(s, 0.6, 4.35, 5.8, 2.35, [
        ("Được viết / nói", {"size": 15, "bold": True, "color": GREEN}),
        ("Khung Pasini: Oracle → RR → Oracle-in-loop", {"size": 14}),
        ("23,4% Mereani chỉ đổi DOM", {"size": 14}),
        ("Artifact tái lập ER ~99% (TH2)", {"size": 14}),
        ("Khép encode → ER ~1%", {"size": 14}),
        ("CRS lab TASR = 0  ·  Purify Δ = 1", {"size": 14}),
    ], gap=3)

    box(s, 6.75, 4.25, 6.10, 2.55, fill=RGBColor(0xF8, 0xE8, 0xE8), line=RED)
    multiline(s, 6.90, 4.35, 5.8, 2.35, [
        ("Cấm", {"size": 15, "bold": True, "color": RED}),
        ("“Em reproduce Chen 99%”", {"size": 14}),
        ("SAC  ·  PPO mạnh hơn Chen", {"size": 14}),
        ("Bypass CRS / AWS WAF", {"size": 14}),
        ("HTTP 200 = thành công  ·  LLM generator", {"size": 14}),
        ("Wilcoxon p=0,5 là có ý nghĩa", {"size": 14}),
    ], gap=3)
    footer(s, 10)
    notes(s,
          "Slide cuối. Nếu Docker chết: chiếu bảng P5, không improv. "
          "Cảm ơn hội đồng.")

    prs.save(str(OUT))
    print(f"Wrote {OUT}  ({OUT.stat().st_size} bytes, {len(prs.slides)} slides)")


if __name__ == "__main__":
    build()
