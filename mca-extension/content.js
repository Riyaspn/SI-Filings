// SI AOC-4 Pro — MCA V3 Portal Content Script Auto-Filler
console.log("SI AOC-4 Pro — Content script initialized on MCA Portal.");

// AOC-4 Schema Key to MCA Portal DOM Selector Mapping
// Maps schema keys to potential DOM input IDs, names, aria-labels, or placeholders on MCA V3
const DOM_FIELD_MAPPINGS = {
  // General Info - Mapped from mca_form_fields_extracted.json AEM Classes
  "cin": ["compnayCin", "CorporateIdentityNumber"],
  "company_name": ["nameOfCompany", "companyName"],
  "address": ["addOfCompany"],
  "email": ["emailOfCompany"],
  "fy_start_date": ["financialYearDateFrom", "fyStart"],
  "fy_end_date": ["financialYearDateTo", "fyEnd"],
  "board_meeting_date": ["dateOfBoardDirectors"],
  "agm_date": ["agmDate"],
  "agm_due_date": ["dueDateAgm"],
  "board_report_date": ["date_signing_board_report"],
  "auditor_name": ["auditorName", "nameOfAuditor", "auditorFirmName"],
  "auditor_frn": ["auditorFrn", "auditorRegistrationNo", "frnNumber"],

  // Balance Sheet — Equity & Liabilities
  "share_capital": ["shareCapital", "sh_capital_cy", "shareCapitalCurrentYear"],
  "reserves_and_surplus": ["reservesAndSurplus", "reserves_surplus_cy", "reservesSurplusCurrentYear"],
  "money_received_share_warrants": ["moneyShareWarrants", "shareWarrants_cy"],
  "share_application_money": ["shareAppMoney", "shareApplicationMoney_cy"],

  // Non-Current Liabilities
  "long_term_borrowings": ["longTermBorrowings", "lt_borrowings_cy", "longTermBorrowingsCurrentYear"],
  "deferred_tax_liabilities": ["deferredTaxLiabilities", "dtl_cy"],
  "other_long_term_liabilities": ["otherLongTermLiabilities", "other_lt_liab_cy"],
  "long_term_provisions": ["longTermProvisions", "lt_provisions_cy"],

  // Current Liabilities
  "short_term_borrowings": ["shortTermBorrowings", "st_borrowings_cy"],
  "trade_payables": ["tradePayables", "trade_payables_cy", "tradePayablesTotal"],
  "other_current_liabilities": ["otherCurrentLiabilities", "other_curr_liab_cy"],
  "short_term_provisions": ["shortTermProvisions", "st_provisions_cy"],

  // Totals
  "total_equity_and_liabilities": ["totalEquityLiabilities", "tot_equity_liab_cy", "totalLiabilitiesCurrentYear"],

  // Balance Sheet — Assets
  "tangible_assets": ["tangibleAssets", "ppe_cy", "propertyPlantEquipment"],
  "intangible_assets": ["intangibleAssets", "intangible_cy"],
  "capital_wip": ["capitalWip", "cwip_cy", "capitalWorkInProgress"],
  "non_current_investments": ["nonCurrentInvestments", "nc_investments_cy"],
  "deferred_tax_assets": ["deferredTaxAssets", "dta_cy"],
  "long_term_loans_advances": ["longTermLoansAdvances", "lt_loans_adv_cy"],
  "other_non_current_assets": ["otherNonCurrentAssets", "other_nc_assets_cy"],

  // Current Assets
  "inventories": ["inventories", "inventories_cy"],
  "trade_receivables": ["tradeReceivables", "trade_receivables_cy"],
  "cash_and_bank_balances": ["cashAndBank", "cash_equivalents_cy", "cashBankBalances"],
  "short_term_loans_advances": ["shortTermLoansAdvances", "st_loans_adv_cy"],
  "other_current_assets": ["otherCurrentAssets", "other_curr_assets_cy"],
  "total_assets": ["totalAssets", "tot_assets_cy", "totalAssetsCurrentYear"],

  // P&L
  "revenue_from_operations": ["revenueFromOperations", "turnover_cy", "revenueOperations"],
  "other_income": ["otherIncome", "other_income_cy"],
  "total_income": ["totalIncome", "tot_income_cy"],
  "employee_benefit_expense": ["employeeBenefitExpense", "employee_exp_cy"],
  "finance_costs": ["financeCosts", "finance_cost_cy"],
  "depreciation_and_amortisation": ["depreciationAmortisation", "depreciation_cy"],
  "other_expenses": ["otherExpenses", "other_exp_cy"],
  "total_expenses": ["totalExpenses", "tot_expenses_cy"],
  "profit_before_tax": ["profitBeforeTax", "pbt_cy"],
  "tax_expense": ["taxExpense", "tax_exp_cy"],
  "profit_after_tax": ["profitAfterTax", "pat_cy"],
};

// Fire native React/Angular/Vue input event dispatches
function setNativeInputValue(element, value) {
  const valueSetter = Object.getOwnPropertyDescriptor(element, 'value')?.set;
  const prototype = Object.getPrototypeOf(element);
  const prototypeValueSetter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;

  if (prototypeValueSetter && valueSetter !== prototypeValueSetter) {
    prototypeValueSetter.call(element, value);
  } else if (valueSetter) {
    valueSetter.call(element, value);
  } else {
    element.value = value;
  }

  element.dispatchEvent(new Event('input', { bubbles: true }));
  element.dispatchEvent(new Event('change', { bubbles: true }));
  element.dispatchEvent(new Event('blur', { bubbles: true }));
}

// Find input field on MCA portal page by fuzzy match
function findElementForField(key, selectors) {
  for (const s of selectors) {
    // Try by ID
    let el = document.getElementById(s);
    if (el) return el;

    // Try by Name
    el = document.querySelector(`input[name="${s}"]`) || document.querySelector(`select[name="${s}"]`);
    if (el) return el;

    // Try by data-attribute
    el = document.querySelector(`[data-field="${s}"]`) || document.querySelector(`[formcontrolname="${s}"]`);
    if (el) return el;

    // Try by AEM/LiveCycle wrapper class (used in MCA V3 portal)
    let parentEl = document.querySelector(`.${s}`);
    if (parentEl) {
      el = parentEl.querySelector('input') || parentEl.querySelector('select');
      if (el) return el;
    }
  }

  // Fallback: search by label text / placeholder proximity
  const labels = Array.from(document.querySelectorAll('label, th, td, span'));
  for (const lbl of labels) {
    const text = lbl.textContent.toLowerCase();
    if (text.includes(key.replace(/_/g, ' '))) {
      const targetId = lbl.getAttribute('for');
      if (targetId) {
        const targetEl = document.getElementById(targetId);
        if (targetEl) return targetEl;
      }

      // Look for sibling or child input
      const input = lbl.querySelector('input') || lbl.nextElementSibling?.querySelector('input') || lbl.nextElementSibling;
      if (input && (input.tagName === 'INPUT' || input.tagName === 'SELECT')) {
        return input;
      }
    }
  }

  return null;
}

// Listen for auto-fill execution message from extension popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "AUTOFILL_AOC4") {
    const payload = request.payload;
    let filledCount = 0;

    console.log("SI AOC-4 Pro — Executing auto-fill with data:", payload);

    for (const [key, value] of Object.entries(payload)) {
      if (value === null || value === undefined) continue;

      const selectors = DOM_FIELD_MAPPINGS[key] || [key];
      const element = findElementForField(key, selectors);

      if (element) {
        let valToSet = "";
        if (typeof value === "object" && value.current_year !== undefined) {
          valToSet = value.current_year !== null ? value.current_year.toString() : "";
        } else {
          valToSet = value.toString();
        }

        if (valToSet !== "") {
          setNativeInputValue(element, valToSet);
          element.style.border = "2px solid #10b981"; // Highlight filled fields in green
          element.style.backgroundColor = "rgba(16, 185, 129, 0.1)";
          filledCount++;
        }
      }
    }

    sendResponse({ success: true, filledCount: filledCount });
  }
  return true;
});
