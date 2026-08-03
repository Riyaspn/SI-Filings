const fs = require('fs');
const path = require('path');

const popupPath = path.join(__dirname, 'popup.js');
let code = fs.readFileSync(popupPath, 'utf8');

// The main function signature
const mainFuncStart = 'async function executeAOC4UltimateAutoFill(payload) {';

// Split the code at the start of the main function
const parts = code.split(mainFuncStart);
if (parts.length !== 2) {
    console.error("Could not find main function");
    process.exit(1);
}

let head = parts[0];
let body = parts[1];

// We need to inject the Context Router at the top of the body, right after the helper functions.
// Let's find the start of the actual logic.
const generalDetailsStartMarker = '  // 1. General Details';
const bodyParts = body.split(generalDetailsStartMarker);

let helpers = bodyParts[0];
let logic = generalDetailsStartMarker + bodyParts[1];

// Extract Table 2 Logic (Board Report Date & Signatory Details)
// It starts at "// 2c1. Board Report Date" and ends at "// 2e. Auditor Report Date (Item 6)"
const t2StartMarker = '  // 2c1. Board Report Date (Item 5a) - MUST BE FILLED BEFORE TABLE 5b!';
const t2EndMarker = '  // 2e. Auditor Report Date (Item 6)';

const t2Split1 = logic.split(t2StartMarker);
const beforeT2 = t2Split1[0];
const t2Split2 = t2Split1[1].split(t2EndMarker);
const table2Logic = t2StartMarker + t2Split2[0];
const afterT2 = t2EndMarker + t2Split2[1];

logic = beforeT2 + afterT2;

// Extract Phase 1 and Phase 2 boundaries
// Phase 1 ends after Auto-Save. Phase 2 starts at "  // 3. Auditor Details"
const phase2StartMarker = '  // 3. Auditor Details';
const phaseSplit = logic.split(phase2StartMarker);

let phase1Logic = phaseSplit[0];
let phase2Logic = phase2StartMarker + phaseSplit[1];

// We need to insert Table 2 logic into Phase 1, right BEFORE the Auto-Save logic!
const autoSaveMarker = '  // Auto-Click the Save button for Tab 1';
const p1Split = phase1Logic.split(autoSaveMarker);

phase1Logic = p1Split[0] + '\n' + table2Logic + '\n' + autoSaveMarker + p1Split[1];

// Now construct the final router!
const routerCode = `
  // ==========================================
  // SMART ROUTER: DETECT CONTEXT
  // ==========================================
  const pageText = document.body.innerText.toLowerCase();
  let context = "UNKNOWN";

  if (pageText.includes("general information") && pageText.includes("nature of financial statements")) {
    const subRadio = Array.from(document.querySelectorAll('input[type="radio"]')).find(r => (r.parentElement?.textContent || "").toLowerCase().includes("is a subsidiary company"));
    if (subRadio && !subRadio.disabled && !subRadio.readOnly) {
      context = "TAB1_PHASE2";
      console.log("🚀 ROUTER: Detected Tab 1 - Phase 2 (Subsidiary Details unlocked)");
    } else {
      context = "TAB1_PHASE1";
      console.log("🚀 ROUTER: Detected Tab 1 - Phase 1 (Pre-Save)");
    }
  } else if (pageText.includes("aoc-2")) {
    context = "AOC2";
  }

  if (context === "TAB1_PHASE1") {
`;

const phase1Closing = `
  } else if (context === "TAB1_PHASE2") {
`;

const phase2Closing = `
  } else {
      console.log("🚀 ROUTER: Unknown Context! Page text:", pageText.substring(0, 200));
  }
`;

// Reassemble the entire file
const newBody = helpers + routerCode + phase1Logic + phase1Closing + phase2Logic + phase2Closing;
// Wait, phase2Logic includes the final closing brace of the function? 
// The original body ended with `}\n`. So phase2Logic ends with `}\n`.
// We need to strip the final `}` from phase2Logic, add our `phase2Closing`, and then add the `}` back!

let lastBraceIndex = phase2Logic.lastIndexOf('}');
if (lastBraceIndex !== -1) {
    phase2Logic = phase2Logic.substring(0, lastBraceIndex) + phase2Closing + phase2Logic.substring(lastBraceIndex);
} else {
    phase2Logic += phase2Closing;
}

const finalCode = head + mainFuncStart + newBody;

fs.writeFileSync(popupPath, finalCode, 'utf8');
console.log("Successfully refactored popup.js!");
