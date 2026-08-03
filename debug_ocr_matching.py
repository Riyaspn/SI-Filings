"""
Debug Local OCR Output & Pattern Matching for FINANCIALS FY 21-22 (1).pdf
Run: python debug_ocr_matching.py
"""

import json
from local_ocr import extract_text_from_scanned_page, extract_scanned_pdf_pages
from parser_engine import _match_rows_to_schema, parse_indian_number, LABEL_PATTERNS
from aoc4_schema import get_empty_aoc4_data

PDF_PATH = r"C:\Users\RIYAS\Downloads\FINANCIALS FY 21-22 (1).pdf"

print("=" * 70)
print("INSPECTING LOCAL OCR OUTPUT ON PAGES 1 TO 6...")
print("=" * 70)

for page_idx in range(6):
    lines, rows = extract_text_from_scanned_page(PDF_PATH, page_idx)
    print(f"\n--- PAGE {page_idx + 1} ({len(lines)} lines, {len(rows)} rows) ---")
    for r in rows[:15]:
        print(f"  ROW: {r}")

# Now test matching across all OCR rows
all_lines, all_rows = extract_scanned_pdf_pages(PDF_PATH, list(range(6)))
data = get_empty_aoc4_data()
matched, unmatched = _match_rows_to_schema(all_rows, data)

print("\n" + "=" * 70)
print(f"MATCHING RESULTS ON LOCAL OCR ROWS ({len(all_rows)} total rows):")
print(f"  Matched ({len(matched)}): {matched}")
print(f"  Unmatched ({len(unmatched)}): {unmatched[:10]}")
print("=" * 70)
