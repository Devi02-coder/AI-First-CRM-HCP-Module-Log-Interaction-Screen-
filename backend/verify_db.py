"""
Database connectivity and table verification script.
Run this to confirm MySQL connection and all 11 tables exist.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pymysql
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "2003"
DB_NAME = "hcp_crm"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

REQUIRED_TABLES = [
    "users",
    "hcp_profiles",
    "interactions",
    "interaction_products",
    "interaction_materials",
    "interaction_edits",
    "follow_up_tasks",
    "agent_memory",
    "chat_messages",
    "tool_execution_logs",
    "audit_logs",
]

def check_raw_pymysql_connection():
    print("\n=== Step 1: Raw PyMySQL Connection Test ===")
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, port=DB_PORT)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"  [OK] Connected to MySQL Server. Version: {version[0]}")

        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"  [OK] Database '{DB_NAME}' ensured to exist.")
        conn.close()
        return True
    except Exception as e:
        print(f"  [FAIL] PyMySQL connection failed: {e}")
        return False

def check_sqlalchemy_connection():
    print("\n=== Step 2: SQLAlchemy Engine Connection Test ===")
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"  [OK] SQLAlchemy engine connected. Test query result: {result.scalar()}")
        return engine
    except Exception as e:
        print(f"  [FAIL] SQLAlchemy connection failed: {e}")
        return None

def check_and_create_tables(engine):
    print("\n=== Step 3: Table Creation via SQLAlchemy Models ===")
    try:
        # Import models to trigger table creation
        from app.database import Base
        from app.models import (
            User, HCPProfile, Interaction, InteractionProduct, 
            InteractionMaterial, InteractionEdit, FollowUpTask,
            AgentMemory, ChatMessage, ToolExecutionLog, AuditLog
        )
        Base.metadata.create_all(bind=engine)
        print("  [OK] All tables created/verified via SQLAlchemy models.")
        return True
    except Exception as e:
        print(f"  [FAIL] Table creation failed: {e}")
        import traceback; traceback.print_exc()
        return False

def verify_tables_exist(engine):
    print("\n=== Step 4: Verifying All 11 Required Tables ===")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    all_ok = True
    for table in REQUIRED_TABLES:
        if table in existing_tables:
            print(f"  [OK] Table '{table}' exists.")
        else:
            print(f"  [MISSING] Table '{table}' NOT FOUND!")
            all_ok = False
    return all_ok

def check_seeded_data(engine):
    print("\n=== Step 5: Checking Seeded Data ===")
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        result = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"  Users: {result} records")
        result = db.execute(text("SELECT COUNT(*) FROM hcp_profiles")).scalar()
        print(f"  HCP Profiles: {result} records")
        result = db.execute(text("SELECT COUNT(*) FROM interactions")).scalar()
        print(f"  Interactions: {result} records")
        result = db.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar()
        print(f"  Audit Logs: {result} records")
    except Exception as e:
        print(f"  [WARN] Could not count records: {e}")
    finally:
        db.close()

def show_table_schemas(engine):
    print("\n=== Step 6: Table Schema Summary ===")
    inspector = inspect(engine)
    for table in REQUIRED_TABLES:
        if table in inspector.get_table_names():
            cols = inspector.get_columns(table)
            col_names = [c['name'] for c in cols]
            print(f"  {table}: {col_names}")

if __name__ == "__main__":
    print("=" * 60)
    print("  HCP CRM Database Verification Report")
    print(f"  Target: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print("=" * 60)

    raw_ok = check_raw_pymysql_connection()
    if not raw_ok:
        sys.exit(1)

    engine = check_sqlalchemy_connection()
    if not engine:
        sys.exit(1)

    tables_created = check_and_create_tables(engine)
    tables_verified = verify_tables_exist(engine)
    check_seeded_data(engine)
    show_table_schemas(engine)

    print("\n" + "=" * 60)
    if tables_created and tables_verified:
        print("  DATABASE VERIFICATION: ALL CHECKS PASSED!")
    else:
        print("  DATABASE VERIFICATION: SOME CHECKS FAILED!")
    print("=" * 60)
