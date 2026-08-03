"""
Neon PostgreSQL — Dedicated Cloud SaaS Database Engine for SI AOC-4 Pro
========================================================================
Provides direct, secure SSL connection to a dedicated Neon Cloud PostgreSQL database
for user authentication, license validation, and real-time filing audit logs.

Requirements: pip install psycopg2-binary
"""

import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

# Try importing psycopg2 for Postgres connectivity
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

# Default Neon connection string (can be configured in .env or settings.json)
DEFAULT_NEON_URI = os.environ.get(
    "SI_AOC4_DB_URL", 
    "" # Enter your dedicated Neon database connection string here
)

class NeonCloudDB:
    """Manages secure SaaS licensing and transaction logging via Neon PostgreSQL."""
    
    def __init__(self, connection_uri: str = DEFAULT_NEON_URI):
        self.connection_uri = connection_uri.strip()
        self._check_driver()

    def _check_driver(self):
        if psycopg2 is None and self.connection_uri:
            print("⚠️ PostgreSQL driver not installed. To connect to Neon DB, run: pip install psycopg2-binary")

    def get_connection(self):
        """Acquire a secure SSL PostgreSQL connection."""
        if not self.connection_uri or not psycopg2:
            return None
        try:
            return psycopg2.connect(self.connection_uri, cursor_factory=RealDictCursor)
        except Exception as e:
            print(f"[NeonDB Error] Failed to connect to database: {e}")
            return None

    def initialize_schema(self, conn_uri: Optional[str] = None) -> bool:
        """Create required SaaS database tables in Neon if they do not already exist."""
        if conn_uri:
            self.connection_uri = conn_uri.strip()
        
        conn = self.get_connection()
        if not conn:
            print("❌ Cannot initialize schema: No valid database connection string provided.")
            return False

        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS aoc4_license_accounts (
            id SERIAL PRIMARY KEY,
            customer_email VARCHAR(255) UNIQUE NOT NULL,
            license_key VARCHAR(100) UNIQUE NOT NULL,
            plan_name VARCHAR(50) DEFAULT 'Professional CA',
            filings_limit INT DEFAULT 50,  -- Use -1 for Unlimited plans
            filings_used INT DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_validated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS aoc4_usage_audit_log (
            id SERIAL PRIMARY KEY,
            customer_email VARCHAR(255),
            license_key VARCHAR(100),
            action_type VARCHAR(50),
            company_cin VARCHAR(50),
            company_name VARCHAR(255),
            client_timestamp VARCHAR(100),
            logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_aoc4_email_key ON aoc4_license_accounts(customer_email, license_key);
        CREATE INDEX IF NOT EXISTS idx_aoc4_cin ON aoc4_usage_audit_log(company_cin);
        """
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(create_tables_sql)
            conn.close()
            print("✅ Successfully initialized SI AOC-4 Pro Cloud SaaS Schema in Neon Database!")
            return True
        except Exception as e:
            print(f"❌ Database Schema Initialization Error: {e}")
            if conn:
                conn.close()
            return False

    def validate_license(self, email: str, license_key: str) -> Optional[Dict[str, Any]]:
        """Verify user credentials and check remaining filing usage limits."""
        conn = self.get_connection()
        if not conn:
            return None

        query = """
            UPDATE aoc4_license_accounts 
            SET last_validated = CURRENT_TIMESTAMP 
            WHERE LOWER(customer_email) = LOWER(%s) AND license_key = %s AND is_active = TRUE
            RETURNING customer_email, license_key, plan_name as plan, filings_limit as leads_limit, filings_used as leads_used;
        """
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, (email.strip(), license_key.strip()))
                    user = cur.fetchone()
            conn.close()
            if user:
                user["valid"] = True
                return dict(user)
            return None
        except Exception as e:
            print(f"[NeonDB] License verification query failed: {e}")
            if conn:
                conn.close()
            return None

    def record_filing_action(self, email: str, license_key: str, cin: str, company_name: str) -> bool:
        """Increment user usage counter and log audit record in real-time."""
        conn = self.get_connection()
        if not conn:
            return False

        update_usage_sql = """
            UPDATE aoc4_license_accounts 
            SET filings_used = filings_used + 1 
            WHERE license_key = %s AND (filings_limit = -1 OR filings_used < filings_limit);
        """
        log_audit_sql = """
            INSERT INTO aoc4_usage_audit_log (customer_email, license_key, action_type, company_cin, company_name, client_timestamp)
            VALUES (%s, %s, 'AOC4_EXCEL_GENERATED', %s, %s, %s);
        """
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(update_usage_sql, (license_key.strip(),))
                    cur.execute(log_audit_sql, (
                        email.strip(), 
                        license_key.strip(), 
                        cin.strip() or "N/A", 
                        company_name.strip() or "N/A", 
                        datetime.now(timezone.utc).isoformat()
                    ))
            conn.close()
            print(f"[NeonDB] Recorded filing usage for CIN: {cin or '[Blank]'} under {email}")
            return True
        except Exception as e:
            print(f"[NeonDB] Failed to record usage to cloud: {e}")
            if conn:
                conn.close()
            return False

    def seed_initial_test_account(self, email: str, license_key: str, plan: str = "CA Pro Unlimited", limit: int = -1) -> bool:
        """Create an initial test/demo customer account in the Neon Postgres database."""
        conn = self.get_connection()
        if not conn:
            return False
        sql = """
            INSERT INTO aoc4_license_accounts (customer_email, license_key, plan_name, filings_limit, filings_used)
            VALUES (%s, %s, %s, %s, 0)
            ON CONFLICT (license_key) DO UPDATE 
            SET plan_name = EXCLUDED.plan_name, filings_limit = EXCLUDED.filings_limit;
        """
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(sql, (email.strip().lower(), license_key.strip(), plan, limit))
            conn.close()
            print(f"✅ Seeded cloud test account for: {email} with key: {license_key}")
            return True
        except Exception as e:
            print(f"[NeonDB] Seed failed: {e}")
            if conn:
                conn.close()
            return False


# Singleton database instance
cloud_db = NeonCloudDB()

if __name__ == "__main__":
    import sys
    print("="*60)
    print("SI AOC-4 Pro — Neon PostgreSQL Database Initializer")
    print("="*60)
    
    uri = input("Enter your Neon PostgreSQL connection string: ").strip()
    if not uri:
        print("❌ No connection string entered. Exiting.")
        sys.exit(1)
        
    db = NeonCloudDB(uri)
    success = db.initialize_schema(uri)
    if success:
        print("\nLet's create your first authorized CA Admin / Test account!")
        email = input("Enter Admin Email [e.g. pnriyas50@gmail.com]: ").strip() or "pnriyas50@gmail.com"
        key = input("Enter License Key [e.g. SA-PRO-2026]: ").strip() or "SA-PRO-2026"
        db.seed_initial_test_account(email, key, plan="Enterprise CA Unlimited", limit=-1)
        print("\n🎉 Setup complete! Add this DB URL to your app configuration to start using it live.")
