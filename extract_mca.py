"""
SI AOC-4 Pro — Complete MCA Form Field Extractor
Extracts EVERY form field from the downloaded MCA HTML file.
Outputs: Label, Type, AEM ID, CSS Classes, Current Value
"""
import re
import json
import os

file_path = r'C:/Users/RIYAS/Downloads/mca_aoc4_full_source_1784938237428.html'

print("=" * 80)
print("SI AOC-4 Pro — Complete MCA Form Field Extractor")
print("=" * 80)
print(f"Loading HTML file: {file_path}")
print("This may take 10-20 seconds for a 6MB file...\n")

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: beautifulsoup4 not installed. Run: pip install beautifulsoup4")
    exit(1)

with open(file_path, 'r', encoding='utf-8') as f:
    raw_html = f.read()

soup = BeautifulSoup(raw_html, 'html.parser')

print(f"HTML loaded. Total size: {len(raw_html):,} bytes\n")

# ============================================================
# PHASE 1: Extract ALL visible form elements
# ============================================================
all_fields = []
field_index = 0

# Find all input, select, textarea elements
for tag in soup.find_all(['input', 'select', 'textarea']):
    tag_type = tag.get('type', 'text')
    tag_id = tag.get('id', '')
    tag_name = tag.get('name', '')
    tag_value = tag.get('value', '')
    tag_class = ' '.join(tag.get('class', []))
    tag_placeholder = tag.get('placeholder', '')

    # Skip hidden inputs and navigation/header elements
    if tag_type == 'hidden':
        continue
    if tag_id in ['searchbox', 'searchbox2', 'themesbox', 'loginRedirect']:
        continue

    # Find the nearest label text
    label_text = ""

    # Strategy 1: Look for guideWidgetLabel inside the parent guideFieldNode
    parent_field = tag.find_parent('div', class_=re.compile(r'guideFieldNode'))
    if parent_field:
        label_el = parent_field.find('label', class_='guideWidgetLabel')
        if label_el:
            label_text = ' '.join(label_el.get_text().split()).strip()

    # Strategy 2: Look for any label with matching 'for' attribute
    if not label_text and tag_id:
        label_el = soup.find('label', {'for': tag_id})
        if label_el:
            label_text = ' '.join(label_el.get_text().split()).strip()

    # Strategy 3: Look at the closest parent's text content (first 100 chars)
    if not label_text:
        parent = tag.parent
        if parent:
            raw_text = ' '.join(parent.get_text().split()).strip()
            if len(raw_text) > 120:
                raw_text = raw_text[:120] + "..."
            label_text = raw_text

    # For radio buttons, also capture the radio's own label
    radio_option_text = ""
    if tag_type == 'radio':
        next_label = tag.find_next_sibling('label')
        if next_label:
            radio_option_text = next_label.get_text().strip()
        else:
            parent_label = tag.find_parent('label')
            if parent_label:
                radio_option_text = parent_label.get_text().strip()

    # For select, capture options
    options_list = []
    if tag.name == 'select':
        for opt in tag.find_all('option'):
            options_list.append({
                "value": opt.get('value', ''),
                "text": opt.get_text().strip(),
                "selected": opt.has_attr('selected')
            })

    field_data = {
        "index": field_index,
        "tag": tag.name.upper(),
        "type": tag_type,
        "id": tag_id,
        "name": tag_name,
        "value": tag_value,
        "placeholder": tag_placeholder,
        "class": tag_class,
        "label": label_text,
        "radio_option": radio_option_text,
        "select_options": options_list if options_list else None,
        "parent_field_id": parent_field.get('id', '') if parent_field else '',
        "parent_field_class": ' '.join(parent_field.get('class', [])) if parent_field else '',
    }

    all_fields.append(field_data)
    field_index += 1

print(f"Found {len(all_fields)} form fields total.\n")

# ============================================================
# PHASE 2: Categorize by type
# ============================================================
text_fields = [f for f in all_fields if f['type'] == 'text' and f['tag'] == 'INPUT']
radio_fields = [f for f in all_fields if f['type'] == 'radio']
select_fields = [f for f in all_fields if f['tag'] == 'SELECT']
date_fields = [f for f in all_fields if 'date' in f['id'].lower() or 'date' in f['class'].lower()]
checkbox_fields = [f for f in all_fields if f['type'] == 'checkbox']

print("=" * 80)
print(f"TEXT INPUTS: {len(text_fields)}")
print(f"RADIO BUTTONS: {len(radio_fields)}")
print(f"SELECT/DROPDOWN: {len(select_fields)}")
print(f"DATE PICKERS: {len(date_fields)}")
print(f"CHECKBOXES: {len(checkbox_fields)}")
print("=" * 80)

# ============================================================
# PHASE 3: Print details
# ============================================================

print("\n\n" + "=" * 80)
print("📋 ALL TEXT INPUT FIELDS")
print("=" * 80)
for f in text_fields:
    print(f"\n[{f['index']}] Label: {f['label'][:100]}")
    print(f"     ID: {f['id'][:80]}")
    print(f"     Value: '{f['value']}'")
    print(f"     Placeholder: '{f['placeholder']}'")

print("\n\n" + "=" * 80)
print("🔘 ALL RADIO BUTTONS")
print("=" * 80)
for f in radio_fields:
    print(f"\n[{f['index']}] Group Label: {f['label'][:100]}")
    print(f"     Option: {f['radio_option']}")
    print(f"     ID: {f['id'][:80]}")
    print(f"     Value: '{f['value']}'")

print("\n\n" + "=" * 80)
print("📜 ALL DROPDOWNS (SELECT)")
print("=" * 80)
for f in select_fields:
    print(f"\n[{f['index']}] Label: {f['label'][:100]}")
    print(f"     ID: {f['id'][:80]}")
    if f['select_options']:
        for opt in f['select_options']:
            sel_marker = " ← SELECTED" if opt['selected'] else ""
            print(f"       Option: value='{opt['value']}' text='{opt['text']}'{sel_marker}")

# ============================================================
# PHASE 4: Save full JSON output
# ============================================================
output_path = os.path.join(os.path.dirname(file_path), 'mca_form_fields_extracted.json')
with open(output_path, 'w', encoding='utf-8') as jf:
    json.dump(all_fields, jf, indent=2, ensure_ascii=False)

print(f"\n\n{'=' * 80}")
print(f"✅ Full JSON saved to: {output_path}")
print(f"{'=' * 80}")
print("\nDone! Copy the console output above and paste it into the chat.")
