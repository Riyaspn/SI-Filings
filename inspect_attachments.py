"""
Inspect MCA Attachment PDFs (Auditor's Report Extract & Board's Report Extract)
Run: python inspect_attachments.py
"""

import pdfplumber

FILES = [
    r"C:\Users\RIYAS\Downloads\Extract of Auditor's Report (Standalone).pdf",
    r"C:\Users\RIYAS\Downloads\Extract of Board's Report.pdf",
]

for filepath in FILES:
    print("=" * 70)
    print(f"ATTACHMENT FILE: {filepath}")
    print("=" * 70)

    pdf = pdfplumber.open(filepath)
    print(f"Total Pages: {len(pdf.pages)}")

    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            print(f"\n--- Page {i+1} ---")
            print(text[:1500])

    pdf.close()
