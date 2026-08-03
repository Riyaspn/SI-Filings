"""
SI Filings — Groq Vision AI Parser Engine
==========================================
Uses Groq Cloud's free, ultra-fast Llama-3.2-11b-vision-preview model
to extract financial statements directly into structured AOC-4 JSON.
"""

import os
import json
import base64
import io
import re
import urllib.request
from typing import Dict, Any, Tuple, List
import pypdfium2 as pdfium
from PIL import Image

from aoc4_schema import get_empty_aoc4_data, get_financial_field_keys, AOC4_SCHEMA

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

EXTRACTION_PROMPT = """You are a senior Chartered Accountant assistant.
Extract all financial figures from this Balance Sheet / Profit & Loss statement page into the exact requested JSON schema.

Schema to follow:
{
  "share_capital": {"current_year": number, "previous_year": number},
  "reserves_and_surplus": {"current_year": number, "previous_year": number},
  "long_term_borrowings": {"current_year": number, "previous_year": number},
  "deferred_tax_liabilities": {"current_year": number, "previous_year": number},
  "other_current_liabilities": {"current_year": number, "previous_year": number},
  "total_equity_and_liabilities": {"current_year": number, "previous_year": number},
  "tangible_assets": {"current_year": number, "previous_year": number},
  "capital_wip": {"current_year": number, "previous_year": number},
  "deferred_tax_assets": {"current_year": number, "previous_year": number},
  "cash_and_bank_balances": {"current_year": number, "previous_year": number},
  "other_current_assets": {"current_year": number, "previous_year": number},
  "total_assets": {"current_year": number, "previous_year": number},
  "revenue_from_operations": {"current_year": number, "previous_year": number},
  "employee_benefit_expense": {"current_year": number, "previous_year": number},
  "finance_costs": {"current_year": number, "previous_year": number},
  "depreciation_and_amortisation": {"current_year": number, "previous_year": number},
  "other_expenses": {"current_year": number, "previous_year": number},
  "total_expenses": {"current_year": number, "previous_year": number},
  "profit_before_tax": {"current_year": number, "previous_year": number},
  "current_tax": {"current_year": number, "previous_year": number},
  "deferred_tax": {"current_year": number, "previous_year": number},
  "profit_after_tax": {"current_year": number, "previous_year": number},
  "earnings_per_share_basic": {"current_year": number, "previous_year": number},
  "earnings_per_share_diluted": {"current_year": number, "previous_year": number}
}

RULES:
1. Ignore Note numbers column! Extract figures for Current Reporting Period (Column 1 of numbers) and Previous Reporting Period (Column 2 of numbers).
2. Use negative numbers for losses or numbers shown in brackets like (24,324).
3. If a field is not present on this page, use null.
4. Return ONLY valid JSON, no markdown codeblocks.
"""

def image_to_base64(pil_image: Image.Image) -> str:
    buffered = io.BytesIO()
    pil_image.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def extract_page_with_groq(pil_image: Image.Image, api_key: str) -> Dict[str, Any]:
    b64_img = image_to_base64(pil_image)
    
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_img}"
                        }
                    }
                ]
            }
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }
    
    req = urllib.request.Request(
        GROQ_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            content = res_json["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as e:
        print(f"Groq API call error: {e}")
        return {}

def extract_with_groq(filepath: str, api_key: str) -> Tuple[Dict[str, Any], List[str], List[str], Dict[str, Any]]:
    pdf = pdfium.PdfDocument(filepath)
    data = get_empty_aoc4_data()
    matched = []
    
    # We scan key pages (usually pages 1-7 contain the Balance Sheet & P&L)
    num_pages = len(pdf)
    scan_pages = range(min(num_pages, 10))
    
    for page_idx in scan_pages:
        page = pdf[page_idx]
        pil_img = page.render(scale=1.5).to_pil()
        
        # Call Groq Vision
        extracted = extract_page_with_groq(pil_img, api_key)
        
        if extracted:
            for k, val in extracted.items():
                if isinstance(val, dict) and k in data:
                    cy = val.get("current_year")
                    py = val.get("previous_year")
                    if cy is not None or py is not None:
                        if data[k]["current_year"] is None:
                            data[k]["current_year"] = cy
                        if data[k]["previous_year"] is None:
                            data[k]["previous_year"] = py
                        if k not in matched:
                            matched.append(k)
                            
    pdf.close()
    
    # Fill defaults
    financial_keys = get_financial_field_keys()
    unmatched = [k for k in financial_keys if k not in matched]
    
    return data, matched, unmatched, {"method": "groq-vision-ai"}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        res, m, u, d = extract_with_groq(sys.argv[1], sys.argv[2])
        print(json.dumps(res, indent=2))
