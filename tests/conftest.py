"""Shared test fixtures — in-memory SQLite database with schema."""

import sys
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture()
def test_engine():
    """Create an in-memory SQLite engine with the full schema loaded."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    schema_path = PROJECT_ROOT / "database" / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    with engine.connect() as conn:
        for stmt in schema_sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()

    return engine


@pytest.fixture()
def db(test_engine, monkeypatch):
    """Patch db_manager to use the in-memory test engine."""
    import database.db_manager as dbm
    monkeypatch.setattr(dbm, "_engine", test_engine)
    monkeypatch.setattr(dbm, "get_engine", lambda: test_engine)
    return test_engine


@pytest.fixture()
def seeded_db(db):
    """DB with minimal seed data for all modules."""
    today = date.today()
    period = f"{today.year}-{today.month:02d}"
    prev_period = f"{today.year}-{today.month - 1:02d}" if today.month > 1 else f"{today.year - 1}-12"

    from database.db_manager import insert_df, execute_sql

    # Dimensions
    insert_df(pd.DataFrame([
        {"product_id": 1, "name": "Producto A", "category": "Cat1", "product_line": "Line1",
         "brand": "Brand1", "unit_cost": 10.0, "list_price": 20.0, "margin_pct": 50.0, "is_active": 1},
        {"product_id": 2, "name": "Producto B", "category": "Cat2", "product_line": "Line2",
         "brand": "Brand2", "unit_cost": 5.0, "list_price": 15.0, "margin_pct": 66.7, "is_active": 1},
    ]), "dim_products")

    insert_df(pd.DataFrame([
        {"customer_id": 1, "name": "Cliente X", "segment": "A", "city": "La Paz",
         "credit_limit": 50000, "payment_terms": "30 días", "is_active": 1},
        {"customer_id": 2, "name": "Cliente Y", "segment": "B", "city": "Santa Cruz",
         "credit_limit": 20000, "payment_terms": "60 días", "is_active": 1},
    ]), "dim_customers")

    insert_df(pd.DataFrame([
        {"vendor_id": 1, "name": "Proveedor 1", "category": "Materiales",
         "payment_terms": "30 días", "lead_time_days": 7, "is_active": 1},
    ]), "dim_vendors")

    insert_df(pd.DataFrame([
        {"seller_id": 1, "name": "Vendedor 1", "team": "Equipo A",
         "region": "La Paz", "target_monthly": 50000, "is_active": 1},
    ]), "dim_sellers")

    insert_df(pd.DataFrame([
        {"account_id": 1, "code": "4100", "name": "Ventas", "account_type": "income",
         "parent_group": "Ingresos", "sub_group": "Ventas"},
        {"account_id": 2, "code": "5100", "name": "Costo de Ventas", "account_type": "expense",
         "parent_group": "Costos", "sub_group": "COGS"},
        {"account_id": 3, "code": "6100", "name": "Gastos Admin", "account_type": "expense",
         "parent_group": "Gastos Operativos", "sub_group": "Administración"},
    ]), "dim_accounts")

    insert_df(pd.DataFrame([
        {"cost_center_id": 1, "code": "CC01", "name": "Administración",
         "department": "Admin", "responsible": "Gerente", "budget_annual": 120000},
    ]), "dim_cost_centers")

    # Fact: Sales (current + previous month)
    sales_rows = []
    for i in range(10):
        d = f"{period}-{15:02d}"
        sales_rows.append({
            "date_id": d, "invoice_number": f"INV-{i+1:04d}",
            "product_id": (i % 2) + 1, "customer_id": (i % 2) + 1,
            "seller_id": 1, "quantity": 10, "unit_price": 20.0, "unit_cost": 10.0,
            "subtotal": 200.0, "cost_total": 100.0, "gross_profit": 100.0,
            "margin_pct": 50.0, "total": 200.0, "status": "posted",
        })
    # Previous month sales
    for i in range(5):
        d = f"{prev_period}-{15:02d}"
        sales_rows.append({
            "date_id": d, "invoice_number": f"INV-P{i+1:04d}",
            "product_id": 1, "customer_id": 1, "seller_id": 1,
            "quantity": 8, "unit_price": 20.0, "unit_cost": 10.0,
            "subtotal": 160.0, "cost_total": 80.0, "gross_profit": 80.0,
            "margin_pct": 50.0, "total": 160.0, "status": "posted",
        })
    insert_df(pd.DataFrame(sales_rows), "fact_sales")

    # Fact: Receivables
    insert_df(pd.DataFrame([
        {"date_id": f"{period}-01", "invoice_number": "RCV-001", "customer_id": 1,
         "invoice_date": f"{period}-01", "due_date": f"{period}-15",
         "original_amount": 1000, "paid_amount": 500, "balance": 500,
         "days_overdue": 0, "aging_bucket": "current", "status": "current"},
        {"date_id": f"{period}-01", "invoice_number": "RCV-002", "customer_id": 2,
         "invoice_date": f"{prev_period}-01", "due_date": f"{prev_period}-15",
         "original_amount": 2000, "paid_amount": 0, "balance": 2000,
         "days_overdue": 45, "aging_bucket": "31-60", "status": "overdue"},
    ]), "fact_receivables")

    # Fact: Payables
    insert_df(pd.DataFrame([
        {"date_id": f"{period}-01", "invoice_number": "PAY-001", "vendor_id": 1,
         "invoice_date": f"{period}-01",
         "due_date": (today + timedelta(days=5)).isoformat(),
         "original_amount": 3000, "balance": 3000, "days_overdue": 0,
         "aging_bucket": "current", "status": "current", "priority": "normal"},
        {"date_id": f"{period}-01", "invoice_number": "PAY-002", "vendor_id": 1,
         "invoice_date": f"{prev_period}-01",
         "due_date": (today - timedelta(days=10)).isoformat(),
         "original_amount": 1500, "balance": 1500, "days_overdue": 10,
         "aging_bucket": "1-30", "status": "overdue", "priority": "critical"},
    ]), "fact_payables")

    # Fact: Inventory
    insert_df(pd.DataFrame([
        {"snapshot_date": today.isoformat(), "product_id": 1,
         "qty_on_hand": 100, "qty_reserved": 10, "qty_available": 90,
         "unit_cost": 10.0, "total_value": 1000.0, "avg_daily_sales": 5.0,
         "days_of_stock": 18.0, "reorder_point": 20.0, "reorder_qty": 50,
         "rotation_class": "A", "days_since_last_sale": 2},
        {"snapshot_date": today.isoformat(), "product_id": 2,
         "qty_on_hand": 5, "qty_reserved": 0, "qty_available": 5,
         "unit_cost": 5.0, "total_value": 25.0, "avg_daily_sales": 2.0,
         "days_of_stock": 2.5, "reorder_point": 10.0, "reorder_qty": 30,
         "rotation_class": "B", "days_since_last_sale": 1},
    ]), "fact_inventory")

    # Fact: Expenses
    insert_df(pd.DataFrame([
        {"date_id": f"{period}-10", "account_id": 3, "cost_center_id": 1,
         "description": "Alquiler", "amount": 5000, "budget_amount": 4500,
         "variance": 500, "category": "fixed"},
        {"date_id": f"{period}-15", "account_id": 3, "cost_center_id": 1,
         "description": "Servicios", "amount": 1200, "budget_amount": 1500,
         "variance": -300, "category": "variable"},
    ]), "fact_expenses")

    # Fact: Financials
    fin_rows = [
        {"period": period, "year": today.year, "month": today.month,
         "statement_type": "income_statement", "account_id": 1,
         "account_code": "4100", "account_name": "Ventas",
         "parent_group": "Ingresos", "sub_group": "Ventas",
         "amount": 2000.0, "prev_period": 1600.0, "prev_year": 1800.0, "budget": 2200.0},
        {"period": period, "year": today.year, "month": today.month,
         "statement_type": "income_statement", "account_id": 2,
         "account_code": "5100", "account_name": "Costo de Ventas",
         "parent_group": "Costos", "sub_group": "COGS",
         "amount": -1000.0, "prev_period": -800.0, "prev_year": -900.0, "budget": -1100.0},
        {"period": period, "year": today.year, "month": today.month,
         "statement_type": "income_statement", "account_id": 3,
         "account_code": "6100", "account_name": "Gastos Admin",
         "parent_group": "Gastos Operativos", "sub_group": "Administración",
         "amount": -300.0, "prev_period": -250.0, "prev_year": -280.0, "budget": -350.0},
        {"period": period, "year": today.year, "month": today.month,
         "statement_type": "balance_sheet", "account_id": None,
         "account_code": "1100", "account_name": "Efectivo",
         "parent_group": "Activo Corriente", "sub_group": "Efectivo",
         "amount": 50000.0, "prev_period": 45000.0, "prev_year": 40000.0, "budget": None},
        {"period": period, "year": today.year, "month": today.month,
         "statement_type": "balance_sheet", "account_id": None,
         "account_code": "1200", "account_name": "Inventarios",
         "parent_group": "Activo Corriente", "sub_group": "Inventarios",
         "amount": 10000.0, "prev_period": 9000.0, "prev_year": 8000.0, "budget": None},
        {"period": period, "year": today.year, "month": today.month,
         "statement_type": "balance_sheet", "account_id": None,
         "account_code": "2100", "account_name": "CxP Corrientes",
         "parent_group": "Pasivo Corriente", "sub_group": "Proveedores",
         "amount": 15000.0, "prev_period": 14000.0, "prev_year": 12000.0, "budget": None},
        {"period": period, "year": today.year, "month": today.month,
         "statement_type": "balance_sheet", "account_id": None,
         "account_code": "3100", "account_name": "Capital Social",
         "parent_group": "Patrimonio", "sub_group": "Capital",
         "amount": 45000.0, "prev_period": 40000.0, "prev_year": 36000.0, "budget": None},
    ]
    insert_df(pd.DataFrame(fin_rows), "fact_financials")

    # Fact: Cash flow
    cf_rows = []
    for i in range(30):
        d = (today - timedelta(days=30 - i)).isoformat()
        balance = 50000 + i * 100
        cf_rows.append({
            "date_id": d, "category": "operating", "sub_category": "collections",
            "inflow": 2000, "outflow": 1500, "net_flow": 500,
            "running_balance": balance, "is_projected": 0,
        })
    insert_df(pd.DataFrame(cf_rows), "fact_cashflow")

    return db
