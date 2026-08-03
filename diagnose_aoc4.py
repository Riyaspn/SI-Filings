"""
AOC-4 Filed Documents Analyzer
Run: python diagnose_aoc4.py
Analyzes the completed AOC-4 filing PDFs to understand
the exact fields and values we need to extract.
"""
import pdfplumber
import json

AOC4_FILES = [
    r"C:\Users\RIYAS\Downloads\AOC-4.pdf",
    r"C:\Users\RIYAS\Downloads\Extract of Auditor's Report (Standalone).pdf",
    r"C:\Users\RIYAS\Downloads\Extract of Board's Report.pdf",
]

def analyze():
    all_results = {}
    
    for filepath in AOC4_FILES:
        filename = filepath.split("\\")[-1]
        print(f"\n{'='*70}")
        print(f"FILE: {filename}")
        print(f"{'='*70}")
        
        try:
            pdf = pdfplumber.open(filepath)
            file_text = []
            file_tables = []
            
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    print(f"\n--- Page {i+1} ---")
                    print(text[:3000])
                    file_text.append(text)
                
                tables = page.extract_tables()
                if tables:
                    for j, table in enumerate(tables):
                        print(f"\n  Table {j+1} on page {i+1} ({len(table)} rows):")
                        for row in table[:20]:
                            print(f"    {row}")
                        file_tables.append({"page": i+1, "rows": table})
            
            all_results[filename] = {
                "pages": len(pdf.pages),
                "text": file_text,
                "tables": [{"page": t["page"], "rows": t["rows"]} for t in file_tables]
            }
            pdf.close()
        
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results[filename] = {"error": str(e)}
    
    with open("aoc4_diagnosis.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n\nFull AOC-4 diagnosis saved to: aoc4_diagnosis.json")


if __name__ == "__main__":
    analyze()
