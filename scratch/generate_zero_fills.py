import re

def generate_zero_fill():
    gap_file = r"c:\Users\RIYAS\.gemini\antigravity-ide\brain\2795f6fe-c257-4886-8374-88a4e78e10dd\gap_analysis.md"
    
    with open(gap_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    zero_fills = []
    
    for line in lines:
        if not line.startswith("|"): continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6: continue
        
        row_str = parts[1]
        if not row_str.isdigit(): continue
        
        row = int(row_str)
        cy_col = parts[3]
        py_col = parts[4]
        mapped = parts[5]
        
        # If it has columns but is NOT mapped
        if (cy_col or py_col) and mapped == "NO":
            # Map column letters to numbers
            c_num = None
            p_num = None
            if cy_col == "G": c_num = 7
            if cy_col == "N": c_num = 14
            if py_col == "J": p_num = 10
            if py_col == "O": p_num = 15
            
            zero_fills.append(f"        ({row}, {c_num if c_num else 'None'}, {p_num if p_num else 'None'}),")

    with open(r"c:\RIYAS\Sharp INtell\SI Filings\scratch\zero_fills.txt", "w") as f:
        f.write("\n".join(zero_fills))

if __name__ == "__main__":
    generate_zero_fill()
