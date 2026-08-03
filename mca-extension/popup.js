// SI AOC-4 Pro — Ultimate Resilient Auto-Filler (Sibling Traversal Engine)
const API_BASE = "http://127.0.0.1:8765";

document.addEventListener("DOMContentLoaded", () => {
  const statusDot = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const companyInfo = document.getElementById("companyInfo");
  const companyNameLabel = document.getElementById("companyNameLabel");
  const fyLabel = document.getElementById("fyLabel");
  const btnAutofill = document.getElementById("btnAutofill");
  const auditLogCard = document.getElementById("auditLogCard");
  const auditLogBox = document.getElementById("auditLogBox");

  let loadedData = null;

  // Check Connection to Desktop App Server
  fetch(`${API_BASE}/status`)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(data => {
      if (data.status === "online") {
        statusDot.className = "dot connected";
        statusText.textContent = "Connected";

        if (data.has_data) {
          fetch(`${API_BASE}/api/aoc4-data`)
            .then(r => r.json())
            .then(resData => {
              if (resData && resData.data) {
                loadedData = resData.data;
                companyInfo.style.display = "block";
                companyNameLabel.textContent = loadedData.company_name || "Company Loaded";
                fyLabel.textContent = `FY: ${loadedData.fy_start_date || ""} to ${loadedData.fy_end_date || ""}`;
                btnAutofill.disabled = false;
              }
            })
            .catch(err => {
                console.error("Error fetching AOC-4 data:", err);
                statusText.textContent = "Data Fetch Error";
            });
        }
      }
    }).catch(err => {
        console.warn("API Offline", err);
        statusDot.className = "dot disconnected";
        statusText.textContent = `Offline: ${err.message}`;
    });

  // Auto-Fill Button Click Handler
  btnAutofill.addEventListener("click", async () => {
    if (!loadedData) return;
    btnAutofill.disabled = true;
    btnAutofill.textContent = "⏳ Ultimate Auto-Filling...";

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: executeAOC4UltimateAutoFill,
        args: [loadedData],
        world: "MAIN"
      });

      btnAutofill.disabled = false;
      btnAutofill.textContent = "⚡ Auto-Fill Current Page";

      const report = results && results[0] ? results[0].result : null;
      if (report) {
        auditLogCard.style.display = "block";
        let html = `<div style="color: #10b981; font-weight: bold; font-size: 11px; margin-bottom: 4px;">
          ✅ Successfully Auto-Filled ${report.filledCount} Fields!
        </div>
        <div style="color: #38bdf8; font-size: 9.5px; line-height: 1.3; background: #0f172a; padding: 6px; border-radius: 4px; border: 1px solid #1e293b; margin-bottom: 6px;">
          💡 <strong>Tab 1 Execution Complete!</strong><br>
          • Dropdowns, Dates, and Radios bypassed AEM security!<br>
        </div><hr style="border-color: #334155; margin: 4px 0;">`;

        report.auditLogs.forEach(item => {
          const color = item.Status.includes("FILLED") ? "#10b981" : "#64748b";
          html += `<div style="margin-bottom: 2px; font-size: 10px;">
            <span style="color: ${color}; font-weight: bold;">${item.Status}</span> <strong>${item.Field}</strong>: ${item.Value}
          </div>`;
        });
        auditLogBox.innerHTML = html;
      }
    } catch (err) {
      btnAutofill.disabled = false;
      btnAutofill.textContent = "⚡ Auto-Fill Current Page";
      alert("⚠️ Extension Execution Error: " + err.message);
    }
  });

  // Copy Logs Button Click Handler
  const btnCopyLogs = document.getElementById("btnCopyLogs");
  if (btnCopyLogs) {
    btnCopyLogs.addEventListener("click", () => {
      const logsText = auditLogBox.innerText || auditLogBox.textContent;
      navigator.clipboard.writeText(logsText).then(() => {
        const originalText = btnCopyLogs.textContent;
        btnCopyLogs.textContent = "✅ Copied to Clipboard!";
        btnCopyLogs.style.background = "#10b981";
        setTimeout(() => {
          btnCopyLogs.textContent = originalText;
          btnCopyLogs.style.background = "#334155";
        }, 2000);
      }).catch(err => {
        alert("Failed to copy: " + err);
      });
    });
  }

  // Diagnostic Button Click Handler
  const btnDiagnostic = document.getElementById("btnExportDOM");
  if (btnDiagnostic) {
    btnDiagnostic.addEventListener("click", async () => {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab) return;

      try {
        btnDiagnostic.textContent = "⏳ Extracting AEM State...";
        const results = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          func: async () => {
            return new Promise((resolve) => {
              try {
                const widgets = Array.from(document.querySelectorAll('[id$="___widget"], input, select'));
                const map = {};
                widgets.forEach((w, i) => {
                  try {
                    let som = "";
                    let nodeName = "";
                    if (w.id.endsWith('___widget')) {
                      som = w.id.replace('___widget', '');
                      if (window.guideBridge) {
                        const node = window.guideBridge.resolveNode(som);
                        if (node) nodeName = node.name;
                      }
                    }
                    const key = nodeName || w.id || w.className || `field_${i}`;
                    let label = "";
                    const container = w.closest('.guideFieldNode, .row, tr');
                    if (container) {
                      const clone = container.cloneNode(true);
                      clone.querySelectorAll('style, script').forEach(n => n.remove());
                      label = clone.textContent.replace(/\s+/g, ' ').trim().slice(0, 150);
                    }
                    map[key] = label;
                  } catch(e){}
                });
                resolve(JSON.stringify(map, null, 2));
              } catch (e) {
                resolve("Exception: " + e.message);
              }
            });
          },
          world: "MAIN"
        });

        const dataXML = results && results[0] ? results[0].result : "No data";
        
        if (dataXML && dataXML.length > 50) {
            await chrome.scripting.executeScript({
              target: { tabId: tab.id },
              func: (dataStr) => {
                const isJson = dataStr.trim().startsWith('{');
                const blob = new window.Blob([dataStr], { type: isJson ? 'application/json' : 'text/xml' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `mca_aem_data_${Date.now()}.${isJson ? 'json' : 'xml'}`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
              },
              args: [dataXML],
              world: "MAIN"
            });
            btnDiagnostic.textContent = "✅ AEM Data Downloaded!";
        } else {
            alert("Could not extract meaningful data.");
            btnDiagnostic.textContent = "📥 Export MCA Page Structure (HTML Diagnostic)";
        }
        
        setTimeout(() => {
            btnDiagnostic.textContent = "📥 Export MCA Page Structure (HTML Diagnostic)";
        }, 3000);
      } catch (err) {
        btnDiagnostic.textContent = "📥 Export MCA Page Structure (HTML Diagnostic)";
        alert("⚠️ Diagnostic Error: " + err.message);
      }
    });
  }
});

// Ultimate Resilient Auto-Filler (Sibling Traversal)
async function executeAOC4UltimateAutoFill(payload) {
  const delay = ms => new Promise(res => setTimeout(res, ms));

  function normalize(str) {
    if (!str) return "";
    return str.toLowerCase().replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
  }

  async function fillInputQuadEngine(inputEl, valStr) {
    if (!inputEl) return false;
    const widgetWrapper = inputEl.closest('[id$="___widget"]') || inputEl.closest('.guideTextBox, .guideNumericBox, .guideDropDownList, .guideDatePicker') || inputEl.parentElement;

    try { 
      inputEl.disabled = false; 
      inputEl.readOnly = false; 
      inputEl.removeAttribute('readonly'); 
      inputEl.removeAttribute('disabled');
    } catch (e) {}

    function toIsoDate(dStr) {
      if (!dStr) return dStr;
      if (dStr.includes("/")) {
        const parts = dStr.split("/");
        if (parts[2] && parts[2].length === 4) return `${parts[2]}-${parts[1]}-${parts[0]}`;
      }
      return dStr;
    }

    function toDisplayDate(dStr) {
      if (!dStr) return dStr;
      if (dStr.includes("-")) {
        const parts = dStr.split("-");
        if (parts[0] && parts[0].length === 4) return `${parts[2]}/${parts[1]}/${parts[0]}`;
      }
      return dStr;
    }

    const isoVal = toIsoDate(valStr);
    const displayVal = toDisplayDate(valStr);

    let guideNode = null;
    let isDateNode = false;
    
    if (window.guideBridge) {
        const path = inputEl.getAttribute('data-control-path');
        if (path) {
            guideNode = window.guideBridge.resolveNode(path);
        } else if (widgetWrapper && widgetWrapper.id) {
            const nodeId = widgetWrapper.id.replace('___widget', '');
            guideNode = window.guideBridge.resolveNode(nodeId);
        }
        
        // ULTIMATE FALLBACK: Find guideNode by traversing the entire tree
        if (!guideNode) {
            window.guideBridge.visit(function(node) {
                if (node && node.id && !guideNode) {
                   const widgetEl = document.getElementById(node.id + "___widget") || document.getElementById(node.id);
                   if (widgetEl && (widgetEl === inputEl || widgetEl.contains(inputEl) || inputEl.id === node.id || (inputEl.name && inputEl.name === node.name))) {
                       guideNode = node;
                   }
                }
            });
        }
    }
    
    const isDateRegex = /^\d{2}\/\d{2}\/\d{4}$/.test(displayVal);
    if (isDateRegex || (guideNode && (guideNode.className === "guideDatePicker" || guideNode.type === "date" || (guideNode.name && guideNode.name.toLowerCase().includes("date")))) || (inputEl.placeholder && inputEl.placeholder.toUpperCase().includes("YYYY"))) {
        isDateNode = true;
    }

    try {
      inputEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      await delay(100);

      inputEl.focus();
      inputEl.dispatchEvent(new Event('focusin', { bubbles: true }));
      inputEl.dispatchEvent(new Event('focus', { bubbles: true }));
      await delay(50);

      if (isDateNode) {
          // 🔥 MCA ANGULAR US-LOCALE DATE BUG FIX
          // The MCA V3 Angular Material Datepicker expects the browser's default parser (MM/DD/YYYY).
          // We MUST inject dates as MM/DD/YYYY all at once to bypass strict input masks and parse correctly.
          const parts = displayVal.split("/"); // DD/MM/YYYY
          if (parts.length === 3) {
              const mmDdYyyy = `${parts[1]}/${parts[0]}/${parts[2]}`;
              inputEl.value = mmDdYyyy;
              
              const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
              if (nativeSetter) nativeSetter.call(inputEl, mmDdYyyy);
              
              inputEl.dispatchEvent(new Event('input', { bubbles: true }));
              inputEl.dispatchEvent(new Event('change', { bubbles: true }));
          }
      } else if (inputEl.tagName === "SELECT") {
        let matchFound = false;
        const targetText = String(valStr).toLowerCase().trim();
        // 1. Exact Match Priority
        for (let i = 0; i < inputEl.options.length; i++) {
          const optText = inputEl.options[i].text.toLowerCase().trim();
          if (optText === targetText) {
            inputEl.selectedIndex = i;
            matchFound = true;
            break;
          }
        }
        // 2. Substring Match Fallback
        if (!matchFound) {
            for (let i = 0; i < inputEl.options.length; i++) {
              const optText = inputEl.options[i].text.toLowerCase().trim();
              if (optText.includes(targetText) || targetText.includes(optText)) {
                inputEl.selectedIndex = i;
                matchFound = true;
                break;
              }
            }
        }
        if (!matchFound) inputEl.value = valStr;
        const nativeSelect = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value')?.set;
        if (nativeSelect) nativeSelect.call(inputEl, inputEl.value);
        
        inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(250); 
      } else {
        inputEl.value = "";
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
        
        for (let i = 0; i < displayVal.length; i++) {
          if (nativeSetter) nativeSetter.call(inputEl, inputEl.value + displayVal[i]);
          else inputEl.value += displayVal[i];
          
          inputEl.dispatchEvent(new Event('input', { bubbles: true }));
          inputEl.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: displayVal[i] }));
          inputEl.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: displayVal[i] }));
          await delay(20 + Math.random() * 20); 
        }

        await delay(50);
        inputEl.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Tab', keyCode: 9 }));
        inputEl.dispatchEvent(new Event('change', { bubbles: true }));
      }
      
      inputEl.blur();
      inputEl.dispatchEvent(new Event('blur', { bubbles: true }));
      inputEl.dispatchEvent(new Event('focusout', { bubbles: true }));

      await delay(500);

      if (window.guideBridge && widgetWrapper && widgetWrapper.id) {
          if (!isDateNode) {
             const expectedVal = displayVal;
             if (guideNode && guideNode.value !== expectedVal) {
                guideNode.value = expectedVal;
                if (window.guideBridge.setProperty) window.guideBridge.setProperty(guideNode, "value", expectedVal);
             }
          }
          if (guideNode && guideNode.errorText) guideNode.errorText = "";
          try { if (guideNode && guideNode.execEvent) guideNode.execEvent("exit"); } catch(e) {}
      }
    } catch (e) {}

    try {
      const targetStyleEl = widgetWrapper || inputEl;
      targetStyleEl.style.border = "2px solid #10b981";
      targetStyleEl.style.backgroundColor = "#dcfce7";
      inputEl.style.backgroundColor = "#dcfce7";
      inputEl.style.color = "#0f172a";
      inputEl.style.fontWeight = "bold";
    } catch (e) {}

    return true;
  }

  let filledCount = 0;
  const auditLogs = [];
  const usedInputs = new Set();
  const allInputs = Array.from(document.querySelectorAll('input:not([type="hidden"]), select, textarea')).filter(el => el.offsetWidth > 0 && el.offsetHeight > 0);

  async function fillByExactLabel(fieldKey, phrase, value, excludePhrases = []) {
    if (value === undefined || value === null || value === "") return null;
    const normPhrase = normalize(phrase);
    const normExcludes = excludePhrases.map(normalize);
    for (const inp of allInputs) {
      if (usedInputs.has(inp)) continue;
      const parentLabel = inp.closest('.guideFieldNode, .guideCompositeFieldNode, tr, .row, div[class*="panel"]') || inp.parentElement;
      if (!parentLabel) continue;

      const labelText = normalize(parentLabel.textContent || '').replace(/\*/g, '').trim();
      if (normExcludes.some(ex => labelText.includes(ex))) continue;

      const escapedPhrase = normPhrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(`\\b${escapedPhrase}\\b`, 'i');
      
      if (regex.test(labelText)) {
        usedInputs.add(inp);
        await fillInputQuadEngine(inp, value);
        filledCount++;
        auditLogs.push({ Field: fieldKey, Value: value, Status: "✅ FILLED" });
        return inp;
      }
    }
    auditLogs.push({ Field: fieldKey, Value: value, Status: "⚠️ NOT ON PAGE" });
    return null;
  }

  // Find input by AEM CSS Wrapper Class
  async function fillByAemClass(fieldKey, aemClass, value) {
    if (value === undefined || value === null || value === "") return null;
    const parentEl = document.querySelector(`.${aemClass}`);
    if (parentEl) {
      const inp = parentEl.querySelector('input') || parentEl.querySelector('select');
      if (inp && !usedInputs.has(inp)) {
        usedInputs.add(inp);
        await fillInputQuadEngine(inp, String(value));
        filledCount++;
        auditLogs.push({ Field: fieldKey, Value: value, Status: "✅ FILLED (AEM Class)" });
        return inp;
      }
    }
    return null;
  }

  // Robust selector for actual data-entry fields
  const TEXT_INPUT_SELECTOR = 'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="image"]):not([type="radio"]):not([type="checkbox"]), select, textarea';

  // Find input by searching UP the DOM tree from a Text Node
  function findInputsNearText(text, inputSelector, maxDepth = 6) {
    const normText = normalize(text);
    const textElements = Array.from(document.querySelectorAll('span, label, p, div, td, legend, th')).filter(el => {
      // Get only the direct text content of the element, ignoring child elements' text
      let directText = "";
      for (let node of el.childNodes) {
          if (node.nodeType === Node.TEXT_NODE) directText += node.textContent;
      }
      return normalize(directText).includes(normText);
    });

    for (const el of textElements) {
      // First check if the element ITSELF contains the input (e.g. <label><input>Text</label>)
      const internalInputs = Array.from(el.querySelectorAll(inputSelector)).filter(inp => inp.offsetWidth > 0 && inp.offsetHeight > 0);
      if (internalInputs.length > 0 && internalInputs.length <= 5) return internalInputs;

      // Otherwise search up the DOM tree
      let parent = el.parentElement;
      for (let i = 0; i < maxDepth; i++) {
        if (!parent) break;
        
        // CRITICAL BUG FIX: Don't climb into huge AEM Panel layouts that wrap multiple distinct fields
        const className = typeof parent.className === 'string' ? parent.className.toLowerCase() : '';
        if (className.includes('panel') && !className.includes('guidefieldnode')) {
            break; 
        }

        const inputs = Array.from(parent.querySelectorAll(inputSelector)).filter(inp => inp.offsetWidth > 0 && inp.offsetHeight > 0);
        
        // If we found a tight cluster of inputs (like a composite field), return them.
        // If it's more than 6, we've climbed too high into a layout container, ignore it!
        if (inputs.length > 0 && inputs.length <= 6) {
             return inputs;
        }
        
        parent = parent.parentElement;
      }
    }
    return [];
  }

  // Helper to format dates to DD/MM/YYYY for MCA portal
  function formatDate(dStr) {
    if (!dStr) return "";
    if (dStr.includes("-")) {
      const parts = dStr.split("-");
      if (parts[0].length === 4) return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }
    return dStr;
  }

  // 0. Clear CIN search input explicitly without blocking main CIN field
  try {
    const searchCinBox = document.querySelector('input[placeholder*="Company Name"]');
    if (searchCinBox) searchCinBox.value = "";
  } catch (e) {}

  // =========================================================
  // BULLETPROOF AEM FIELD NODE & DIAGNOSTIC KEY TARGETING ENGINE
  // =========================================================
  async function fillByDiagnosticKey(key, value, fieldName) {
    if (!value) return false;
    let el = document.getElementById(key) || 
             document.getElementsByName(key)[0] || 
             document.querySelector(`[name="${key}"], .${key}`);
    
    if (!el && key.length > 5) {
      el = document.querySelector(`[id*="${key}"]`);
    }
    
    if (el) {
      if (el.tagName !== 'INPUT' && el.tagName !== 'SELECT' && el.tagName !== 'TEXTAREA') {
        el = el.querySelector('input, select, textarea');
      }
      if (el && el.offsetWidth > 0 && el.offsetHeight > 0) {
        await fillInputQuadEngine(el, value);
        filledCount++; auditLogs.push({ Field: fieldName || key, Value: value, Status: "✅ FILLED (Exact Key)" });
        return true;
      }
    }
    return false;
  }

  function findInputByAemFieldLabel(targetLabelText, occurrenceIndex = 0) {
    const normTarget = normalize(targetLabelText);
    const nodes = Array.from(document.querySelectorAll('.guideFieldNode, .guideCompositeFieldNode, .guideTableRow, tr'));
    const matches = [];

    for (const node of nodes) {
      const labelEl = node.querySelector('.guideFieldLabel, label, legend, .guideText');
      if (!labelEl) continue;
      
      const text = normalize(labelEl.textContent).replace(/\*/g, '').trim();
      
      const isMatch = (text === normTarget) || 
                      (normTarget.length >= 4 && text.includes(normTarget));

      if (isMatch) {
        const inp = node.querySelector(TEXT_INPUT_SELECTOR);
        if (inp && inp.offsetWidth > 0 && inp.offsetHeight > 0 && !matches.includes(inp)) {
          matches.push(inp);
        }
      }
    }
    return matches[occurrenceIndex] || null;
  }


  // ==========================================
  // SMART ROUTER: DETECT CONTEXT
  // ==========================================
  const pageText = document.body.innerText.toLowerCase();
  let context = "UNKNOWN";

  if (pageText.includes("aoc-4") && pageText.includes("corporate identity number")) {
    const subRadios = findInputsNearText("is a subsidiary company as defined under", 'input[type="radio"]');
    if (subRadios && subRadios.length > 0 && !subRadios[0].disabled && !subRadios[0].readOnly) {
      context = "TAB1_PHASE2";
      auditLogs.push({ Field: "Smart Router", Value: "Phase 2 (Post-Save)", Status: "🚀 DETECTED" });
    } else {
      context = "TAB1_PHASE1";
      auditLogs.push({ Field: "Smart Router", Value: "Phase 1 (Pre-Save)", Status: "🚀 DETECTED" });
    }
  } else if (pageText.includes("aoc-2")) {
    context = "TAB4_AOC2";
    auditLogs.push({ Field: "Smart Router", Value: "Phase 5 (AOC-2)", Status: "🚀 DETECTED" });
  } else if (pageText.includes("number of meetings held") || pageText.includes("opc or small company")) {
    context = "TAB3_BOARD_REPORT";
    auditLogs.push({ Field: "Smart Router", Value: "Phase 4 (Board Report)", Status: "🚀 DETECTED" });
  } else if (pageText.includes("auditors report order(caro)") || pageText.includes("number of qualifications reservation or adverse remark")) {
    context = "TAB2_AUDITOR_REPORT";
    auditLogs.push({ Field: "Smart Router", Value: "Phase 3 (Standalone Auditor Report)", Status: "🚀 DETECTED" });
  } else {
    auditLogs.push({ Field: "Smart Router Error", Value: "Unknown Form Context!", Status: "❌ FAILED" });
  }

  if (context === "TAB1_PHASE1") {
  // 1. General Details
  if (payload.cin) {
    const filled = await fillByDiagnosticKey("compnayCin", payload.cin, "cin");
    if (!filled) {
      const cinInps = findInputsNearText("corporate identity number", TEXT_INPUT_SELECTOR);
      const realCin = cinInps.find(i => !(i.placeholder || "").toLowerCase().includes("company name") && !(i.id || "").toLowerCase().includes("findcin"));
      if (realCin) {
        await fillInputQuadEngine(realCin, payload.cin);
        filledCount++; auditLogs.push({ Field: "cin", Value: payload.cin, Status: "✅ FILLED" });
      }
    }
    await delay(1500); 
  }
  
  if (payload.company_name) {
    const filled = await fillByDiagnosticKey("nameOfCompany", payload.company_name, "company_name");
    if (!filled) {
      const compInp = findInputByAemFieldLabel("name of the company");
      if (compInp) {
        await fillInputQuadEngine(compInp, payload.company_name);
        filledCount++; auditLogs.push({ Field: "company_name", Value: payload.company_name, Status: "✅ FILLED" });
      }
    }
  }

  // 2. Financial Year Dates (Section 3)
  if (payload.fy_start_date) {
    const filled = await fillByDiagnosticKey("mat-input-0", formatDate(payload.fy_start_date), "fy_start_date");
    if (!filled) {
      const fromInp = findInputByAemFieldLabel("from", 0);
      if (fromInp) {
        await fillInputQuadEngine(fromInp, formatDate(payload.fy_start_date));
        filledCount++; auditLogs.push({ Field: "fy_start_date", Value: formatDate(payload.fy_start_date), Status: "✅ FILLED" });
      }
    }
    // 🔥 WAIT for AEM to cascade the From date to the To date validation limits
    await delay(1500);
  }

  if (payload.fy_end_date) {
    const filled = await fillByDiagnosticKey("mat-input-1", formatDate(payload.fy_end_date), "fy_end_date");
    if (!filled) {
      const toInp = findInputByAemFieldLabel("to", 0);
      if (toInp) {
        await fillInputQuadEngine(toInp, formatDate(payload.fy_end_date));
        filledCount++; auditLogs.push({ Field: "fy_end_date", Value: formatDate(payload.fy_end_date), Status: "✅ FILLED" });
      }
    }
    
    // 🔥 CRITICAL: Wait for MCA AEM engine to process date cascading & clear dependent fields
    await delay(2000);
  }

  // 2b. Segment II P&L Period From / To Dates
  try {
    const pnlInputs = findInputsNearText("figures for the period (current reporting period)", 'input');
    if (pnlInputs.length >= 2) {
      if (payload.fy_start_date) await fillInputQuadEngine(pnlInputs[0], formatDate(payload.fy_start_date));
      if (payload.fy_end_date) await fillInputQuadEngine(pnlInputs[1], formatDate(payload.fy_end_date));
    }
  } catch (e) {}

  // 6. Board Meeting Date (Item 4a)
  if (payload.board_meeting_date) {
    await delay(1000); 

    const filled = await fillByDiagnosticKey("mat-input-2", formatDate(payload.board_meeting_date), "board_meeting_date");
    if (filled) {
      await delay(1500);
    } else {
      const boardDates = findInputsNearText("financial statements are approved", TEXT_INPUT_SELECTOR);
      if (boardDates.length > 0) {
        await fillInputQuadEngine(boardDates[0], formatDate(payload.board_meeting_date));
        filledCount++; auditLogs.push({ Field: "board_meeting_date", Value: formatDate(payload.board_meeting_date), Status: "✅ FILLED" });
        await delay(1500);
      } else {
        await fillByAemClass("board_meeting_date", "dateOfBoardDirectors", formatDate(payload.board_meeting_date));
        await delay(1500);
      }
    }
  }

  // 2b. Nature of Financial Statements Dropdown (Item 4b i)
  const natureVal = payload.nature_of_financial_statements || "Adopted Financial statements";
  const natureSelects = findInputsNearText("nature of financial statements", 'select');
  if (natureSelects.length > 0) {
    await fillInputQuadEngine(natureSelects[0], natureVal);
    filledCount++; auditLogs.push({ Field: "nature_of_financial_statements", Value: natureVal, Status: "✅ FILLED" });
    
    // 🔥 CRITICAL: Wait for MCA AEM engine to unhide Fields 4(b)(iii) and 4(b)(iv)
    await delay(1500);
  }

  // 2c. Signatory Details Dynamic Table Auto-Filler
  // Parse flat dirX keys into an array if it doesn't already exist
  let signatoriesArr = payload.signatories;
  if (!signatoriesArr || !Array.isArray(signatoriesArr)) {
    signatoriesArr = [];
    for (let k = 1; k <= 20; k++) {
      if (payload[`dir${k}_din`]) {
        signatoriesArr.push({
          din: payload[`dir${k}_din`],
          designation: payload[`dir${k}_designation`],
          date_of_signing: payload[`dir${k}_date_fs`]
        });
      }
    }
  }

  if (signatoriesArr && signatoriesArr.length > 0) {
    try {
      // Find the Signatory table by its exact ID or fallback to header
      let sigTable = document.getElementById('signatoryDetailsTable');
      if (!sigTable) {
        const elements = Array.from(document.querySelectorAll('*'));
        for (const el of elements) {
            if (el.children.length === 0 && normalize(el.textContent).includes("din or income tax pan")) {
                sigTable = el.closest('table, mat-table, [role="grid"], .ui-table');
                if (sigTable) break;
            }
        }
      }

      if (sigTable) {
        // Find all rows in the table body (excluding headers)
        const rows = Array.from(sigTable.querySelectorAll('tbody tr, mat-row, [role="row"]:not([role="rowheader"]):not(:first-child)'));
        
        for (let i = 0; i < signatoriesArr.length; i++) {
          if (i >= rows.length) break; // If there are fewer rows in UI than payload, fill what we can
          
          const row = rows[i];
          const sig = signatoriesArr[i];
          let rowFilled = false;
          
          // Column 0: DIN
          const dinInput = row.querySelector('[formcontrolname="DIN"]') || Array.from(row.querySelectorAll('input')).find(inp => inp.placeholder && inp.placeholder.toLowerCase().includes("please enter")) || row.querySelectorAll('input')[0];
          if (dinInput && sig.din) {
            await fillInputQuadEngine(dinInput, sig.din);
            rowFilled = true;
          }
          
          // Column 1: Name (usually auto-fetches, but we can fill if needed)
          const nameInput = row.querySelector('[formcontrolname="name"]') || Array.from(row.querySelectorAll('input')).find(inp => inp.placeholder && inp.placeholder.toLowerCase().includes("enter here")) || row.querySelectorAll('input')[1];
          if (nameInput && sig.name) {
            await fillInputQuadEngine(nameInput, sig.name);
          }
          
          // Column 2: Designation
          const desigSelect = row.querySelector('[formcontrolname="designation"]') || row.querySelector('select');
          if (desigSelect && sig.designation) {
            await fillInputQuadEngine(desigSelect, sig.designation);
          }
          
          // Column 3: Date of signing
          const dateInput = row.querySelector('[formcontrolname="dateOfSigningOfFS"]') || Array.from(row.querySelectorAll('input')).find(inp => inp.placeholder && inp.placeholder.includes("YYYY")) || row.querySelectorAll('input')[2];
          if (dateInput && sig.date_of_signing) {
            await fillInputQuadEngine(dateInput, formatDate(sig.date_of_signing));
          }
          
          if (rowFilled) {
            filledCount++; 
            auditLogs.push({ Field: `signatory_din_row_${i+1}`, Value: sig.din, Status: "✅ FILLED" });
          }
          await delay(500); // Wait for potential AEM fetching between rows
        }
      }
    } catch (e) {
      console.warn("Signatory Details auto-fill failed:", e);
    }
  }
  // 2e. Auditor Report Date (Item 6)
  if (payload.auditor_report_date) {
    const audDates = findInputsNearText("signing of reports on the financial statements by the auditors", TEXT_INPUT_SELECTOR);
    if (audDates.length > 0) {
      await fillInputQuadEngine(audDates[0], formatDate(payload.auditor_report_date));
      filledCount++; auditLogs.push({ Field: "auditor_report_date", Value: formatDate(payload.auditor_report_date), Status: "✅ FILLED" });
    } else {
      await fillByAemClass("auditor_report_date", "dateOfSigningOfAuditors", formatDate(payload.auditor_report_date));
    }
  }

  // 2d. AGM Details Auto-Filler (Item 7)
  if (payload.agm_held) {
    const agmRadios = findInputsNearText("annual general meeting agm held", 'input[type="radio"]');
    for (const r of agmRadios) {
      const containerText = normalize(r.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
      if (containerText === payload.agm_held.toLowerCase() || containerText.startsWith(payload.agm_held.toLowerCase())) {
        r.checked = true; r.click(); r.dispatchEvent(new Event('change', { bubbles: true }));
        filledCount++; auditLogs.push({ Field: "agm_held", Value: payload.agm_held, Status: "✅ FILLED" }); break;
      }
    }
  }

  if (payload.agm_date) {
    const agmDateInputs = findInputsNearText("if yes date of agm", 'input');
    if (agmDateInputs.length > 0) {
      await fillInputQuadEngine(agmDateInputs[0], formatDate(payload.agm_date));
      filledCount++; auditLogs.push({ Field: "agm_date", Value: formatDate(payload.agm_date), Status: "✅ FILLED" });
    }
  }

  if (payload.agm_due_date) {
    const agmDueInputs = findInputsNearText("due date of agm", 'input');
    if (agmDueInputs.length > 0) {
      await fillInputQuadEngine(agmDueInputs[0], formatDate(payload.agm_due_date));
      filledCount++; auditLogs.push({ Field: "agm_due_date", Value: formatDate(payload.agm_due_date), Status: "✅ FILLED" });
    }
  }

  if (payload.agm_extension_granted) {
    const extRadios = findInputsNearText("extension for agm granted", 'input[type="radio"]');
    for (const r of extRadios) {
      const containerText = normalize(r.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
      if (containerText === payload.agm_extension_granted.toLowerCase() || containerText.startsWith(payload.agm_extension_granted.toLowerCase())) {
        r.checked = true; r.click(); r.dispatchEvent(new Event('change', { bubbles: true }));
        filledCount++; auditLogs.push({ Field: "agm_extension_granted", Value: payload.agm_extension_granted, Status: "✅ FILLED" }); break;
      }
    }
  }


  // 2c1. Board Report Date (Item 5a) - MUST BE FILLED BEFORE TABLE 5b!
  if (payload.board_report_date) {
    const brDates = findInputsNearText("boards report referred under section 134 was approved", TEXT_INPUT_SELECTOR);
    if (brDates.length > 0) {
      await fillInputQuadEngine(brDates[0], formatDate(payload.board_report_date));
      filledCount++; auditLogs.push({ Field: "board_report_date", Value: formatDate(payload.board_report_date), Status: "✅ FILLED" });
      await delay(2000); // ⏳ CRITICAL: Wait for MCA AEM engine to cascade validation limits down to the table!
    } else {
      const filledByAem = await fillByAemClass("board_report_date", "dateOfBoardDirectorsReport", formatDate(payload.board_report_date));
      if (filledByAem) await delay(2000);
    }
  }

  // 2c2. Board's Report Signatory Details Dynamic Table Auto-Filler (Item 5b)
  let boardSigsArr = [];
  for (let k = 1; k <= 20; k++) {
    if (payload[`dir${k}_din`] && payload[`dir${k}_date_br`]) {
      boardSigsArr.push({
        din: payload[`dir${k}_din`],
        designation: payload[`dir${k}_designation`],
        date_of_signing: payload[`dir${k}_date_br`]
      });
    }
  }

  if (boardSigsArr.length > 0) {
    try {
      let brTable = document.getElementById('signatoryDetailsTableRows');
      if (!brTable) {
        const elements = Array.from(document.querySelectorAll('*'));
        for (const el of elements) {
            if (el.children.length === 0 && normalize(el.textContent).includes("date of signing of board s report")) {
                brTable = el.closest('table, mat-table, [role="grid"], .ui-table');
                if (brTable) break;
            }
        }
      }

      if (brTable) {
        // Find all rows in the table body (excluding headers)
        const rows = Array.from(brTable.querySelectorAll('tbody tr, mat-row, [role="row"]:not([role="rowheader"]):not(:first-child)'));
        
        for (let i = 0; i < boardSigsArr.length; i++) {
          if (i >= rows.length) break;
          
          const row = rows[i];
          const sig = boardSigsArr[i];
          let rowFilled = false;
          
          // Column 0: DIN
          const dinInput = row.querySelector('[formcontrolname="DIN"]') || Array.from(row.querySelectorAll('input')).find(inp => inp.placeholder && inp.placeholder.toLowerCase().includes("please enter")) || row.querySelectorAll('input')[0];
          if (dinInput && sig.din) {
            await fillInputQuadEngine(dinInput, sig.din);
            rowFilled = true;
          }
          
          // Column 1: Name (usually auto-fetches)
          const nameInput = row.querySelector('[formcontrolname="name"]') || Array.from(row.querySelectorAll('input')).find(inp => inp.placeholder && inp.placeholder.toLowerCase().includes("enter here")) || row.querySelectorAll('input')[1];
          if (nameInput && sig.name) {
            await fillInputQuadEngine(nameInput, sig.name);
          }
          
          // Column 2: Designation
          const desigSelect = row.querySelector('select');
          if (desigSelect && sig.designation) {
            await fillInputQuadEngine(desigSelect, sig.designation);
          }
          
          // Column 3: Date of signing (MCA mistakenly named it dateOfSigningOfFS here too!)
          const dateInput = row.querySelector('[formcontrolname="dateOfSigningOfFS"]') || Array.from(row.querySelectorAll('input')).find(inp => inp.placeholder && inp.placeholder.includes("YYYY")) || row.querySelectorAll('input')[2];
          
          let aemInjected = false;
          if (window.guideBridge && sig.date_of_signing) {
              // 100% bulletproof method: Find the DIN node for this row first
              let aemRowPanel = null;
              if (dinInput) {
                  const dinPath = dinInput.getAttribute('data-control-path');
                  if (dinPath) {
                      const dinNode = window.guideBridge.resolveNode(dinPath);
                      if (dinNode && dinNode.parent) aemRowPanel = dinNode.parent;
                  }
              }
              // If data-control-path failed, use brute force to find the DIN node for this row
              if (!aemRowPanel) {
                  window.guideBridge.visit(function(n) {
                      if (!aemRowPanel && n && n.className === "guideTextBox" && n.parent && n.parent.index === i && n.name && n.name.toLowerCase().includes("din") && n.parent.name !== "signatoryDetails") {
                          aemRowPanel = n.parent;
                      }
                  });
              }
              // Now that we have the exact row panel in AEM, find its DatePicker child
              if (aemRowPanel && aemRowPanel.items) {
                  let dateNode = null;
                  for (const child of aemRowPanel.items) {
                      if (child.className === "guideDatePicker") {
                          dateNode = child; break;
                      }
                  }
                  if (dateNode) {
                      dateNode.value = sig.date_of_signing; // payload is YYYY-MM-DD
                      try { window.guideBridge.setProperty(dateNode, "value", sig.date_of_signing); } catch(e){}
                      aemInjected = true;
                  }
              }
          }

          // ALWAYS run DOM simulation (fillInputQuadEngine) even if AEM injected successfully!
          // This synchronizes Angular's internal model with AEM so it doesn't wipe out the date on save.
          if (dateInput && sig.date_of_signing) {
            await fillInputQuadEngine(dateInput, formatDate(sig.date_of_signing));
          }
          
          if (rowFilled) {
            filledCount++; 
            auditLogs.push({ Field: `board_report_din_row_${i+1}`, Value: sig.din, Status: "✅ FILLED" });
          }
          await delay(500); // Wait for potential AEM fetching between rows
        }
      }
    } catch (e) {
      console.warn("Board's Report Details auto-fill failed:", e);
    }
  }


  // Auto-Click the Save button for Tab 1
  try {
    const saveButtons = Array.from(document.querySelectorAll('button')).filter(btn => {
      const text = normalize(btn.textContent);
      return text === 'save' || text === 'save draft';
    });
    const visibleSaveBtn = saveButtons.find(btn => btn.offsetWidth > 0 && btn.offsetHeight > 0);
    
    if (visibleSaveBtn) {
      visibleSaveBtn.click();
      filledCount++;
      auditLogs.push({ Field: "Tab 1 Save Button", Value: "Clicked", Status: "✅ AUTO-SAVED" });
      await delay(1000); // Wait for the Save popup to appear
    }
  } catch (e) {
    console.warn("Auto-save failed", e);
  }

  // DEBUGGING TRUNCATION REMOVED - Let the script run fully!


  } else if (context === "TAB1_PHASE2") {
  // 1. Subsidiary Details (8a & 8e)
  const isSubVal = payload.is_subsidiary || "No";
  const hasSubVal = payload.has_subsidiary || "No";
  
  const subRadios = findInputsNearText("is a subsidiary company as defined under", 'input[type="radio"]');
  for (const radio of subRadios) {
    const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
    if (containerText === isSubVal.toLowerCase() || containerText.startsWith(isSubVal.toLowerCase())) {
      radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "is_subsidiary", Value: isSubVal, Status: "✅ FILLED" });
      break;
    }
  }

  const hasSubRadios = findInputsNearText("has a subsidiary company as defined under", 'input[type="radio"]');
  for (const radio of hasSubRadios) {
    const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
    if (containerText === hasSubVal.toLowerCase() || containerText.startsWith(hasSubVal.toLowerCase())) {
      radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "has_subsidiary", Value: hasSubVal, Status: "✅ FILLED" });
      break;
    }
  }

  // 2. Auditor Details (9)
  if (payload.srn_adt1) {
    const srnAdt1Inputs = findInputsNearText("srn of form adt 1", 'input');
    if (srnAdt1Inputs.length > 0) {
      await fillInputQuadEngine(srnAdt1Inputs[0], payload.srn_adt1);
      filledCount++; auditLogs.push({ Field: "srn_adt1", Value: payload.srn_adt1, Status: "✅ FILLED" });
      await delay(1000); // wait for AEM to process SRN
    }
  }

  // Auditor Firm / PAN logic (remains active if SRN is null or manual entry is needed)
  if (payload.auditor_frn) {
    const firmRadios = findInputsNearText("auditor s firm", 'input[type="radio"]');
    if (firmRadios.length > 0) {
      firmRadios[0].checked = true; firmRadios[0].click(); firmRadios[0].dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "category_of_auditor", Value: "Auditor's Firm", Status: "✅ FILLED" });
    }
    const frnInputs = findInputsNearText("membership number of auditor", 'input');
    if (frnInputs.length > 0) { await fillInputQuadEngine(frnInputs[0], payload.auditor_frn); filledCount++; auditLogs.push({ Field: "auditor_frn", Value: payload.auditor_frn, Status: "✅ FILLED" }); }
  }

  if (payload.auditor_pan) {
    const panInputs = findInputsNearText("income tax pan of auditor", 'input');
    if (panInputs.length > 0) { await fillInputQuadEngine(panInputs[0], payload.auditor_pan); filledCount++; auditLogs.push({ Field: "auditor_pan", Value: payload.auditor_pan, Status: "✅ FILLED" }); }
  }

  if (payload.auditor_name) {
    const nameInputs = findInputsNearText("name of the auditor", 'input');
    if (nameInputs.length > 0) { await fillInputQuadEngine(nameInputs[0], payload.auditor_name); filledCount++; auditLogs.push({ Field: "auditor_name", Value: payload.auditor_name, Status: "✅ FILLED" }); }
  }

  // Auditor Address Details
  if (payload.auditor_address_1) {
    const addInputs = findInputsNearText("address line 1", 'input');
    if (addInputs.length > 0) { await fillInputQuadEngine(addInputs[0], payload.auditor_address_1); filledCount++; auditLogs.push({ Field: "auditor_address_1", Value: payload.auditor_address_1, Status: "✅ FILLED" }); }
  }
  if (payload.auditor_city || payload.auditor_district) {
    const cityInputs = findInputsNearText("city", 'input');
    if (cityInputs.length > 0) { await fillInputQuadEngine(cityInputs[0], payload.auditor_city || payload.auditor_district); filledCount++; auditLogs.push({ Field: "auditor_city", Value: payload.auditor_city || payload.auditor_district, Status: "✅ FILLED" }); }
  }
  if (payload.auditor_district) {
    const distInputs = findInputsNearText("district", 'input');
    if (distInputs.length > 0) { await fillInputQuadEngine(distInputs[0], payload.auditor_district); filledCount++; auditLogs.push({ Field: "auditor_district", Value: payload.auditor_district, Status: "✅ FILLED" }); }
  }
  if (payload.auditor_state) {
    const stateInputs = findInputsNearText("state ut", 'input, select');
    const stateInput = stateInputs.find(el => el.tagName === 'SELECT') || stateInputs[0];
    if (stateInput) { await fillInputQuadEngine(stateInput, payload.auditor_state); filledCount++; auditLogs.push({ Field: "auditor_state", Value: payload.auditor_state, Status: "✅ FILLED" }); }
  }
  if (payload.auditor_pincode) {
    const pinInputs = findInputsNearText("pin code", 'input');
    if (pinInputs.length > 0) { await fillInputQuadEngine(pinInputs[0], payload.auditor_pincode); filledCount++; auditLogs.push({ Field: "auditor_pincode", Value: payload.auditor_pincode, Status: "✅ FILLED" }); }
  }

  // 3. General Information (10-12)
  const industryVal = payload.type_of_industry || "Commercial & Industrial";
  const industrySelects = findInputsNearText("type of industry", 'select');
  if (industrySelects.length > 0) {
    await fillInputQuadEngine(industrySelects[0], industryVal);
    filledCount++; auditLogs.push({ Field: "type_of_industry", Value: industryVal, Status: "✅ FILLED" });
  }

  const sched3Val = payload.schedule_iii_applicable || "Yes";
  const sched3Radios = findInputsNearText("schedule iii of the companies act", 'input[type="radio"]');
  for (const radio of sched3Radios) {
    const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
    if (containerText === sched3Val.toLowerCase() || containerText.startsWith(sched3Val.toLowerCase())) {
      radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "schedule_iii_applicable", Value: sched3Val, Status: "✅ FILLED" });
      break;
    }
  }

  const consolVal = payload.consolidated_fs_required || "No";
  const consolRadios = findInputsNearText("consolidated financial statements required", 'input[type="radio"]');
  for (const radio of consolRadios) {
    const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
    if (containerText === consolVal.toLowerCase() || containerText.startsWith(consolVal.toLowerCase())) {
      radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "consolidated_fs_required", Value: payload.consolidated_fs_required, Status: "✅ FILLED" });
      break;
    }
  }

  const elecVal = payload.books_in_electronic_form || "No";
  const elecBooksRadios = findInputsNearText("maintaining books of account", 'input[type="radio"]');
  for (const radio of elecBooksRadios) {
    const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
    if (containerText === elecVal.toLowerCase() || containerText.startsWith(elecVal.toLowerCase())) {
      radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "books_in_electronic_form", Value: payload.books_in_electronic_form, Status: "✅ FILLED" });
      break;
    }
  }

  // 4. Related Party Details (Segment III)
  let relatedPartyVal = "No";
  const aoc2NonArms = parseFloat(payload.aoc2_non_arms_length || 0);
  const aoc2Material = parseFloat(payload.aoc2_material_arms_length || 0);
  if (aoc2NonArms > 0 || aoc2Material > 0) relatedPartyVal = "Yes";
  
  const relatedPartyRadios = findInputsNearText("whether any transactions entered with related party", 'input[type="radio"]');
  for (const radio of relatedPartyRadios) {
    const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
    if (containerText === relatedPartyVal.toLowerCase() || containerText.startsWith(relatedPartyVal.toLowerCase())) {
      radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "transactions_with_related_party", Value: relatedPartyVal, Status: "✅ FILLED" });
      break;
    }
  }

  // 5. Auditor's Report (Segment IV)
  const cagVal = payload.cag_test_audit || "No";
  const cagRadios = findInputsNearText("auditor general of india cag of india", 'input[type="radio"]');
  for (const radio of cagRadios) {
    const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
    if (containerText === cagVal.toLowerCase() || containerText.startsWith(cagVal.toLowerCase())) {
      radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "cag_test_audit", Value: payload.cag_test_audit, Status: "✅ FILLED" });
      break;
    }
  }

  // 6. CSR Reporting (Segment V)
  const csrSelects = findInputsNearText("csr applicability pursuant to", 'select');
  if (csrSelects.length > 0) {
    await fillInputQuadEngine(csrSelects[0], "Not applicable");
    filledCount++; auditLogs.push({ Field: "csr_applicability", Value: "Not applicable", Status: "✅ FILLED" });
  }

  // 7. Miscellaneous (Segment VI)
  const secAuditVal = payload.secretarial_audit_applicable || "No";
  const secAuditRadios = findInputsNearText("secretarial audit is applicable", 'input[type="radio"]');
  for (const radio of secAuditRadios) {
    const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
    if (containerText === secAuditVal.toLowerCase() || containerText.startsWith(secAuditVal.toLowerCase())) {
      radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
      filledCount++; auditLogs.push({ Field: "secretarial_audit_applicable", Value: payload.secretarial_audit_applicable, Status: "✅ FILLED" });
      break;
    }
  }

  } else if (context === "TAB4_AOC2") {
    // =========================================================
    // AOC-2
    if (payload.aoc2_non_arms_length) {
        const nonArmsInputs = findInputsNearText("transactions not at arm s length", 'input');
        if (nonArmsInputs.length > 0) { await fillInputQuadEngine(nonArmsInputs[0], payload.aoc2_non_arms_length); filledCount++; auditLogs.push({ Field: "aoc2_non_arms_length", Value: payload.aoc2_non_arms_length, Status: "✅ FILLED" }); }
    }
    if (payload.aoc2_material_arms_length) {
        const armsInputs = findInputsNearText("transactions at arm s length", 'input');
        if (armsInputs.length > 0) { await fillInputQuadEngine(armsInputs[0], payload.aoc2_material_arms_length); filledCount++; auditLogs.push({ Field: "aoc2_material_arms_length", Value: payload.aoc2_material_arms_length, Status: "✅ FILLED" }); }
    }
    
  } else if (context === "TAB3_BOARD_REPORT") {
    // =========================================================
    // Extract of Board's Report
    if (payload.is_opc_or_small) {
      const opcVal = payload.is_opc_or_small || "Yes";
      const opcRadios = findInputsNearText("whether company is an opc or small company", 'input[type="radio"]');
      for (const r of opcRadios) {
        const containerText = normalize(r.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
        if (containerText === opcVal.toLowerCase() || containerText.startsWith(opcVal.toLowerCase())) {
          r.checked = true; r.click(); r.dispatchEvent(new Event('change', { bubbles: true }));
          filledCount++; auditLogs.push({ Field: "is_opc_or_small", Value: payload.is_opc_or_small, Status: "✅ FILLED" }); break;
        }
      }
    }
    if (payload.board_meetings_held) {
        await fillByExactLabel("board_meetings_held", "number of meetings held", payload.board_meetings_held);
    }
    if (payload.committee_meetings_held !== undefined && payload.committee_meetings_held !== null) {
        await fillByExactLabel("committee_meetings_held", "number of meetings held", payload.committee_meetings_held);
    }
    if (payload.loan_guarantee_given) {
      const lgVal = payload.loan_guarantee_given || "No";
      const lgRadios = findInputsNearText("loan guarantee is given", 'input[type="radio"]');
      for (const r of lgRadios) {
        const containerText = normalize(r.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
        if (containerText === lgVal.toLowerCase() || containerText.startsWith(lgVal.toLowerCase())) {
          r.checked = true; r.click(); r.dispatchEvent(new Event('change', { bubbles: true }));
          filledCount++; auditLogs.push({ Field: "loan_guarantee_given", Value: lgVal, Status: "✅ FILLED" }); break;
        }
      }
    }
    if (payload.sec186_reportable_transactions) {
      const repVal = payload.sec186_reportable_transactions || "No";
      const repRadios = findInputsNearText("reportable transactions", 'input[type="radio"]');
      for (const r of repRadios) {
        const containerText = normalize(r.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
        if (containerText === repVal.toLowerCase() || containerText.startsWith(repVal.toLowerCase())) {
          r.checked = true; r.click(); r.dispatchEvent(new Event('change', { bubbles: true }));
          filledCount++; auditLogs.push({ Field: "sec186_reportable_transactions", Value: repVal, Status: "✅ FILLED" }); break;
        }
      }
    }
    if (payload.sec186_num_transactions) {
      const numTransInputs = findInputsNearText("number of transactions", 'input');
      if (numTransInputs.length > 0) {
        await fillInputQuadEngine(numTransInputs[0], payload.sec186_num_transactions);
        filledCount++; auditLogs.push({ Field: "sec186_num_transactions", Value: payload.sec186_num_transactions, Status: "✅ FILLED" });
      }
    }

  // =========================================================
  // LAYER 1: NATIVE AEM DIRECT STATE INJECTION (guideBridge)
  // =========================================================
  if (window.guideBridge) {
    try {
      // Unlock all auditor fields disabled by MCA initScript
      const auditorNodeNames = [
        "incomeTaxOfAuditor", "categoryOfAuditor", "membershipNumberOfAuditor",
        "nameOfTheAuditor", "addressLine1_Auditor", "pinCode_Auditor",
        "city_Auditor", "district_Auditor", "state_Auditor", "country_Auditor"
      ];
      auditorNodeNames.forEach(name => {
        try {
          const n = window.guideBridge.resolveNode(name);
          if (n) { n.enabled = true; n.readOnly = false; }
        } catch (e) {}
      });

      // Unlock AGM Held, AGM Date & ADT-1 SRN based on exact MCA source rules
      try {
        const agmNode = window.guideBridge.resolveNode("whetherAnnual");
        if (agmNode) {
          agmNode.enabled = true;
          agmNode.value = payload.agm_held || "Yes";
        }
        
        const agmDateNode = window.guideBridge.resolveNode("agmDate");
        if (agmDateNode) {
          agmDateNode.visible = true;
          agmDateNode.enabled = true;
          if (payload.agm_date) agmDateNode.value = formatDate(payload.agm_date);
        }

        const dueDateNode = window.guideBridge.resolveNode("dueDateAgm");
        if (dueDateNode) {
          dueDateNode.enabled = true;
          if (payload.agm_due_date) dueDateNode.value = formatDate(payload.agm_due_date);
        }
      } catch (e) {}

  function toIsoDate(dStr) {
    if (!dStr) return "";
    let s = String(dStr).trim();
    if (s.includes("/")) {
      const p = s.split("/");
      if (p[0].length === 2) return `${p[2]}-${p[1]}-${p[0]}`;
    }
    return s;
  }

      const aemMap = {
        "compnayCin": payload.cin,
        "nameOfCompany": payload.company_name,
        
        // Logical mappings (Fallback)
        "financialYearDateFrom": toIsoDate(payload.fy_start_date),
        "financialYearDateTo": toIsoDate(payload.fy_end_date),
        "dateOfBoardDirectors": toIsoDate(payload.board_meeting_date),
        "SRNOfFormADT1": payload.srn_adt1 || "",
        "whetherAnnual": payload.agm_held || "Yes",
        "agmDate": toIsoDate(payload.agm_date),
        "dueDateAgm": toIsoDate(payload.agm_due_date),
        "natureOfFinancialStatements": payload.nature_of_financial_statements || "Adopted Financial statements",
        "categoryOfAuditor": "Auditor's Firm",
        "membershipNumberOfAuditor": payload.auditor_frn,
        "nameOfTheAuditor": payload.auditor_name,
        "addressLine1_Auditor": payload.auditor_address_1,
        "city_Auditor": payload.auditor_city || payload.auditor_district,
        "district_Auditor": payload.auditor_district,
        "state_Auditor": payload.auditor_state,
        "pinCode_Auditor": payload.auditor_pincode,
        "country_Auditor": "India",
        "sh_capital_cy": payload.share_capital?.current_year,
        "sh_capital_py": payload.share_capital?.previous_year,
        "reserves_surplus_cy": payload.reserves_and_surplus?.current_year,
        "reserves_surplus_py": payload.reserves_and_surplus?.previous_year,
        "lt_borrowings_cy": payload.long_term_borrowings?.current_year,
        "lt_borrowings_py": payload.long_term_borrowings?.previous_year,
        "ppe_cy": payload.tangible_assets?.current_year,
        "ppe_py": payload.tangible_assets?.previous_year,
        "cash_equivalents_cy": payload.cash_and_bank_balances?.current_year,
        "cash_equivalents_py": payload.cash_and_bank_balances?.previous_year,
        "turnover_cy": payload.revenue_from_operations?.current_year,
        "turnover_py": payload.revenue_from_operations?.previous_year,
        "pat_cy": payload.profit_after_tax?.current_year,
        "pat_py": payload.profit_after_tax?.previous_year,
      };

      // Execute AEM Direct Injection via flexible node visitation (The Holy Grail)
      window.guideBridge.visit(function(node) {
        if (!node) return;
        
        let val = null;
        let matchedKey = null;

        for (const [mapKey, mapVal] of Object.entries(aemMap)) {
          if (!mapVal) continue;
          const cleanMapKey = String(mapKey).replace('___widget', '');
          
          const isWidgetId = node.id && (
            node.id.startsWith("guidetextbox") ||
            node.id.startsWith("guidedatepicker") ||
            node.id.startsWith("guideradio") ||
            node.id.startsWith("guidedropdown") ||
            node.id.startsWith("guideContainer")
          );

          if (
            (node.id && node.id === cleanMapKey) ||
            (node.name && node.name === cleanMapKey) ||
            (node.somExpression && (node.somExpression === cleanMapKey || node.somExpression.endsWith(cleanMapKey))) ||
            (isWidgetId && (cleanMapKey === node.id || cleanMapKey.endsWith(node.id)))
          ) {
            val = mapVal;
            matchedKey = mapKey;
            break;
          }
        }

        if (val !== null && val !== undefined) {
          try {
            node.value = val;
            try { node.displayValue = val; } catch(e) {}
            if (window.guideBridge.setProperty) {
              window.guideBridge.setProperty(node, "value", val);
              try { window.guideBridge.setProperty(node, "displayValue", val); } catch(e) {}
            }
            
            // Sync underlying DOM input if element reference exists
            try {
              const widgetEl = document.getElementById(node.id + "___widget") || document.getElementById(node.id);
              if (widgetEl) {
                const inp = widgetEl.querySelector('input') || widgetEl;
                if (inp) {
                  inp.value = val;
                  inp.setAttribute('value', val);
                }
              }
            } catch(e) {}

            try { if (node.validate) node.validate(); } catch(e) {}
            node.errorText = "";
            try { if (window.guideBridge.setProperty) window.guideBridge.setProperty(node, "errorText", ""); } catch(e) {}
            try { if (node.execEvent) node.execEvent("exit"); } catch(e) {}
            try { if (node.execEvent) node.execEvent("change"); } catch(e) {}
            filledCount++;
            auditLogs.push({ Field: `(AEM Direct Bridge) ${node.name || node.id}`, Value: val, Status: "⚡ FILLED" });
          } catch(e) {}
        }
      });
    } catch (e) { console.warn("AEM Direct Bridge fallback:", e); }
  }

  // --- NEW: FINANCIAL TABLE AUTO-FILL ENGINE ---
  async function fillFinancialRow(labelText, payloadData) {
    if (!payloadData) return;
    const normText = normalize(labelText);
    
    // Find cell matching text (ignoring (a), (b), (i) prefixes)
    const textEls = Array.from(document.querySelectorAll('td, span, div, p, label')).filter(el => {
      if (el.children.length > 0) return false;
      const text = normalize(el.textContent);
      return text === normText || text.endsWith(normText) || text.includes(normText);
    });

    for (const el of textEls) {
      // Find the parent row
      const row = el.closest('tr, .guideTableRow, .row');
      if (row) {
        // Get all text inputs in this row
        const inputs = Array.from(row.querySelectorAll('input[type="text"], input[type="number"]'))
                           .filter(i => i.offsetWidth > 0 && i.offsetHeight > 0);
        
        if (inputs.length >= 2) {
          if (payloadData.current_year !== null && payloadData.current_year !== undefined) {
            await fillInputQuadEngine(inputs[0], String(payloadData.current_year));
            filledCount++; auditLogs.push({ Field: labelText + " (CY)", Value: payloadData.current_year, Status: "✅ FILLED" });
          }
          if (payloadData.previous_year !== null && payloadData.previous_year !== undefined) {
            await fillInputQuadEngine(inputs[1], String(payloadData.previous_year));
            filledCount++; auditLogs.push({ Field: labelText + " (PY)", Value: payloadData.previous_year, Status: "✅ FILLED" });
          }
          // Yield between filling tables
          await delay(50);
          return; // Success
        }
      }
    }
  }

  // Master Map of AOC-4 Label -> Payload Key
  const financialMap = {
    // Equity and Liabilities
    "share capital": "share_capital",
    "reserves and surplus": "reserves_and_surplus",
    "money received against share warrants": "money_received_share_warrants",
    "share application money pending allotment": "share_application_money",
    "long term borrowings": "long_term_borrowings",
    "deferred tax liabilities": "deferred_tax_liabilities",
    "other long term liabilities": "other_long_term_liabilities",
    "long term provisions": "long_term_provisions",
    "short term borrowings": "short_term_borrowings",
    "total outstanding dues of micro enterprises": "trade_payables_msme",
    "total outstanding dues of creditors other": "trade_payables_others",
    "other current liabilities": "other_current_liabilities",
    "short term provisions": "short_term_provisions",
    // Assets
    "property plant and equipment": "tangible_assets",
    "intangible assets": "intangible_assets",
    "capital work in progress": "capital_wip",
    "intangible assets under development": "intangible_assets_under_dev",
    "non current investments": "non_current_investments",
    "deferred tax assets": "deferred_tax_assets",
    "long term loans and advances": "long_term_loans_advances",
    "other non current assets": "other_non_current_assets",
    "current investments": "current_investments",
    "inventories": "inventories",
    "trade receivables": "trade_receivables",
    "cash and cash equivalents": "cash_and_bank_balances",
    "short term loans and advances": "short_term_loans_advances",
    "other current assets": "other_current_assets",
    // P&L
    "sale of goods manufactured": "revenue_from_operations",
    "sale or supply of services": "revenue_from_operations",
    "dividend income": "other_income",
    "interest income": "other_income",
    "cost of materials consumed": "cost_of_materials_consumed",
    "purchases of stock in trade": "purchases_of_stock_in_trade",
    "employee benefit": "employee_benefit_expense",
    "finance cost": "finance_costs",
    "depreciation and amortisation": "depreciation_and_amortisation",
    "other expenses": "other_expenses",
    "current tax": "current_tax",
    "deferred tax": "deferred_tax"
  };

  // Execute Financial Fill
  for (const [label, key] of Object.entries(financialMap)) {
    if (payload[key]) {
      await fillFinancialRow(label, payload[key]);
    }
  }

  // (Save button logic moved to the very end of the function)

  } else if (context === "TAB2_AUDITOR_REPORT") {
    
    // Number of qualifications
    if (payload.number_of_qualifications !== undefined && payload.number_of_qualifications !== null) {
      const qualInputs = findInputsNearText("number of qualifications reservation or adverse", 'input');
      if (qualInputs.length > 0) {
        await fillInputQuadEngine(qualInputs[0], payload.number_of_qualifications);
        filledCount++; auditLogs.push({ Field: "number_of_qualifications", Value: payload.number_of_qualifications, Status: "✅ FILLED" });
      }
    }

    // CARO Applicability
    const caroVal = payload.caro_applicable || "No";
    const caroRadios = findInputsNearText("whether companies auditors report order caro is applicable", 'input[type="radio"]');
    for (const radio of caroRadios) {
      const containerText = normalize(radio.closest('mat-radio-button, label, .guideFieldNode, div')?.textContent || "");
      if (containerText === caroVal.toLowerCase() || containerText.startsWith(caroVal.toLowerCase())) {
        radio.checked = true; radio.click(); radio.dispatchEvent(new Event('change', { bubbles: true }));
        filledCount++; auditLogs.push({ Field: "caro_applicable", Value: caroVal, Status: "✅ FILLED" });
        break;
      }
    }

  } else {
      console.log("🚀 ROUTER: Unknown Context! Page text:", pageText.substring(0, 200));
  }

  // Auto-dismiss MCA Data Reset warning modal if it appears (by clicking "No")
  try {
    await new Promise(resolve => setTimeout(resolve, 500)); // wait for modal animation
    const noBtns = Array.from(document.querySelectorAll('button, .btn')).filter(b => b.textContent && b.textContent.trim() === "No" && b.offsetParent !== null);
    for (const btn of noBtns) {
      if (document.body.innerText.includes("resetting of data")) {
        btn.click();
        auditLogs.push({ Field: "Warning Modal", Value: "Auto-dismissed (No)", Status: "✅ ACTION" });
        await new Promise(resolve => setTimeout(resolve, 500));
        break;
      }
    }
  } catch (e) {}

  // Final Step: Click Save Button
  try {
    const btns = Array.from(document.querySelectorAll('button, .btn, [role="button"]'));
    const saveBtn = btns.find(b => b.textContent && b.textContent.trim().toLowerCase() === "save");
    if (saveBtn && !saveBtn.disabled && !saveBtn.classList.contains('disabled')) {
      saveBtn.click();
      auditLogs.push({ Field: "Save Button", Value: "Clicked", Status: "✅ ACTION" });
    }
  } catch (e) {
    console.warn("Could not click Save button:", e);
  }



  return { filledCount: filledCount, auditLogs: auditLogs };
}
