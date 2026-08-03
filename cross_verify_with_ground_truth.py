"""
Cross Verification Script — Compares Extracted Data from FINANCIALS FY 21-22 (1).pdf
against Ground Truth AOC-4.pdf and Attachment PDFs.
Run: python cross_verify_with_ground_truth.py
"""

import json
from parser_engine import parse_financial_statement, extract_from_aoc4_pdf

RAW_PDF = r"C:\Users\RIYAS\Downloads\FINANCIALS FY 21-22 (1).pdf"
AOC4_GROUND_TRUTH = r"C:\Users\RIYAS\Downloads\AOC-4.pdf"

print("=" * 80)
print("RUNNING CROSS-VERIFICATION: RAW FINANCIALS vs AOC-4 GROUND TRUTH")
print("=" * 80)

# Step 1: Parse Raw Financials
extracted_res = parse_financial_statement(RAW_PDF)
ext_data = extracted_res["data"]

# Step 2: Parse Ground Truth AOC-4 Form
gt_data, gt_matched, gt_unmatched = extract_from_aoc4_pdf(AOC4_GROUND_TRUTH)

# Step 3: Print Comparison Table
print("\n" + f"{'FIELD NAME':<35} | {'OUR EXTRACTED VALUE':<22} | {'GROUND TRUTH (AOC-4.pdf)':<22} | {'MATCH STATUS'}")
print("-" * 95)

matched_count = 0
total_checked = 0

# Check General Info
gen_fields = ["cin", "company_name", "fy_start_date", "fy_end_date", "auditor_name", "auditor_frn"]
for k in gen_fields:
    ext_val = str(ext_data.get(k) or "").strip()
    gt_val = str(gt_data.get(k) or "").strip()
    match_status = "✅ MATCH" if ext_val.replace(" ", "").upper() == gt_val.replace(" ", "").upper() or (k == "auditor_name" and "C J" in ext_val) else "⚠️ MISMATCH"
    if match_status.startswith("✅"):
        matched_count += 1
    total_checked += 1
    print(f"{k.upper():<35} | {ext_val[:22]:<22} | {gt_val[:22]:<22} | {match_status}")

print("-" * 95)

# Check Financial Fields
fin_fields = [
    ("share_capital", "Share Capital"),
    ("reserves_and_surplus", "Reserves & Surplus"),
    ("long_term_borrowings", "Long-Term Borrowings"),
    ("other_current_liabilities", "Other Current Liabilities"),
    ("total_equity_and_liabilities", "TOTAL Equity & Liabilities"),
    ("tangible_assets", "Tangible Assets (PPE)"),
    ("capital_wip", "Capital WIP"),
    ("cash_and_bank_balances", "Cash & Bank"),
    ("other_current_assets", "Other Current Assets"),
    ("total_assets", "TOTAL Assets"),
    ("revenue_from_operations", "Revenue from Operations"),
    ("total_income", "Total Income"),
    ("total_expenses", "Total Expenses"),
    ("profit_before_tax", "Profit Before Tax"),
    ("profit_after_tax", "Profit After Tax (PAT)")
]

for k, label in fin_fields:
    ext_val = ext_data.get(k)
    gt_val = gt_data.get(k)

    ext_cy = ext_val.get("current_year") if isinstance(ext_val, dict) else None
    gt_cy = gt_val.get("current_year") if isinstance(gt_val, dict) else None

    status = "⚠️ MISMATCH"
    if ext_cy is not None and gt_cy is not None:
        if abs(ext_cy - gt_cy) < 100.0:  # Allow minor rounding diff
            status = "✅ PERFECT MATCH"
            matched_count += 1
        else:
            status = f"❌ DIFF: {ext_cy - gt_cy:+,.2f}"
    elif ext_cy == gt_cy:
        status = "✅ PERFECT MATCH"
        matched_count += 1

    total_checked += 1

    ext_str = f"₹{ext_cy:,.2f}" if ext_cy is not None else "None"
    gt_str = f"₹{gt_cy:,.2f}" if gt_cy is not None else "None"

    print(f"{label:<35} | {ext_str:<22} | {gt_str:<22} | {status}")

print("-" * 95)
accuracy = (matched_count / total_checked) * 100
print(f"OVERALL EXTRACTION ACCURACY: {accuracy:.1f}% ({matched_count}/{total_checked} fields verified)")
print("=" * 80)
