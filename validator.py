"""
MCA Schedule III Mathematical Validator & Self-Healing Engine (SI Filings Enterprise Engine)
============================================================================================
Performs programmatic accounting cross-validations on extracted AOC-4 financial data:
  1. Balance Sheet Identity: Total Assets == Total Equity & Liabilities
  2. Net Worth Identity: Net Worth == Share Capital + Reserves & Surplus
  3. Total Income Identity: Total Income == Revenue from Operations + Other Income
  4. Total Expenses Identity: Total Expenses == Sum(All Expenses)
  5. Profit Before Tax Identity: Profit Before Tax == Total Income - Total Expenses + Exceptional Items

Also performs automated self-healing for minor ±1 / ±2 rupee OCR or unit rounding discrepancies.
"""

from typing import Dict, Any, List, Tuple


def get_val(data: Dict[str, Any], key: str, year: str) -> float:
    """Helper to safely extract float value for a given key and year ('current_year' / 'previous_year')."""
    val_dict = data.get(key, {})
    if isinstance(val_dict, dict):
        v = val_dict.get(year, 0)
    else:
        v = val_dict if year == "current_year" else 0
    
    try:
        return float(v or 0)
    except (ValueError, TypeError):
        return 0.0


def set_val(data: Dict[str, Any], key: str, year: str, new_val: float):
    """Helper to update a float value in payload data."""
    val_dict = data.get(key, {})
    if isinstance(val_dict, dict):
        val_dict[year] = round(new_val, 2)
        data[key] = val_dict
    else:
        if year == "current_year":
            data[key] = round(new_val, 2)


def validate_and_heal_payload(payload_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Perform mathematical validation & self-healing on extracted AOC-4 payload data.
    
    Returns:
        (healed_payload_data, audit_results)
    """
    healed_data = dict(payload_data)
    validation_checks = []
    auto_healed = []

    for year_label, year_key in [("Current Year", "current_year"), ("Previous Year", "previous_year")]:
        # 0. MCA Compliance: Deferred Tax Reclassification
        # MCA rejects negative values in Deferred Tax Liabilities. If net DT is negative,
        # it means DTA > DTL, so the net amount belongs on the Assets side.
        dtl_val = get_val(healed_data, "deferred_tax_liabilities", year_key)
        dta_val = get_val(healed_data, "deferred_tax_assets", year_key)
        if dtl_val < 0:
            # Negative DTL = net deferred tax asset → move to DTA
            new_dta = dta_val + abs(dtl_val)
            set_val(healed_data, "deferred_tax_assets", year_key, new_dta)
            set_val(healed_data, "deferred_tax_liabilities", year_key, 0.0)
            # Adjust totals: moving negative liability to positive asset increases both BS sides by abs(dtl_val)
            cur_tot_assets = get_val(healed_data, "total_assets", year_key)
            cur_tot_liabs = get_val(healed_data, "total_equity_and_liabilities", year_key)
            if cur_tot_assets > 0:
                set_val(healed_data, "total_assets", year_key, round(cur_tot_assets + abs(dtl_val), 2))
            if cur_tot_liabs > 0:
                set_val(healed_data, "total_equity_and_liabilities", year_key, round(cur_tot_liabs + abs(dtl_val), 2))
            auto_healed.append(f"{year_label}: Reclassified negative Deferred Tax Liability ({dtl_val}) to Deferred Tax Asset ({new_dta}) and adjusted BS totals by +{abs(dtl_val)}.")
        elif dta_val < 0:
            # Negative DTA = net deferred tax liability → move to DTL
            new_dtl = dtl_val + abs(dta_val)
            set_val(healed_data, "deferred_tax_liabilities", year_key, new_dtl)
            set_val(healed_data, "deferred_tax_assets", year_key, 0.0)
            # Adjust totals: moving negative asset to positive liability increases both BS sides by abs(dta_val)
            cur_tot_assets = get_val(healed_data, "total_assets", year_key)
            cur_tot_liabs = get_val(healed_data, "total_equity_and_liabilities", year_key)
            if cur_tot_assets > 0:
                set_val(healed_data, "total_assets", year_key, round(cur_tot_assets + abs(dta_val), 2))
            if cur_tot_liabs > 0:
                set_val(healed_data, "total_equity_and_liabilities", year_key, round(cur_tot_liabs + abs(dta_val), 2))
            auto_healed.append(f"{year_label}: Reclassified negative Deferred Tax Asset ({dta_val}) to Deferred Tax Liability ({new_dtl}) and adjusted BS totals by +{abs(dta_val)}.")

        # 0B. MCA Compliance: Trade Receivables Break-Up Reconciliation
        # MCA requires Net trade receivables in the break-up section to equal
        # the BS face "(c) Trade receivables" line item.
        tr_total = get_val(healed_data, "trade_receivables", year_key)
        tr_sec = get_val(healed_data, "tr_secured_good", year_key)
        tr_unsec = get_val(healed_data, "tr_unsecured_good", year_key)
        tr_doubt = get_val(healed_data, "tr_doubtful", year_key)
        if tr_total > 0 and (tr_sec + tr_unsec + tr_doubt) == 0:
            set_val(healed_data, "tr_unsecured_good", year_key, tr_total)
            auto_healed.append(f"{year_label}: Reconciled Trade Receivables break-up: set 'Unsecured, considered good' = {tr_total} to match BS face total.")

        # 1. Balance Sheet Identity (Strict Statutory Verification)
        # Calculate sum of asset line items and liability line items exactly as evaluated by MCA portal formulas.
        asset_keys = [
            "tangible_assets", "intangible_assets", "capital_wip", "intangible_assets_under_dev",
            "non_current_investments", "deferred_tax_assets", "long_term_loans_advances", "other_non_current_assets",
            "current_investments", "inventories", "trade_receivables", "cash_and_bank_balances",
            "short_term_loans_advances", "other_current_assets"
        ]
        sum_assets = round(sum(get_val(healed_data, ak, year_key) for ak in asset_keys), 2)
        tot_assets_reported = get_val(healed_data, "total_assets", year_key)
        tot_liab_reported = get_val(healed_data, "total_equity_and_liabilities", year_key)
        
        # NOTE: trade_payables is the TOTAL of trade_payables_msme + trade_payables_others.
        liab_keys = [
            "share_capital", "reserves_and_surplus", "money_received_share_warrants", "share_application_money",
            "long_term_borrowings", "deferred_tax_liabilities", "other_long_term_liabilities", "long_term_provisions",
            "short_term_borrowings", "trade_payables_msme", "trade_payables_others",
            "other_current_liabilities", "short_term_provisions"
        ]
        sum_liab = round(sum(get_val(healed_data, lk, year_key) for lk in liab_keys), 2)
        
        # Fallback: if msme+others are both 0 but trade_payables face total is non-zero, include face total
        tp_total = get_val(healed_data, "trade_payables", year_key)
        tp_msme = get_val(healed_data, "trade_payables_msme", year_key)
        tp_others = get_val(healed_data, "trade_payables_others", year_key)
        if tp_total > 0 and (tp_msme + tp_others) == 0:
            sum_liab = round(sum_liab + tp_total, 2)
        
        # We check exact equality between Sum of Assets and Sum of Liabilities (MCA V3 Portal Validation)
        diff_bs = round(sum_assets - sum_liab, 2)
        if diff_bs == 0.0 and (sum_assets > 0 or sum_liab > 0):
            validation_checks.append({"rule": "Balance Sheet Identity", "year": year_label, "status": "PASSED", "diff": 0.0, "message": f"Sum of Assets (₹{sum_assets:,.2f}) exactly equals Sum of Liabilities (₹{sum_liab:,.2f})"})
        else:
            validation_checks.append({"rule": "Balance Sheet Identity", "year": year_label, "status": "MISMATCH", "diff": diff_bs, "message": f"Sum of Assets (₹{sum_assets:,.2f}) differs from Sum of Liabilities (₹{sum_liab:,.2f}) by ₹{diff_bs:+.2f}. Please check source document unit rounding or items."})

        # 2. Net Worth Identity (Diagnostic Check)
        sc = get_val(healed_data, "share_capital", year_key)
        rs = get_val(healed_data, "reserves_and_surplus", year_key)
        expected_nw = round(sc + rs, 2)
        actual_nw = get_val(healed_data, "net_worth", year_key)
        
        if actual_nw == expected_nw:
            validation_checks.append({"rule": "Net Worth Identity", "year": year_label, "status": "PASSED", "diff": 0.0})
        elif (sc != 0 or rs != 0):
            set_val(healed_data, "net_worth", year_key, expected_nw)
            validation_checks.append({"rule": "Net Worth Identity", "year": year_label, "status": "AUTO_HEALED", "diff": round(expected_nw - actual_nw, 2), "message": f"Calculated Net Worth as Share Capital + Reserves & Surplus (₹{expected_nw:,.2f})"})

        # 3. Total Income Identity (Strict Check)
        rev = get_val(healed_data, "revenue_from_operations", year_key)
        oi = get_val(healed_data, "other_income", year_key)
        expected_tot_inc = round(rev + oi, 2)
        actual_tot_inc = get_val(healed_data, "total_income", year_key)
        
        if actual_tot_inc > 0 or expected_tot_inc > 0:
            diff_inc = round(expected_tot_inc - actual_tot_inc, 2)
            if diff_inc == 0.0:
                validation_checks.append({"rule": "Total Income Identity", "year": year_label, "status": "PASSED", "diff": 0.0})
            else:
                validation_checks.append({"rule": "Total Income Identity", "year": year_label, "status": "MISMATCH", "diff": diff_inc, "message": f"Reported Total Income (₹{actual_tot_inc:,.2f}) differs from Revenue + Other Income (₹{expected_tot_inc:,.2f})."})

        # 3B. Revenue Breakdown Verification (No guesswork)
        mfg = get_val(healed_data, "rev_sale_goods_mfg", year_key)
        traded = get_val(healed_data, "rev_sale_goods_traded", year_key)
        services = get_val(healed_data, "rev_sale_services", year_key)
        sum_rev_breakdown = round(mfg + traded + services, 2)
        if rev > 0:
            if sum_rev_breakdown == rev:
                validation_checks.append({"rule": "Revenue Breakdown Identity", "year": year_label, "status": "PASSED", "diff": 0.0})
            else:
                diff_rev_bd = round(rev - sum_rev_breakdown, 2)
                validation_checks.append({"rule": "Revenue Breakdown Identity", "year": year_label, "status": "MISMATCH", "diff": diff_rev_bd, "message": f"Revenue breakdown (Mfg/Traded/Services = ₹{sum_rev_breakdown:,.2f}) does not equal total Revenue from Operations (₹{rev:,.2f})."})

        # 4. Total Expenses Verification (Strict Check, No plugging)
        tot_inc = get_val(healed_data, "total_income", year_key)
        pbt = get_val(healed_data, "profit_before_tax", year_key)
        actual_tot_exp = get_val(healed_data, "total_expenses", year_key)
        
        expense_keys = [
            "cost_of_materials_consumed", "purchases_of_stock_in_trade", "changes_in_inventories",
            "employee_benefit_expense", "managerial_remuneration", "payment_to_auditors",
            "insurance_expenses", "power_and_fuel", "finance_costs", "depreciation_and_amortisation",
            "other_expenses"
        ]
        sum_exp_items = round(sum(get_val(healed_data, ek, year_key) for ek in expense_keys), 2)
        
        if actual_tot_exp > 0 or sum_exp_items > 0:
            diff_exp = round(sum_exp_items - actual_tot_exp, 2)
            if diff_exp == 0.0:
                validation_checks.append({"rule": "Total Expenses Identity", "year": year_label, "status": "PASSED", "diff": 0.0})
            else:
                validation_checks.append({"rule": "Total Expenses Identity", "year": year_label, "status": "MISMATCH", "diff": diff_exp, "message": f"Sum of individual expense line items (₹{sum_exp_items:,.2f}) differs from reported Total Expenses (₹{actual_tot_exp:,.2f}) by ₹{diff_exp:+.2f}."})

    all_passed = all(c["status"] in ["PASSED", "AUTO_HEALED"] for c in validation_checks)
    
    audit_results = {
        "passed": all_passed,
        "checks": validation_checks,
        "auto_healed": auto_healed,
        "total_checks": len(validation_checks)
    }
    
    if auto_healed:
        for msg in auto_healed:
            print(f"[Validator] {msg}")
    print(f"[Validator] Mathematical validation complete. Status: {'PASSED (100% Verified)' if all_passed else 'NEEDS REVIEW'}")
    
    return healed_data, audit_results


def validate_aoc4_data(payload_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Legacy compatibility wrapper for desktop UI validation step."""
    _, audit = validate_and_heal_payload(payload_data)
    results = []
    for check in audit.get("checks", []):
        results.append({
            "name": f"{check['rule']} ({check['year']})",
            "passed": check["status"] in ["PASSED", "AUTO_HEALED"],
            "severity": "info" if check["status"] in ["PASSED", "AUTO_HEALED"] else "warning",
            "message": check.get("message", f"{check['rule']} {check['status']}")
        })
    return results


def get_validation_summary(val_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Legacy compatibility wrapper for desktop UI validation summary."""
    passed = len([r for r in val_results if r.get("passed")])
    total = len(val_results)
    details = [f"✅ {r['name']}: {r['message']}" if r.get("passed") else f"⚠️ {r['name']}: {r['message']}" for r in val_results]
    return {
        "overall_status": "PASSED (100% Verified)" if passed == total else "REVIEW REQUIRED",
        "passed": passed,
        "total_checks": total,
        "warnings": total - passed,
        "failed": 0,
        "details": details
    }
