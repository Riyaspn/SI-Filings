"""
Gemini AI Parser — Fallback for Scanned / Low-Confidence PDFs
==============================================================
Called ONLY when the free non-AI parser fails to achieve >= 95%
confidence. Uses Google Gemini 1.5 Flash with structured JSON
output to parse scanned or irregular financial statement PDFs.

Cost: ~₹0.01 per page (extremely low).
"""

import os
import json
from typing import Dict, Any, Optional

from aoc4_schema import get_empty_aoc4_data, get_financial_field_keys, AOC4_SCHEMA, is_general_section

# ============================================================
# Gemini Structured Extraction Prompt
# ============================================================

EXTRACTION_PROMPT = """You are a Chartered Accountant's assistant AI. 
You are given a PDF of an Indian company's Audited Financial Statement.

Extract ALL financial figures from the Balance Sheet and Statement of Profit & Loss,
following Indian Companies Act Schedule III format.

Return ONLY a valid JSON object with the following structure. Use null for any values 
you cannot find. Use negative numbers for losses/negative values.
All monetary values MUST be extracted EXACTLY as written in the financial document's table columns, without any mathematical arithmetic or conversion.

{schema_json}

IMPORTANT RULES:
1. Extract BOTH current year AND previous year figures where available.
2. Extract numerical values EXACTLY as displayed in table columns without any arithmetic multiplication or unit scaling (e.g., if a table shows 8,08,797 or 4,16,194, return 808797.0 and 416194.0 directly). NEVER multiply numbers by 100, 1000, or 100000 even if a header mentions hundreds or lakhs.
3. For values shown in brackets like (1,23,456), treat them as NEGATIVE numbers.
4. For "Nil" or "-" or "—", use 0.
5. Do NOT guess values — use null if a field is genuinely not present.
6. For general info fields (CIN, company name, dates), extract as strings.
7. For 'nature_of_financial_statements', default to "Adopted Financial statements" unless specified otherwise.
8. For 'provisional_filed_earlier', 'adopted_in_adjourned_agm', 'consolidated_fs_required', and 'books_in_electronic_form', default to "No" or "Not applicable" as appropriate for standard filings unless the document explicitly states otherwise.
9. For Director DINs: Extract the number. If it starts with '1', output the whole number. Otherwise, ALWAYS prepend a '0' to the front of the extracted DIN (e.g., '8929395' -> '08929395').
10. EXPLICITLY search the 'Notes to Accounts' or sub-schedules for the detailed breakdowns (e.g., LTB: Term Loans, TR: Secured/Doubtful, FX: Foreign Exchange Earnings/Expenditures). Do not just extract top-level Balance Sheet items.
11. Return ONLY the JSON — no markdown, no explanation, no code blocks.
"""


def _build_schema_json() -> str:
    """Build the target JSON schema for the Gemini prompt."""
    schema = {}
    for field_def in AOC4_SCHEMA:
        key = field_def["key"]
        instr = f" ({field_def['instructions']})" if "instructions" in field_def and field_def["instructions"] else ""
        if is_general_section(field_def["section"]):
            schema[key] = f"<string: {field_def['label']}{instr}>"
        else:
            schema[key] = {
                "current_year": f"<number or null: {field_def['label']}{instr}>",
                "previous_year": "<number or null>"
            }
    return json.dumps(schema, indent=2)


def extract_with_gemini(
    filepath: str, 
    api_keys: Any,
    model_name: str = "gemini-3.5-flash-lite"
) -> Dict[str, Any]:
    """
    Extract financial data from a PDF using Google Gemini Vision API.
    Supports a list or comma-separated string of API keys for automatic failover.
    
    Args:
        filepath: Path to the PDF file.
        api_keys: Single API key string, comma-separated keys, or List of keys.
        model_name: Default preferred model.
    """
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning)
    import google.generativeai as genai

    # Parse key pool (automatically load from .env if not provided)
    if not api_keys:
        # Load from .env if present
        if os.path.exists(".env"):
            with open(".env", "r") as env_f:
                for line in env_f:
                    if line.startswith("GEMINI_API_KEYS="):
                        api_keys = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        if not api_keys:
            api_keys = os.getenv("GEMINI_API_KEYS", "")

    if isinstance(api_keys, str):
        key_list = [k.strip().strip('"').strip("'") for k in api_keys.split(",") if k.strip().strip('"').strip("'")]
    elif isinstance(api_keys, (list, tuple)):
        key_list = [str(k).strip().strip('"').strip("'") for k in api_keys if str(k).strip().strip('"').strip("'")]
    else:
        key_list = [str(api_keys).strip().strip('"').strip("'")] if api_keys else []

    if not key_list:
        raise ValueError("No Gemini API keys provided or found in .env file.")

    # Build prompt
    schema_json = _build_schema_json()
    prompt = EXTRACTION_PROMPT.replace("{schema_json}", schema_json)

    models_to_try = [
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash", 
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        model_name,
    ]
    
    # Remove duplicates preserving order
    models_to_try = list(dict.fromkeys(models_to_try))

    # Pre-read PDF bytes and base64 encode for direct REST Header requests (supports AQ... Auth keys)
    import base64
    import requests
    with open(filepath, "rb") as f_pdf:
        pdf_bytes = f_pdf.read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    response_text = None
    last_error = None
    successful_key = None

    # Rotate through API Keys if rate limit / quota exceeded occurs
    for k_idx, current_key in enumerate(key_list):
        print(f"  📤 [Gemini AI Engine] Initializing AI extraction (Key #{k_idx+1}: {current_key[:8]}...)...")
        
        # Method 1: Direct REST with 2026 x-goog-api-key Header (supports AQ... Auth Keys & AIzaSy... Keys)
        for m_name in models_to_try:
            try:
                print(f"  🧠 [Model: {m_name}] Analyzing financial statement & extracting 117 fields...")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": current_key
                }
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt},
                                {
                                    "inline_data": {
                                        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if filepath.lower().endswith(".xlsx") else ("application/vnd.ms-excel" if filepath.lower().endswith(".xls") else ("application/vnd.openxmlformats-officedocument.wordprocessingml.document" if filepath.lower().endswith(".docx") else "application/pdf")),
                                        "data": pdf_base64
                                    }
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "response_mime_type": "application/json",
                        "temperature": 0.1
                    }
                }
                resp = requests.post(url, json=payload, headers=headers, timeout=120)
                if resp.status_code == 200:
                    data_json = resp.json()
                    candidates = data_json.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts and "text" in parts[0]:
                            response_text = parts[0]["text"]
                            successful_key = current_key[:8] + "..."
                            print(f"  ✨ Extraction successfully completed via {m_name} (Header Auth)!")
                            break
                else:
                    err_msg = resp.text
                    print(f"  ⚠️ [Model: {m_name}] REST Header Notice: HTTP {resp.status_code} - {err_msg[:120]}...")
                    last_error = f"HTTP {resp.status_code}: {err_msg}"
            except Exception as r_err:
                last_error = str(r_err)
                continue

        if response_text:
            break

        # Method 2: SDK File Upload API Fallback
        try:
            genai.configure(api_key=current_key)
            uploaded_file = genai.upload_file(filepath, mime_type="application/pdf")
            for m_name in models_to_try:
                try:
                    model = genai.GenerativeModel(m_name)
                    res = model.generate_content(
                        [prompt, uploaded_file],
                        generation_config=genai.GenerationConfig(
                            response_mime_type="application/json",
                            temperature=0.1,
                        )
                    )
                    if res and res.text:
                        response_text = res.text
                        successful_key = current_key[:8] + "..."
                        print(f"  ✨ Extraction successfully completed via {m_name} (File API)!")
                        break
                except Exception as m_err:
                    last_error = m_err
                    continue

            try:
                genai.delete_file(uploaded_file.name)
            except Exception:
                pass

            if response_text:
                break
        except Exception as sdk_err:
            last_error = sdk_err
            continue

    if not response_text:
        raise Exception(f"All {len(key_list)} Gemini API keys exhausted or failed. Last error: {last_error}")

    # Parse the response
    try:
        extracted = json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response text
        text = response_text.strip()
        # Remove possible markdown code block wrapping
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        extracted = json.loads(text.strip())

    # Map extracted data to our schema
    data = get_empty_aoc4_data()
    matched = []
    financial_keys = get_financial_field_keys()

    for key in [f["key"] for f in AOC4_SCHEMA]:
        if key in extracted and extracted[key] is not None:
            if key in financial_keys:
                val = extracted[key]
                if isinstance(val, dict):
                    cy = val.get("current_year")
                    py = val.get("previous_year")
                    cy_num, py_num = None, None
                    if cy is not None:
                        try:
                            cy_num = round(float(cy), 2)
                        except (ValueError, TypeError):
                            pass
                    if py is not None:
                        try:
                            py_num = round(float(py), 2)
                        except (ValueError, TypeError):
                            pass
                    if cy_num is not None or py_num is not None or cy is not None or py is not None:
                        data[key] = {
                            "current_year": cy_num,
                            "previous_year": py_num,
                        }
                        matched.append(key)
                elif isinstance(val, (int, float)):
                    data[key] = {"current_year": float(val), "previous_year": None}
                    matched.append(key)
                elif isinstance(val, str):
                    try:
                        data[key] = {"current_year": round(float(val.strip()), 2), "previous_year": None}
                        matched.append(key)
                    except (ValueError, TypeError):
                        pass
            else:
                # General info field
                val_str = str(extracted[key]).strip()
                
                # Apply strict DIN formatting logic
                if key in ["dir1_din", "dir2_din", "dir3_din"] and val_str and val_str.lower() not in ["null", "none"]:
                    # Clean any leading zeros the AI might have preemptively added
                    val_str_clean = val_str.lstrip("0")
                    if val_str_clean:  # Ensure it's not empty after stripping
                        if val_str_clean.startswith("1"):
                            val_str = val_str_clean
                        else:
                            val_str = "0" + val_str_clean
                            
                data[key] = val_str
                matched.append(key)

    total_fields = len(financial_keys)
    unmatched = [k for k in financial_keys if k not in matched]
    confidence = len([k for k in matched if k in financial_keys]) / total_fields if total_fields > 0 else 0.0

    # Clean up uploaded file
    try:
        genai.delete_file(uploaded_file.name)
    except Exception:
        pass

    # Pipeline through SI Filings Enterprise Engine Modules
    from unit_scaler import scale_payload_to_rupees
    from industry_codes import enrich_industry_codes
    from validator import validate_and_heal_payload

    # 1. Unit Scaling to Absolute Rupees
    scaled_data, unit_audit = scale_payload_to_rupees(data)

    # 2. ITC / NPCS Industry Code Enrichment
    enriched_data = enrich_industry_codes(scaled_data)

    # 3. MCA Schedule III Mathematical Cross-Validation & Self-Healing
    final_data, math_audit = validate_and_heal_payload(enriched_data)

    return {
        "data": final_data,
        "matched": matched,
        "unmatched": unmatched,
        "confidence": round(confidence, 4),
        "total_fields": total_fields,
        "matched_count": len([k for k in matched if k in financial_keys]),
        "method": f"gemini-ai ({model_name})",
        "enterprise_audit": {
            "unit": unit_audit,
            "validation": math_audit
        }
    }
