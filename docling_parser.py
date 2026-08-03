"""
SI Filings - Docling AI Parser Engine
=====================================
Uses IBM Docling's deep learning layout models to extract tables and text
without relying on raw OCR coordinates. Highly resilient to varying formats.
"""

import re
import math
import pandas as pd
from typing import Dict, Any, List, Tuple
from docling.document_converter import DocumentConverter
from difflib import SequenceMatcher

def clean_indian_number(text: Any) -> float:
    if pd.isna(text) or text is None:
        return 0.0
    text_str = str(text).replace(",", "").replace("₹", "").replace("Rs.", "").strip()
    # Handle brackets as negative
    is_negative = False
    if text_str.startswith("(") and text_str.endswith(")"):
        is_negative = True
        text_str = text_str[1:-1].strip()
    elif text_str.startswith("-"):
        is_negative = True
        text_str = text_str[1:].strip()
        
    try:
        val = float(text_str)
        return -val if is_negative else val
    except ValueError:
        return 0.0

def fuzzy_match(s1: str, s2: str) -> bool:
    if not isinstance(s1, str) or not isinstance(s2, str):
        return False
    s1 = re.sub(r'[^a-z]', '', s1.lower())
    s2 = re.sub(r'[^a-z]', '', s2.lower())
    if not s1 or not s2: return False
    return SequenceMatcher(None, s1, s2).ratio() > 0.85

def parse_with_docling(filepath: str) -> Tuple[Dict[str, Any], List[str], List[str], Dict[str, Any]]:
    # Initialize Docling
    converter = DocumentConverter()
    doc = converter.convert(filepath).document
    
    # 1. Get raw text for NLP extraction (Dates, CIN, Auditor, etc.)
    full_text = doc.export_to_markdown()
    
    data = {}
    matched = []
    
    # Define targets
    targets = {
        "share_capital": ["share capital", "equity share capital"],
        "reserves_and_surplus": ["reserves and surplus", "other equity"],
        "long_term_borrowings": ["long term borrowings", "long-term borrowings"],
        "short_term_borrowings": ["short term borrowings", "short-term borrowings"],
        "trade_payables": ["trade payables"],
        "other_current_liabilities": ["other current liabilities"],
        "total_equity_and_liabilities": ["total equity and liabilities", "total equity & liabilities"],
        "tangible_assets": ["property plant and equipment", "tangible assets"],
        "intangible_assets": ["intangible assets"],
        "capital_wip": ["capital work in progress", "capital work-in-progress", "capital wip"],
        "deferred_tax_assets": ["deferred tax assets", "deferred tax asset", "deffered tax asset"],
        "cash_and_bank_balances": ["cash and cash equivalents", "cash and bank balances"],
        "other_current_assets": ["other current assets"],
        "total_assets": ["total assets", "total - assets"],
        "revenue_from_operations": ["revenue from operations"],
        "other_income": ["other income"],
        "total_income": ["total income", "total revenue"],
        "employee_benefit_expense": ["employee benefit expenses", "employee benefits expense"],
        "finance_costs": ["finance costs", "finance cost"],
        "depreciation_and_amortisation": ["depreciation and amortisation"],
        "other_expenses": ["other expenses"],
        "total_expenses": ["total expenses"],
        "profit_before_tax": ["profit before tax", "loss before tax"],
        "current_tax": ["current tax"],
        "deferred_tax": ["deferred tax", "deffered tax"],
        "tax_expense": ["tax expense"],
        "profit_after_tax": ["profit for the period", "profit for the year", "loss for the year", "profit after tax"],
        "earnings_per_share_basic": ["basic"], # Usually under EPS header
        "earnings_per_share_diluted": ["diluted"]
    }
    
    # 2. Iterate through all tables extracted by Docling's AI
    for table_idx, table in enumerate(doc.tables):
        df = table.export_to_dataframe()
        if df.empty:
            continue
            
        # Scan rows
        for index, row in df.iterrows():
            row_vals = [str(x).strip().lower() for x in row.values if pd.notna(x)]
            if not row_vals: continue
            
            # The first column usually contains the label
            label_cell = row_vals[0]
            
            # Find matching target
            matched_key = None
            for key, aliases in targets.items():
                if key in matched: continue # Already found
                for alias in aliases:
                    if alias in label_cell or fuzzy_match(alias, label_cell):
                        matched_key = key
                        break
                if matched_key: break
                
            if matched_key:
                # We found a row! Now find the numbers from left to right.
                # In India, Column 1 = Note (optional), Column 2 = CY, Column 3 = PY
                numbers = []
                for val in row.values[1:]: # Skip the label column
                    val_str = str(val).strip()
                    # Check if it looks like a number (can have comma, minus, brackets)
                    if re.search(r'\d', val_str):
                        num = clean_indian_number(val_str)
                        # Filter out 'Note' numbers which are usually small integers (1, 2, 3...)
                        # If a number is < 100 and has no decimals in the string, it might be a note number.
                        if num < 100 and "." not in val_str and len(numbers) == 0:
                            continue 
                        numbers.append(num)
                
                # CY is first valid number, PY is second
                cy = numbers[0] if len(numbers) > 0 else 0.0
                py = numbers[1] if len(numbers) > 1 else 0.0
                
                # Multiply by 100 if values are in Hundreds (defaulting to 100 for now, can add detection later)
                unit_mult = 100.0 
                
                data[matched_key] = {
                    "current_year": round(cy * unit_mult, 2),
                    "previous_year": round(py * unit_mult, 2)
                }
                matched.append(matched_key)
                
    # TODO: Add NLP extraction for Dates, CIN, Auditor using `full_text`
    
    return data, matched, [], {"method": "docling_ai"}

if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) > 1:
        res, m, _, _ = parse_with_docling(sys.argv[1])
        print(json.dumps(res, indent=2))
