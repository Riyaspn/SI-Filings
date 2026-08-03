import openpyxl
import sys

def dump_excel(filepath, output_path):
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        sheet = wb["FORM"]
    except Exception as e:
        with open(output_path, "w") as f:
            f.write(f"Error loading Excel: {e}")
        return

    with open(output_path, "w", encoding="utf-8") as f:
        for row in range(500, 800):
            row_data = []
            for col in range(1, 20): # A to T
                cell = sheet.cell(row=row, column=col)
                val = cell.value
                if val is not None and str(val).strip() != "":
                    val = str(val).strip().replace("\n", " ")
                    row_data.append(f"{cell.coordinate}: {val}")
            
            if row_data:
                f.write(" | ".join(row_data) + "\n")

if __name__ == "__main__":
    filepath = r"c:\RIYAS\Sharp INtell\SI Filings\AOC-4_U92410KL2020PTC065216_2021-2022_20260729.xlsx"
    output_path = r"c:\RIYAS\Sharp INtell\SI Filings\scratch\excel_dump.txt"
    dump_excel(filepath, output_path)
