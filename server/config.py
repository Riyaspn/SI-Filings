"""
SI Filings Pro — Cloud SaaS & Billing Server Configuration
==========================================================
Manages environment connections (Neon PostgreSQL, PhonePe, UPI QR, Gmail SMTP)
and canonical definitions for universal SI Credits packages and filing module pricing.
"""

import os

# --- Neon Cloud PostgreSQL Database ---
# Replace with your dedicated SI Filings Pro Neon DB connection string in production
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///sifilings_dev.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# --- App & Security Settings ---
SECRET_KEY = os.environ.get("SECRET_KEY", "sifilings-enterprise-secret-key-prod-2026")
APP_VERSION_LATEST = "1.1.0"
DOWNLOAD_EXE_URL = os.environ.get("DOWNLOAD_EXE_URL", "https://si-filings.pages.dev/#download-section")

# --- Razorpay Payment Gateway Credentials ---
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_YourTestKeyId")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "YourTestKeySecret")

# --- Direct Business UPI Intent / QR Billing ---
UPI_MERCHANT_VPA = os.environ.get("UPI_MERCHANT_VPA", "sharpintell@upi")
UPI_MERCHANT_NAME = "SI Filings Pro"

# --- Gmail SMTP via Google App Password ---
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "pnriyas50@gmail.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "") # Set your Google App Password here
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# --- Module Consumption Cost Mapping (in SI Credits) ---
MODULE_CREDIT_COSTS = {
    "AOC4_EXCEL": 10,   # Financial Statement AI Auto-Fill (~₹100 value)
    "MGT7_EXCEL": 5,    # Annual Return Automation (~₹50 value)
    "GST_RECON": 3,     # Monthly GST Reconciliation & Return (~₹30 value)
    "ITR_AUDIT": 5,     # ITR Computation & Upload Automation (~₹50 value)
    "SECRETARIAL_XBRL": 15 # Secretarial Audit & XBRL Validator (~₹150 value)
}

# --- Recharge Packages (SI Credits) ---
CREDIT_PACKAGES = {
    "trial": {
        "name": "Welcome Trial (10 Free Filings)",
        "credits": 100,
        "price_inr": 0,
        "description": "100 Free SI Credits on registration — 10 AOC-4 filings totally free!"
    },
    "starter": {
        "name": "Starter Recharge (250 Credits)",
        "credits": 250,
        "price_inr": 2499,
        "description": "250 SI Credits — ~₹10.00 / credit. Ideal for solo CAs & CSs."
    },
    "pro": {
        "name": "Professional CA Bundle (800 Credits)",
        "credits": 800,
        "price_inr": 5999,
        "description": "800 SI Credits — 25% Bonus Discount (~₹7.50 / credit). Most Popular!"
    },
    "enterprise": {
        "name": "Enterprise Firm Vault (2500 Credits)",
        "credits": 2500,
        "price_inr": 14999,
        "description": "2500 SI Credits — 40% Bonus Discount (~₹6.00 / credit). Maximum volume ROI!"
    }
}
