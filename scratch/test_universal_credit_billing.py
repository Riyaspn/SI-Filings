"""
SI Filings Pro — Automated Verification Test Suite
==================================================
Verifies Universal Pay-As-You-Go Credit metering, 100 Free Trial Credit registration,
Smart CIN + FY Duplicate Filing Shield, and PhonePe / Direct Business UPI recharge workflows.

Run with: python -m pytest scratch/test_universal_credit_billing.py -v
or simply: python scratch/test_universal_credit_billing.py
"""

import sys
import os

# Add root directory to path to import server and models
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
server_dir = os.path.join(root_dir, "server")
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

from app import app, db
from models import FirmAccount, PaymentTransaction, ModuleUsageAudit
import config

def run_all_tests():
    print("=" * 70)
    print("⚡ Starting SI Filings Pro Cloud Architecture & Billing Test Suite")
    print("=" * 70)

    # Configure app for testing in temporary SQLite memory db
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    client = app.test_client()

    with app.app_context():
        db.create_all()

        # --------------------------------------------------------
        # TEST 1: Registration with 100 Free Trial Credits
        # --------------------------------------------------------
        print("\n[TEST 1] Registering firm account & verifying 100 Free Trial Credits...")
        res = client.post("/api/auth/register", json={
            "email": "riyas@sharpintell.com",
            "firm_name": "Riyas & Associates CAs"
        })
        assert res.status_code in (200, 201), f"Unexpected status code: {res.status_code}"
        data = res.get_json()
        account_data = data.get("account", {})
        license_key = account_data.get("license_key", "")
        
        assert license_key.startswith("SFP-"), f"Invalid key format: {license_key}"
        assert account_data["credits_balance"] == 100, f"Expected 100 credits, got {account_data['credits_balance']}"
        print(f"✅ Registration successful! Key issued: {license_key} | Wallet Balance: 100 SI Credits (10 Free Filings)")

        # --------------------------------------------------------
        # TEST 2: First-time Filing Execution (Deducts 10 Credits)
        # --------------------------------------------------------
        print("\n[TEST 2] Executing AOC-4 Filing for new company (U74999KL2021PTC068310 / FY 2024-25)...")
        res_consume1 = client.post("/api/usage/consume", json={
            "license_key": license_key,
            "module": "AOC4_EXCEL",
            "cin": "U74999KL2021PTC068310",
            "fy": "2024-2025",
            "company_name": "Techfiling Private Limited"
        })
        assert res_consume1.status_code == 200, f"Consume failed: {res_consume1.get_json()}"
        data1 = res_consume1.get_json()
        assert data1["credits_deducted"] == 10, "Expected 10 credits deducted"
        assert data1["credits_balance"] == 90, f"Expected 90 balance, got {data1['credits_balance']}"
        assert data1["was_duplicate_pass"] is False, "Should not be marked duplicate on initial run"
        print(f"✅ First filing consumed 10 credits! Remaining balance: 90 SI Credits.")

        # --------------------------------------------------------
        # TEST 3: Smart CIN + FY Lock-in Duplicate Shield
        # --------------------------------------------------------
        print("\n[TEST 3] Testing Smart Duplicate Shield (Re-generating exact same CIN & FY)...")
        res_consume2 = client.post("/api/usage/consume", json={
            "license_key": license_key,
            "module": "AOC4_EXCEL",
            "cin": "U74999KL2021PTC068310",
            "fy": "2024-2025",
            "company_name": "Techfiling Private Limited (Edited)"
        })
        assert res_consume2.status_code == 200
        data2 = res_consume2.get_json()
        assert data2["credits_deducted"] == 0, f"Expected 0 deduction, got {data2['credits_deducted']}"
        assert data2["credits_balance"] == 90, "Balance must remain unchanged at 90"
        assert data2["was_duplicate_pass"] is True, "Must be marked as duplicate pass!"
        print(f"✅ Duplicate Shield triggered successfully! Message returned:\n   >> '{data2['message']}'")
        print("✅ Balance remains 90 SI Credits. Zero extra billing incurred by CA partner!")

        # --------------------------------------------------------
        # TEST 4: Zero-Fee Direct Business UPI QR Recharge Invoice
        # --------------------------------------------------------
        print("\n[TEST 4] Requesting Direct Business UPI recharge order (Professional CA Bundle - 800 Credits)...")
        res_recharge_upi = client.post("/api/billing/recharge", json={
            "email": "riyas@sharpintell.com",
            "package": "pro",
            "mode": "UPI_DIRECT"
        })
        assert res_recharge_upi.status_code == 200
        data_upi = res_recharge_upi.get_json()
        assert data_upi["payment_mode"] == "UPI_DIRECT"
        assert "upi://pay" in data_upi["upi_intent"], f"Invalid UPI Intent: {data_upi.get('upi_intent')}"
        print(f"✅ Direct Business UPI invoice generated! Zero PG fee VPA URL:\n   >> {data_upi['upi_intent']}")

        # --------------------------------------------------------
        # TEST 5: PhonePe Payment Gateway & Simulated Webhook Top-up
        # --------------------------------------------------------
        print("\n[TEST 5] Requesting PhonePe Payment Gateway recharge & simulating payment completion...")
        res_recharge_pg = client.post("/api/billing/recharge", json={
            "email": "riyas@sharpintell.com",
            "package": "enterprise",
            "mode": "PHONEPE_PG"
        })
        assert res_recharge_pg.status_code == 200
        pg_data = res_recharge_pg.get_json()
        order_id = pg_data["order_id"]
        print(f"✅ Order {order_id} generated. Simulating bank payment receipt...")

        res_sim = client.get(f"/api/billing/dev_simulate_pay?order_id={order_id}")
        assert res_sim.status_code == 200, "Payment simulation failed"
        print(f"✅ Payment completed! Server message: {res_sim.get_json()['message']}")

        # Validate final wallet balance (90 remaining + 2500 enterprise recharge = 2590)
        res_val = client.post("/api/license/validate", json={"license_key": license_key})
        assert res_val.status_code == 200
        final_acc = res_val.get_json()
        assert final_acc["credits_balance"] == 2590, f"Expected 2590 final balance, got {final_acc['credits_balance']}"
        print(f"🎉 All tests passed with 100% success! Final Wallet Balance: {final_acc['credits_balance']} SI Credits.")
        print("=" * 70)
        print("🏆 SI FILINGS PRO ARCHITECTURE READY FOR PRODUCTION DEPLOYMENT!")
        print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
