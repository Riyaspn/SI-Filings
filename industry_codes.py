"""
Embedded ITC / NPCS Industrial Code Database & Mapper (SI Filings Enterprise Engine)
=====================================================================================
Maps company business activities and nature of industry to official 4-digit and 8-digit
ITC (Indian Trade Classification) / NPCS (National Product Classification for Services) codes.
"""

from typing import Dict, Any, Tuple, Optional

# Curated ITC/NPCS Industry Code Database
INDUSTRY_CODE_DATABASE = [
    {
        "keywords": ["sport", "fitness", "recreation", "game", "gaming", "amusement", "entertainment", "event", "adventure"],
        "code_4digit": "9996",
        "code_8digit": "99965900",
        "description": "Sports activities and recreational services"
    },
    {
        "keywords": ["software", "it ", "information tech", "web", "app", "digital", "data", "cloud", "technology", "tech", "computer"],
        "code_4digit": "9983",
        "code_8digit": "99831100",
        "description": "IT consulting, software development and support services"
    },
    {
        "keywords": ["consult", "advisory", "management", "corporate", "business support", "professional"],
        "code_4digit": "9983",
        "code_8digit": "99831200",
        "description": "Business management and professional consultancy services"
    },
    {
        "keywords": ["trade", "trading", "retail", "wholesale", "e-commerce", "store", "export", "import", "merchant"],
        "code_4digit": "9961",
        "code_8digit": "99611100",
        "description": "Wholesale and retail trade services"
    },
    {
        "keywords": ["construct", "build", "real estate", "property", "infra", "engineering", "housing", "developer"],
        "code_4digit": "9954",
        "code_8digit": "99541100",
        "description": "General construction and real estate development services"
    },
    {
        "keywords": ["manufac", "factory", "producer", "fabricat", "assembl", "textile", "chemical", "pharma"],
        "code_4digit": "9988",
        "code_8digit": "99881100",
        "description": "Manufacturing services on physical inputs owned by others"
    },
    {
        "keywords": ["health", "medical", "hospital", "clinic", "pharma", "diagnostic", "wellness"],
        "code_4digit": "9993",
        "code_8digit": "99931100",
        "description": "Human health and medical services"
    },
    {
        "keywords": ["education", "school", "college", "institute", "training", "coaching", "academy"],
        "code_4digit": "9992",
        "code_8digit": "99921100",
        "description": "Higher education and skill training services"
    },
    {
        "keywords": ["hotel", "resort", "restaurant", "food", "hospitality", "catering", "cafe"],
        "code_4digit": "9963",
        "code_8digit": "99631100",
        "description": "Accommodation, food and beverage services"
    },
    {
        "keywords": ["finance", "fintech", "invest", "holding", "loan", "nbfc", "credit"],
        "code_4digit": "9971",
        "code_8digit": "99711100",
        "description": "Financial intermediation and investment services"
    }
]

# Fallback default code (Commercial & Industrial Services)
DEFAULT_CODE = {
    "code_4digit": "9983",
    "code_8digit": "99831900",
    "description": "Business services"
}


def lookup_industry_code(company_name: str, pcs_desc: str = "", type_of_industry: str = "") -> Dict[str, str]:
    """Search database for matching keywords in company name or activity description."""
    text_to_search = f"{company_name} {pcs_desc} {type_of_industry}".lower()
    
    for entry in INDUSTRY_CODE_DATABASE:
        for kw in entry["keywords"]:
            if kw in text_to_search:
                return entry
                
    return DEFAULT_CODE


def enrich_industry_codes(payload_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich extracted AOC-4 payload data with validated ITC/NPCS codes for Principal Products/Services.
    """
    enriched = dict(payload_data)
    
    company_name = str(enriched.get("company_name") or "")
    pcs_desc = str(enriched.get("pcs_description") or "")
    type_ind = str(enriched.get("type_of_industry") or "")
    
    # Check if turnover exists
    rev_dict = enriched.get("revenue_from_operations", {})
    if isinstance(rev_dict, dict):
        rev_cy = float(rev_dict.get("current_year", 0) or 0)
    else:
        rev_cy = float(rev_dict or 0)
        
    code_info = lookup_industry_code(company_name, pcs_desc, type_ind)
    
    def _is_zero(val: Any) -> bool:
        if val is None:
            return True
        if isinstance(val, dict):
            v_cy = float(val.get("current_year", 0) or 0)
            return v_cy == 0.0
        try:
            return float(val or 0) == 0.0
        except (ValueError, TypeError):
            return str(val).strip() in ["", "0", "0.0", "None", "null"]

    # Fill/Enrich pcs fields with validated industry codes and description
    # Note: MCA requires the category count box (Row 540) to exactly equal the number of populated rows
    # in the table below (Row 543). Since we always populate 1 row with the company's ITC code, count must be 1.0.
    enriched["pcs_num_categories"] = {"current_year": 1.0, "previous_year": 0.0}
    enriched["pcs_code"] = {"current_year": float(code_info["code_4digit"]), "previous_year": 0.0}
    enriched["pcs_description"] = code_info["description"]
    
    # Clamp turnover to rev_cy if zero or if AI added trailing zeros (e.g. 41619400 -> 416194)
    pcs_turnover_val = float(enriched.get("pcs_turnover", {}).get("current_year", 0) if isinstance(enriched.get("pcs_turnover"), dict) else (enriched.get("pcs_turnover") or 0))
    if pcs_turnover_val <= 0 or pcs_turnover_val > rev_cy:
        pcs_turnover_val = rev_cy
    enriched["pcs_turnover"] = {"current_year": pcs_turnover_val, "previous_year": 0.0}

    enriched["pcs_highest_code"] = {"current_year": float(code_info["code_8digit"]), "previous_year": 0.0}
    # MCA portal has character limits on product/service descriptions — truncate to 40 chars
    desc = code_info["description"]
    if len(desc) > 40:
        desc = desc[:40].rstrip()
    enriched["pcs_highest_description"] = desc
    enriched["pcs_highest_turnover"] = {"current_year": pcs_turnover_val, "previous_year": 0.0}

    print(f"[IndustryCodes] Enriched Principal Products/Services with ITC Code {code_info['code_4digit']} ({code_info['description']})")
    return enriched
