"""
SI Filings Pro — Universal Cloud Database Schema for Neon PostgreSQL
=====================================================================
Defines SQLAlchemy ORM tables for managing customer accounts, Pay-As-You-Go credit wallets,
payment recharge order audit trails, and modular compliance usage logs.
"""

from datetime import datetime, timedelta, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class FirmAccount(db.Model):
    """
    Stores authorized customer firm profiles and their Pay-As-You-Go credit balance.
    Source of truth for desktop license key authentication and token preservation.
    """
    __tablename__ = "firm_accounts"

    id = db.Column(db.Integer, primary_key=True)
    customer_email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    firm_name = db.Column(db.String(255), default="Chartered & Company Secretaries")
    license_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    credits_balance = db.Column(db.Integer, default=100, nullable=False) # Default 100 Trial Credits (10 AOC-4 Filings)
    total_credits_purchased = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_validated = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "customer_email": self.customer_email,
            "firm_name": self.firm_name,
            "license_key": self.license_key,
            "credits_balance": self.credits_balance,
            "total_credits_purchased": self.total_credits_purchased,
            "is_active": self.is_active,
            "valid": self.is_active and self.credits_balance > 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PaymentTransaction(db.Model):
    """
    Tracks customer recharge transactions via PhonePe PG and Direct Business UPI.
    Lifecycle: PENDING ➔ PAID / FAILED.
    """
    __tablename__ = "payment_transactions"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    customer_email = db.Column(db.String(255), nullable=False, index=True)
    package_key = db.Column(db.String(50), nullable=False)  # 'starter', 'pro', 'enterprise'
    credits_added = db.Column(db.Integer, nullable=False)
    amount_inr = db.Column(db.Numeric(10, 2), nullable=False)
    payment_mode = db.Column(db.String(50), default="PHONEPE_PG") # 'PHONEPE_PG' or 'UPI_DIRECT'
    pg_reference = db.Column(db.String(150), default="")
    status = db.Column(db.String(20), default="PENDING")    # 'PENDING', 'PAID', 'FAILED'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "customer_email": self.customer_email,
            "package_key": self.package_key,
            "credits_added": self.credits_added,
            "amount_inr": float(self.amount_inr),
            "payment_mode": self.payment_mode,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ModuleUsageAudit(db.Model):
    """
    Compliance audit trail recording every completed filing across all modules.
    Powers the Smart CIN + Financial Year Lock-in Algorithm (no double charging within 30 days).
    """
    __tablename__ = "module_usage_audit"

    id = db.Column(db.Integer, primary_key=True)
    customer_email = db.Column(db.String(255), nullable=False, index=True)
    license_key = db.Column(db.String(100), nullable=False, index=True)
    module_type = db.Column(db.String(50), nullable=False) # e.g. 'AOC4_EXCEL', 'MGT7_EXCEL'
    company_cin = db.Column(db.String(50), nullable=False, index=True)
    financial_year = db.Column(db.String(30), nullable=False, index=True) # e.g. '2024-2025'
    filing_token = db.Column(db.String(150), nullable=False, index=True)  # e.g. 'AOC4_EXCEL_U74999KL2021PTC068310_2024-2025'
    company_name = db.Column(db.String(255), default="Unknown Company")
    credits_deducted = db.Column(db.Integer, nullable=False, default=0)   # 0 if duplicate within 30 days, else module cost
    was_duplicate_pass = db.Column(db.Boolean, default=False)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "module_type": self.module_type,
            "company_cin": self.company_cin,
            "financial_year": self.financial_year,
            "filing_token": self.filing_token,
            "company_name": self.company_name,
            "credits_deducted": self.credits_deducted,
            "was_duplicate_pass": self.was_duplicate_pass,
            "logged_at": self.logged_at.isoformat() if self.logged_at else None,
        }
