import bs4
import re
import json

file_path = r'C:/Users/RIYAS/Downloads/mca_aoc4_full_source_1784938237428.html'
output_md = r'C:/Users/RIYAS/.gemini/antigravity-ide/brain/2795f6fe-c257-4886-8374-88a4e78e10dd/aoc4_portal_structure.md'

print("Loading HTML file...")
with open(file_path, 'r', encoding='utf-8') as f:
    soup = bs4.BeautifulSoup(f.read(), 'html.parser')

print("Extracting AOC-4 form components...")

md_lines = []
md_lines.append("# MCA Form AOC-4 Portal HTML Component & Architecture Map")
md_lines.append("\nThis document contains the extracted HTML architecture, inputs, dropdowns, and radio buttons from the official MCA V3 AOC-4 portal page.\n")

# Find all guideFieldNode elements (AEM form components)
nodes = soup.find_all(class_=re.compile(r'guideFieldNode'))

md_lines.append(f"Total Form Nodes Found: **{len(nodes)}**\n")

sections = {}
current_section = "General Information"

for node in nodes:
    # Check if this node represents a section title or legend
    legend = node.find(class_=re.compile(r'guideFieldLabel|guidePanelTitle|legend'))
    label_text = ""
    if legend:
        label_text = legend.get_text(strip=True)

    # Check for text inputs
    text_input = node.find('input', attrs={'type': re.compile(r'text|number|hidden', re.I)})
    if not text_input and node.name == 'input':
        text_input = node

    # Check for select dropdowns
    select_el = node.find('select')

    # Check for radio buttons
    radios = node.find_all('input', attrs={'type': 'radio'})

    if label_text and ("SEGMENT" in label_text or "Part" in label_text or "General Information" in label_text):
        current_section = label_text

    if current_section not in sections:
        sections[current_section] = []

    if text_input:
        input_id = text_input.get('id', 'N/A')
        input_name = text_input.get('name', 'N/A')
        sections[current_section].append({
            "type": "Text/Date Input",
            "label": label_text,
            "id": input_id,
            "name": input_name
        })
    elif select_el:
        select_id = select_el.get('id', 'N/A')
        options = [opt.get_text(strip=True) for opt in select_el.find_all('option')]
        sections[current_section].append({
            "type": "Select Dropdown",
            "label": label_text,
            "id": select_id,
            "options": options[:5]
        })
    elif radios:
        radio_ids = [r.get('id', 'N/A') for r in radios]
        sections[current_section].append({
            "type": "Radio Group",
            "label": label_text,
            "ids": radio_ids
        })

for sec, items in sections.items():
    if not items:
        continue
    md_lines.append(f"## {sec}")
    md_lines.append(f"Total elements: {len(items)}\n")
    md_lines.append("| Type | Label | Element ID | Details |")
    md_lines.append("| :--- | :--- | :--- | :--- |")
    for item in items[:25]: # limit per section for brevity
        itype = item["type"]
        lbl = item["label"][:60].replace('|', '-')
        eid = item.get("id") or ", ".join(item.get("ids", []))
        eid = eid[:50]
        details = ", ".join(item.get("options", [])) if "options" in item else ""
        md_lines.append(f"| {itype} | {lbl} | `{eid}` | {details} |")
    md_lines.append("\n")

with open(output_md, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print("Successfully generated AOC-4 portal structure map at:", output_md)
