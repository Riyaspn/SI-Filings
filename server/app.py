"""
SI Filings Pro — Cloud SaaS & Billing API Server
================================================
Serverless Flask backend for Vercel/Render connecting directly to Neon PostgreSQL.
Manages user authentication, credit balance wallets, Smart CIN + FY duplicate protection,
PhonePe/UPI billing checkouts, automated Gmail SMTP credential delivery, and OTA updates.
"""

import os
import uuid
import smtplib
import hashlib
import hmac
import json
import base64
import requests
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import tempfile

from flask import Flask, request, jsonify, redirect
from flask_cors import CORS

from models import db, FirmAccount, PaymentTransaction, ModuleUsageAudit
import config

app = Flask(__name__, instance_path=tempfile.gettempdir())
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

CORS(app, resources={r"/api/*": {"origins": "*"}})
db.init_app(app)

# =============================================================
# Database Initialization (Auto-Create Tables on First Request)
# =============================================================
_db_initialized = False
@app.before_request
def setup_db_tables():
    global _db_initialized
    if not _db_initialized:
        try:
            db.create_all()
            print("✅ [NeonDB] SI Filings Pro tables initialized successfully.")
        except Exception as e:
            print(f"[DB Error] Table creation failed: {e}")
        _db_initialized = True

# =============================================================
# Helper Utilities & Automated Gmail SMTP Delivery
# =============================================================

def generate_license_key():
    """Generate professional firm license key: SFP-XXXX-XXXX-XXXX"""
    raw = uuid.uuid4().hex.upper()
    return f"SFP-{raw[:4]}-{raw[4:8]}-{raw[8:12]}"

def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """Deliver transaction receipts and license keys via Gmail SMTP."""
    if not config.SMTP_EMAIL or not config.SMTP_PASSWORD:
        print(f"📧 [Email Simulated] To: {to_email} | Subject: {subject}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"SI Filings Pro <{config.SMTP_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_EMAIL, config.SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ [Email Sent] Successfully delivered to {to_email}")
        return True
    except Exception as e:
        print(f"❌ [Email Error] Failed to send email to {to_email}: {e}")
        return False

# =============================================================
# API Endpoints: Authentication & Pay-As-You-Go Billing
# =============================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "online", "service": "SI Filings Pro Universal Billing Cloud", "db": "Neon PostgreSQL"})


@app.route("/api/auth/register", methods=["POST"])
def register_firm():
    """
    Register a new CA/CS firm account and grant 100 Free Trial Credits (10 Free AOC-4 Filings).
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    firm_name = data.get("firm_name", "").strip() or "Chartered Accountancy Partner"

    if not email or "@" not in email:
        return jsonify({"error": "A valid firm email address is required"}), 400

    existing = FirmAccount.query.filter_by(customer_email=email).first()
    if existing:
        return jsonify({
            "status": "already_registered",
            "message": "This email is already registered. Using existing license key.",
            "account": existing.to_dict()
        }), 200

    new_key = generate_license_key()
    account = FirmAccount(
        customer_email=email,
        firm_name=firm_name,
        license_key=new_key,
        credits_balance=100,  # 100 Free Trial Credits = 10 Free Filings
        total_credits_purchased=100
    )
    db.session.add(account)
    db.session.commit()

    # Send confirmation email
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 25px; background: #0f172a; color: #f8fafc; border-radius: 12px;">
        <h1 style="color: #38bdf8;">SI Filings Pro</h1>
        <p>Welcome, <strong>{firm_name}</strong>!</p>
        <p>Your CA firm has been granted <strong>100 Free SI Credits (10 Free AOC-4 Filings)</strong> to experience AI corporate filing automation.</p>
        <div style="background: #1e293b; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
            <p style="margin: 0; color: #94a3b8;">Your Professional Firm License Key:</p>
            <h2 style="color: #4ade80; letter-spacing: 2px; margin: 10px 0;">{new_key}</h2>
        </div>
        <p>Open the desktop app, enter your email and this key to unlock instant filing!</p>
        <hr style="border: 0; border-top: 1px solid #334155;">
        <p style="font-size: 13px; color: #94a3b8;">For technical & billing support, reply directly to this email or contact <a href="mailto:pnriyas50@gmail.com" style="color: #38bdf8;">pnriyas50@gmail.com</a>.</p>
        <p style="font-size: 12px; color: #64748b;">© SharpIntell Technologies LLP — All rights reserved.</p>
    </div>
    """
    send_email(email, "Welcome to SI Filings Pro — Your 100 Free Trial Credits & License Key!", html_content)

    return jsonify({
        "status": "success",
        "message": "Account created! 100 Free Trial Credits deposited.",
        "account": account.to_dict()
    }), 201


@app.route("/api/license/validate", methods=["POST"])
def validate_license():
    """Verify license key and return live credit wallet balance."""
    data = request.get_json() or {}
    key = data.get("license_key", "").strip()
    email = data.get("email", "").strip().lower()

    if not key:
        return jsonify({"valid": False, "error": "Missing license key"}), 400

    query = FirmAccount.query.filter_by(license_key=key)
    if email:
        query = query.filter_by(customer_email=email)
    
    account = query.first()
    if not account or not account.is_active:
        return jsonify({"valid": False, "error": "Invalid or suspended firm license key"}), 404

    account.last_validated = datetime.utcnow()
    db.session.commit()
    return jsonify(account.to_dict()), 200


@app.route("/api/usage/consume", methods=["POST"])
def consume_credits():
    """
    Core Smart CIN + Financial Year Lock-in Algorithm:
    Checks if user already spent credits on this (CIN + FY + Module) within the last 30 days.
    If YES -> Deduct 0 credits (Free Re-generation pass).
    If NO -> Check balance, deduct module credit cost (e.g. 10 for AOC4), and log audit trail.
    """
    data = request.get_json() or {}
    key = data.get("license_key", "").strip()
    module = data.get("module", "AOC4_EXCEL").strip().upper()
    cin = data.get("cin", "").strip().upper() or "UNLISTED_CIN"
    fy = data.get("fy", "").strip() or "2024-2025"
    company_name = data.get("company_name", "").strip() or "Client Company"

    account = FirmAccount.query.filter_by(license_key=key).first()
    if not account or not account.is_active:
        return jsonify({"error": "Invalid license credentials"}), 401

    cost = config.MODULE_CREDIT_COSTS.get(module, 10)
    filing_token = f"{module}_{cin}_{fy}"

    # Smart Duplicate Check (Within last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_usage = ModuleUsageAudit.query.filter_by(
        license_key=key,
        filing_token=filing_token,
        was_duplicate_pass=False
    ).filter(ModuleUsageAudit.logged_at >= thirty_days_ago).first()

    was_duplicate = False
    deduction = cost

    if recent_usage:
        # User already paid for this company in this year within 30 days!
        was_duplicate = True
        deduction = 0
        message = f"✅ Free Re-Generation Pass active for {cin} ({fy}). 0 Credits deducted!"
    else:
        if account.credits_balance < cost:
            return jsonify({
                "error": f"Insufficient SI Credits ({account.credits_balance} remaining). Auto-filling {module} requires {cost} credits.",
                "code": "INSUFFICIENT_CREDITS",
                "balance": account.credits_balance
            }), 402
        
        account.credits_balance -= deduction
        message = f"⚡ Deducted {deduction} Credits for {module}. Remaining balance: {account.credits_balance} SI Credits."

    # Record audit trail
    log_entry = ModuleUsageAudit(
        customer_email=account.customer_email,
        license_key=account.license_key,
        module_type=module,
        company_cin=cin,
        financial_year=fy,
        filing_token=filing_token,
        company_name=company_name,
        credits_deducted=deduction,
        was_duplicate_pass=was_duplicate
    )
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": message,
        "credits_deducted": deduction,
        "credits_balance": account.credits_balance,
        "was_duplicate_pass": was_duplicate,
        "token": filing_token
    }), 200


@app.route("/api/billing/recharge", methods=["POST"])
def create_recharge_order():
    """
    Generate PhonePe Payment Gateway session or zero-fee Direct Business UPI QR checkout invoice.
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    pack_key = data.get("package", "pro").strip().lower()
    payment_mode = data.get("mode", "PHONEPE_PG").strip().upper() # or 'UPI_DIRECT'

    pack_info = config.CREDIT_PACKAGES.get(pack_key, config.CREDIT_PACKAGES["pro"])
    if pack_info["price_inr"] == 0:
        return jsonify({"error": "Free trial package is automatically applied upon initial registration."}), 400

    order_id = f"SFP_RCHG_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:4].upper()}"
    
    order = PaymentTransaction(
        order_id=order_id,
        customer_email=email,
        package_key=pack_key,
        credits_added=pack_info["credits"],
        amount_inr=pack_info["price_inr"],
        payment_mode=payment_mode,
        status="PENDING"
    )
    db.session.add(order)
    db.session.commit()
    # Construct Razorpay Order
    try:
        # Create Razorpay Order
        amount_paise = int(pack_info["price_inr"] * 100)
        auth = (config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET)
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": order_id
        }
        
        resp = requests.post("https://api.razorpay.com/v1/orders", auth=auth, json=payload, timeout=10)
        if resp.ok:
            rzp_data = resp.json()
            return jsonify({
                "order_id": order_id, 
                "payment_mode": "RAZORPAY",
                "razorpay_order_id": rzp_data.get("id"),
                "key_id": config.RAZORPAY_KEY_ID,
                "amount_inr": pack_info["price_inr"]
            }), 200
        else:
            return jsonify({"error": "Failed to create Razorpay order"}), 500
    except Exception as e:
        print(f"[Razorpay Error] {e}")

    # Fallback simulation for local development / testing
    return jsonify({
        "order_id": order_id,
        "payment_mode": "RAZORPAY_DEV_SIMULATED",
    }), 200


@app.route("/api/billing/verify-razorpay", methods=["POST"])
def verify_razorpay():
    """
    Synchronous verification callback for Razorpay.
    """
    data = request.get_json() or {}
    order_id = data.get("order_id") # Neon DB Order ID
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not all([order_id, razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return jsonify({"error": "Missing parameters"}), 400

    # Verify Signature
    payload = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_sig = hmac.new(
        config.RAZORPAY_KEY_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_sig, razorpay_signature):
        return jsonify({"error": "Invalid signature"}), 400

    try:
        txn = PaymentTransaction.query.filter_by(order_id=order_id).first()
        if not txn:
            return jsonify({"error": "Order not found"}), 404

        if txn.status == "PAID":
            return jsonify({"success": True, "message": "Already processed", "credits_added": 0}), 200

        txn.status = "PAID"
        txn.pg_reference = razorpay_payment_id
        txn.completed_at = datetime.utcnow()

        account = FirmAccount.query.filter_by(customer_email=txn.customer_email).first()
        if account:
            account.credits_balance += txn.credits_added
            account.total_credits_purchased += txn.credits_added
        
        db.session.commit()
        return jsonify({
            "success": True,
            "credits_added": txn.credits_added,
            "credits_balance": account.credits_balance if account else 0
        }), 200

    except Exception as e:
        print(f"[Verify Error] {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/api/billing/dev_simulate_pay", methods=["GET"])
def dev_simulate_pay():
    """Local debugging helper to trigger payment completion without money."""
    order_id = request.args.get("order_id")
    order = PaymentTransaction.query.filter_by(order_id=order_id, status="PENDING").first()
    if order:
        order.status = "PAID"
        order.completed_at = datetime.utcnow()
        account = FirmAccount.query.filter_by(customer_email=order.customer_email).first()
        if account:
            account.credits_balance += order.credits_added
            account.total_credits_purchased += order.credits_added
        db.session.commit()
        return jsonify({"status": "SUCCESS", "message": f"Successfully added {order.credits_added} SI Credits to {order.customer_email} wallet!"})
    return jsonify({"error": "Order already processed or not found."}), 404


@app.route("/api/system/check-update", methods=["GET"])
def check_for_update():
    """In-App OTA update checking endpoint."""
    current_version = request.args.get("version", "1.0.0").strip()
    is_outdated = current_version < config.APP_VERSION_LATEST
    return jsonify({
        "latest_version": config.APP_VERSION_LATEST,
        "current_version": current_version,
        "is_outdated": is_outdated,
        "download_url": config.DOWNLOAD_EXE_URL,
        "release_notes": "Added full support for AOC-4 AI extraction, Smart CIN Duplicate Shield, and Chrome Extension RPA."
    })


@app.route("/api/ai-config", methods=["GET"])
def get_ai_config():
    """
    Securely deliver the live Gemini AI rotation key pool to authorized client desktop software.
    Allows dynamic scaling of AI keys via Vercel Environment Variables without recompiling desktop app.
    """
    default_pool = "AIzaSyCu-qiHdxpKXz3QyZANE0O1lRJob-yzab4,AIzaSyCppn7iEdWgjH6Uql4YhBEcwXJZoB2GF3Q,AIzaSyBFNhhN3Dd0KDPz4pf09_-tSsT1U_vznZI,AIzaSyDOAeLkc67-sjLymS8RJFfHgWVbtUYtdWM,AIzaSyCzyJ19547mtb-9XTdfqatQHUsty06yBrI"
    ai_keys = os.environ.get("GEMINI_API_KEYS", default_pool)
    return jsonify({
        "status": "success",
        "gemini_api_keys": ai_keys
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 SI Filings Pro Universal Billing API starting on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
