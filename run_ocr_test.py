"""
Test local OCR directly on FINANCIALS FY 21-22 (1).pdf
Run: python run_ocr_test.py
"""

from local_ocr import extract_scanned_pdf_pages

PDF_PATH = r"C:\Users\RIYAS\Downloads\FINANCIALS FY 21-22 (1).pdf"

print("Testing Local OCR on scanned pages 1-6...")
lines, rows = extract_scanned_pdf_pages(PDF_PATH, [0, 1, 2, 3, 4, 5])

print(f"\nExtracted {len(lines)} total text lines across pages 1-6!")
print("Sample extracted lines:")
for line in lines[:20]:
    print(f"  {line}")

print(f"\nSample extracted table rows:")
for row in rows[:15]:
    print(f"  {row}")
