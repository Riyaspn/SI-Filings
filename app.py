"""
SI Filings Pro — All-In-One Statutory Filing Automation
=========================================================
Desktop application for CAs, CSs, and CMAs to automate
MCA Forms (AOC-4, MGT-7), GST, and Corporate Filings.

Architecture:
  - CustomTkinter GUI (Dark Mode, SI Lead Xtract styling)
  - License verification (ported from SI Lead Xtract)
  - Non-AI PDF/Word parser + Gemini AI fallback
  - Side-by-side CA/CS verification screen
  - Local API server for Chrome Extension communication
"""

import os
import sys
import threading
import json
import webbrowser
from tkinter import filedialog, messagebox
from datetime import datetime

import customtkinter as ctk

from license_manager import LicenseManager
from parser_engine import parse_financial_statement
from validator import validate_aoc4_data, get_validation_summary
from aoc4_schema import (
    AOC4_SCHEMA, get_all_sections, get_fields_by_section,
    get_field_label, get_financial_field_keys, is_general_section
)


from server import start_local_api_server, set_app_data
from excel_populator import ExcelPopulator

# ============================================================
# Theme & App Configuration
# ============================================================

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Colors (matching SI Lead Xtract palette)
PRIMARY = "#38bdf8"
PRIMARY_DARK = "#0ea5e9"
BG_DARK = "#0f172a"
BG_CARD = "#1E293B"
BORDER = "#334155"
TEXT_MUTED = "#94a3b8"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
TEXT_LIGHT = "#E2E8F0"


# ============================================================
# Main Application
# ============================================================

class AOC4App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SI Filings Pro — CA & CS Corporate Filing Automation")
        self.geometry("950x720")
        self.minsize(850, 650)

        # Core State
        self.license_mgr = LicenseManager()
        self.current_file = None
        self.parsed_result = None
        self.validation_results = None
        self.field_entries = {}  # key -> CTkEntry widget for editing

        # Start Local API Server for Chrome Extension Communication
        try:
            self.api_server = start_local_api_server()
        except Exception as e:
            print(f"API Server Notice: {e}")

        # Main Container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        # Check license on startup
        self._check_license()

    # ==========================================================
    # License Flow
    # ==========================================================

    def _check_license(self):
        """Check license on startup."""
        result = self.license_mgr.check_license_on_startup()
        status = result["status"]

        if status in ("valid", "offline_grace"):
            self._show_main_screen()
        else:
            self._show_license_screen(result.get("message", ""))

    def _show_license_screen(self, err_msg=""):
        """Render the license key activation view."""
        self._clear_container()

        # Logo / Title
        title = ctk.CTkLabel(
            self.container,
            text="SI Filings Pro",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=PRIMARY
        )
        title.pack(pady=(50, 5))

        subtitle = ctk.CTkLabel(
            self.container,
            text="Universal Filing & AI Automation for Chartered Accountants, CSs & CMAs",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED
        )
        subtitle.pack(pady=(0, 5))

        version_label = ctk.CTkLabel(
            self.container,
            text="by Sharp Intell Technologies",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED
        )
        version_label.pack(pady=(0, 30))

        if err_msg:
            err_label = ctk.CTkLabel(
                self.container,
                text=err_msg,
                text_color=DANGER,
                font=ctk.CTkFont(weight="bold")
            )
            err_label.pack(pady=5)

        # Form Frame
        form_frame = ctk.CTkFrame(self.container, fg_color=BG_CARD, border_width=1, border_color=BORDER)
        form_frame.pack(pady=10, padx=80, fill="x")

        # Email Entry
        ctk.CTkLabel(form_frame, text="Registered Email:", font=ctk.CTkFont(size=12)).pack(
            pady=(15, 2), padx=20, anchor="w"
        )
        self.email_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. name@cafirm.com", height=35)
        self.email_entry.pack(pady=(0, 15), padx=20, fill="x")

        # License Key Entry
        ctk.CTkLabel(form_frame, text="Firm License Key:", font=ctk.CTkFont(size=12)).pack(
            pady=(0, 2), padx=20, anchor="w"
        )
        self.key_entry = ctk.CTkEntry(form_frame, placeholder_text="SFP-XXXX-XXXX-XXXX", height=35)
        self.key_entry.pack(pady=(0, 20), padx=20, fill="x")

        # Activate Button
        self.activate_btn = ctk.CTkButton(
            self.container,
            text="Activate License",
            command=self._activate_key,
            height=42,
            fg_color=PRIMARY,
            text_color=BG_DARK,
            hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(weight="bold", size=14)
        )
        self.activate_btn.pack(pady=20, padx=80, fill="x")

        # Links
        links_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        links_frame.pack(pady=10)

        buy_link = ctk.CTkLabel(
            links_frame,
            text="Don't have a license key? Contact us.",
            text_color=PRIMARY,
            cursor="hand2"
        )
        buy_link.pack(side="left", padx=10)
        buy_link.bind("<Button-1>", lambda e: webbrowser.open("https://sharpintell.com"))

    def _activate_key(self):
        """Validate license key entered by user."""
        key = self.key_entry.get().strip()
        email = self.email_entry.get().strip()

        if not key or not email:
            messagebox.showerror("Error", "Please enter both your Email and License Key.")
            return

        self.activate_btn.configure(state="disabled", text="Validating...")

        def run_activation():
            result = self.license_mgr.activate_key(email, key)
            if result["status"] == "success":
                self.after(0, self._show_main_screen)
            else:
                self.after(0, lambda: messagebox.showerror("Error", result["message"]))
                self.after(0, lambda: self.activate_btn.configure(state="normal", text="Activate License"))

        threading.Thread(target=run_activation, daemon=True).start()

    # ==========================================================
    # Main Application Screen
    # ==========================================================

    def _show_main_screen(self):
        """Render the main application interface with tabs."""
        self._clear_container()

        # Header Banner
        header = ctk.CTkFrame(self.container, fg_color=BG_CARD, height=40)
        header.pack(fill="x", pady=(0, 10))

        email_display = self.license_mgr.get_customer_email()
        firm_name = self.license_mgr.get_firm_name()
        credits_bal = self.license_mgr.get_credits_balance()
        status_text = f"🏢 {firm_name}  |  👤 {email_display}  |  ⚡ Wallet: {credits_bal} SI Credits"
        if self.license_mgr.is_offline_mode:
            status_text += " [OFFLINE GRACE MODE]"

        ctk.CTkLabel(
            header, text=status_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=PRIMARY
        ).pack(side="left", padx=15, pady=5)

        logout_btn = ctk.CTkLabel(
            header, text="🚪 Log Out",
            text_color=DANGER, cursor="hand2",
            font=ctk.CTkFont(size=11, weight="bold", underline=True)
        )
        logout_btn.pack(side="right", padx=15, pady=5)
        logout_btn.bind("<Button-1>", lambda e: self._logout())

        recharge_btn = ctk.CTkButton(
            header, text="💳 Recharge Wallet", width=120, height=26,
            fg_color=PRIMARY_DARK, hover_color="#0284c7",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: webbrowser.open("https://si-filings.pages.dev/#pricing")
        )
        recharge_btn.pack(side="right", padx=(5, 10), pady=5)

        # Tabs
        self.tabview = ctk.CTkTabview(self.container)
        self.tabview.pack(fill="both", expand=True)

        self.tab_filing = self.tabview.add("📄 AOC-4 Filing")
        self.tab_results = self.tabview.add("✅ Verification")
        self.tab_excel = self.tabview.add("📊 Excel Auto-Fill")
        self.tab_extension = self.tabview.add("⚡ Chrome RPA")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        self._build_filing_tab()
        self._build_results_tab()
        self._build_excel_tab()
        self._build_extension_tab()
        self._build_settings_tab()

    # ==========================================================
    # Tab 1: AOC-4 Filing (Upload & Parse)
    # ==========================================================

    def _build_filing_tab(self):
        """Build the file upload and parsing tab."""
        tab = self.tab_filing

        # Title
        ctk.CTkLabel(
            tab, text="Upload Financial Statement",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_LIGHT
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            tab,
            text="Upload a PDF or Word (.docx) file of the company's Audited Financial Statement.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED
        ).pack(pady=(0, 15))

        # File Selection Row
        file_row = ctk.CTkFrame(tab, fg_color="transparent")
        file_row.pack(pady=5, fill="x", padx=20)

        self.file_btn = ctk.CTkButton(
            file_row, text="📁 Browse File",
            command=self._browse_file,
            width=150, height=38,
            fg_color=PRIMARY, text_color=BG_DARK,
            hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(weight="bold")
        )
        self.file_btn.pack(side="left", padx=(0, 10))

        self.file_label = ctk.CTkLabel(
            file_row, text="No file selected",
            text_color=TEXT_MUTED, font=ctk.CTkFont(size=12)
        )
        self.file_label.pack(side="left", fill="x", expand=True)

        # Parse Button
        self.parse_btn = ctk.CTkButton(
            tab, text="🔍 Extract Financial Data (Free Parser)",
            command=self._start_parsing,
            height=42, width=350,
            fg_color=SUCCESS, text_color=BG_DARK,
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold", size=13),
            state="disabled"
        )
        self.parse_btn.pack(pady=15)

        # Progress
        self.progress = ctk.CTkProgressBar(tab, width=500)
        self.progress.pack(pady=5)
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            tab, text="Ready.", text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=5)

        # Console Output
        self.console = ctk.CTkTextbox(
            tab, width=600, height=200,
            font=ctk.CTkFont(family="Consolas", size=11),
            border_width=1, border_color=BORDER,
            fg_color=BG_DARK, text_color=PRIMARY
        )
        self.console.pack(pady=10, fill="both", expand=True, padx=20)
        self.console.insert("0.0", "SI Filings Pro v1.0.0 — Ready.\n")
        self.console.configure(state="disabled")

    def _browse_file(self):
        """Open file dialog to select a PDF or Word file."""
        filepath = filedialog.askopenfilename(
            title="Select Financial Statement",
            filetypes=[
                ("Financial Statements", "*.pdf *.docx"),
                ("PDF Files", "*.pdf"),
                ("Word Documents", "*.docx"),
                ("All Files", "*.*"),
            ],
            initialdir=self.license_mgr.settings_data.get("last_used_directory", "")
        )
        if filepath:
            self.current_file = filepath
            self.file_label.configure(text=os.path.basename(filepath), text_color=SUCCESS)
            self.parse_btn.configure(state="normal")

            # Save last used directory
            self.license_mgr.save_settings({
                "last_used_directory": os.path.dirname(filepath)
            })

    def _start_parsing(self):
        """Start parsing in a background thread."""
        if not self.current_file:
            return

        self.parse_btn.configure(state="disabled", text="⏳ Parsing...")
        self.progress.set(0.1)
        self._log("Parsing started...")
        self._log(f"File: {os.path.basename(self.current_file)}")

        threading.Thread(target=self._run_parsing, daemon=True).start()

    def _run_parsing(self):
        """Background parsing task using Gemini Vision AI (Primary) with local fallback."""
        try:
            # Check for Gemini API Key pool
            gemini_key = self.license_mgr.get_gemini_api_key()
            if not gemini_key:
                if os.path.exists(".env"):
                    with open(".env", "r") as env_f:
                        for line in env_f:
                            if line.startswith("GEMINI_API_KEYS="):
                                gemini_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                                break
                if not gemini_key:
                    gemini_key = os.getenv("GEMINI_API_KEYS", "")

            # If Gemini Key is available, use Gemini Vision AI as Primary Engine
            if gemini_key:
                self.after(0, lambda: self._log("🚀 Step 1: Running Gemini Vision AI Parser (Primary Engine)..."))
                self.after(0, lambda: self.progress.set(0.3))

                from gemini_parser import extract_with_gemini
                result = extract_with_gemini(self.current_file, gemini_key)
                confidence = result["confidence"]

                self.after(0, lambda: self.progress.set(0.7))
                self.after(0, lambda: self._log(
                    f"✨ Gemini AI Extraction Complete! Confidence: {confidence:.1%} | "
                    f"Matched: {result['matched_count']}/{result['total_fields']} fields | "
                    f"Engine: {result['method']}"
                ))

            else:
                # Fallback to local pdfplumber if no API key present
                self.after(0, lambda: self._log("Step 1: Running local non-AI parser (pdfplumber / python-docx)..."))
                self.after(0, lambda: self.progress.set(0.3))

                result = parse_financial_statement(self.current_file)
                confidence = result["confidence"]

                self.after(0, lambda: self.progress.set(0.7))
                self.after(0, lambda: self._log(
                    f"Local Parser Complete. Confidence: {confidence:.1%} | "
                    f"Matched: {result['matched_count']}/{result['total_fields']} fields"
                ))

            self.parsed_result = result

            # Log SI Filings Enterprise Engine Audit Badges
            ent_audit = result.get("enterprise_audit", {})
            unit_info = ent_audit.get("unit", {})
            math_info = ent_audit.get("validation", {})
            
            if unit_info:
                if unit_info.get("scaled"):
                    self.after(0, lambda: self._log(f"  🟢 Unit Scaler: Auto-scaled {unit_info.get('fields_scaled')} fields from '{unit_info.get('unit')}' to Absolute Rupees."))
                else:
                    self.after(0, lambda: self._log(f"  🟢 Unit Scaler: Verified unit '{unit_info.get('unit')}' (Absolute Rupees)."))

            if math_info:
                status_str = "🟢 100% Verified (Passed All Accounting Identities)" if math_info.get("passed") else "🟡 Mathematical Review Suggested"
                self.after(0, lambda: self._log(f"  {status_str}"))
                for check in math_info.get("checks", []):
                    if check.get("status") == "AUTO_HEALED":
                        self.after(0, lambda c=check: self._log(f"    ✨ Auto-Healed {c.get('rule')} ({c.get('year')}): {c.get('diff'):+.2f} rupee rounding adjustment applied."))

            # Step 3: Validation
            self.after(0, lambda: self._log("\nStep 2: Running mathematical validation checks..."))
            self.after(0, lambda: self.progress.set(0.8))

            val_results = validate_aoc4_data(result["data"])
            self.validation_results = val_results
            summary = get_validation_summary(val_results)

            for detail in summary["details"]:
                self.after(0, lambda d=detail: self._log(f"  {d}"))

            self.after(0, lambda: self._log(
                f"\nOverall Status: {summary['overall_status']} | "
                f"Passed: {summary['passed']}/{summary['total_checks']} | "
                f"Warnings: {summary['warnings']} | Failures: {summary['failed']}"
            ))

            self.after(0, lambda: self.progress.set(1.0))
            self.after(0, lambda: self._log("\n✅ Extraction complete. Switching to 'Verification' tab..."))
            self.after(0, lambda: self.parse_btn.configure(state="normal", text="🔍 Extract Financial Data"))
            self.after(0, self._populate_verification_tab)
            self.after(0, lambda: self.tabview.set("✅ Verification"))

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            self.after(0, lambda: self._log(f"\n❌ ERROR: {str(e)}\n{tb}"))
            self.after(0, lambda: self.parse_btn.configure(state="normal", text="🔍 Extract Financial Data (Free Parser)"))
            self.after(0, lambda: self.progress.set(0))

    def _log(self, message: str):
        """Append a message to the console."""
        self.console.configure(state="normal")
        self.console.insert("end", f"{message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    # ==========================================================
    # Tab 2: CA/CS Verification Screen
    # ==========================================================

    def _build_results_tab(self):
        """Build the side-by-side verification tab."""
        tab = self.tab_results

        ctk.CTkLabel(
            tab, text="CA / CS Cross-Verification",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_LIGHT
        ).pack(pady=(10, 5))

        ctk.CTkLabel(
            tab,
            text="Review extracted values against the original financial statement. Edit any field before approving.",
            font=ctk.CTkFont(size=12),
            text_color=TEXT_MUTED
        ).pack(pady=(0, 10))

        self.filing_mode = ctk.StringVar(value="Offline Filing Mode")
        self.mode_switch = ctk.CTkSegmentedButton(
            tab,
            values=["Online Filing Mode", "Offline Filing Mode"],
            variable=self.filing_mode,
            command=lambda v: self._populate_verification_tab()
        )
        self.mode_switch.pack(pady=(0, 10))

        # Scrollable form
        self.verify_scroll = ctk.CTkScrollableFrame(
            tab, fg_color="transparent",
            label_text="Extracted AOC-4 Form Fields",
            label_font=ctk.CTkFont(size=13, weight="bold"),
            label_fg_color=BG_CARD
        )
        self.verify_scroll.pack(fill="both", expand=True, padx=10, pady=5)

        # Placeholder
        self.verify_placeholder = ctk.CTkLabel(
            self.verify_scroll,
            text="📂 No data yet.\nUpload a financial statement in the 'AOC-4 Filing' tab to begin.",
            font=ctk.CTkFont(size=13),
            text_color=TEXT_MUTED
        )
        self.verify_placeholder.pack(pady=40)

        # Action buttons
        btn_row = ctk.CTkFrame(tab, fg_color="transparent")
        btn_row.pack(pady=10, fill="x", padx=20)

        self.approve_btn = ctk.CTkButton(
            btn_row, text="✅ Approve Data & Save",
            command=self._approve_data,
            height=40, width=200,
            fg_color=SUCCESS, text_color=BG_DARK,
            hover_color="#059669",
            font=ctk.CTkFont(weight="bold"),
            state="disabled"
        )
        self.approve_btn.pack(side="left", padx=5)

        self.export_btn = ctk.CTkButton(
            btn_row, text="📥 Export to JSON",
            command=self._export_json,
            height=40, width=180,
            fg_color=PRIMARY, text_color=BG_DARK,
            hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(weight="bold"),
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=5)

    def _populate_verification_tab(self):
        """Populate the verification tab with parsed data."""
        if not self.parsed_result:
            return

        # Clear placeholder
        for widget in self.verify_scroll.winfo_children():
            widget.destroy()

        data = self.parsed_result["data"]
        matched = self.parsed_result.get("matched", [])
        self.field_entries = {}

        # Group fields by section based on mode
        from aoc4_schema import is_general_section
        all_sections = get_all_sections()
        
        if getattr(self, "filing_mode", None) and self.filing_mode.get() == "Offline Filing Mode":
            non_fin = [s for s in all_sections if is_general_section(s)]
            fin = [s for s in all_sections if not is_general_section(s)]
            ordered_sections = non_fin + fin
        else:
            ordered_sections = all_sections

        for section in ordered_sections:
            fields = get_fields_by_section(section)
            if not fields:
                continue

            # Section header
            section_frame = ctk.CTkFrame(self.verify_scroll, fg_color=BG_CARD, border_width=1, border_color=BORDER)
            section_frame.pack(fill="x", pady=(10, 2), padx=5)

            ctk.CTkLabel(
                section_frame, text=section,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=PRIMARY
            ).pack(pady=8, padx=15, anchor="w")

            for field_def in fields:
                key = field_def["key"]
                label = field_def["label"]
                val = data.get(key)

                row = ctk.CTkFrame(self.verify_scroll, fg_color="transparent")
                row.pack(fill="x", padx=15, pady=2)

                # Status indicator
                if key in matched:
                    indicator = "🟢"
                elif field_def["required"]:
                    indicator = "🔴"
                else:
                    indicator = "🟡"

                ctk.CTkLabel(
                    row, text=indicator, width=25
                ).pack(side="left", padx=(0, 5))

                # Label
                ctk.CTkLabel(
                    row, text=label,
                    font=ctk.CTkFont(size=11),
                    text_color=TEXT_LIGHT,
                    width=300, anchor="w"
                ).pack(side="left", padx=(0, 10))

                if is_general_section(field_def["section"]):
                    if "options" in field_def:
                        # Dropdown menu for predefined options
                        entry = ctk.CTkOptionMenu(row, width=300, height=30, values=field_def["options"])
                        entry.pack(side="left", padx=2)
                        if val:
                            entry.set(str(val))
                        else:
                            entry.set(field_def["options"][0]) # Default to first option if null
                        self.field_entries[key] = entry
                    else:
                        # Single text entry
                        entry = ctk.CTkEntry(row, width=300, height=30)
                        entry.pack(side="left", padx=2)
                        if val:
                            entry.insert(0, str(val))
                        self.field_entries[key] = entry
                else:
                    # Current Year + Previous Year entries
                    ctk.CTkLabel(row, text="CY:", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(side="left", padx=(0, 2))
                    cy_entry = ctk.CTkEntry(row, width=130, height=28)
                    cy_entry.pack(side="left", padx=2)

                    ctk.CTkLabel(row, text="PY:", font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(side="left", padx=(10, 2))
                    py_entry = ctk.CTkEntry(row, width=130, height=28)
                    py_entry.pack(side="left", padx=2)

                    if isinstance(val, dict):
                        cy = val.get("current_year")
                        py = val.get("previous_year")
                        if cy is not None:
                            cy_entry.insert(0, f"{cy:,.2f}")
                        if py is not None:
                            py_entry.insert(0, f"{py:,.2f}")

                    self.field_entries[key] = {"cy": cy_entry, "py": py_entry}

        # Enable buttons
        self.approve_btn.configure(state="normal")
        self.export_btn.configure(state="normal")

    def _approve_data(self):
        """CA/CS approves the verified data."""
        if not self.parsed_result:
            return

        # Read edited values from entries
        data = self.parsed_result["data"]

        for key, widget in self.field_entries.items():
            if isinstance(widget, dict):
                # Financial field with CY/PY
                cy_text = widget["cy"].get().strip().replace(",", "")
                py_text = widget["py"].get().strip().replace(",", "")

                try:
                    cy = float(cy_text) if cy_text else None
                except ValueError:
                    cy = None
                try:
                    py = float(py_text) if py_text else None
                except ValueError:
                    py = None

                data[key] = {"current_year": cy, "previous_year": py}
            else:
                # General info field
                data[key] = widget.get().strip() or None

        self.parsed_result["data"] = data
        self.parsed_result["approved"] = True
        self.parsed_result["approved_at"] = datetime.now().isoformat()

        # Update local HTTP API server state for Chrome Extension
        set_app_data(self.parsed_result)

        messagebox.showinfo(
            "Data Approved",
            "✅ Financial data has been verified and approved.\n\n"
            "You can now:\n"
            "• Use the SI Filings Pro Chrome Extension to 1-Click Auto-Fill on MCA Portal\n"
            "• Export to JSON file"
        )

        self._log("✅ Data approved by CA/CS at " + datetime.now().strftime("%H:%M:%S") + " — Synced to Chrome Extension API.")

    def _export_json(self):
        """Export approved data to JSON file."""
        if not self.parsed_result:
            return

        filepath = filedialog.asksaveasfilename(
            title="Export AOC-4 Data as JSON",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile=f"AOC4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.parsed_result, f, indent=2, ensure_ascii=False, default=str)
            messagebox.showinfo("Exported", f"AOC-4 data exported to:\n{filepath}")
            self._log(f"📥 Data exported to: {filepath}")

    # ==========================================================
    # Tab 3: Settings
    # ==========================================================

    def _build_settings_tab(self):
        """Build the settings tab."""
        tab = self.tab_settings

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=15)

        # Gemini API Key
        ctk.CTkLabel(
            scroll, text="Google Gemini API Key (AI Fallback)",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            scroll,
            text="Used only when the free parser confidence is below threshold. Leave blank to disable AI fallback.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
        ).pack(anchor="w", pady=(0, 8))

        self.gemini_key_entry = ctk.CTkEntry(
            scroll, width=500, height=35,
            placeholder_text="AIza..."
        )
        self.gemini_key_entry.pack(anchor="w", pady=(0, 20))
        self.gemini_key_entry.insert(0, self.license_mgr.get_gemini_api_key())

        # Confidence Threshold
        ctk.CTkLabel(
            scroll, text="Parser Confidence Threshold",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 5))

        ctk.CTkLabel(
            scroll,
            text="If the free parser confidence falls below this value, the Gemini AI fallback is triggered.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
        ).pack(anchor="w", pady=(0, 8))

        threshold_row = ctk.CTkFrame(scroll, fg_color="transparent")
        threshold_row.pack(anchor="w", pady=(0, 20))

        self.threshold_entry = ctk.CTkEntry(threshold_row, width=80, height=35)
        self.threshold_entry.pack(side="left", padx=(0, 10))
        self.threshold_entry.insert(0, str(int(self.license_mgr.get_confidence_threshold() * 100)))

        ctk.CTkLabel(threshold_row, text="% (default: 95%)", text_color=TEXT_MUTED).pack(side="left")

        # Save Button
        save_btn = ctk.CTkButton(
            scroll, text="💾 Save Settings",
            command=self._save_settings,
            height=40, width=200,
            fg_color=PRIMARY, text_color=BG_DARK,
            hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(weight="bold")
        )
        save_btn.pack(anchor="w", pady=20)

    def _save_settings(self):
        """Save settings to local storage."""
        gemini_key = self.gemini_key_entry.get().strip()

        try:
            threshold = int(self.threshold_entry.get().strip()) / 100.0
            threshold = max(0.5, min(1.0, threshold))
        except (ValueError, TypeError):
            threshold = 0.95

        self.license_mgr.save_settings({
            "gemini_api_key": gemini_key,
            "confidence_threshold": threshold,
        })

        messagebox.showinfo("Settings Saved", "Settings saved successfully!")

    # ==========================================================
    # Excel Tab
    # ==========================================================

    def _build_excel_tab(self):
        """Build the Excel auto-fill tab interface."""
        frame = self.tab_excel

        # Title
        ctk.CTkLabel(
            frame, text="Excel Auto-Fill Engine",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PRIMARY
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            frame,
            text="Inject verified financial data directly into the downloaded MCA Excel templates.",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        ).pack(pady=(0, 20))

        # File selection frame
        file_frame = ctk.CTkFrame(frame, fg_color=BG_CARD)
        file_frame.pack(fill="x", padx=40, pady=10, ipady=10)

        ctk.CTkLabel(file_frame, text="AOC-4 Excel Template:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        
        self.excel_path_label = ctk.CTkLabel(file_frame, text="No file selected", text_color=TEXT_MUTED)
        self.excel_path_label.grid(row=0, column=1, padx=10, pady=15, sticky="w")

        def select_excel():
            path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx *.xlsm *.xlsb")])
            if path:
                self.excel_path_label.configure(text=os.path.basename(path), text_color=TEXT_LIGHT)
                self.selected_excel_path = path

        self.selected_excel_path = None
        ctk.CTkButton(file_frame, text="Browse", width=80, command=select_excel).grid(row=0, column=2, padx=20, pady=15, sticky="e")
        file_frame.grid_columnconfigure(1, weight=1)

        # Status and Progress
        self.excel_status_lbl = ctk.CTkLabel(frame, text="", text_color=SUCCESS, font=ctk.CTkFont(weight="bold"))
        self.excel_status_lbl.pack(pady=10)

        # Action Button
        self.run_excel_btn = ctk.CTkButton(
            frame, text="⚡ Auto-Fill Excel Template",
            command=self._run_excel_autofill,
            height=45, width=250,
            fg_color=PRIMARY, text_color=BG_DARK,
            hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(weight="bold", size=14)
        )
        self.run_excel_btn.pack(pady=20)

    def _run_excel_autofill(self):
        if not getattr(self, 'selected_excel_path', None):
            messagebox.showerror("Error", "Please select the downloaded AOC-4 Excel file first.")
            return

        if not self.parsed_result or "data" not in self.parsed_result:
            messagebox.showerror("Error", "No verified data found. Please parse a PDF and verify it first.")
            return

        if not self.license_mgr.can_perform_filing("AOC4_EXCEL"):
            messagebox.showerror(
                "Insufficient SI Credits",
                f"You currently have {self.license_mgr.get_credits_balance()} SI Credits remaining.\n\nAuto-filling an AOC-4 Financial Statement requires 10 SI Credits.\nPlease click '💳 Recharge Wallet' in the top bar to top-up your firm account!"
            )
            return

        self.run_excel_btn.configure(state="disabled", text="Injecting Data (Do not touch Excel)...")
        self.excel_status_lbl.configure(text="Connecting to Excel COM interface...", text_color=WARNING)
        
        def process():
            populator = ExcelPopulator(self.selected_excel_path)
            
            # Create output filename
            dir_name = os.path.dirname(self.selected_excel_path)
            base_name = os.path.basename(self.selected_excel_path)
            name, ext = os.path.splitext(base_name)
            out_path = os.path.join(dir_name, f"{name}_FILLED{ext}")
            
            success, msg = populator.populate(self.parsed_result["data"], out_path)
            
            if success:
                # Execute Smart CIN + FY Lock-in Algorithm & deduct credits
                cin_val = str(self.parsed_result["data"].get("cin", "UNLISTED")).strip()
                name_val = str(self.parsed_result["data"].get("company_name", "Client Company")).strip()
                fy_val = str(self.parsed_result["data"].get("financial_year", "2024-2025")).strip()
                
                credit_res = self.license_mgr.consume_credits(module="AOC4_EXCEL", cin=cin_val, fy=fy_val, company_name=name_val)
                credit_msg = credit_res.get("message", "Filing completed successfully!")
                
                self.after(0, lambda: self.excel_status_lbl.configure(text=f"{msg}\nSaved to: {out_path}", text_color=SUCCESS))
                self.after(0, lambda: messagebox.showinfo("SI Filings Pro — Success", f"{msg}\n\n{credit_msg}\n\nYou can now upload this file to the MCA portal!"))
                # Refresh UI header to reflect new credit balance
                self.after(500, self._show_main_screen)
            else:
                self.after(0, lambda: self.excel_status_lbl.configure(text="Auto-Fill Failed", text_color=DANGER))
                self.after(0, lambda: messagebox.showerror("Error", msg))
                
            self.after(0, lambda: self.run_excel_btn.configure(state="normal", text="⚡ Auto-Fill Excel Template"))

        threading.Thread(target=process, daemon=True).start()

    # ==========================================================
    # Tab 4: Chrome Extension & RPA Setup
    # ==========================================================

    def _build_extension_tab(self):
        """Build the automated Chrome RPA extension setup wizard."""
        tab = self.tab_extension

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=10)

        # Title & Status
        ctk.CTkLabel(
            scroll, text="⚡ MCA V3 Portal Chrome RPA Auto-Filler",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PRIMARY
        ).pack(anchor="w", pady=(5, 5))

        status_box = ctk.CTkFrame(scroll, fg_color=BG_CARD, border_width=1, border_color=BORDER)
        status_box.pack(fill="x", pady=10, ipady=8, padx=5)

        ctk.CTkLabel(
            status_box, text="● Local Loopback RPA Bridge Active & Listening @ http://127.0.0.1:8765",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=SUCCESS
        ).pack(pady=5)

        ctk.CTkLabel(
            status_box, text="Your hardware USB Digital Signature Certificates (DSC) remain 100% locally secure.",
            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED
        ).pack(pady=(0, 5))

        # 3-Step Setup Guide Card
        guide_box = ctk.CTkFrame(scroll, fg_color=BG_CARD, border_width=1, border_color=BORDER)
        guide_box.pack(fill="x", pady=15, ipady=12, padx=5)

        ctk.CTkLabel(
            guide_box, text="🚀 30-Second Quick Installation Guide (One-Time Setup):",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=TEXT_LIGHT
        ).pack(anchor="w", padx=20, pady=(10, 15))

        # Step 1
        s1_row = ctk.CTkFrame(guide_box, fg_color="transparent")
        s1_row.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(
            s1_row, text="1️⃣  Open Chrome Extension Manager:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left")

        def copy_ext_link():
            self.clipboard_clear()
            self.clipboard_append("chrome://extensions")
            messagebox.showinfo("Copied!", "✅ Link copied to clipboard!\n\nNow open Google Chrome, paste 'chrome://extensions' into the address bar, and hit Enter.")

        ctk.CTkButton(
            s1_row, text="📋 Copy 'chrome://extensions'",
            command=copy_ext_link, width=200, height=28,
            fg_color="#1e293b", border_width=1, border_color=PRIMARY, text_color=PRIMARY
        ).pack(side="right", padx=(10, 0))

        # Step 2
        ctk.CTkLabel(
            guide_box, text="2️⃣  Enable the \"Developer mode\" toggle switch at the top-right corner of Chrome.",
            font=ctk.CTkFont(size=13), text_color="#cbd5e1"
        ).pack(anchor="w", padx=20, pady=10)

        # Step 3
        s3_row = ctk.CTkFrame(guide_box, fg_color="transparent")
        s3_row.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(
            s3_row, text="3️⃣  Click \"Load unpacked\" in Chrome and select your bundled extension folder.",
            font=ctk.CTkFont(size=13), text_color="#cbd5e1"
        ).pack(side="left")

        def open_ext_folder():
            try:
                if getattr(sys, "frozen", False):
                    base_dir = os.path.dirname(sys.executable)
                    ext_path = os.path.join(base_dir, "chrome_extension")
                else:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    ext_path = os.path.join(base_dir, "mca-extension")

                if os.path.exists(ext_path):
                    os.startfile(ext_path)
                else:
                    os.startfile(base_dir)
                    messagebox.showinfo("Notice", f"Opening software folder: {base_dir}\nSelect the extension folder inside Chrome.")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder automatically: {e}")

        ctk.CTkButton(
            guide_box, text="📂 Open Chrome Extension Folder in Windows Explorer",
            command=open_ext_folder, width=380, height=38,
            fg_color=PRIMARY, text_color=BG_DARK, hover_color=PRIMARY_DARK,
            font=ctk.CTkFont(weight="bold", size=13)
        ).pack(pady=(15, 10))

        # Testing & Verification section
        test_box = ctk.CTkFrame(scroll, fg_color="#0e1320", border_width=1, border_color="#334155")
        test_box.pack(fill="x", pady=15, ipady=10, padx=5)

        ctk.CTkLabel(
            test_box, text="💡 How to Auto-Fill on MCA Portal:",
            font=ctk.CTkFont(size=13, weight="bold"), text_color=WARNING
        ).pack(anchor="w", padx=20, pady=(10, 5))

        ctk.CTkLabel(
            test_box, text="Once installed, simply approve financial data in the '✅ Verification' tab,\nthen open your MCA AOC-4 / MGT-7 web form in Chrome and click the SI Filings Pro toolbar icon!",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))

    # ==========================================================
    # Utilities
    # ==========================================================

    def _clear_container(self):
        """Remove all widgets from the main container."""
        for widget in self.container.winfo_children():
            widget.destroy()

    def _logout(self):
        """Clear license and show activation screen."""
        if messagebox.askyesno("Confirm Log Out", "Are you sure you want to log out of your SI Filings Pro firm account?"):
            self.license_mgr.clear_license()
            self._show_license_screen("You have been logged out.")


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    app = AOC4App()
    app.mainloop()
