"""
PDF Diagnostic Script — Analyzes financial statement PDF structure
Run: python diagnose_pdf.py
"""
import pdfplumber
import json
import sys

PDF_PATH = r"C:\Users\RIYAS\Downloads\FINANCIALS FY 21-22 (1).pdf"

def diagnose():
    pdf = pdfplumber.open(PDF_PATH)
    print(f"Total pages: {len(pdf.pages)}")
    
    all_text = []
    all_tables = []
    
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            print(f"\n{'='*60}")
            print(f"PAGE {i+1}")
            print(f"{'='*60}")
            print(text[:3000])
            all_text.append(text)
        
        tables = page.extract_tables()
        if tables:
            print(f"\n--- TABLES on page {i+1}: {len(tables)} tables ---")
            for j, table in enumerate(tables):
                print(f"\nTable {j+1} ({len(table)} rows):")
                for row in table[:15]:
                    print(f"  {row}")
                if len(table) > 15:
                    print(f"  ... ({len(table)-15} more rows)")
                all_tables.append({"page": i+1, "table": j+1, "rows": table})
    
    pdf.close()
    
    # Save full extracted text and tables to JSON for analysis
    output = {
        "total_pages": len(all_text),
        "full_text": all_text,
        "tables": [
            {"page": t["page"], "table_num": t["table"], "row_count": len(t["rows"]), "rows": t["rows"]}
            for t in all_tables
        ]
    }
    
    with open("pdf_diagnosis.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nFull diagnosis saved to: pdf_diagnosis.json")


if __name__ == "__main__":
    diagnose()
