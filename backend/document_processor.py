import re
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH


# ===========================================================
# Patterns that clearly indicate the line is NOT a heading
# ===========================================================
MCQ_OPTION_PATTERN    = re.compile(r'^\s*[a-dA-D][\.\)]\s+\S')  # a) or A. option
MCQ_QUESTION_PATTERN  = re.compile(r'^\s*Q?\d+[\.\)]\s+\S')     # 1. or Q1. question
BULLET_PATTERN        = re.compile(r'^\s*[-•*]\s+\S')            # bullet points
NUMBERED_LIST_PATTERN = re.compile(r'^\s*\d+\.\s+[a-z]')        # 1. lowercase sentence
URL_PATTERN           = re.compile(r'https?://\S+')              # web links
EMAIL_PATTERN         = re.compile(r'\S+@\S+\.\S+')              # email addresses

# ===========================================================
# Patterns that clearly indicate a heading or subheading
# ===========================================================
NUMBERED_SECTION_PATTERN  = re.compile(r'^\d+\.\d+(\.\d+)?[\s\t]+\S')   # 1.1 Title
MAIN_SECTION_PATTERN      = re.compile(r'^\d+\.\s+\S')                   # 1. Title


def extract_formatting_rules(instructions):
    """
    Uses Python regex to extract user-defined formatting rules without any API.
    Supports keywords: heading/headings, subheading/subheadings, text/paragraph/font.
    Also supports bold, italic, color instructions.
    """
    if not instructions.strip():
        return {
            "heading":    {"size": 16, "bold": True},
            "subheading": {"size": 14, "bold": True},
            "paragraph":  {"size": 12, "bold": False},
            "mcq":        {"size": 12, "bold": False},
            "option":     {"size": 11, "bold": False},
        }

    text = instructions.lower()

    rules = {
        "heading":    {"size": 16, "bold": True},
        "subheading": {"size": 14, "bold": True},
        "paragraph":  {"size": 12, "bold": False},
        "mcq":        {"size": 12, "bold": False},
        "option":     {"size": 11, "bold": False},
    }

    # --- Paragraph / Text / Font size ---
    m = re.search(r'(?:text|paragraph|font)\s*(?:size)?\s*(?:to\s*)?(?:be\s*)?(\d+)', text)
    if m:
        rules["paragraph"]["size"] = int(m.group(1))
        rules["mcq"]["size"]       = int(m.group(1))

    # --- Heading size ---
    m = re.search(r'(?<!sub)heading[s]?\s*(?:size)?\s*(?:to\s*)?(?:be\s*)?(\d+)', text)
    if m:
        rules["heading"]["size"] = int(m.group(1))

    # --- Subheading size ---
    m = re.search(r'subheading[s]?\s*(?:size)?\s*(?:to\s*)?(?:be\s*)?(\d+)', text)
    if m:
        rules["subheading"]["size"] = int(m.group(1))

    # --- Option size (e.g., "options 10" or "option size 10") ---
    m = re.search(r'option[s]?\s*(?:size)?\s*(?:to\s*)?(?:be\s*)?(\d+)', text)
    if m:
        rules["option"]["size"] = int(m.group(1))

    # --- Bold control ---
    if re.search(r'subheading[s]?\s+bold|bold\s+subheading[s]?', text):
        rules["subheading"]["bold"] = True
    if re.search(r'heading[s]?\s+not\s+bold|no\s+bold\s+heading[s]?', text):
        rules["heading"]["bold"] = False

    return rules


def classify_paragraph(para):
    """
    Multi-tier classifier using:
    1. Word built-in styles (most reliable)
    2. Regex patterns (MCQ options, numbered sections, bullets, etc.)
    3. Heuristic word count / casing rules (fallback)
    """
    text       = para.text.strip()
    style_name = para.style.name.lower() if para.style and para.style.name else ""

    if not text:
        return None

    # ---- Tier 1: Word built-in styles ----
    if 'title' in style_name or 'heading 1' in style_name:
        return 'heading'
    if 'heading' in style_name:
        return 'subheading'

    # ---- Tier 2: Strict regex patterns ----

    # MCQ option lines: a) ..., B. ..., c) ...
    if MCQ_OPTION_PATTERN.match(text):
        return 'option'

    # MCQ question lines: 1. ..., Q2. ..., 10. ...
    if MCQ_QUESTION_PATTERN.match(text):
        return 'mcq'

    # Bullet point lines — treat as paragraph content
    if BULLET_PATTERN.match(text):
        return 'paragraph'

    # Numbered list with lowercase sentence — it's a paragraph
    if NUMBERED_LIST_PATTERN.match(text):
        return 'paragraph'

    # Numbered section heading: 1. Title or 1.1 Title or 1.1.1 Title
    if MAIN_SECTION_PATTERN.match(text):
        return 'heading'
    if NUMBERED_SECTION_PATTERN.match(text):
        return 'subheading'

    # Lines that are clearly data (URLs, emails) → paragraph
    if URL_PATTERN.search(text) or EMAIL_PATTERN.search(text):
        return 'paragraph'

    # ---- Tier 3: Heuristic word count / casing ----
    words = text.split()

    # If it ends with a colon it is probably a heading/subheading (e.g., "References:")
    if text.endswith(':') and len(words) <= 6:
        return 'heading' if len(words) <= 3 else 'subheading'

    # ALL CAPS short line → main heading
    if text.isupper() and len(words) <= 10:
        return 'heading'

    # Short phrase, no sentence-ending punctuation
    if len(words) <= 12 and not text.endswith(('.', ',', ';', ':', '?', '!')):
        if len(words) <= 5:
            return 'heading'
        return 'subheading'

    return 'paragraph'


def process_document(input_path, output_path, instructions):
    """
    Completely offline and free document processor.
    Applies user-defined (or default) formatting rules to each paragraph.
    """
    doc   = Document(input_path)
    rules = extract_formatting_rules(instructions)
    print("Extracted Rules (Offline Mode):", rules)

    for para in doc.paragraphs:
        if not para.text.strip():
            continue

        ptype = classify_paragraph(para)
        if not ptype:
            continue

        original_text = para.text
        para.clear()

        run        = para.add_run(original_text)
        style_rule = rules.get(ptype, rules["paragraph"])

        # Font size
        if style_rule.get("size"):
            run.font.size = Pt(int(style_rule["size"]))

        # Bold
        run.bold = bool(style_rule.get("bold", False))

    doc.save(output_path)
