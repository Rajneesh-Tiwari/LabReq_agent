"""
Generate the client alignment deck as native PowerPoint shapes.

Usage:
    python3 build_client_deck.py

Produces: client_alignment_deck.pptx alongside this script.

8 slides:
  1. What we are building
  2. What "prior discipline to learn from" means
  3. The agents (cast of characters)
  4. The full flow at a glance (3 phases)
  5. Phase 1 — Setup: flowchart + theme catalog schema example
  6. Phase 2 — Per-document: flowchart + story schema example
  7. Phase 3 — Combine: flowchart + capability story example
  8. What ships and the alignment ask
"""

from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# ---- palette ---------------------------------------------------------------
BOX_FILL = RGBColor(0xE7, 0xEF, 0xF8)
BOX_LINE = RGBColor(0x4A, 0x6E, 0xA0)
ACCENT = RGBColor(0x1F, 0x4E, 0x79)
TEXT_DARK = RGBColor(0x1F, 0x2D, 0x3D)
TEXT_GREY = RGBColor(0x55, 0x60, 0x6E)
ARROW_COLOR = RGBColor(0x4A, 0x6E, 0xA0)
SYS_FILL = RGBColor(0xFA, 0xE9, 0xCB)
SYS_LINE = RGBColor(0xC9, 0x95, 0x2C)
DECISION_FILL = RGBColor(0xFC, 0xE7, 0xC4)
DECISION_LINE = RGBColor(0xC9, 0x95, 0x2C)
START_FILL = RGBColor(0xE0, 0xEC, 0xF8)
START_LINE = RGBColor(0x4A, 0x6E, 0xA0)
END_FILL = RGBColor(0xDC, 0xE9, 0xD7)
END_LINE = RGBColor(0x5C, 0x83, 0x47)
OUT_FILL = RGBColor(0xDC, 0xE9, 0xD7)
OUT_LINE = RGBColor(0x5C, 0x83, 0x47)
HUB_FILL = RGBColor(0xFC, 0xE0, 0xC4)
HUB_LINE = RGBColor(0xB8, 0x6A, 0x29)
PHASE_FILL = RGBColor(0xEE, 0xE7, 0xF8)
PHASE_LINE = RGBColor(0x6E, 0x4F, 0xA0)
CODE_FILL = RGBColor(0xF6, 0xF6, 0xF6)
CODE_LINE = RGBColor(0xC0, 0xC8, 0xD0)
SIDE_BRANCH_FILL = RGBColor(0xEC, 0xF4, 0xE8)
SIDE_BRANCH_LINE = RGBColor(0x5C, 0x83, 0x47)
PARK_FILL = RGBColor(0xF8, 0xE3, 0xE3)
PARK_LINE = RGBColor(0xA8, 0x4A, 0x4A)


# ---- text/shape helpers ---------------------------------------------------

def _set_text(shape, text, font_size, bold, color, align,
              anchor=MSO_ANCHOR.MIDDLE, font_name="Calibri", italic=False):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font_name


def add_box(slide, left, top, width, height, text, fill=BOX_FILL, line=BOX_LINE,
            font_size=12, bold=False, font_color=TEXT_DARK, align=PP_ALIGN.CENTER,
            shape_type=MSO_SHAPE.ROUNDED_RECTANGLE):
    box = slide.shapes.add_shape(shape_type, Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = fill
    box.line.color.rgb = line
    box.line.width = Pt(1.0)
    _set_text(box, text, font_size, bold, font_color, align)
    return box


def add_diamond(slide, left, top, width, height, text,
                fill=DECISION_FILL, line=DECISION_LINE,
                font_size=11, bold=True, color=TEXT_DARK):
    d = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(left), Inches(top),
                               Inches(width), Inches(height))
    d.fill.solid()
    d.fill.fore_color.rgb = fill
    d.line.color.rgb = line
    d.line.width = Pt(1.25)
    _set_text(d, text, font_size, bold, color, PP_ALIGN.CENTER)
    return d


def add_node(slide, left, top, width, height, text, kind="process",
             font_size=11, bold=False):
    """kind ∈ {start, end, process, agent, side, park}."""
    if kind == "start":
        return add_box(slide, left, top, width, height, text,
                       fill=START_FILL, line=START_LINE,
                       font_size=font_size, bold=True,
                       shape_type=MSO_SHAPE.ROUNDED_RECTANGLE)
    if kind == "end":
        return add_box(slide, left, top, width, height, text,
                       fill=END_FILL, line=END_LINE,
                       font_size=font_size, bold=True,
                       shape_type=MSO_SHAPE.ROUNDED_RECTANGLE)
    if kind == "agent":
        return add_box(slide, left, top, width, height, text,
                       fill=SYS_FILL, line=SYS_LINE,
                       font_size=font_size, bold=True)
    if kind == "side":
        return add_box(slide, left, top, width, height, text,
                       fill=SIDE_BRANCH_FILL, line=SIDE_BRANCH_LINE,
                       font_size=font_size, bold=bold)
    if kind == "park":
        return add_box(slide, left, top, width, height, text,
                       fill=PARK_FILL, line=PARK_LINE,
                       font_size=font_size, bold=bold)
    return add_box(slide, left, top, width, height, text,
                   font_size=font_size, bold=bold)


def add_text(slide, left, top, width, height, text, font_size=14,
             bold=False, italic=False, color=TEXT_DARK,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font_name="Calibri"):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top),
                                  Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font_name
    return tb


def add_bullets(slide, left, top, width, height, items, font_size=11,
                color=TEXT_DARK):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top),
                                  Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = "•  " + item
        run.font.size = Pt(font_size)
        run.font.color.rgb = color
        run.font.name = "Calibri"
        p.space_after = Pt(3)
    return tb


def add_arrow(slide, x1, y1, x2, y2, color=ARROW_COLOR, weight=2.0,
              connector_type=MSO_CONNECTOR.STRAIGHT, label=None,
              label_offset=(0, -0.18), label_color=TEXT_GREY,
              label_size=10, label_bold=False):
    conn = slide.shapes.add_connector(connector_type,
                                      Inches(x1), Inches(y1),
                                      Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(weight)
    line_elem = conn.line._get_or_add_ln()
    tail_end = etree.SubElement(line_elem, qn("a:tailEnd"))
    tail_end.set("type", "triangle")
    tail_end.set("w", "med")
    tail_end.set("h", "med")
    if label:
        lx = (x1 + x2) / 2 + label_offset[0]
        ly = (y1 + y2) / 2 + label_offset[1]
        tb = slide.shapes.add_textbox(Inches(lx), Inches(ly),
                                      Inches(0.9), Inches(0.3))
        tf = tb.text_frame
        tf.margin_left = Inches(0.04)
        tf.margin_right = Inches(0.04)
        tf.margin_top = Inches(0.0)
        tf.margin_bottom = Inches(0.0)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = label
        run.font.size = Pt(label_size)
        run.font.bold = label_bold
        run.font.color.rgb = label_color
        run.font.name = "Calibri"
    return conn


def add_title(slide, text, color=ACCENT):
    add_text(slide, 0.5, 0.32, 12.5, 0.6, text,
             font_size=26, bold=True, color=color)
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(0.5), Inches(0.95),
                                 Inches(1.6), Inches(0.06))
    bar.fill.solid()
    bar.fill.fore_color.rgb = color
    bar.line.fill.background()


def add_footer(slide, slide_num, total_slides, deck_label="LIMS Story Generation — Client Alignment"):
    """Subtle footer: thin horizontal line + deck label (left) + slide number (right)."""
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                  Inches(0.5), Inches(7.18),
                                  Inches(12.33), Inches(0.012))
    line.fill.solid()
    line.fill.fore_color.rgb = RGBColor(0xD0, 0xD6, 0xDC)
    line.line.fill.background()
    add_text(slide, 0.5, 7.22, 8.0, 0.25, deck_label,
             font_size=8, italic=True, color=RGBColor(0x90, 0x97, 0x9F),
             align=PP_ALIGN.LEFT)
    add_text(slide, 11.83, 7.22, 1.0, 0.25,
             f"{slide_num} / {total_slides}",
             font_size=8, color=RGBColor(0x90, 0x97, 0x9F),
             align=PP_ALIGN.RIGHT)


def add_code_box(slide, left, top, width, height, content, font_size=10,
                 title=None, fill=CODE_FILL, line=CODE_LINE):
    """Code-style block with monospace font for schema examples."""
    if title:
        add_text(slide, left, top - 0.32, width, 0.3, title,
                 font_size=11, bold=True, color=ACCENT)
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                 Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = fill
    box.line.color.rgb = line
    box.line.width = Pt(0.75)
    tf = box.text_frame
    tf.word_wrap = False
    tf.margin_left = Inches(0.12)
    tf.margin_right = Inches(0.12)
    tf.margin_top = Inches(0.08)
    tf.margin_bottom = Inches(0.08)
    tf.vertical_anchor = MSO_ANCHOR.TOP
    lines = content.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        run = p.add_run()
        run.text = ln
        run.font.size = Pt(font_size)
        run.font.color.rgb = TEXT_DARK
        run.font.name = "Consolas"
        p.space_after = Pt(0)
    return box


def add_step_box(slide, left, top, width, height, number, text,
                 fill=BOX_FILL, line=BOX_LINE, number_color=ACCENT,
                 font_size=11):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                 Inches(left), Inches(top),
                                 Inches(width), Inches(height))
    box.fill.solid()
    box.fill.fore_color.rgb = fill
    box.line.color.rgb = line
    box.line.width = Pt(1.0)
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.5)
    tf.margin_right = Inches(0.1)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.color.rgb = TEXT_DARK
    run.font.name = "Calibri"
    badge_d = 0.36
    badge = slide.shapes.add_shape(MSO_SHAPE.OVAL,
                                   Inches(left + 0.07),
                                   Inches(top + (height - badge_d) / 2),
                                   Inches(badge_d), Inches(badge_d))
    badge.fill.solid()
    badge.fill.fore_color.rgb = number_color
    badge.line.fill.background()
    _set_text(badge, str(number), font_size=11, bold=True,
              color=RGBColor(0xFF, 0xFF, 0xFF), align=PP_ALIGN.CENTER)
    return box


# ---- slide 1 --------------------------------------------------------------

def slide_one(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "What we are building")

    add_text(slide, 0.5, 1.1, 12.5, 0.6,
             "A system that turns lab procedure documents into a ready-to-use "
             "backlog of dev work — without an expert reviewing each item.",
             font_size=15, color=TEXT_DARK)

    box_w, box_h, y = 3.4, 1.4, 2.0
    x1, x2, x3 = 0.6, 4.95, 9.3
    add_box(slide, x1, y, box_w, box_h,
            "Lab procedure documents\n(SOPs)",
            font_size=14, bold=True)
    add_box(slide, x2, y, box_w, box_h, "Our system",
            fill=SYS_FILL, line=SYS_LINE, font_size=18, bold=True)
    add_box(slide, x3, y, box_w, box_h,
            "Dev backlog\n(Jira: Epics + Stories)",
            fill=OUT_FILL, line=OUT_LINE, font_size=14, bold=True)
    add_arrow(slide, x1 + box_w + 0.05, y + box_h / 2,
              x2 - 0.05, y + box_h / 2)
    add_arrow(slide, x2 + box_w + 0.05, y + box_h / 2,
              x3 - 0.05, y + box_h / 2)
    add_text(slide, x2, y + box_h + 0.1, box_w, 0.4,
             "Plus: configuration files + audit log",
             font_size=11, italic=True, color=TEXT_GREY,
             align=PP_ALIGN.CENTER)

    add_text(slide, 0.5, 4.4, 12.5, 0.4,
             "Why this matters", font_size=18, bold=True, color=ACCENT)
    add_bullets(slide, 0.7, 4.9, 12.0, 1.5, [
        "Today: every new procedure → manual expert review → hand-written stories. Slow, costly, inconsistent.",
        "With this system: documents in, structured stories out. Quality is built into the rules, not into one expert's review.",
        "Same system, any clinical discipline. Each new discipline is a configuration change, not an engineering project.",
    ], font_size=13)


# ---- slide 2 --------------------------------------------------------------

def slide_two(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "What does \"prior discipline to learn from\" mean?")

    add_text(slide, 0.5, 1.1, 12.5, 0.5,
             "It's a teaching reference — a discipline whose dev work has already been "
             "validated. For our project, that's Cytology.",
             font_size=14, color=TEXT_DARK)

    hub_w, hub_h = 2.6, 1.1
    hub_x = (13.333 - hub_w) / 2
    hub_y = 2.0
    add_box(slide, hub_x, hub_y, hub_w, hub_h,
            "Prior discipline\n(Cytology)",
            fill=HUB_FILL, line=HUB_LINE, font_size=15, bold=True)

    # MANDATORY row (top): two larger boxes
    mand_w, mand_h = 3.6, 1.35
    mand_y = 1.85
    add_box(slide, 0.5, mand_y, mand_w, mand_h,
            "Theme starter set\nVocabulary of workflow categories\n(Pre-Analytic, Analytic, Reporting, …)",
            fill=BOX_FILL, line=BOX_LINE, font_size=12, bold=True)
    add_box(slide, 13.333 - mand_w - 0.5, mand_y, mand_w, mand_h,
            "Epic starter set\nHigh-level dev groupings\n(Specimen Receiving, Reporting, Billing, …)",
            fill=BOX_FILL, line=BOX_LINE, font_size=12, bold=True)
    # mandatory badges
    add_text(slide, 0.5, mand_y - 0.3, 1.4, 0.3, "MANDATORY",
             font_size=9, bold=True, color=ACCENT)
    add_text(slide, 13.333 - mand_w - 0.5, mand_y - 0.3, 1.4, 0.3,
             "MANDATORY", font_size=9, bold=True, color=ACCENT)

    # arrows from hub to two mandatory boxes
    add_arrow(slide, hub_x, hub_y + hub_h * 0.45,
              0.5 + mand_w, mand_y + mand_h * 0.5,
              color=HUB_LINE, weight=2.0)
    add_arrow(slide, hub_x + hub_w, hub_y + hub_h * 0.45,
              13.333 - mand_w - 0.5, mand_y + mand_h * 0.5,
              color=HUB_LINE, weight=2.0)

    # OPTIONAL row (bottom): single box, dimmer
    opt_w, opt_h = 6.0, 1.2
    opt_y = 4.05
    opt_x = (13.333 - opt_w) / 2
    add_box(slide, opt_x, opt_y, opt_w, opt_h,
            "Story exemplars\nFew-shot examples for the Story Extractor\n"
            "Used IF prior-discipline Jira is accessible — system runs without them",
            fill=RGBColor(0xF6, 0xF6, 0xF6), line=RGBColor(0xA0, 0xA0, 0xA0),
            font_size=11)
    add_text(slide, opt_x, opt_y - 0.3, 2.0, 0.3,
             "OPTIONAL (enhancement)", font_size=9, bold=True,
             color=RGBColor(0x80, 0x80, 0x80))
    # arrow from hub down to optional box (dashed-feel via lighter color)
    add_arrow(slide, hub_x + hub_w / 2, hub_y + hub_h,
              opt_x + opt_w / 2, opt_y,
              color=RGBColor(0xA0, 0xA0, 0xA0), weight=1.5)

    # bottom: not inherited
    add_text(slide, 0.5, 5.55, 12.5, 0.35,
             "Not inherited from the prior discipline",
             font_size=14, bold=True, color=ACCENT)
    add_text(slide, 0.7, 5.92, 12.5, 0.45,
             "Tests   •   Roles   •   Documents (new discipline's SOPs)   •   "
             "Tasks (out of scope; dev team owns decomposition)",
             font_size=11, color=TEXT_GREY)
    add_text(slide, 0.5, 6.45, 12.5, 0.6,
             "Quality-check thresholds use defaults tuned by first-run telemetry — "
             "no holdout calibration against the prior discipline is needed.",
             font_size=10, italic=True, color=TEXT_GREY)


# ---- slide 3: the agents --------------------------------------------------

def slide_three(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "The agents — cast of characters")

    add_text(slide, 0.5, 1.1, 12.5, 0.5,
             "Six agents do the work. Plus a 5-reviewer panel that votes "
             "when admitting new categories.",
             font_size=13, color=TEXT_DARK)

    # table of agents
    headers = ["#", "Agent", "What it does", "When it runs"]
    rows = [
        ["1", "Theme Discovery",
         "Builds the new discipline's theme catalog (categories) by classifying "
         "sample documents against the prior discipline's themes; new themes "
         "emerge only with evidence.",
         "Once per new discipline\n(re-runs only on alarm)"],
        ["2", "Epic Extractor (conditioned)",
         "Drafts high-level epics from each document; matches each draft "
         "against the prior discipline's epic catalog. Matches inherit; "
         "non-matches are clustered for novelty review.",
         "Once per document\n+ batch novelty pass"],
        ["3", "Story Extractor",
         "Drafts user stories from document chunks using schema + shape "
         "definitions + closed-enum catalogs. Optionally retrieves "
         "(test, role, stage, shape)-matched exemplars from the prior "
         "discipline's Jira if it's available — improves style fidelity.",
         "Per epic, per document"],
        ["4", "Validator (quality check)",
         "Quality-checks every emitted story against shape-specific rules "
         "(MUST/SHALL for capabilities; concrete values for configurations; "
         "named artifact for cleanups). Failures auto-park.",
         "Twice per story\n(after extract + after synthesis)"],
        ["5", "Cross-SOP Synthesis",
         "After all documents are processed, finds patterns recurring across "
         "≥ 2 documents and lifts them into broader \"capability stories\" "
         "with parameters.",
         "Once per batch"],
        ["6", "Dependency Resolver",
         "Resolves dependencies between stories into a topological order — "
         "the final ordered backlog the dev team consumes.",
         "Once per batch"],
    ]

    n_rows = len(rows) + 1
    table_x = 0.4
    table_y = 1.65
    table_w = 12.55
    table_h = 0.4 + (n_rows - 1) * 0.6
    tbl_shape = slide.shapes.add_table(n_rows, len(headers),
                                       Inches(table_x), Inches(table_y),
                                       Inches(table_w), Inches(table_h))
    table = tbl_shape.table

    widths_in = [0.5, 2.4, 6.5, 3.15]
    for i, w in enumerate(widths_in):
        table.columns[i].width = Inches(w)

    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT
        tf = cell.text_frame
        tf.margin_left = Inches(0.08)
        tf.margin_right = Inches(0.08)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT if j > 0 else PP_ALIGN.CENTER
        run = p.add_run()
        run.text = h
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.name = "Calibri"
    table.rows[0].height = Inches(0.4)

    for i, row in enumerate(rows):
        table.rows[i + 1].height = Inches(0.6)
        for j, val in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.fill.solid()
            cell.fill.fore_color.rgb = (
                RGBColor(0xFA, 0xE9, 0xCB) if j == 1 else
                RGBColor(0xF8, 0xFA, 0xFC) if i % 2 == 0 else
                RGBColor(0xFF, 0xFF, 0xFF)
            )
            tf = cell.text_frame
            tf.word_wrap = True
            tf.margin_left = Inches(0.08)
            tf.margin_right = Inches(0.08)
            tf.margin_top = Inches(0.04)
            tf.margin_bottom = Inches(0.04)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if j in (0, 3) else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = val
            run.font.size = Pt(10) if j == 2 else Pt(10)
            run.font.bold = (j == 1)
            run.font.color.rgb = TEXT_DARK
            run.font.name = "Calibri"

    callout_y = table_y + table_h + 0.18
    callout_h = 7.05 - callout_y
    add_box(slide, 0.4, callout_y, 12.55, callout_h,
            "Quorum panel (5 reviewer agents):  used by Theme Discovery and Epic Extractor when admitting "
            "new categories. Each reviewer asks a different question — \"is this coherent?\", \"is it distinct?\", "
            "\"is the description sharp?\", etc. Need 3 of 5 agreeing on the same action; their descriptions must "
            "be similar enough to count. Otherwise the candidate goes to the review pile for the next round.",
            fill=SYS_FILL, line=SYS_LINE,
            font_size=11, bold=False, font_color=TEXT_DARK,
            align=PP_ALIGN.LEFT, shape_type=MSO_SHAPE.ROUNDED_RECTANGLE)


# ---- slide 4: full flow at a glance ---------------------------------------

def slide_four(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "The full flow — three phases")

    add_text(slide, 0.5, 1.1, 12.5, 0.5,
             "End-to-end view. Each phase is detailed in the next three slides.",
             font_size=13, italic=True, color=TEXT_GREY)

    phase_w, phase_h = 3.95, 3.4
    phase_y = 2.0
    px = [0.4, 4.7, 9.0]
    titles = [
        ("Phase 1\nSetup",
         "Build theme & epic catalogs for the new discipline, conditioned on the prior discipline.",
         "Agents: Theme Discovery, Epic Extractor, Quorum panel.",
         "Runs once per new discipline.\nRepeats only if alarm fires."),
        ("Phase 2\nPer-document",
         "Read each procedure document, draft stories, quality-check.",
         "Agents: Epic Extractor, Story Extractor, Validator.",
         "Runs for every new procedure document."),
        ("Phase 3\nCombine + ship",
         "Look across all documents, lift recurring patterns, generate outputs.",
         "Agents: Cross-SOP Synthesis, Validator, Dependency Resolver.",
         "Runs after a batch of documents is processed."),
    ]
    for x, (head, mid, agents, foot) in zip(px, titles):
        add_box(slide, x, phase_y, phase_w, 0.85, head,
                fill=PHASE_FILL, line=PHASE_LINE,
                font_size=15, bold=True, font_color=ACCENT)
        add_text(slide, x + 0.15, phase_y + 1.0, phase_w - 0.3, 1.1,
                 mid, font_size=12, color=TEXT_DARK,
                 align=PP_ALIGN.CENTER)
        add_text(slide, x + 0.15, phase_y + 2.1, phase_w - 0.3, 0.65,
                 agents, font_size=10, italic=True, color=TEXT_GREY,
                 align=PP_ALIGN.CENTER)
        add_text(slide, x + 0.15, phase_y + 2.7, phase_w - 0.3, 0.6,
                 foot, font_size=10, italic=True, color=TEXT_GREY,
                 align=PP_ALIGN.CENTER)

    arrow_y = phase_y + 0.4
    add_arrow(slide, px[0] + phase_w + 0.05, arrow_y, px[1] - 0.05, arrow_y, weight=2.5)
    add_arrow(slide, px[1] + phase_w + 0.05, arrow_y, px[2] - 0.05, arrow_y, weight=2.5)

    cont_y = 5.85
    add_box(slide, 0.4, cont_y, 12.55, 0.6,
            "Continuous (alongside all phases): "
            "drift report   •   alarm-driven re-runs when too many items go to the review pile",
            fill=RGBColor(0xF1, 0xF5, 0xFA), line=BOX_LINE,
            font_size=11, font_color=TEXT_DARK,
            align=PP_ALIGN.CENTER, shape_type=MSO_SHAPE.RECTANGLE)


# ---- slide 5: phase 1 — flowchart + theme catalog example ----------------

def slide_five(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "Phase 1 — Setup: building the theme catalog")

    add_text(slide, 0.5, 1.05, 12.5, 0.4,
             "Run once for a new discipline. Result: a theme catalog mostly inherited "
             "from the prior discipline + 0–N new themes (each with evidence).",
             font_size=12, color=TEXT_DARK)

    # ----- left half: flowchart (compact for footer fit) -----
    fx = 0.5
    nw = 3.0
    nh = 0.45
    cx = fx + nw / 2
    dh = 0.6

    y1 = 1.55
    add_node(slide, fx, y1, nw, nh, "Sample SOPs (~20)\n+ prior discipline's themes",
             kind="start", font_size=9, bold=True)
    y2 = y1 + nh + 0.15
    add_node(slide, fx, y2, nw, nh, "Tag chunks: theme, test, role, stage",
             kind="process", font_size=9)
    y3 = y2 + nh + 0.15
    add_node(slide, fx, y3, nw, nh, "Compare each chunk to prior discipline's themes",
             kind="process", font_size=9)
    y4 = y3 + nh + 0.15
    add_diamond(slide, fx + 0.4, y4, nw - 0.8, dh,
                "Score ≥ match\nthreshold?", font_size=9)
    inh_x = fx + nw + 0.4
    inh_y = y4 + (dh - nh) / 2
    add_node(slide, inh_x, inh_y, 2.5, nh,
             "Inherit theme\n(into new catalog)",
             kind="side", font_size=9, bold=True)
    y6 = y4 + dh + 0.3
    add_node(slide, fx, y6, nw, nh, "Cluster residual into candidates",
             kind="process", font_size=9)
    y7 = y6 + nh + 0.15
    add_node(slide, fx, y7, nw, nh, "5-reviewer quorum panel votes",
             kind="agent", font_size=9, bold=True)
    y8 = y7 + nh + 0.15
    add_diamond(slide, fx + 0.4, y8, nw - 0.8, dh,
                "3 of 5 agree?", font_size=9)
    park_x = fx + nw + 0.4
    park_y = y8 + (dh - nh) / 2
    add_node(slide, park_x, park_y, 2.5, nh,
             "Park to review pile\n(retry next cycle)",
             kind="park", font_size=9, bold=True)
    y9 = y8 + dh + 0.3
    add_node(slide, fx, y9, nw, nh, "New discipline's theme catalog",
             kind="end", font_size=10, bold=True)

    # arrows in the flowchart
    add_arrow(slide, cx, y1 + nh, cx, y2)
    add_arrow(slide, cx, y2 + nh, cx, y3)
    add_arrow(slide, cx, y3 + nh, cx, y4)
    # diamond branches
    add_arrow(slide, fx + nw - 0.4, y4 + dh / 2, inh_x, inh_y + nh / 2,
              label="yes\n(inherit)", label_offset=(0.05, -0.32),
              label_color=END_LINE, label_bold=True)
    add_arrow(slide, cx, y4 + dh, cx, y6,
              label="no\n(residual)", label_offset=(0.08, -0.18),
              label_color=PARK_LINE, label_bold=True)
    add_arrow(slide, cx, y6 + nh, cx, y7)
    add_arrow(slide, cx, y7 + nh, cx, y8)
    # quorum branches
    add_arrow(slide, fx + nw - 0.4, y8 + dh / 2, park_x, park_y + nh / 2,
              label="no", label_offset=(0.05, -0.18),
              label_color=PARK_LINE, label_bold=True)
    add_arrow(slide, cx, y8 + dh, cx, y9,
              label="yes (admit)", label_offset=(0.05, -0.18),
              label_color=END_LINE, label_bold=True)
    # branches converge into final node from the side branches
    # inherit → final
    add_arrow(slide, inh_x + 1.25, inh_y + nh, inh_x + 1.25, y9 + nh / 2,
              color=SIDE_BRANCH_LINE, weight=1.25,
              connector_type=MSO_CONNECTOR.ELBOW)

    # ----- right half: theme catalog YAML example -----
    code_x = 7.7
    code_y = 1.6
    code_w = 5.4
    code_h = 4.7
    yaml_text = """new_lab_theme_catalog:
  catalog_id: micro_v1
  parent_catalog: cyto_v1     # prior discipline

  inherited_from_cytology:    # carried over by Pass 1
    - Pre-Analytic
    - Analytic
    - Post-Analytic
    - Reporting
    - QC
    - Compliance
    - Instrumentation
    - Platform

  newly_added:                # admitted by quorum
    - id: MI1
      name: Susceptibility Testing
      evidence: 42 chunks
      quorum_decision:
        votes: [admit×5]
        decision: admit
    - id: MI2
      name: Biosafety Containment
      evidence: 28 chunks
      quorum_decision:
        votes: [admit×4, fold→Compliance]
        decision: admit

  unclassified_bucket:        # left for next round
    count: 38
    pct: 6.3%"""
    add_code_box(slide, code_x, code_y, code_w, code_h, yaml_text,
                 font_size=9.5, title="Example output: theme catalog (simplified)")

    # short explainer below the yaml
    add_text(slide, code_x, code_y + code_h + 0.1, code_w, 0.65,
             "Read this top-down: most categories carry over from Cytology. "
             "Two new ones (Susceptibility Testing, Biosafety Containment) "
             "earned their place via quorum vote with evidence.",
             font_size=10, italic=True, color=TEXT_GREY)


# ---- slide 6: phase 2 — flowchart + story example ------------------------

def slide_six(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "Phase 2 — Per-document processing")

    add_text(slide, 0.5, 1.05, 12.5, 0.4,
             "Runs once per procedure document. Result: validated stories under the right epics.",
             font_size=12, color=TEXT_DARK)

    # ----- left half: flowchart -----
    fx = 0.5
    nw = 3.0
    nh = 0.55
    cx = fx + nw / 2
    dh = 0.75

    y1 = 1.55
    add_node(slide, fx, y1, nw, nh, "SOP arrives", kind="start",
             font_size=10, bold=True)

    y2 = y1 + 0.75
    add_node(slide, fx, y2, nw, nh,
             "Tag chunks: theme, test, role, stage",
             kind="process", font_size=10)

    y3 = y2 + 0.75
    add_node(slide, fx, y3, nw, nh,
             "Epic Extractor: draft + match",
             kind="agent", font_size=10, bold=True)

    y4 = y3 + 0.75
    add_node(slide, fx, y4, nw, nh,
             "Story Extractor: draft\n(uses exemplars if available)",
             kind="agent", font_size=10, bold=True)

    y5 = y4 + 0.85
    add_node(slide, fx, y5, nw, nh,
             "Validator: quality-check (shape rules)",
             kind="agent", font_size=10, bold=True)

    y6 = y5 + 0.75
    add_diamond(slide, fx + 0.4, y6, nw - 0.8, dh,
                "Pass quality?", font_size=10)
    # fail branch (right)
    fail_x = fx + nw + 0.4
    fail_y = y6 + 0.1
    add_node(slide, fail_x, fail_y, 2.4, nh,
             "Revise (≤2 tries)\nthen review pile",
             kind="park", font_size=10, bold=True)

    y7 = y6 + dh + 0.45
    add_node(slide, fx, y7, nw, nh, "Story kept (validated)",
             kind="end", font_size=11, bold=True)

    # arrows
    add_arrow(slide, cx, y1 + nh, cx, y2)
    add_arrow(slide, cx, y2 + nh, cx, y3)
    add_arrow(slide, cx, y3 + nh, cx, y4)
    add_arrow(slide, cx, y4 + nh, cx, y5)
    add_arrow(slide, cx, y5 + nh, cx, y6)
    add_arrow(slide, fx + nw - 0.4, y6 + dh / 2, fail_x, fail_y + nh / 2,
              label="no", label_color=PARK_LINE, label_bold=True,
              label_offset=(0.05, -0.18))
    add_arrow(slide, cx, y6 + dh, cx, y7,
              label="yes", label_color=END_LINE, label_bold=True,
              label_offset=(0.05, -0.18))

    # ----- right half: story schema example -----
    code_x = 7.7
    code_y = 1.55
    code_w = 5.4
    code_h = 4.5
    yaml_text = """story:
  id: STORY-MICRO-0042
  shape: capability       # one of:
                          #   capability,
                          #   workflow-stage-split,
                          #   configuration-instance,
                          #   cleanup
  title: "Validate received specimens
          against open orders"
  acceptance_criteria:
    - when: "specimen received with
             accession number"
      then: "system MUST match against
             open order"
  tests: [gram_stain, blood_culture]
  persona: lims           # closed enum
  stage: accessioning_verification
  source_citation: SOP-MICRO-014, lines 23-31
  epic_id: EPIC-MICRO-001 (Specimen Receiving)
  quality: passed         # or: parked"""
    add_code_box(slide, code_x, code_y, code_w, code_h, yaml_text,
                 font_size=9.5, title="Example output: a single story (simplified)")

    add_text(slide, code_x, code_y + code_h + 0.05, code_w, 0.85,
             "Every story carries: shape, tests, role, stage, source citation, "
             "and quality verdict. Closed-enum fields are checked against the "
             "catalogs — out-of-list values are rejected, no questions asked.",
             font_size=10, italic=True, color=TEXT_GREY)


# ---- slide 7: phase 3 — flowchart + capability story example ------------

def slide_seven(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "Phase 3 — Combine patterns + continuous monitoring")

    add_text(slide, 0.5, 1.05, 12.5, 0.4,
             "Runs after a batch of documents. Recurring patterns lift to "
             "broader \"capability stories\" with parameters.",
             font_size=12, color=TEXT_DARK)

    # ----- left half: flowchart (compact for footer fit) -----
    fx = 0.5
    nw = 3.0
    nh = 0.45
    cx = fx + nw / 2
    dh = 0.6

    y1 = 1.55
    add_node(slide, fx, y1, nw, nh,
             "All kept stories\nfrom all documents",
             kind="start", font_size=9, bold=True)

    y2 = y1 + nh + 0.15
    add_node(slide, fx, y2, nw, nh,
             "Cluster on (test, role, stage,\nshape, behavior)",
             kind="process", font_size=9)

    y3 = y2 + nh + 0.15
    add_diamond(slide, fx + 0.3, y3, nw - 0.6, dh,
                "Pattern in\n≥ 2 docs?", font_size=9)
    keep_x = fx + nw + 0.4
    keep_y = y3 + (dh - nh) / 2
    add_node(slide, keep_x, keep_y, 2.5, nh,
             "Keep concrete\nstory only",
             kind="side", font_size=9, bold=True)

    y4 = y3 + dh + 0.3
    add_node(slide, fx, y4, nw, nh,
             "Lift to capability story\n(parameterized)",
             kind="agent", font_size=9, bold=True)

    y5 = y4 + nh + 0.15
    add_node(slide, fx, y5, nw, nh,
             "Validator (gate 2)",
             kind="agent", font_size=9, bold=True)

    y6 = y5 + nh + 0.15
    add_node(slide, fx, y6, nw, nh,
             "Dependency Resolver\n(topological order)",
             kind="agent", font_size=9, bold=True)

    y7 = y6 + nh + 0.15
    add_node(slide, fx, y7, nw, nh,
             "Final ordered backlog",
             kind="end", font_size=10, bold=True)

    add_arrow(slide, cx, y1 + nh, cx, y2)
    add_arrow(slide, cx, y2 + nh, cx, y3)
    add_arrow(slide, fx + nw - 0.3, y3 + dh / 2, keep_x, keep_y + nh / 2,
              label="no", label_color=SIDE_BRANCH_LINE, label_bold=True,
              label_offset=(0.05, -0.18))
    add_arrow(slide, cx, y3 + dh, cx, y4,
              label="yes", label_color=END_LINE, label_bold=True,
              label_offset=(0.05, -0.18))
    add_arrow(slide, cx, y4 + nh, cx, y5)
    add_arrow(slide, cx, y5 + nh, cx, y6)
    add_arrow(slide, cx, y6 + nh, cx, y7)
    # keep-branch joins the final
    add_arrow(slide, keep_x + 1.25, keep_y + nh,
              keep_x + 1.25, y7 + nh / 2,
              color=SIDE_BRANCH_LINE, weight=1.25,
              connector_type=MSO_CONNECTOR.ELBOW)

    # ----- right half: capability story example -----
    code_x = 7.7
    code_y = 1.6
    code_w = 5.4
    code_h = 4.0
    yaml_text = """capability_story:
  id: STORY-MICRO-CAP-0007
  shape: capability
  title: "Configurable critical-result
          notification across tests"

  parameters:                # what varies
    - test:      enum
    - threshold: number+units
    - persona_owner: supervisor

  acceptance_criteria:
    - when: "{test} flagged critical"
      then: "notify {persona_owner}
             within 1 hour"

  child_stories:             # the concrete
    - STORY-MICRO-0023       # cases
    - STORY-MICRO-0041       # this lifted
    - STORY-MICRO-0089       # from
  source_documents: [SOP-014, SOP-019, SOP-022]"""
    add_code_box(slide, code_x, code_y, code_w, code_h, yaml_text,
                 font_size=9.5, title="Example: a lifted capability story")

    # continuous-monitoring banner
    cont_y = 5.8
    add_box(slide, code_x, cont_y, code_w, 0.7,
            "Continuous monitoring (alongside): drift report; "
            "alarm when review pile or unclassified bucket > 5%; auto-rerun "
            "with looser threshold on alarm.",
            fill=RGBColor(0xF1, 0xF5, 0xFA), line=BOX_LINE,
            font_size=10, font_color=TEXT_DARK,
            align=PP_ALIGN.LEFT, shape_type=MSO_SHAPE.RECTANGLE)


# ---- slide 8: what ships + alignment --------------------------------------

def slide_eight(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(slide, "What ships and the alignment ask")

    deliv_y = 1.3
    deliv_w = 4.0
    deliv_h = 1.5
    gap = 0.3
    total = 3 * deliv_w + 2 * gap
    start_x = (13.333 - total) / 2

    deliveries = [
        ("Jira backlog",
         "Epics + Stories\nReady for the dev team\nIncludes traceability to source docs"),
        ("Configuration files",
         "Per-test settings\n(e.g. blood culture parameters)\nDeterministic structure"),
        ("Reference + audit",
         "Theme catalog, epic catalog\nCross-discipline mapping\nReview pile + decision log"),
    ]
    for i, (head, body) in enumerate(deliveries):
        x = start_x + i * (deliv_w + gap)
        add_box(slide, x, deliv_y, deliv_w, 0.55, head,
                fill=OUT_FILL, line=OUT_LINE,
                font_size=15, bold=True)
        bb = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE,
                                    Inches(x), Inches(deliv_y + 0.55),
                                    Inches(deliv_w), Inches(deliv_h - 0.55))
        bb.fill.solid()
        bb.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        bb.line.color.rgb = OUT_LINE
        bb.line.width = Pt(1.0)
        _set_text(bb, body, font_size=11, bold=False, color=TEXT_DARK,
                  align=PP_ALIGN.CENTER)

    add_text(slide, 0.5, 3.15, 12.5, 0.4,
             "What we need from the client — mandatory",
             font_size=15, bold=True, color=ACCENT)
    add_bullets(slide, 0.7, 3.55, 12.0, 1.6, [
        "The list of tests for each discipline in scope (blood culture, urine culture, target pathogens for Microbiology).",
        "The list of roles in those disciplines (with type: human / system / external).",
        "The prior discipline's theme catalog and epic catalog (small structured YAMLs — Cytology for the seminal extension).",
        "A sample of ~20 procedure documents per new discipline to seed Phase 1.",
    ], font_size=11)

    add_text(slide, 0.5, 5.15, 12.5, 0.35,
             "Optional — quality enhancement",
             font_size=12, bold=True, italic=True, color=TEXT_GREY)
    add_bullets(slide, 0.7, 5.5, 12.0, 0.5, [
        "Sanitized prior-discipline Jira export — improves story style fidelity if available; not required for the system to function.",
    ], font_size=11, color=TEXT_GREY)

    add_box(slide, 0.5, 6.15, 12.55, 0.85,
            "Alignment ask: do these inputs match what's available on your side, "
            "and does the output match what your dev team would consume?",
            fill=SYS_FILL, line=SYS_LINE,
            font_size=13, bold=True, font_color=ACCENT,
            align=PP_ALIGN.CENTER)


# ---- main -----------------------------------------------------------------

def main():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    slide_one(prs)
    slide_two(prs)
    slide_three(prs)
    slide_four(prs)
    slide_five(prs)
    slide_six(prs)
    slide_seven(prs)
    slide_eight(prs)

    # add footers with slide numbers
    total = len(prs.slides)
    for i, slide in enumerate(prs.slides, start=1):
        add_footer(slide, i, total)

    out = Path(__file__).parent / "client_alignment_deck.pptx"
    prs.save(str(out))
    print(f"wrote: {out}  ({total} slides)")


if __name__ == "__main__":
    main()
