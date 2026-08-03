"""
Audit the FILLED Excel to find:
1. Cells with 0 that should NOT have 0 (e.g., "Reason for change" text columns)
2. Empty cells that SHOULD have 0 but don't
"""
import openpyxl

filepath = r"C:\Users\RIYAS\Downloads\AOC-4_U92410KL2020PTC065216_2021-2022_20260729_FILLED.xlsx"

wb = openpyxl.load_workbook(filepath, data_only=True)
sheet = wb["FORM"]

print("=== AUDIT: Cells with value 0 that look suspicious ===")
print("Looking at columns I(9), L(12) which are 'Reason for change' text columns...")
print()

# Check "Reason for change" columns - typically columns I(9) or further right
# These should NEVER have 0 - they are text fields
reason_cols = []

# First, let's dump ALL columns A-O for key row ranges to understand the structure
sections = [
    ("Balance Sheet", 200, 250),
    ("Break-up LTB", 248, 262),
    ("Break-up STB", 263, 271),
    ("Break-up LTLA", 274, 300),
    ("Trade Receivables", 316, 330),
    ("Financial Params BS", 330, 380),
    ("Share Capital", 380, 440),
    ("P&L", 445, 500),
    ("FX Earnings", 500, 522),
    ("P&L Params", 523, 540),
    ("Products", 538, 550),
]

for name, start, end in sections:
    print(f"\n{'='*80}")
    print(f"SECTION: {name} (Rows {start}-{end})")
    print(f"{'='*80}")
    for row in range(start, end + 1):
        row_data = []
        for col in range(1, 16):  # A to O
            val = sheet.cell(row=row, column=col).value
            if val is not None and str(val).strip() != "":
                col_letter = chr(64 + col) if col <= 26 else f"C{col}"
                row_data.append(f"{col_letter}({col})={val}")
        if row_data:
            print(f"Row {row}: {' | '.join(row_data)}")

wb.close()
