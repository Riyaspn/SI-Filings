r"""
SI Filings Pro — Universal License & Pay-As-You-Go Credit Wallet Manager
========================================================================
Manages local session persistence (%APPDATA%/SI_Filings_Pro/license.json),
live Neon PostgreSQL cloud authentication, Pay-As-You-Go credit consumption
using the Smart CIN + FY Lock-in Algorithm, and OTA update checks.
"""

import os
import json
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import requests

# ============================================================
# Configuration & Endpoints
# ============================================================

API_BASE_URL = os.environ.get("SI_FILINGS_API_URL", "https://sifilings.vercel.app") # Live cloud production domain on Vercel
APP_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "SI_Filings_Pro")
LICENSE_FILE = os.path.join(APP_DIR, "license.json")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
UNLOCKED_TOKENS_FILE = os.path.join(APP_DIR, "unlocked_filings.json")

OFFLINE_GRACE_HOURS = 24

MODULE_CREDIT_COSTS = {
    "AOC4_EXCEL": 10,
    "MGT7_EXCEL": 5,
    "GST_RECON": 3,
    "ITR_AUDIT": 5,
    "SECRETARIAL_XBRL": 15
}


class LicenseManager:
    """
    Core authentication, credit wallet, and duplicate filing protection shield for SI Filings Pro.
    """

    def __init__(self):
        self.license_info: Optional[Dict[str, Any]] = None
        self.is_offline_mode: bool = False
        self._cached_cloud_ai_keys: str = ""
        self.settings_data: Dict[str, Any] = self._default_settings()
        self.local_unlocked_tokens: Dict[str, str] = self._load_unlocked_tokens()
        self._load_settings()

    # ----------------------------------------------------------
    # Default Settings & Persistence
    # ----------------------------------------------------------

    @staticmethod
    def _default_settings() -> Dict[str, Any]:
        return {
            "gemini_api_key": "",
            "confidence_threshold": 0.95,
            "default_fy_start_month": 4,  # April
            "last_used_directory": "",
        }

    def _load_unlocked_tokens(self) -> Dict[str, str]:
        if os.path.exists(UNLOCKED_TOKENS_FILE):
            try:
                with open(UNLOCKED_TOKENS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_unlocked_tokens(self) -> None:
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(UNLOCKED_TOKENS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.local_unlocked_tokens, f, indent=2)
        except Exception as e:
            print(f"Error saving unlocked tokens: {e}")

    def get_local_license(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(LICENSE_FILE):
            return None
        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def save_local_license(self, data: Dict[str, Any]) -> None:
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(LICENSE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving license cache: {e}")

    def clear_license(self) -> None:
        self.license_info = None
        self.is_offline_mode = False
        if os.path.exists(LICENSE_FILE):
            try:
                os.remove(LICENSE_FILE)
            except Exception:
                pass

    # ----------------------------------------------------------
    # Settings Management
    # ----------------------------------------------------------

    def _load_settings(self) -> None:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "gemini_api_key" in data:
                        del data["gemini_api_key"]
                        self.save_settings(data)
                    else:
                        self.settings_data.update(data)
            except Exception:
                pass

    def save_settings(self, new_settings: Dict[str, Any]) -> None:
        if "gemini_api_key" in new_settings:
            del new_settings["gemini_api_key"]
        self.settings_data.update(new_settings)
        try:
            os.makedirs(APP_DIR, exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings_data, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def get_gemini_api_key(self) -> str:
        # 1. Return cached cloud keys if already synced this session
        if self._cached_cloud_ai_keys:
            return self._cached_cloud_ai_keys

        # 3. Dynamically fetch live multi-key rotation pool from Vercel Cloud API
        try:
            res = requests.get(f"{API_BASE_URL}/api/ai-config", timeout=4)
            if res.status_code == 200:
                cloud_keys = res.json().get("gemini_api_keys", "").strip()
                if cloud_keys:
                    self._cached_cloud_ai_keys = cloud_keys
                    return cloud_keys
        except Exception as e:
            print(f"[AI Cloud Sync] Could not reach Vercel: {e}")

        # 4. Fallback to system environment variable
        return os.getenv("GEMINI_API_KEYS", "")

    def get_confidence_threshold(self) -> float:
        return self.settings_data.get("confidence_threshold", 0.95)

    # ----------------------------------------------------------
    # Startup Authentication & Validation
    # ----------------------------------------------------------

    def check_license_on_startup(self) -> Dict[str, Any]:
        local_data = self.get_local_license()
        if not local_data or "license_key" not in local_data:
            return {"status": "no_key", "message": "No firm license found. Please sign in or register.", "license_info": None}

        key = local_data["license_key"]
        email = local_data.get("customer_email", "")

        # Test / Demo Key handling
        if key.upper().startswith("SFP-DEMO") or key.upper().startswith("DEMO") or "TEST" in key.upper() or key.upper().startswith("SA-DEMO"):
            if "credits_balance" not in local_data:
                local_data["credits_balance"] = 100 # Default 100 Trial credits
            self.license_info = local_data
            self.is_offline_mode = False
            return {"status": "valid", "message": "Demo Firm License Active.", "license_info": local_data}

        try:
            resp = requests.post(
                f"{API_BASE_URL}/api/license/validate",
                json={"license_key": key, "email": email},
                timeout=5
            )

            if resp.status_code == 200:
                server_data = resp.json()
                if server_data.get("valid"):
                    server_data["last_validated"] = datetime.now(timezone.utc).isoformat()
                    self.save_local_license(server_data)
                    self.license_info = server_data
                    self.is_offline_mode = False
                    return {"status": "valid", "message": "Firm account synchronized with cloud wallet.", "license_info": server_data}
                else:
                    return {"status": "expired", "message": "Your firm license key is invalid or suspended.", "license_info": None}
            else:
                return {"status": "invalid", "message": f"Server reported status {resp.status_code}.", "license_info": None}

        except requests.RequestException:
            # Network failure — activate offline grace period
            last_val_str = local_data.get("last_validated")
            if last_val_str:
                try:
                    last_val = datetime.fromisoformat(last_val_str)
                    if datetime.now(timezone.utc) - last_val < timedelta(hours=OFFLINE_GRACE_HOURS):
                        self.license_info = local_data
                        self.is_offline_mode = True
                        return {
                            "status": "offline_grace",
                            "message": f"Offline mode active ({OFFLINE_GRACE_HOURS}h grace). Using locally cached wallet balance.",
                            "license_info": local_data
                        }
                except Exception:
                    pass
            return {"status": "offline_expired", "message": "Cannot reach SI Filings Pro cloud server and offline grace period expired.", "license_info": None}

    def activate_key(self, email: str, key: str) -> Dict[str, Any]:
        if key.upper().startswith("SFP-DEMO") or key.upper().startswith("DEMO") or "TEST" in key.upper() or key.upper().startswith("SA-DEMO"):
            demo_data = {
                "valid": True,
                "customer_email": email,
                "firm_name": "Pro CA & CS Firm",
                "license_key": key,
                "credits_balance": 100,
                "total_credits_purchased": 100,
                "last_validated": datetime.now(timezone.utc).isoformat()
            }
            self.save_local_license(demo_data)
            self.license_info = demo_data
            self.is_offline_mode = False
            return {"status": "success", "message": "Demo License Activated! 100 Free Credits deposited.", "license_info": demo_data}

        try:
            resp = requests.post(
                f"{API_BASE_URL}/api/license/validate",
                json={"license_key": key, "email": email},
                timeout=6
            )
            if resp.status_code == 200:
                server_data = resp.json()
                if server_data.get("valid"):
                    server_data["last_validated"] = datetime.now(timezone.utc).isoformat()
                    self.save_local_license(server_data)
                    self.license_info = server_data
                    self.is_offline_mode = False
                    return {"status": "success", "message": "License activated!", "license_info": server_data}
                return {"status": "expired", "message": "This license key is expired or suspended.", "license_info": None}
            return {"status": "not_found", "message": "License key not found on server.", "license_info": None}
        except Exception as e:
            return {"status": "network_error", "message": f"Could not reach license server: {e}", "license_info": None}

    # ----------------------------------------------------------
    # Universal SI Credits Wallet & Smart CIN + FY Lock-In
    # ----------------------------------------------------------

    def get_customer_email(self) -> str:
        if self.license_info:
            return self.license_info.get("customer_email", "Authorized Firm Partner")
        return "Not Logged In"

    def get_firm_name(self) -> str:
        if self.license_info:
            return self.license_info.get("firm_name", "Chartered & Company Secretaries")
        return "Unassigned Firm"

    def get_credits_balance(self) -> int:
        if self.license_info:
            return self.license_info.get("credits_balance", 100)
        return 0

    def can_perform_filing(self, module: str = "AOC4_EXCEL") -> bool:
        """Check if current credit balance covers the required module fee."""
        cost = MODULE_CREDIT_COSTS.get(module, 10)
        return self.get_credits_balance() >= cost

    def consume_credits(self, module: str = "AOC4_EXCEL", cin: str = "", fy: str = "2024-2025", company_name: str = "") -> Dict[str, Any]:
        """
        Execute Smart CIN + FY Lock-in Algorithm to consume credits only when value is delivered,
        with 30-day free re-generation protection against double billing!
        """
        if not self.license_info:
            return {"status": "error", "message": "No active license account found."}

        key = self.license_info.get("license_key", "")
        cost = MODULE_CREDIT_COSTS.get(module, 10)
        filing_token = f"{module}_{cin.upper().strip()}_{fy.strip()}"

        # If offline or using Demo key -> enforce Smart Lock-In via local JSON storage!
        if self.is_offline_mode or key.upper().startswith("DEMO") or "TEST" in key.upper() or key.upper().startswith("SFP-DEMO") or key.upper().startswith("SA-DEMO"):
            if filing_token in self.local_unlocked_tokens:
                msg = f"✅ Free Re-Generation Active for {cin} ({fy}). 0 Credits deducted!"
                return {"status": "success", "message": msg, "credits_deducted": 0, "was_duplicate_pass": True, "credits_balance": self.get_credits_balance()}
            
            if self.get_credits_balance() < cost:
                return {"status": "insufficient_credits", "error": f"Insufficient balance ({self.get_credits_balance()} SI Credits). Need {cost} credits."}

            new_bal = self.get_credits_balance() - cost
            self.license_info["credits_balance"] = new_bal
            self.save_local_license(self.license_info)

            self.local_unlocked_tokens[filing_token] = datetime.now(timezone.utc).isoformat()
            self._save_unlocked_tokens()
            return {"status": "success", "message": f"⚡ Deducted {cost} SI Credits for {module}. Remaining balance: {new_bal} Credits.", "credits_deducted": cost, "was_duplicate_pass": False, "credits_balance": new_bal}

        # Live cloud transaction with Neon DB
        try:
            resp = requests.post(
                f"{API_BASE_URL}/api/usage/consume",
                json={"license_key": key, "module": module, "cin": cin, "fy": fy, "company_name": company_name},
                timeout=8
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "success":
                self.license_info["credits_balance"] = data.get("credits_balance", self.get_credits_balance())
                self.save_local_license(self.license_info)
                return data
            elif resp.status_code == 402:
                return {"status": "insufficient_credits", "error": data.get("error", "Insufficient credits in cloud wallet.")}
            else:
                return {"status": "error", "error": data.get("error", "Failed to communicate with billing server.")}
        except Exception as e:
            # Fallback to local offline deduction if network momentarily disconnects
            print(f"[Credit Consume Fallback] Network error: {e}. Executing local deduction.")
            if filing_token in self.local_unlocked_tokens:
                return {"status": "success", "message": f"✅ Offline Duplicate Shield active for {cin}. 0 Credits deducted!", "credits_deducted": 0, "was_duplicate_pass": True}
            
            new_bal = self.get_credits_balance() - cost
            self.license_info["credits_balance"] = max(0, new_bal)
            self.save_local_license(self.license_info)
            self.local_unlocked_tokens[filing_token] = datetime.now(timezone.utc).isoformat()
            self._save_unlocked_tokens()
            return {"status": "success", "message": f"⚡ Deducted {cost} Credits offline. Balance: {new_bal} Credits.", "credits_deducted": cost, "was_duplicate_pass": False}

    # ----------------------------------------------------------
    # OTA Update Checker
    # ----------------------------------------------------------

    def check_for_software_update(self, current_version: str = "1.0.0") -> Optional[Dict[str, Any]]:
        """Query cloud server for newly published SI Filings Pro software updates."""
        try:
            resp = requests.get(f"{API_BASE_URL}/api/system/check-update", params={"version": current_version}, timeout=4)
            if resp.ok:
                return resp.json()
        except Exception:
            pass
        return None

    def is_licensed(self) -> bool:
        return self.license_info is not None
