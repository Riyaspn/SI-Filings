import json
import os
from parser_engine import parse_financial_statement, extract_from_aoc4_pdf

financials_pdf = r'C:\Users\RIYAS\Downloads\FINANCIALS FY 21-22 (1).pdf'
aoc4_pdf = r'C:\Users\RIYAS\Downloads\AOC-4.pdf'

print("================================================================================")
print("INDEPENDENT AUDIT: Parsing FINANCIALS FY 21-22 (1).pdf with updated parser")
print("================================================================================")

# Step 1: Parse Financials PDF
parsed_result = parse_financial_statement(financials_pdf)
financials_data = parsed_result["data"]

# Step 2: Parse Ground Truth AOC-4 PDF
aoc4_data, aoc4_matched, _ = extract_from_aoc4_pdf(aoc4_pdf)

print("\n--- NEW PARSED DATA FROM FINANCIALS PDF ---")
print(json.dumps(financials_data, indent=2))

print("\n================================================================================")
print("AUDIT COMPARISON TABLE: FINANCIALS PDF PARSER vs AOC-4.PDF GROUND TRUTH")
print("================================================================================")

audit_report = []
audit_report.append("| Field Key | Field Label | Extracted from Financials PDF (CY / PY) | AOC-4.pdf Ground Truth (CY / PY) | Audit Result |")
audit_report.append("| :--- | :--- | :--- | :--- | :--- |")

for key, val in financials_data.items():
    aoc_val = aoc4_data.get(key)
    
    if isinstance(val, dict):
        cy_ext = val.get("current_year")
        py_ext = val.get("previous_year")
        ext_str = f"CY: {cy_ext} | PY: {py_ext}"
        
        if isinstance(aoc_val, dict):
            cy_gt = aoc_val.get("current_year")
            py_gt = aoc_val.get("previous_year")
            gt_str = f"CY: {cy_gt} | PY: {py_gt}"
        else:
            gt_str = f"{aoc_val}"
            
        status = "✅ MATCH" if (cy_ext == cy_gt and (py_ext == py_gt or py_gt is None)) else "🔍 CHECK"
    else:
        ext_str = str(val)
        gt_str = str(aoc_val)
        status = "✅ MATCH" if ext_str == gt_str else "💡 DISCREPANCY / DEFAULT"

    audit_report.append(f"| `{key}` | {key.replace('_', ' ').title()} | `{ext_str}` | `{gt_str}` | {status} |")

report_text = "\n".join(audit_report)
print(report_text)

with open(r'C:\Users\RIYAS\.gemini\antigravity-ide\brain\2795f6fe-c257-4886-8374-88a4e78e10dd\independent_parser_audit.md', 'w', encoding='utf-8') as f:
    f.write("# Independent Audit: Financials PDF Parser vs AOC-4 PDF Ground Truth\n\n" + report_text)

print("\nSaved full audit report to independent_parser_audit.md")
