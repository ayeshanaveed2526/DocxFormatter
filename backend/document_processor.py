import re
from docx import Document
from docx.shared import Pt

def extract_formatting_rules(instructions):
    """
    Uses Python regex to extract rules offline without any API!
    """
    instructions = instructions.lower()
    
    # Defaults
    rules = {
        "heading": {"size": 16, "bold": True},
        "subheading": {"size": 14, "bold": True},
        "paragraph": {"size": 12, "bold": False}
    }
    
    if not instructions.strip():
        return rules
        
    # Extract Paragraph / Text font size (keywords: "text", "paragraph", "font size")
    para_match = re.search(r'(?:text|paragraph|font)\s*(?:size)?\s*(?:to\s*)?(?:be\s*)?(\d+)', instructions)
    if para_match:
        rules["paragraph"]["size"] = int(para_match.group(1))
        
    # Extract Heading font size (keywords: "heading", "headings")
    head_match = re.search(r'(?<!sub)heading[s]?\s*(?:size)?\s*(?:to\s*)?(?:be\s*)?(\d+)', instructions)
    if head_match:
        rules["heading"]["size"] = int(head_match.group(1))
        
    # Extract Subheading font size (keywords: "subheading", "subheadings")
    subhead_match = re.search(r'subheading[s]?\s*(?:size)?\s*(?:to\s*)?(?:be\s*)?(\d+)', instructions)
    if subhead_match:
        rules["subheading"]["size"] = int(subhead_match.group(1))
        
    # Extract Subheading bold (e.g., "make subheadings bold")
    if 'subheading' in instructions and 'bold' in instructions:
        rules["subheading"]["bold"] = True

    return rules

def classify_paragraph(para):
    """
    A simple offline heuristic to guess if a text is a heading, subheading, or paragraph.
    """
    text = para.text.strip()
    style_name = para.style.name.lower() if para.style and para.style.name else ""
    
    if not text:
        return None
        
    # Check Word's built-in styles first
    if 'heading 1' in style_name or 'title' in style_name:
        return 'heading'
    if 'heading' in style_name:
        return 'subheading'
        
    # Detect numerical subheading figures like 1.1, 2.2, 3.4.1
    if re.match(r'^\d+\.\d+(\.\d+)?\b', text):
        return 'subheading'
        
    # Fallback to visual heuristics:
    # Check word count and ending punctuation
    words = text.split()
    if len(words) <= 12 and not text.endswith('.') and not text.endswith(','):
        # ALL CAPS is a strong indicator of a main heading
        if text.isupper():
            return 'heading'
            
        # Very short phrases (1-5 words) are usually main headings regardless of case
        if len(words) <= 5:
            return 'heading'
            
        # Otherwise, if it's slightly longer (6-12 words) without a period, it's a subheading
        return 'subheading'
        
    return 'paragraph'

def process_document(input_path, output_path, instructions):
    """
    Completely offline and free document processor.
    """
    doc = Document(input_path)
    rules = extract_formatting_rules(instructions)
    print("Extracted Rules (Offline Mode):", rules)
    
    for para in doc.paragraphs:
        if not para.text.strip():
            continue
            
        ptype = classify_paragraph(para)
        if not ptype:
            continue
            
        original_text = para.text
        
        # Clear existing text
        para.clear()
        
        # Apply style based on extracted rules
        run = para.add_run(original_text)
        style_rule = rules.get(ptype, rules["paragraph"])
        
        # Set Font Size
        if "size" in style_rule and style_rule["size"]:
            run.font.size = Pt(int(style_rule["size"]))
            
        # Set Bold
        if "bold" in style_rule:
            run.bold = bool(style_rule["bold"])
            
    doc.save(output_path)
