"""
Dump key numeric cells from the CS-completed reference Excel.
Focuses on sections where zero-fill or value discrepancies were reported.
"""
import openpyxl

ref_path = r"C:\Users\RIYAS\Downloads\Copy of AOC-4_U92410KL2020PTC065216_2021-2022_20260728.xlsx"

wb = openpyxl.load_workbook(ref_path, data_only=True)
sheet = wb["FORM"]

# Sections to dump with their column ranges
sections = [
    ("BALANCE SHEET", 196, 246, range(1, 16)),
    ("BREAK-UP LTB (A)", 247, 266, range(1, 16)),
    ("BREAK-UP STB (B)", 267, 281, range(1, 16)),
    ("BREAK-UP LTLA GOOD (C)", 282, 300, range(1, 16)),
    ("BREAK-UP LTLA DOUBT (D)", 301, 316, range(1, 16)),
    ("BREAK-UP TR (E)", 317, 328, range(1, 16)),
    ("FIN PARAMS BS (III)", 329, 378, range(1, 16)),
    ("SHARE CAPITAL (IV)", 379, 416, range(1, 16)),
    ("SBN (V)", 417, 425, range(1, 16)),
    ("COST RECORDS (VI)", 426, 440, range(1, 16)),
    ("P&L STATEMENT (I)", 441, 496, range(1, 16)),
    ("DETAILED PL FX EARN (II-A)", 497, 507, range(1, 16)),
    ("DETAILED PL FX EXP (II-B)", 508, 522, range(1, 16)),
    ("FIN PARAMS PL (III)", 523, 537, range(1, 16)),
    ("PRINCIPAL PRODUCTS (IV)", 538, 555, range(1, 16)),
    ("RPT & AUDITOR (III+)", 556, 600, range(1, 16)),
]

for name, start, end, cols in sections:
    print(f"\n{'='*100}")
    print(f"SECTION: {name} (Rows {start}-{end})")
    print(f"{'='*100}")
    for row in range(start, end + 1):
        row_data = []
        for col in cols:
            val = sheet.cell(row=row, column=col).value
            if val is not None and str(val).strip() != "":
                col_letter = chr(64 + col) if col <= 26 else f"C{col}"
                val_str = str(val).strip().replace("\n", " ")[:40]
                row_data.append(f"{col_letter}={val_str}")
        if row_data:
            print(f"  Row {row:>3}: {' | '.join(row_data)}")

wb.close()
print("\nDONE.")
