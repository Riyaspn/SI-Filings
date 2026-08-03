"""
Test zero/nil field matching on FINANCIALS FY 21-22 (1).pdf
Run: python test_zero_fields.py
"""

from local_ocr import extract_scanned_pdf_pages
from parser_engine import parse_financial_statement

PDF_PATH = r"C:\Users\RIYAS\Downloads\FINANCIALS FY 21-22 (1).pdf"

result = parse_financial_statement(PDF_PATH)

print("=" * 70)
print(f"RESULTS FOR: {PDF_PATH}")
print("=" * 70)
print(f"Confidence: {result['confidence']:.1%}")
print(f"Matched ({result['matched_count']}/{result['total_fields']}): {result['matched']}")
print(f"Unmatched ({len(result['unmatched'])}): {result['unmatched']}")

print("\nDetailed Field Values Extracted:")
for k, v in result['data'].items():
    if v is not None:
        print(f"  {k:<32}: {v}")
