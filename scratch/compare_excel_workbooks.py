import os
import win32com.client

def compare_workbooks(file1_path, file2_path):
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False

    print("Opening Generated File:", file1_path)
    wb1 = excel.Workbooks.Open(os.path.abspath(file1_path))
    try:
        sh1 = wb1.Sheets("FORM")
    except:
        sh1 = wb1.Sheets(1)

    print("Opening CS Reference File:", file2_path)
    wb2 = excel.Workbooks.Open(os.path.abspath(file2_path))
    try:
        sh2 = wb2.Sheets("FORM")
    except:
        sh2 = wb2.Sheets(1)

    print("\n" + "="*120)
    print(f"{'Row':<5} | {'Section / Label':<40} | {'Gen CY (Col G/M)':<18} | {'CS Ref CY (Col G/M)':<18} | {'Gen PY':<15} | {'CS PY':<15}")
    print("="*120)

    # We check columns G (7) and J (10), as well as M (13) and N (14)
    mismatch_count = 0
    match_count = 0

    for r in range(1, 560):
        try:
            label_b = str(sh2.Cells(r, 2).Value or "").strip()
            label_c = str(sh2.Cells(r, 3).Value or "").strip()
            label_d = str(sh2.Cells(r, 4).Value or "").strip()
            label = (label_c or label_b or label_d)[:38]

            # Check primary columns: G(7) and J(10)
            g1 = sh1.Cells(r, 7).Value
            g2 = sh2.Cells(r, 7).Value
            j1 = sh1.Cells(r, 10).Value
            j2 = sh2.Cells(r, 10).Value

            # Also check M(13) and N(14) for parameter sections
            m1 = sh1.Cells(r, 13).Value
            m2 = sh2.Cells(r, 13).Value
            n1 = sh1.Cells(r, 14).Value
            n2 = sh2.Cells(r, 14).Value

            # Format helper
            def fmt(val):
                if val is None or str(val).strip() in ("", "0", "0.0", "None"):
                    return "-"
                try:
                    return f"{float(val):,.2f}"
                except:
                    return str(val)[:16]

            # We care if CS reference or generated file has non-zero values in G, J, M, or N
            has_val_1 = any(fmt(x) != "-" for x in [g1, j1, m1, n1])
            has_val_2 = any(fmt(x) != "-" for x in [g2, j2, m2, n2])

            if has_val_1 or has_val_2:
                cy_gen = fmt(g1) if fmt(g1) != "-" else fmt(m1)
                cy_cs  = fmt(g2) if fmt(g2) != "-" else fmt(m2)
                py_gen = fmt(j1) if fmt(j1) != "-" else fmt(n1)
                py_cs  = fmt(j2) if fmt(j2) != "-" else fmt(n2)

                status = "✅" if cy_gen == cy_cs and py_gen == py_cs else "⚠️"
                if status == "✅":
                    match_count += 1
                else:
                    mismatch_count += 1

                print(f"{r:<5} | {label:<40} | {cy_gen:<18} | {cy_cs:<18} | {py_gen:<15} | {py_cs:<15} {status}")
        except Exception as e:
            pass

    print("="*120)
    print(f"Summary: Matches = {match_count}, Mismatches/Differences = {mismatch_count}")
    print("="*120)

    try:
        wb1.Close(False)
        wb2.Close(False)
    except:
        pass
    excel.Quit()

if __name__ == "__main__":
    gen_path = r"C:\Users\RIYAS\Downloads\AOC-4_U92410KL2020PTC065216_2021-2022_20260729_FILLED.xlsx"
    cs_path = r"C:\Users\RIYAS\Downloads\Copy of AOC-4_U92410KL2020PTC065216_2021-2022_20260728.xlsx"
    if not os.path.exists(gen_path):
        print(f"Error: Could not find generated file at {gen_path}")
    elif not os.path.exists(cs_path):
        print(f"Error: Could not find CS reference file at {cs_path}")
    else:
        compare_workbooks(gen_path, cs_path)
