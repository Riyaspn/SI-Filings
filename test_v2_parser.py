"""
Test script for Parser V2 with real client files.
Run: python test_v2_parser.py
"""

import json
from parser_engine import parse_financial_statement

FILES = [
    r"C:\Users\RIYAS\Downloads\AOC-4.pdf",
    r"C:\Users\RIYAS\Downloads\FINANCIALS FY 21-22 (1).pdf",
]

def run_tests():
    for filepath in FILES:
        print("=" * 70)
        print(f"TESTING FILE: {filepath}")
        print("=" * 70)

        result = parse_financial_statement(filepath)

        print(f"Method Used:     {result['method']}")
        print(f"Confidence:      {result['confidence']:.1%}")
        print(f"Matched Count:   {result['matched_count']}/{result['total_fields']}")
        print(f"Needs AI:        {result['needs_ai']}")
        print(f"Image Pages:     {result['image_pages']}")
        print(f"\nExtracted General Info:")
        print(f"  CIN:           {result['data'].get('cin')}")
        print(f"  Company Name:  {result['data'].get('company_name')}")
        print(f"  FY Start:      {result['data'].get('fy_start_date')}")
        print(f"  FY End:        {result['data'].get('fy_end_date')}")
        print(f"  AGM Date:      {result['data'].get('agm_date')}")
        print(f"  Auditor Name:  {result['data'].get('auditor_name')}")
        print(f"  Auditor FRN:   {result['data'].get('auditor_frn')}")

        print(f"\nExtracted Balance Sheet Samples (CY / PY):")
        sample_keys = [
            "share_capital", "reserves_and_surplus", "long_term_borrowings",
            "other_current_liabilities", "total_equity_and_liabilities",
            "tangible_assets", "cash_and_bank_balances", "other_current_assets",
            "total_assets"
        ]
        for key in sample_keys:
            val = result['data'].get(key)
            if val and isinstance(val, dict):
                print(f"  {key:<30}: CY={val.get('current_year')}, PY={val.get('previous_year')}")

        print("\nMatched Keys List:")
        print(f"  {result['matched']}\n")

if __name__ == "__main__":
    run_tests()
