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
        
    # Extract Paragraph font size (e.g., "font size 14" or "font size to 14")
    para_match = re.search(r'font size.*?(\d+)', instructions)
    if para_match:
        rules["paragraph"]["size"] = int(para_match.group(1))
        
    # Extract Heading font size (e.g., "heading 16")
    head_match = re.search(r'heading.*?(\d+)', instructions)
    if head_match:
        rules["heading"]["size"] = int(head_match.group(1))
        
    # Extract Subheading bold (e.g., "make subheadings bold")
    if 'subheading' in instructions and 'bold' in instructions:
        rules["subheading"]["bold"] = True

    return rules

def classify_paragraph(para):
    """
    A simple offline heuristic to guess if a text is a heading, subheading, or paragraph.
    """
    text = para.text.strip()
    style_name = para.style.name.lower()
    
    if not text:
        return None
        
    # Check Word's built-in styles first
    if 'heading 1' in style_name or 'title' in style_name:
        return 'heading'
    if 'heading' in style_name:
        return 'subheading'
        
    # Fallback to visual heuristics:
    # If it's short, doesn't end with a period, it's likely a subheading
    if len(text) < 60 and not text.endswith('.'):
        # If it's very short and title-cased, maybe it's a main heading
        if len(text) < 30 and text.istitle():
            return 'heading'
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
