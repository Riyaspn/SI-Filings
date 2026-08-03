import os
import glob
import win32com.client

def inspect_rows():
    downloads_dir = os.path.expanduser("~\\Downloads")
    files = sorted(glob.glob(os.path.join(downloads_dir, "AOC-4_*.xlsx")), key=os.path.getmtime, reverse=True)
    if not files:
        files = glob.glob(os.path.join(downloads_dir, "*.xlsx"))
    
    if not files:
        print("No files found.")
        return
    
    file_path = files[0]

    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    wb = excel.Workbooks.Open(os.path.abspath(file_path))
    try:
        sh = wb.Sheets("FORM")
    except:
        sh = wb.Sheets(1)

    print(f"Inspecting Declaration rows (605-630) of newest file: {file_path}")
    for r in range(605, 631):
        row_vals = []
        for c in range(1, 27):
            val = str(sh.Cells(r, c).Value or "").strip()
            if val:
                col_letter = chr(64 + c)
                row_vals.append(f"{col_letter}={val[:25]}")
        if row_vals:
            print(f"Row {r:<3}: " + " | ".join(row_vals))

    wb.Close(False)
    excel.Quit()

if __name__ == "__main__":
    inspect_rows()
