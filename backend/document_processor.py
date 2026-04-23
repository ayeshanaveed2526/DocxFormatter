import re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

MCQ_OPTION_PATTERN    = re.compile(r'^\s*[a-dA-D][\.\)]\s+\S')
MCQ_QUESTION_PATTERN  = re.compile(r'^\s*Q?\d+[\.\)]\s+\S')
BULLET_PATTERN        = re.compile(r'^\s*[-•*]\s+\S')
NUMBERED_LIST_PATTERN = re.compile(r'^\s*\d+\.\s+[a-z]')
URL_PATTERN           = re.compile(r'https?://\S+')
EMAIL_PATTERN         = re.compile(r'\S+@\S+\.\S+')
NUMBERED_SECTION_PATTERN = re.compile(r'^\d+\.\d+(\.\d+)?[\s\t]+\S')
MAIN_SECTION_PATTERN     = re.compile(r'^\d+\.\s+\S')


def classify_paragraph(para):
    text       = para.text.strip()
    style_name = para.style.name.lower() if para.style and para.style.name else ""
    if not text:
        return None
    if 'title' in style_name or 'heading 1' in style_name:
        return 'heading'
    if 'heading' in style_name:
        return 'subheading'
    if MCQ_OPTION_PATTERN.match(text):
        return 'option'
    if MCQ_QUESTION_PATTERN.match(text):
        return 'mcq'
    if BULLET_PATTERN.match(text) or NUMBERED_LIST_PATTERN.match(text):
        return 'paragraph'
    if MAIN_SECTION_PATTERN.match(text):
        return 'heading'
    if NUMBERED_SECTION_PATTERN.match(text):
        return 'subheading'
    if URL_PATTERN.search(text) or EMAIL_PATTERN.search(text):
        return 'paragraph'
    words = text.split()
    if text.endswith(':') and len(words) <= 6:
        return 'heading' if len(words) <= 3 else 'subheading'
    if text.isupper() and len(words) <= 10:
        return 'heading'
    if len(words) <= 12 and not text.endswith(('.', ',', ';', ':', '?', '!')):
        return 'heading' if len(words) <= 5 else 'subheading'
    return 'paragraph'


def set_page_margins(doc, top, bottom, left, right):
    for section in doc.sections:
        section.top_margin    = Cm(top)
        section.bottom_margin = Cm(bottom)
        section.left_margin   = Cm(left)
        section.right_margin  = Cm(right)


def set_page_orientation(doc, orientation):
    from docx.enum.section import WD_ORIENT
    for section in doc.sections:
        if orientation == 'landscape':
            section.orientation = WD_ORIENT.LANDSCAPE
            if section.page_width < section.page_height:
                section.page_width, section.page_height = section.page_height, section.page_width
        else:
            section.orientation = WD_ORIENT.PORTRAIT
            if section.page_width > section.page_height:
                section.page_width, section.page_height = section.page_height, section.page_width


def add_page_number_field(run):
    """Insert an auto-updating page number field into a run."""
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.text = 'PAGE'
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)


def set_header(doc, header_text, page_number_position):
    """Set header text and optional page number."""
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        # Clear existing content
        for p in header.paragraphs:
            p.clear()

        para = header.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if header_text:
            run = para.add_run(header_text)
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        if page_number_position == 'top':
            if header_text:
                para.add_run('  |  Page ')
            else:
                para.add_run('Page ')
            num_run = para.add_run()
            num_run.font.size = Pt(10)
            add_page_number_field(num_run)


def set_footer(doc, footer_text, page_number_position):
    """Set footer text and optional page number."""
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        for p in footer.paragraphs:
            p.clear()

        para = footer.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if footer_text:
            run = para.add_run(footer_text)
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        if page_number_position == 'bottom':
            if footer_text:
                para.add_run('  |  Page ')
            else:
                para.add_run('Page ')
            num_run = para.add_run()
            num_run.font.size = Pt(10)
            add_page_number_field(num_run)


def process_document(input_path, output_path, rules):
    """
    Offline document processor with full formatting control.
    """
    doc = Document(input_path)
    print("Applying Rules:", rules)

    # ── Margins ──────────────────────────────────────────────
    margins = rules.get("margins", {})
    if margins:
        set_page_margins(
            doc,
            top    = float(margins.get("top",    2.54)),
            bottom = float(margins.get("bottom", 2.54)),
            left   = float(margins.get("left",   2.54)),
            right  = float(margins.get("right",  2.54)),
        )

    # ── Orientation ───────────────────────────────────────────
    set_page_orientation(doc, rules.get("orientation", "portrait"))

    # ── Header & Footer ───────────────────────────────────────
    header_text           = rules.get("headerText", "")
    footer_text           = rules.get("footerText", "")
    page_number_position  = rules.get("pageNumbers", "none")  # 'top' | 'bottom' | 'none'

    set_header(doc, header_text, page_number_position)
    set_footer(doc, footer_text, page_number_position)

    # ── Typography ─────────────────────────────────────────────
    for para in doc.paragraphs:
        if not para.text.strip():
            continue
        ptype = classify_paragraph(para)
        if not ptype:
            continue

        original_text = para.text
        para.clear()
        run = para.add_run(original_text)
        style_rule = rules.get(ptype, rules.get("paragraph", {"size": 12, "bold": False}))

        if style_rule.get("size"):
            run.font.size = Pt(int(style_rule["size"]))
        run.bold = bool(style_rule.get("bold", False))

    doc.save(output_path)
