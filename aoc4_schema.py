"""
AOC-4 Form Data Schema
======================
Defines the canonical JSON schema for all financial fields required by
MCA Form AOC-4 (Annual Financial Statement Filing).

Fields are organized per Indian Companies Act Schedule III:
  - Part I:  Balance Sheet
  - Part II: Statement of Profit & Loss

Each field has:
  - key:          Internal JSON key
  - label:        Human-readable label (displayed in verification UI)
  - section:      Balance Sheet / P&L / General / Ratios
  - required:     Whether MCA mandates this field
  - current_year: Value for the filing financial year
  - previous_year: Comparative value from the prior year
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


# ============================================================
# AOC-4 Field Definition
# ============================================================

@dataclass
class AOC4Field:
    """Single AOC-4 form field definition."""
    key: str
    label: str
    section: str
    required: bool = True
    current_year: Optional[float] = None
    previous_year: Optional[float] = None


# ============================================================
# Complete AOC-4 Schema (Schedule III)
# ============================================================

AOC4_SCHEMA: List[Dict[str, Any]] = [
    # ----------------------------------------------------------
    # PART A - GENERAL INFORMATION OF THE COMPANY
    # ----------------------------------------------------------
    {"key": "cin", "label": "1 (a) Corporate Identity Number (CIN)", "section": "Part A - General information of the Company", "required": True},
    {"key": "company_name", "label": "2 (a) Name of the company", "section": "Part A - General information of the Company", "required": True, "instructions": "Extract the company name exactly as registered. Do NOT include prefixes like 'M/s', 'Messrs', 'Shri', etc."},
    {"key": "reporting_unit", "label": "Reporting Unit / Denomination in Financial Statements", "section": "Part A - General information of the Company", "required": False, "instructions": "Look at table headers in the Balance Sheet and P&L (e.g., '(in ₹)', '(in Hundreds)', '(in \\'00)', '(in Thousands)', '(in Lakhs)', or '(in Crores)'). Return the EXACT unit denomination stated in the table header: e.g. 'Hundreds' (if tables state in hundreds or in \\'00), 'Thousands', 'Lakhs', 'Crores', 'Millions', or 'Absolute Rupees' if in full rupees."},
    {"key": "fy_start_date", "label": "3 Financial year - From", "section": "Part A - General information of the Company", "required": True},
    {"key": "fy_end_date", "label": "3 Financial year - To", "section": "Part A - General information of the Company", "required": True},
    {"key": "board_meeting_date", "label": "4 (a) Date of Board of directors' meeting in which financial statements are approved", "section": "Part A - General information of the Company", "required": True},
    {"key": "nature_of_financial_statements", "label": "4 (b) (i) Nature of financial statements", "section": "Part A - General information of the Company", "required": True, "options": ["Adopted Financial statements", "Provisional un-adopted Financial statements", "Revised Financial statements u/s 130", "Revised Financial statements u/s 131"], "instructions": "Default to 'Adopted Financial statements' unless explicitly stated as provisional or un-adopted."},
    {"key": "provisional_filed_earlier", "label": "4 (b) (iii) Whether provisional financial statements filed earlier", "section": "Part A - General information of the Company", "required": True, "options": ["Yes", "No", "Not applicable"]},
    {"key": "adopted_in_adjourned_agm", "label": "4 (b) (iv) Whether adopted in adjourned AGM", "section": "Part A - General information of the Company", "required": True, "options": ["Yes", "No", "Not applicable"]},
    {"key": "date_of_adjourned_agm", "label": "4 (b) (v) Date of adjourned AGM in which financial statements were adopted", "section": "Part A - General information of the Company", "required": False},
    {"key": "srn_inc28", "label": "4 (b) (vi) SRN of form INC-28", "section": "Part A - General information of the Company", "required": False},
    {"key": "srn_aoc4", "label": "4 (b) (vii) SRN of form AOC-4", "section": "Part A - General information of the Company", "required": False},
    {"key": "board_report_date", "label": "5 (a) Date of Board of directors' meeting in which boards' report was approved", "section": "Part A - General information of the Company", "required": False},
    {"key": "auditor_report_date", "label": "6 Date of signing of reports on the financial statements by the auditors", "section": "Part A - General information of the Company", "required": True},

    # ----------------------------------------------------------
    # SUBSIDIARY DETAILS
    # ----------------------------------------------------------
    {"key": "is_subsidiary", "label": "8 (a) * Whether the company is a subsidiary company as defined under clause (87) of section 2", "section": "Subsidiary Details", "required": True, "options": ["Yes", "No"]},
    {"key": "has_subsidiary", "label": "8 (e) *Whether the company has a subsidiary company as defined under clause (87) of section 2 or the company has an associate company, or a joint venture as defined under clause (6) of section 2", "section": "Subsidiary Details", "required": True, "options": ["Yes", "No"]},


    # ----------------------------------------------------------
    # AGM DETAILS
    # ----------------------------------------------------------
    {"key": "agm_held", "label": "7 (a) Whether annual general meeting (AGM) held", "section": "AGM Details", "required": True, "options": ["Yes", "No", "Not applicable"], "instructions": "Default to 'Yes' if financial statements are adopted."},
    {"key": "agm_date", "label": "7 (b) If yes, date of AGM", "section": "AGM Details", "required": False, "instructions": "Search the entire document (including cover letters, notices, Director's Report, AGM Notice, adoption certificates, or footnotes) for the date of the Annual General Meeting (AGM) where statements were adopted (e.g., 'AGM held on', 'Annual General Meeting date', or 'adopted at AGM'). Notice: It is often held immediately after the Board Meeting Date (e.g. if Board Meeting is 2026-06-26, check for AGM on 2026-06-27). Format as YYYY-MM-DD."},
    {"key": "agm_due_date", "label": "(Computed) Due date of AGM", "section": "AGM Details", "required": False, "instructions": "Statutory due date of AGM under Companies Act (typically September 30 of the financial year end year, e.g., 2022-09-30 for FY 21-22). Format as YYYY-MM-DD."},
    {"key": "agm_extension_granted", "label": "7 (d) Whether any extension for AGM granted", "section": "AGM Details", "required": True, "options": ["Yes", "No"]},
    {"key": "srn_gnl1", "label": "7 (e) SRN of GNL-1", "section": "AGM Details", "required": False},
    {"key": "agm_due_date_extended", "label": "7 (f) Due date of AGM after grant of extension", "section": "AGM Details", "required": False},

    # ----------------------------------------------------------
    # AUDITOR DETAILS
    # ----------------------------------------------------------
    {"key": "srn_adt1", "label": "9 SRN of Form ADT-1", "section": "Auditor Details", "required": False},
    {"key": "auditor_pan", "label": "9 (a) Income-tax PAN of auditor or auditor's firm", "section": "Auditor Details", "required": False},
    {"key": "category_of_auditor", "label": "9 (b) Category of auditor", "section": "Auditor Details", "required": True, "options": ["Auditor's Firm", "Individual"]},
    {"key": "auditor_frn", "label": "9 (c) Membership number of auditor or auditor's firm's registration number", "section": "Auditor Details", "required": True},
    {"key": "auditor_name", "label": "9 (d) Name of the auditor or auditor's firm", "section": "Auditor Details", "required": True},
    {"key": "auditor_address_1", "label": "9 (e) Address Line 1", "section": "Auditor Details", "required": False},
    {"key": "auditor_city", "label": "9 (e) City", "section": "Auditor Details", "required": False},
    {"key": "auditor_district", "label": "9 (e) District", "section": "Auditor Details", "required": False},
    {"key": "auditor_state", "label": "9 (e) State/UT", "section": "Auditor Details", "required": False},
    {"key": "auditor_pincode", "label": "9 (e) Pin Code/Zip Code", "section": "Auditor Details", "required": False},
    {"key": "auditor_membership_no", "label": "9 (f) (ii) Membership number", "section": "Auditor Details", "required": False},
    {"key": "auditor_qualification", "label": "Whether Audit Report is Qualified (CARO)", "section": "Auditor Details", "required": True, "options": ["Yes", "No"]},

    # ----------------------------------------------------------
    # SIGNATORY & DECLARATION DETAILS
    # ----------------------------------------------------------
    {"key": "board_resolution_number", "label": "Board Resolution Number for signing form and declaration", "section": "Signatory Details", "required": False, "instructions": "Extract the specific Board Resolution number authorizing directors to sign the AOC-4 declaration, if mentioned in the Board Report or Director's Report."},
    {"key": "board_resolution_date", "label": "Date of Board Resolution for signing form and declaration", "section": "Signatory Details", "required": False, "instructions": "Extract the date of the resolution authorizing directors to sign the form/declaration. Usually identical to the Board Meeting date where financial statements are approved."},
    {"key": "dir1_din", "label": "Director 1 - DIN", "section": "Signatory Details", "required": False},
    {"key": "dir1_designation", "label": "Director 1 - Designation", "section": "Signatory Details", "required": False, "options": ["Managing Director", "Director", "Manager", "Secretary", "CEO", "CFO", "IRP", "RP", "Liquidator"]},
    {"key": "dir1_date_fs", "label": "Director 1 - Date of signing of financial statements", "section": "Signatory Details", "required": False},
    {"key": "dir1_date_br", "label": "Director 1 - Date of signing of Board's Report", "section": "Signatory Details", "required": False},

    {"key": "dir2_din", "label": "Director 2 - DIN", "section": "Signatory Details", "required": False},
    {"key": "dir2_designation", "label": "Director 2 - Designation", "section": "Signatory Details", "required": False, "options": ["Managing Director", "Director", "Manager", "Secretary", "CEO", "CFO", "IRP", "RP", "Liquidator"]},
    {"key": "dir2_date_fs", "label": "Director 2 - Date of signing of financial statements", "section": "Signatory Details", "required": False},
    {"key": "dir2_date_br", "label": "Director 2 - Date of signing of Board's Report", "section": "Signatory Details", "required": False},

    {"key": "dir3_din", "label": "Director 3 - DIN", "section": "Signatory Details", "required": False},
    {"key": "dir3_designation", "label": "Director 3 - Designation", "section": "Signatory Details", "required": False, "options": ["Managing Director", "Director", "Manager", "Secretary", "CEO", "CFO", "IRP", "RP", "Liquidator"]},
    {"key": "dir3_date_fs", "label": "Director 3 - Date of signing of financial statements", "section": "Signatory Details", "required": False},
    {"key": "dir3_date_br", "label": "Director 3 - Date of signing of Board's Report", "section": "Signatory Details", "required": False},

    # ----------------------------------------------------------
    # EXTRACT OF BOARD'S REPORT, AUDITOR'S REPORT & AOC-2
    # ----------------------------------------------------------
    {"key": "is_opc_or_small", "label": "2 (a) Whether Company is an OPC or Small Company", "section": "Extract of Board's Report", "required": True, "options": ["Yes", "No"]},
    {"key": "board_meetings_held", "label": "2 (b) (i) Number of Board meetings held", "section": "Extract of Board's Report", "required": True},
    {"key": "committee_meetings_held", "label": "2 (c) (i) Number of Committee meetings held", "section": "Extract of Board's Report", "required": False},
    {"key": "loan_guarantee_given", "label": "9 (a) Whether any loan, guarantee is given as per section 186", "section": "Extract of Board's Report", "required": True, "options": ["Yes", "No"]},
    {"key": "sec186_reportable_transactions", "label": "9 (c) Are there any reportable transactions on which sec 186 applies?", "section": "Extract of Board's Report", "required": True, "options": ["Yes", "No"]},
    {"key": "sec186_num_transactions", "label": "10 Number of transactions", "section": "Extract of Board's Report", "required": False},
    
    {"key": "aoc2_non_arms_length", "label": "1. Number of contracts/transactions not at arm's length basis", "section": "AOC-2", "required": True},
    {"key": "aoc2_material_arms_length", "label": "2. Number of material contracts/transactions at arm's length basis", "section": "AOC-2", "required": True},

    {"key": "cag_test_audit", "label": "I (a) In case of a government company, whether Comptroller and Auditor-General of India (CAG of India) has commented upon or supplemented the audit report under section 143 of the Companies Act, 2013", "section": "Extract of Auditor's Report", "required": False, "options": ["Yes", "No", "Not Applicable"]},
    
    # Standalone Auditor's Report Page Fields
    {"key": "number_of_qualifications", "label": "2. Number of qualifications, reservation or adverse remark or disclaimer", "section": "Extract of Auditor's Report", "required": False},
    {"key": "caro_applicable", "label": "6 (b)* Whether companies auditors report order(CARO) is applicable on company", "section": "Extract of Auditor's Report", "required": True, "options": ["Yes", "No"]},

    {"key": "secretarial_audit_applicable", "label": "1 *Whether the Secretarial Audit is applicable", "section": "Extract of Auditor's Report", "required": True, "options": ["Yes", "No"]},
    {"key": "secretarial_audit_qualified", "label": "2 Secretarial audit report has been qualified", "section": "Extract of Auditor's Report", "required": False, "options": ["Yes", "No"]},
    {"key": "secretarial_audit_observations", "label": "3 Number of observations made", "section": "Extract of Auditor's Report", "required": False},

    {"key": "csr_applicability", "label": "1 CSR applicability pursuant to", "section": "Reporting of Corporate Social Responsibility", "required": False, "options": ["Section 135", "Report for unspent CSR amount", "Not applicable"]},

    # ----------------------------------------------------------
    # GENERAL INFORMATION AND OTHER APPLICANT DETAILS
    # ----------------------------------------------------------
    {"key": "type_of_industry", "label": "10 (a) *Type of Industry", "section": "General Information and Other Applicant Details", "required": True, "options": ["Commercial & Industrial", "Banking Company", "Insurance Company", "Power Company", "Non banking Financial Company (NBFC) registered with RBI"]},
    {"key": "schedule_iii_applicable", "label": "10 (b) *Whether Schedule III of the Companies Act, 2013 is applicable", "section": "General Information and Other Applicant Details", "required": True, "options": ["Yes", "No"]},
    {"key": "consolidated_fs_required", "label": "11 *Whether consolidated financial statements required or not", "section": "General Information and Other Applicant Details", "required": True, "options": ["Yes", "No"]},
    {"key": "books_in_electronic_form", "label": "12 (a) *Whether company is maintaining books of account and other relevant books and papers in electric form", "section": "General Information and Other Applicant Details", "required": True, "options": ["Yes", "No"]},

    # ----------------------------------------------------------
    # BALANCE SHEET — EQUITY & LIABILITIES
    # ----------------------------------------------------------

    # Shareholders' Funds
    {"key": "share_capital", "label": "Share Capital", "section": "Balance Sheet - Equity", "required": True},
    {"key": "reserves_and_surplus", "label": "Reserves and Surplus", "section": "Balance Sheet - Equity", "required": True},
    {"key": "money_received_share_warrants", "label": "Money Received Against Share Warrants", "section": "Balance Sheet - Equity", "required": False},
    {"key": "share_application_money", "label": "Share Application Money Pending Allotment", "section": "Balance Sheet - Equity", "required": False},

    # Non-Current Liabilities
    {"key": "long_term_borrowings", "label": "Long-Term Borrowings", "section": "Balance Sheet - Non-Current Liabilities", "required": True},
    {"key": "ltb_bonds_debentures", "label": "LTB: Bonds/debentures", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "ltb_term_loans_banks", "label": "LTB: Term Loans - From banks", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "ltb_term_loans_others", "label": "LTB: Term Loans - From other parties", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "ltb_deferred_payment", "label": "LTB: Deferred payment liabilities", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "ltb_deposits", "label": "LTB: Deposits", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "ltb_loans_related", "label": "LTB: Loans and advances from related parties", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "ltb_finance_lease", "label": "LTB: Long term maturities of financial lease", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "ltb_other_loans", "label": "LTB: Other loans & advances", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "ltb_guaranteed_directors", "label": "LTB: Amount guaranteed by directors", "section": "Balance Sheet - Non-Current Liabilities", "required": False},

    {"key": "deferred_tax_liabilities", "label": "Deferred Tax Liabilities (Net)", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "other_long_term_liabilities", "label": "Other Long-Term Liabilities", "section": "Balance Sheet - Non-Current Liabilities", "required": False},
    {"key": "long_term_provisions", "label": "Long-Term Provisions", "section": "Balance Sheet - Non-Current Liabilities", "required": False},

    # Current Liabilities
    {"key": "short_term_borrowings", "label": "Short-Term Borrowings", "section": "Balance Sheet - Current Liabilities", "required": True},
    {"key": "stb_loans_demand_banks", "label": "STB: Loans repayable on demand - banks", "section": "Balance Sheet - Current Liabilities", "required": False},
    {"key": "stb_loans_demand_others", "label": "STB: Loans repayable on demand - others", "section": "Balance Sheet - Current Liabilities", "required": False},
    {"key": "stb_loans_related", "label": "STB: Loans from related parties", "section": "Balance Sheet - Current Liabilities", "required": False},
    {"key": "stb_deposits", "label": "STB: Deposits", "section": "Balance Sheet - Current Liabilities", "required": False},
    {"key": "stb_other_loans", "label": "STB: Other loans and advances", "section": "Balance Sheet - Current Liabilities", "required": False},
    {"key": "stb_guaranteed_directors", "label": "STB: Amount guaranteed by directors", "section": "Balance Sheet - Current Liabilities", "required": False},

    {"key": "trade_payables", "label": "Trade Payables (Total)", "section": "Balance Sheet - Current Liabilities", "required": True},
    {"key": "trade_payables_msme", "label": "Trade Payables — MSME", "section": "Balance Sheet - Current Liabilities", "required": False},
    {"key": "trade_payables_others", "label": "Trade Payables — Others", "section": "Balance Sheet - Current Liabilities", "required": False},
    {"key": "other_current_liabilities", "label": "Other Current Liabilities", "section": "Balance Sheet - Current Liabilities", "required": False},
    {"key": "short_term_provisions", "label": "Short-Term Provisions", "section": "Balance Sheet - Current Liabilities", "required": False},

    # TOTAL EQUITY & LIABILITIES
    {"key": "total_equity_and_liabilities", "label": "TOTAL Equity and Liabilities", "section": "Balance Sheet - Total", "required": True},

    # ----------------------------------------------------------
    # BALANCE SHEET — ASSETS
    # ----------------------------------------------------------

    # Non-Current Assets
    {"key": "tangible_assets", "label": "Tangible Assets (Property, Plant & Equipment) — Net Book Value from Balance Sheet face", "section": "Balance Sheet - Non-Current Assets", "required": True},
    {"key": "gross_ppe", "label": "Gross Block of Property, Plant & Equipment and Intangible Assets", "section": "Balance Sheet - Non-Current Assets", "required": False, "instructions": "Extract the GROSS BLOCK total (before depreciation) from the Fixed Assets Schedule / PPE Schedule note. This is NOT the net book value shown on the Balance Sheet face. Look for the line 'As at [end date]' under 'Gross Block' or 'Cost' column in the PPE note."},
    {"key": "accumulated_depreciation_ppe", "label": "Accumulated Depreciation on PPE (from Fixed Assets Schedule)", "section": "Balance Sheet - Non-Current Assets", "required": False, "instructions": "Extract the total accumulated depreciation from the Fixed Assets Schedule / PPE Schedule note. Look for 'As at [end date]' under 'Depreciation and Amortization' section."},
    {"key": "intangible_assets", "label": "Intangible Assets", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "capital_wip", "label": "Capital Work-in-Progress", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "intangible_assets_under_dev", "label": "Intangible Assets Under Development", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "non_current_investments", "label": "Non-Current Investments", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "deferred_tax_assets", "label": "Deferred Tax Assets (Net)", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "long_term_loans_advances", "label": "Long-Term Loans and Advances", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "ltla_capital_advances", "label": "LTLA: Capital advances", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "ltla_related_parties", "label": "LTLA: Loans to related parties", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "ltla_other_loans", "label": "LTLA: Other loans and advances", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "ltla_provision_doubtful", "label": "LTLA: Less Provision for bad debts", "section": "Balance Sheet - Non-Current Assets", "required": False},
    {"key": "ltla_due_directors", "label": "LTLA: Loans due by directors", "section": "Balance Sheet - Non-Current Assets", "required": False},
    
    {"key": "other_non_current_assets", "label": "Other Non-Current Assets", "section": "Balance Sheet - Non-Current Assets", "required": False},

    # Current Assets
    {"key": "current_investments", "label": "Current Investments", "section": "Balance Sheet - Current Assets", "required": False},
    {"key": "inventories", "label": "Inventories", "section": "Balance Sheet - Current Assets", "required": True},
    
    {"key": "trade_receivables", "label": "Trade Receivables", "section": "Balance Sheet - Current Assets", "required": True},
    {"key": "tr_secured_good", "label": "TR: Secured, considered good", "section": "Balance Sheet - Current Assets", "required": False},
    {"key": "tr_unsecured_good", "label": "TR: Unsecured, considered good", "section": "Balance Sheet - Current Assets", "required": False},
    {"key": "tr_doubtful", "label": "TR: Doubtful", "section": "Balance Sheet - Current Assets", "required": False},
    {"key": "tr_provision", "label": "TR: Less provision/allowance", "section": "Balance Sheet - Current Assets", "required": False},
    {"key": "tr_due_directors", "label": "TR: Debt due by directors", "section": "Balance Sheet - Current Assets", "required": False},

    {"key": "cash_and_bank_balances", "label": "Cash and Cash Equivalents / Bank Balances", "section": "Balance Sheet - Current Assets", "required": True},
    {"key": "short_term_loans_advances", "label": "Short-Term Loans and Advances", "section": "Balance Sheet - Current Assets", "required": False},
    {"key": "other_current_assets", "label": "Other Current Assets", "section": "Balance Sheet - Current Assets", "required": False},

    # TOTAL ASSETS
    {"key": "total_assets", "label": "TOTAL Assets", "section": "Balance Sheet - Total", "required": True},

    # ----------------------------------------------------------
    # STATEMENT OF PROFIT AND LOSS
    # ----------------------------------------------------------
    {"key": "revenue_from_operations", "label": "Revenue from Operations", "section": "P&L - Income", "required": True},
    {"key": "rev_sale_goods_mfg", "label": "Rev: Sale of goods manufactured", "section": "P&L - Income", "required": False},
    {"key": "rev_sale_goods_traded", "label": "Rev: Sale of goods traded", "section": "P&L - Income", "required": False},
    {"key": "rev_sale_services", "label": "Rev: Sale or supply of services", "section": "P&L - Income", "required": False, "instructions": "If the company's revenue is from rendering services (not manufacturing or trading goods), classify the revenue_from_operations amount here. Look at the P&L line items or notes to determine whether revenue is from goods or services."},

    {"key": "other_income", "label": "Other Income", "section": "P&L - Income", "required": False},
    {"key": "oi_dividend", "label": "OI: Dividend income", "section": "P&L - Income", "required": False},
    {"key": "oi_interest", "label": "OI: Interest income", "section": "P&L - Income", "required": False},
    {"key": "oi_net_gain_investments", "label": "OI: Net gain/loss on sale of investments", "section": "P&L - Income", "required": False},
    {"key": "oi_other_non_operating", "label": "OI: Other non-operating income", "section": "P&L - Income", "required": False},

    {"key": "total_income", "label": "Total Income (Revenue + Other Income)", "section": "P&L - Income", "required": True},

    # Expenses
    {"key": "cost_of_materials_consumed", "label": "Cost of Materials Consumed", "section": "P&L - Expenses", "required": False},
    {"key": "purchases_of_stock_in_trade", "label": "Purchases of Stock-in-Trade", "section": "P&L - Expenses", "required": False},
    {"key": "changes_in_inventories", "label": "Changes in Inventories of FG, WIP & Stock-in-Trade", "section": "P&L - Expenses", "required": False},
    {"key": "employee_benefit_expense", "label": "Employee Benefit Expense", "section": "P&L - Expenses", "required": True},
    {"key": "managerial_remuneration", "label": "Managerial Remuneration", "section": "P&L - Expenses", "required": False},
    {"key": "payment_to_auditors", "label": "Payment to Auditors / Audit Fees", "section": "P&L - Expenses", "required": False, "instructions": "Search P&L notes. If not found, look for 'Audit fee payable' or 'Statutory audit fees' under Balance Sheet Liabilities (e.g. Other Current Liabilities)."},
    {"key": "insurance_expenses", "label": "Insurance Expenses", "section": "P&L - Expenses", "required": False},
    {"key": "power_and_fuel", "label": "Power and Fuel", "section": "P&L - Expenses", "required": False, "instructions": "ONLY extract amounts explicitly listed as a standalone main face item under Statement of Profit & Loss expenses. Do NOT extract electricity, water, generator, or power charges from sub-schedules or Note breakdown of Other Expenses."},
    {"key": "finance_costs", "label": "Finance Costs", "section": "P&L - Expenses", "required": False},
    {"key": "depreciation_and_amortisation", "label": "Depreciation and Amortisation Expense", "section": "P&L - Expenses", "required": True},
    {"key": "other_expenses", "label": "Other Expenses", "section": "P&L - Expenses", "required": True, "instructions": "IMPORTANT: In the MCA AOC-4 form, the following items have their own SEPARATE dedicated rows and must NOT be included in Other Expenses: (1) Payment to Auditors / Audit fees, (2) Managerial Remuneration, (3) Insurance Expenses, (4) Power and Fuel. If the financial statement's 'Other Expenses' note includes any of these as sub-items, SUBTRACT them from the total. For example, if Other Expenses note shows total Rs 283,098 and includes Audit fee Rs 10,000 as a sub-item, report Other Expenses as 283,098 - 10,000 = 273,098."},
    {"key": "total_expenses", "label": "Total Expenses", "section": "P&L - Expenses", "required": True},

    # Profit
    {"key": "profit_before_exceptional_items", "label": "Profit Before Exceptional Items and Tax", "section": "P&L - Profit", "required": True},
    {"key": "exceptional_items", "label": "Exceptional Items", "section": "P&L - Profit", "required": False},
    {"key": "profit_before_tax", "label": "Profit Before Tax", "section": "P&L - Profit", "required": True},
    {"key": "current_tax", "label": "Current Tax", "section": "P&L - Tax", "required": True},
    {"key": "deferred_tax", "label": "Deferred Tax", "section": "P&L - Tax", "required": False},
    {"key": "tax_expense", "label": "Tax Expense (Total)", "section": "P&L - Tax", "required": True},
    {"key": "profit_after_tax", "label": "Profit / (Loss) After Tax (PAT)", "section": "P&L - Profit", "required": True},
    {"key": "earnings_per_share_basic", "label": "Earnings Per Share — Basic (₹)", "section": "P&L - EPS", "required": False},
    {"key": "earnings_per_share_diluted", "label": "Earnings Per Share — Diluted (₹)", "section": "P&L - EPS", "required": False},

    # ----------------------------------------------------------
    # FINANCIAL RATIOS (if disclosed in Notes)
    # ----------------------------------------------------------
    {"key": "current_ratio", "label": "Current Ratio", "section": "Ratios", "required": False},
    {"key": "debt_equity_ratio", "label": "Debt-Equity Ratio", "section": "Ratios", "required": False},
    {"key": "debt_service_coverage_ratio", "label": "Debt Service Coverage Ratio", "section": "Ratios", "required": False},
    {"key": "return_on_equity", "label": "Return on Equity (%)", "section": "Ratios", "required": False},
    {"key": "trade_receivables_turnover", "label": "Trade Receivables Turnover Ratio", "section": "Ratios", "required": False},
    {"key": "trade_payables_turnover", "label": "Trade Payables Turnover Ratio", "section": "Ratios", "required": False},
    {"key": "net_capital_turnover", "label": "Net Capital Turnover Ratio", "section": "Ratios", "required": False},
    {"key": "net_profit_ratio", "label": "Net Profit Ratio (%)", "section": "Ratios", "required": False},
    {"key": "return_on_capital_employed", "label": "Return on Capital Employed (%)", "section": "Ratios", "required": False},

    # ----------------------------------------------------------
    # FOREIGN EXCHANGE & MISC FINANCIAL PARAMETERS
    # ----------------------------------------------------------
    {"key": "gross_transaction_as_18", "label": "Gross value of transactions with related parties as per AS-18 during the reporting period", "section": "Misc", "required": False, "instructions": "IMPORTANT: This is the TOTAL VOLUME of all transactions with related parties DURING THE YEAR — NOT the outstanding balance at year end. Look for the Related Party Transactions disclosure table (AS-18 / Ind AS 24). Sum up all 'Accepted during the period' / 'Loans taken' / 'Loans given' / 'Transactions during the year' amounts for ALL related parties (directors, key management personnel, relatives, entities). If multiple directors are listed, sum their individual transaction amounts. Do NOT use the closing loan balance."},
    {"key": "fx_earn_export_fob", "label": "FX Earn: Export of goods FOB", "section": "P&L - Forex", "required": False},
    {"key": "fx_earn_interest_div", "label": "FX Earn: Interest and dividend", "section": "P&L - Forex", "required": False},
    {"key": "fx_earn_royalty", "label": "FX Earn: Royalty", "section": "P&L - Forex", "required": False},
    {"key": "fx_earn_knowhow", "label": "FX Earn: Know-how", "section": "P&L - Forex", "required": False},
    {"key": "fx_earn_pro_fees", "label": "FX Earn: Professional and consultation fees", "section": "P&L - Forex", "required": False},
    {"key": "fx_earn_other", "label": "FX Earn: Other income", "section": "P&L - Forex", "required": False},

    {"key": "fx_exp_import_raw", "label": "FX Exp: Import - Raw material", "section": "P&L - Forex", "required": False},
    {"key": "fx_exp_import_spares", "label": "FX Exp: Import - Component and spare parts", "section": "P&L - Forex", "required": False},
    {"key": "fx_exp_import_capital", "label": "FX Exp: Import - Capital goods", "section": "P&L - Forex", "required": False},
    {"key": "fx_exp_royalty", "label": "FX Exp: Royalty", "section": "P&L - Forex", "required": False},
    {"key": "fx_exp_knowhow", "label": "FX Exp: Know-how", "section": "P&L - Forex", "required": False},
    {"key": "fx_exp_pro_fees", "label": "FX Exp: Professional and consultation fees", "section": "P&L - Forex", "required": False},
    {"key": "fx_exp_interest", "label": "FX Exp: Interest", "section": "P&L - Forex", "required": False},
    {"key": "fx_exp_other", "label": "FX Exp: Other matters", "section": "P&L - Forex", "required": False},
    {"key": "fx_exp_dividend", "label": "FX Exp: Dividend paid", "section": "P&L - Forex", "required": False},

    {"key": "param_proposed_dividend", "label": "Param: Proposed Dividend (%)", "section": "P&L - Misc", "required": False},
    {"key": "param_rent_paid", "label": "Param: Rent paid", "section": "P&L - Misc", "required": False, "instructions": "Only extract rent paid if reported under standalone general financial parameters or operating lease summary tables. Do NOT extract office/building rent from the Note breakdown of Other Expenses."},
    {"key": "param_consumption_stores", "label": "Param: Consumption of stores and spare parts", "section": "P&L - Misc", "required": False},
    {"key": "param_bad_debts_related", "label": "Param: Bad debts of related parties", "section": "P&L - Misc", "required": False},

    # ----------------------------------------------------------
    # PRINCIPAL PRODUCTS OR SERVICES
    # ----------------------------------------------------------
    {"key": "pcs_num_categories", "label": "Total number of product/services category(ies)", "section": "Principal Products/Services", "required": False, "instructions": "Count how many distinct product or service categories the company operates in. If only one main business activity, return 1. If company has revenue from operations, this should be at least 1."},
    {"key": "pcs_code", "label": "Product or service category code (ITC/NPCS 4 digit)", "section": "Principal Products/Services", "required": False, "instructions": "Look for the ITC (Indian Trade Classification) or NPCS (National Product Classification for Services) 4-digit code. Common codes: Manufacturing='as per product', IT Services='9983', Consulting='9983', Sports/Recreation='9996', Trading='as per goods'. If not found in the document, infer from the company's nature of business and industry."},
    {"key": "pcs_description", "label": "Description of the product or service category", "section": "Principal Products/Services", "required": False, "instructions": "Describe the main product or service category. E.g., 'Sports activities', 'IT consulting services', 'Trading of goods'. Infer from the company's main object clause or revenue description."},
    {"key": "pcs_turnover", "label": "Turnover of the product or service category (in ₹)", "section": "Principal Products/Services", "required": False, "instructions": "The revenue from operations attributable to this product/service category. If the company has only one category, this equals revenue_from_operations."},
    {"key": "pcs_highest_code", "label": "Highest turnover product or service code (ITC/NPCS 8 digit)", "section": "Principal Products/Services", "required": False, "instructions": "The 8-digit ITC/NPCS code for the highest contributing product/service. E.g., for Sports activities the 8-digit code is '99965900'. For IT services it could be '99831100'. If unknown, append '00' to the 4-digit code twice to make 8 digits."},
    {"key": "pcs_highest_description", "label": "Description of the highest turnover product or service", "section": "Principal Products/Services", "required": False, "instructions": "Description of the specific highest-turnover product or service within the category."},
    {"key": "pcs_highest_turnover", "label": "Turnover of highest contributing product or service (in ₹)", "section": "Principal Products/Services", "required": False, "instructions": "Turnover of the highest contributing product or service. If there's only one product/service, this equals pcs_turnover."},
]


def is_general_section(section: str) -> bool:
    """Check if the section is a flat (non-financial) section."""
    non_financial = [
        "Part A - General information of the Company",
        "Subsidiary Details",
        "AGM Details",
        "Auditor Details",
        "Signatory Details",
        "Extract of Board's Report",
        "Extract of Auditor's Report",
        "AOC-2",
        "Reporting of Corporate Social Responsibility",
        "General Information and Other Applicant Details",
        "Principal Products/Services"
    ]
    return section in non_financial


def get_empty_aoc4_data() -> Dict[str, Any]:
    """Return a completely empty dictionary matching the schema."""
    data = {}
    for f in AOC4_SCHEMA:
        section = f["section"]
        if is_general_section(section):
            data[f["key"]] = ""
        else:
            data[f["key"]] = {"current_year": 0.00, "previous_year": 0.00}
    return data


def get_financial_field_keys() -> List[str]:
    """Returns only keys for financial fields (Balance Sheet & P&L)."""
    return [
        f["key"] for f in AOC4_SCHEMA 
        if not is_general_section(f["section"])
    ]


def get_required_field_keys() -> List[str]:
    """Returns list of required field keys."""
    return [f["key"] for f in AOC4_SCHEMA if f["required"]]


def get_field_label(key: str) -> str:
    """Lookup the human-readable label for a given field key."""
    for f in AOC4_SCHEMA:
        if f["key"] == key:
            return f["label"]
    return key


def get_fields_by_section(section: str) -> List[Dict[str, Any]]:
    """Returns all field definitions belonging to a given section."""
    return [f for f in AOC4_SCHEMA if f["section"] == section]


def get_all_sections() -> List[str]:
    """Returns an ordered list of unique sections."""
    seen = set()
    sections = []
    for f in AOC4_SCHEMA:
        if f["section"] not in seen:
            seen.add(f["section"])
            sections.append(f["section"])
    return sections
