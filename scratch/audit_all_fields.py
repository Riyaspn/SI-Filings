import sys
import openpyxl
import re

# Load AOC4_SCHEMA keys from aoc4_schema.py
from aoc4_schema import AOC4_SCHEMA, get_financial_field_keys
from excel_populator import ExcelPopulator

def audit():
    schema_keys = set(f["key"] for f in AOC4_SCHEMA)
    
    # Extract populator mappings by creating a dummy populator object or reading the file
    with open("excel_populator.py", "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract mapping dict from content using regex or python execution
    # Let's inspect mapping keys
    populator_keys = set(re.findall(r'"([a-zA-Z0-9_]+)":\s*\[\(', content))
    
    print("=== AUDIT SUMMARY ===")
    print(f"Total Schema Keys in AI Extractor: {len(schema_keys)}")
    print(f"Total Populator Mapped Keys: {len(populator_keys)}")
    
    unmapped_in_populator = schema_keys - populator_keys
    print(f"\nSchema keys NOT mapped in Excel Populator ({len(unmapped_in_populator)}):")
    for k in sorted(unmapped_in_populator):
        print(f" - {k}")

    # Check gap_analysis.md for all input rows in Excel
    with open(r"c:\Users\RIYAS\.gemini\antigravity-ide\brain\2795f6fe-c257-4886-8374-88a4e78e10dd\gap_analysis.md", "r", encoding="utf-8") as f:
        gap_lines = f.readlines()
        
    excel_rows = []
    for line in gap_lines:
        # Match table row | row_num | label | cy_col | py_col | mapped_key | ...
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 6 and parts[1].isdigit():
            row_num = int(parts[1])
            label = parts[2]
            cy_col = parts[3]
            py_col = parts[4]
            mapped_key = parts[5]
            if cy_col or py_col:
                excel_rows.append((row_num, label, cy_col, py_col, mapped_key))
                
    print(f"\nTotal Input-Capable Rows in Excel Template: {len(excel_rows)}")
    
    # Unmapped Excel rows
    unmapped_excel = [r for r in excel_rows if r[4] in ("NO", "")]
    print(f"Excel Rows currently unmapped to AI Schema ({len(unmapped_excel)}):")
    for r in unmapped_excel[:30]:
        print(f" - Row {r[0]}: {r[1]} (CY: {r[2]}, PY: {r[3]})")

if __name__ == "__main__":
    audit()
