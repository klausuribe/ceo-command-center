#!/usr/bin/env python3
"""Generate 24 months of realistic synthetic data for the CEO Command Center.

Creates: 200+ products, 100+ customers, 20+ vendors, 5 sellers,
full sales/AR/AP/inventory/expenses/financial/cashflow data.
"""

import sys
import random
from pathlib import Path
from datetime import date, timedelta
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import get_engine, insert_df, query_scalar, execute_script

# Reproducible randomness
random.seed(42)
np.random.seed(42)

# ── Date range: 24 months ending current month ──────────────────────
TODAY = date.today()
START_DATE = date(TODAY.year - 2, TODAY.month, 1)
END_DATE = TODAY

MONTH_NAMES_ES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]


# ════════════════════════════════════════════════════════════════════
#  DIMENSION DATA
# ════════════════════════════════════════════════════════════════════

def gen_dim_time() -> pd.DataFrame:
    """Generate dim_time for every day in the 24-month range."""
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    rows = []
    for d in dates:
        rows.append({
            "date_id": d.strftime("%Y-%m-%d"),
            "date": d.strftime("%Y-%m-%d"),
            "day": d.day,
            "month": d.month,
            "month_name": MONTH_NAMES_ES[d.month],
            "quarter": (d.month - 1) // 3 + 1,
            "year": d.year,
            "week_number": d.isocalendar()[1],
            "day_of_week": d.isoweekday(),
            "is_weekend": d.isoweekday() >= 6,
            "fiscal_year": d.year,
            "fiscal_quarter": (d.month - 1) // 3 + 1,
        })
    return pd.DataFrame(rows)


# ── Products ─────────────────────────────────────────────────────────
CATEGORIES = {
    "Electrónica": {
        "lines": ["Smartphones", "Laptops", "Tablets", "Accesorios Tech"],
        "brands": ["TechPro", "DigiMax"],
        "cost_range": (150, 3000),
        "margin_range": (0.15, 0.35),
    },
    "Hogar": {
        "lines": ["Muebles", "Decoración", "Cocina"],
        "brands": ["CasaViva", "Komfort"],
        "cost_range": (50, 1500),
        "margin_range": (0.25, 0.45),
    },
    "Ropa y Calzado": {
        "lines": ["Casual", "Formal", "Deportivo"],
        "brands": ["UrbanStyle", "SportFit"],
        "cost_range": (20, 300),
        "margin_range": (0.40, 0.65),
    },
    "Alimentos": {
        "lines": ["Snacks", "Bebidas", "Conservas"],
        "brands": ["NutriBol", "FreshCo"],
        "cost_range": (5, 80),
        "margin_range": (0.20, 0.40),
    },
    "Construcción": {
        "lines": ["Herramientas", "Materiales"],
        "brands": ["BuildMax", "FerroPlus"],
        "cost_range": (30, 2000),
        "margin_range": (0.18, 0.35),
    },
}


def gen_dim_products() -> pd.DataFrame:
    """Generate 200+ products across 5 categories."""
    rows = []
    pid = 1
    for cat, info in CATEGORIES.items():
        for line in info["lines"]:
            n_products = random.randint(8, 15)
            for i in range(n_products):
                cost = round(random.uniform(*info["cost_range"]), 2)
                margin = round(random.uniform(*info["margin_range"]), 2)
                price = round(cost / (1 - margin), 2)
                brand = random.choice(info["brands"])
                rows.append({
                    "product_id": pid,
                    "odoo_product_id": 1000 + pid,
                    "sku": f"{cat[:3].upper()}-{line[:3].upper()}-{pid:04d}",
                    "name": f"{line} {brand} #{i+1}",
                    "category": cat,
                    "product_line": line,
                    "brand": brand,
                    "unit_cost": cost,
                    "list_price": price,
                    "margin_pct": margin,
                    "is_active": 1,
                })
                pid += 1
    return pd.DataFrame(rows)


# ── Customers ────────────────────────────────────────────────────────
CITIES = [
    ("Santa Cruz", "Oriente"), ("La Paz", "Altiplano"), ("Cochabamba", "Valle"),
    ("Sucre", "Valle"), ("Tarija", "Sur"), ("Oruro", "Altiplano"),
    ("Potosí", "Altiplano"), ("Trinidad", "Oriente"), ("Cobija", "Oriente"),
]

FIRST_NAMES = [
    "Comercial", "Distribuidora", "Importadora", "Servicios", "Grupo",
    "Empresa", "Corporación", "Sociedad", "Almacén", "Tienda",
]
LAST_NAMES = [
    "Andina", "Boliviana", "del Sur", "Oriental", "Central",
    "Nacional", "Imperial", "Global", "Premier", "Express",
    "Mercantil", "Progreso", "Unión", "Pionera", "Continental",
]


def gen_dim_customers() -> pd.DataFrame:
    """Generate 120 customers in A/B/C segments."""
    rows = []
    segments = ["A"] * 20 + ["B"] * 40 + ["C"] * 60
    random.shuffle(segments)
    sellers = list(range(1, 6))  # 5 sellers
    for cid in range(1, 121):
        city, region = random.choice(CITIES)
        seg = segments[cid - 1]
        credit = {"A": 50000, "B": 20000, "C": 5000}[seg]
        terms = random.choice(["30 días", "60 días", "90 días"])
        rows.append({
            "customer_id": cid,
            "odoo_partner_id": 2000 + cid,
            "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} {cid}",
            "customer_code": f"CLI-{cid:04d}",
            "segment": seg,
            "city": city,
            "region": region,
            "credit_limit": credit + random.randint(-2000, 5000),
            "payment_terms": terms,
            "assigned_seller": f"Vendedor {random.choice(sellers)}",
            "is_active": 1,
            "created_date": (START_DATE + timedelta(days=random.randint(0, 100))).isoformat(),
        })
    return pd.DataFrame(rows)


# ── Vendors ──────────────────────────────────────────────────────────
VENDOR_TYPES = ["Nacional", "Importador", "Fabricante", "Distribuidor"]


def gen_dim_vendors() -> pd.DataFrame:
    """Generate 25 vendors."""
    rows = []
    for vid in range(1, 26):
        rows.append({
            "vendor_id": vid,
            "odoo_partner_id": 3000 + vid,
            "name": f"Proveedor {random.choice(LAST_NAMES)} {vid}",
            "vendor_code": f"PROV-{vid:04d}",
            "category": random.choice(VENDOR_TYPES),
            "country": random.choice(["Bolivia", "Bolivia", "China", "Brasil", "Argentina"]),
            "currency": "BOB",
            "payment_terms": random.choice(["30 días", "45 días", "60 días"]),
            "lead_time_days": random.randint(3, 30),
            "is_active": 1,
        })
    return pd.DataFrame(rows)


# ── Sellers ──────────────────────────────────────────────────────────
def gen_dim_sellers() -> pd.DataFrame:
    names = ["Carlos Mendoza", "Ana Gutiérrez", "Roberto Flores",
             "María Salazar", "Diego Vargas"]
    teams = ["Equipo A", "Equipo A", "Equipo B", "Equipo B", "Equipo A"]
    regions = ["Oriente", "Altiplano", "Valle", "Oriente", "Valle"]
    rows = []
    for i, name in enumerate(names, 1):
        rows.append({
            "seller_id": i,
            "odoo_user_id": 100 + i,
            "name": name,
            "team": teams[i - 1],
            "region": regions[i - 1],
            "target_monthly": random.randint(80000, 150000),
            "is_active": 1,
        })
    return pd.DataFrame(rows)


# ── Accounts (Chart of Accounts) ────────────────────────────────────
ACCOUNTS = [
    # (code, name, type, parent_group, sub_group)
    ("1100", "Caja y Bancos", "asset", "Activo Corriente", "Efectivo"),
    ("1200", "Cuentas por Cobrar", "asset", "Activo Corriente", "Cuentas por Cobrar"),
    ("1300", "Inventarios", "asset", "Activo Corriente", "Inventarios"),
    ("1400", "Anticipos", "asset", "Activo Corriente", "Anticipos"),
    ("1500", "Activo Fijo", "asset", "Activo No Corriente", "Propiedad"),
    ("1600", "Depreciación Acumulada", "asset", "Activo No Corriente", "Depreciación"),
    ("2100", "Cuentas por Pagar", "liability", "Pasivo Corriente", "Proveedores"),
    ("2200", "Impuestos por Pagar", "liability", "Pasivo Corriente", "Impuestos"),
    ("2300", "Préstamos Corto Plazo", "liability", "Pasivo Corriente", "Préstamos"),
    ("2400", "Sueldos por Pagar", "liability", "Pasivo Corriente", "Sueldos"),
    ("2500", "Préstamos Largo Plazo", "liability", "Pasivo No Corriente", "Préstamos LP"),
    ("3100", "Capital Social", "equity", "Patrimonio", "Capital"),
    ("3200", "Reservas", "equity", "Patrimonio", "Reservas"),
    ("3300", "Resultados Acumulados", "equity", "Patrimonio", "Resultados"),
    ("4100", "Ingresos por Ventas", "income", "Ingresos", "Ventas"),
    ("4200", "Otros Ingresos", "income", "Ingresos", "Otros"),
    ("5100", "Costo de Ventas", "expense", "Costos", "CMV"),
    ("6100", "Sueldos y Salarios", "expense", "Gastos Operativos", "Personal"),
    ("6200", "Alquiler", "expense", "Gastos Operativos", "Infraestructura"),
    ("6300", "Servicios Básicos", "expense", "Gastos Operativos", "Servicios"),
    ("6400", "Marketing y Publicidad", "expense", "Gastos Operativos", "Marketing"),
    ("6500", "Transporte y Logística", "expense", "Gastos Operativos", "Logística"),
    ("6600", "Mantenimiento", "expense", "Gastos Operativos", "Mantenimiento"),
    ("6700", "Seguros", "expense", "Gastos Operativos", "Seguros"),
    ("6800", "Depreciación", "expense", "Gastos Operativos", "Depreciación"),
    ("6900", "Gastos Financieros", "expense", "Gastos Financieros", "Intereses"),
    ("7100", "Impuesto a las Utilidades", "expense", "Impuestos", "IUE"),
]


def gen_dim_accounts() -> pd.DataFrame:
    rows = []
    for i, (code, name, atype, parent, sub) in enumerate(ACCOUNTS, 1):
        rows.append({
            "account_id": i,
            "odoo_account_id": 4000 + i,
            "code": code,
            "name": name,
            "account_type": atype,
            "parent_group": parent,
            "sub_group": sub,
            "is_active": 1,
        })
    return pd.DataFrame(rows)


# ── Cost Centers ─────────────────────────────────────────────────────
COST_CENTERS = [
    ("CC01", "Administración", "Administración", "Gerencia General", 30000),
    ("CC02", "Ventas", "Comercial", "Dir. Comercial", 45000),
    ("CC03", "Almacén", "Logística", "Jefe Almacén", 20000),
    ("CC04", "Marketing", "Comercial", "Dir. Marketing", 25000),
    ("CC05", "TI", "Tecnología", "Jefe TI", 15000),
    ("CC06", "RRHH", "Administración", "Dir. RRHH", 12000),
]


def gen_dim_cost_centers() -> pd.DataFrame:
    rows = []
    for i, (code, name, dept, resp, budget) in enumerate(COST_CENTERS, 1):
        rows.append({
            "cost_center_id": i,
            "code": code,
            "name": name,
            "department": dept,
            "responsible": resp,
            "budget_annual": budget * 12,
        })
    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════
#  FACT DATA
# ════════════════════════════════════════════════════════════════════

def _business_days(start: date, end: date) -> list[date]:
    """Return list of weekdays between start and end."""
    days = []
    d = start
    while d <= end:
        if d.isoweekday() <= 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def gen_fact_sales(products_df: pd.DataFrame, n_customers: int) -> pd.DataFrame:
    """Generate ~24 months of daily sales with seasonal trends."""
    bdays = _business_days(START_DATE, END_DATE)
    product_ids = products_df["product_id"].tolist()
    costs = dict(zip(products_df["product_id"], products_df["unit_cost"]))
    prices = dict(zip(products_df["product_id"], products_df["list_price"]))

    rows = []
    invoice_num = 1000

    for day in bdays:
        # Seasonal multiplier: higher in Nov-Dec (holiday), lower in Feb
        month_factor = {1: 0.9, 2: 0.8, 3: 0.95, 4: 1.0, 5: 1.0, 6: 0.95,
                        7: 0.9, 8: 1.0, 9: 1.05, 10: 1.1, 11: 1.3, 12: 1.4}
        factor = month_factor.get(day.month, 1.0)

        # Growth trend: +1.5% per month from start
        months_from_start = (day.year - START_DATE.year) * 12 + (day.month - START_DATE.month)
        growth = 1 + 0.015 * months_from_start

        n_invoices = int(random.gauss(8, 2) * factor * growth)
        n_invoices = max(3, n_invoices)

        for _ in range(n_invoices):
            invoice_num += 1
            cust_id = random.randint(1, n_customers)
            seller_id = random.randint(1, 5)
            n_lines = random.randint(1, 5)

            for _ in range(n_lines):
                prod_id = random.choice(product_ids)
                qty = random.randint(1, 20)
                price = prices[prod_id]
                cost = costs[prod_id]
                discount = random.choice([0, 0, 0, 0, 5, 10, 15])
                subtotal = round(qty * price * (1 - discount / 100), 2)
                cost_total = round(qty * cost, 2)
                gross_profit = round(subtotal - cost_total, 2)
                margin = round(gross_profit / subtotal, 4) if subtotal else 0
                tax = round(subtotal * 0.13, 2)

                rows.append({
                    "date_id": day.strftime("%Y-%m-%d"),
                    "invoice_number": f"FAC-{invoice_num:06d}",
                    "odoo_invoice_id": invoice_num,
                    "product_id": prod_id,
                    "customer_id": cust_id,
                    "seller_id": seller_id,
                    "quantity": qty,
                    "unit_price": price,
                    "unit_cost": cost,
                    "discount_pct": discount,
                    "subtotal": subtotal,
                    "cost_total": cost_total,
                    "gross_profit": gross_profit,
                    "margin_pct": margin,
                    "tax_amount": tax,
                    "total": round(subtotal + tax, 2),
                    "currency": "BOB",
                    "status": "posted",
                })

    return pd.DataFrame(rows)


def gen_fact_receivables(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Generate open receivables from recent sales (some overdue)."""
    # Take invoices from last 4 months, ~40% still unpaid
    cutoff = (TODAY - timedelta(days=120)).strftime("%Y-%m-%d")
    recent = sales_df[sales_df["date_id"] >= cutoff].copy()

    # Aggregate by invoice
    invoices = recent.groupby(["invoice_number", "customer_id", "seller_id", "date_id"]).agg(
        original_amount=("total", "sum")
    ).reset_index()

    rows = []
    for _, inv in invoices.iterrows():
        # 60% are paid, 40% still open
        if random.random() < 0.6:
            continue
        inv_date = date.fromisoformat(inv["date_id"])
        terms_days = random.choice([30, 30, 60, 60, 90])
        due = inv_date + timedelta(days=terms_days)
        days_over = max(0, (TODAY - due).days)

        if days_over == 0:
            bucket = "current"
        elif days_over <= 30:
            bucket = "1-30"
        elif days_over <= 60:
            bucket = "31-60"
        elif days_over <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"

        paid_pct = random.choice([0, 0, 0, 0.3, 0.5, 0.7])
        original = round(inv["original_amount"], 2)
        paid = round(original * paid_pct, 2)
        balance = round(original - paid, 2)

        status = "current" if days_over == 0 else "overdue"

        rows.append({
            "date_id": inv["date_id"],
            "invoice_number": inv["invoice_number"],
            "odoo_move_id": random.randint(5000, 9999),
            "customer_id": inv["customer_id"],
            "seller_id": inv["seller_id"],
            "invoice_date": inv["date_id"],
            "due_date": due.isoformat(),
            "original_amount": original,
            "paid_amount": paid,
            "balance": balance,
            "days_overdue": days_over,
            "aging_bucket": bucket,
            "status": status,
            "last_payment_date": (TODAY - timedelta(days=random.randint(1, 30))).isoformat() if paid > 0 else None,
            "collection_notes": None,
        })

    return pd.DataFrame(rows)


def gen_fact_payables() -> pd.DataFrame:
    """Generate open payables to vendors."""
    rows = []
    for _ in range(random.randint(80, 120)):
        inv_date = TODAY - timedelta(days=random.randint(5, 150))
        terms_days = random.choice([30, 45, 60])
        due = inv_date + timedelta(days=terms_days)
        days_over = max(0, (TODAY - due).days)

        if days_over == 0:
            bucket = "current"
        elif days_over <= 30:
            bucket = "1-30"
        elif days_over <= 60:
            bucket = "31-60"
        elif days_over <= 90:
            bucket = "61-90"
        else:
            bucket = "90+"

        original = round(random.uniform(500, 50000), 2)
        paid_pct = random.choice([0, 0, 0, 0.5])
        paid = round(original * paid_pct, 2)
        balance = round(original - paid, 2)
        status = "current" if days_over == 0 else "overdue"
        priority = "critical" if days_over > 60 else ("high" if days_over > 30 else "normal")

        rows.append({
            "date_id": inv_date.strftime("%Y-%m-%d"),
            "invoice_number": f"PROV-{random.randint(10000, 99999)}",
            "odoo_move_id": random.randint(10000, 19999),
            "vendor_id": random.randint(1, 25),
            "invoice_date": inv_date.isoformat(),
            "due_date": due.isoformat(),
            "original_amount": original,
            "paid_amount": paid,
            "balance": balance,
            "days_overdue": days_over,
            "aging_bucket": bucket,
            "status": status,
            "currency": "BOB",
            "priority": priority,
        })

    return pd.DataFrame(rows)


def gen_fact_inventory(products_df: pd.DataFrame, sales_df: pd.DataFrame) -> pd.DataFrame:
    """Generate current inventory snapshot for all products."""
    # Calculate avg daily sales per product from last 30 days
    cutoff = (TODAY - timedelta(days=30)).strftime("%Y-%m-%d")
    recent_sales = sales_df[sales_df["date_id"] >= cutoff]
    avg_daily = recent_sales.groupby("product_id")["quantity"].sum() / 30

    rows = []
    for _, p in products_df.iterrows():
        pid = p["product_id"]
        avg_d = avg_daily.get(pid, random.uniform(0.1, 2))
        qty_on_hand = round(random.uniform(5, 500), 0)
        qty_reserved = round(min(qty_on_hand * 0.1, random.uniform(0, 20)), 0)
        qty_available = qty_on_hand - qty_reserved
        qty_incoming = round(random.uniform(0, 100), 0) if random.random() < 0.3 else 0
        days_stock = round(qty_available / avg_d, 1) if avg_d > 0 else 999
        lead_time = random.randint(5, 20)
        safety = 1.5
        reorder_pt = round(avg_d * lead_time * safety, 0)
        reorder_qty = round(avg_d * 30, 0)  # 1 month supply

        # ABC classification
        if avg_d > 5:
            rotation = "A"
        elif avg_d > 1:
            rotation = "B"
        elif avg_d > 0.1:
            rotation = "C"
        else:
            rotation = "dead_stock"

        last_sale_days = random.randint(0, 60) if rotation != "dead_stock" else random.randint(90, 365)
        last_sale = (TODAY - timedelta(days=last_sale_days)).isoformat()

        rows.append({
            "snapshot_date": TODAY.strftime("%Y-%m-%d"),
            "product_id": pid,
            "warehouse": "main",
            "qty_on_hand": qty_on_hand,
            "qty_reserved": qty_reserved,
            "qty_available": qty_available,
            "qty_incoming": qty_incoming,
            "unit_cost": p["unit_cost"],
            "total_value": round(qty_on_hand * p["unit_cost"], 2),
            "avg_daily_sales": round(avg_d, 2),
            "days_of_stock": days_stock,
            "reorder_point": reorder_pt,
            "reorder_qty": reorder_qty,
            "rotation_class": rotation,
            "last_sale_date": last_sale,
            "days_since_last_sale": last_sale_days,
        })

    return pd.DataFrame(rows)


def gen_fact_expenses() -> pd.DataFrame:
    """Generate 24 months of monthly expenses by account/cost center."""
    # Expense accounts are IDs 17-27 in dim_accounts (codes 5100-7100)
    expense_accounts = list(range(17, 28))
    cost_centers = list(range(1, 7))

    # Monthly base amounts by account
    base_amounts: dict[int, float] = {
        17: 120000,  # Costo de Ventas (correlates with sales)
        18: 45000,   # Sueldos
        19: 8000,    # Alquiler
        20: 3000,    # Servicios
        21: 12000,   # Marketing
        22: 5000,    # Transporte
        23: 2000,    # Mantenimiento
        24: 3000,    # Seguros
        25: 4000,    # Depreciación
        26: 6000,    # Gastos Financieros
        27: 8000,    # IUE
    }

    rows = []
    d = START_DATE
    while d <= END_DATE:
        period_end = date(d.year, d.month, 28)
        months_elapsed = (d.year - START_DATE.year) * 12 + (d.month - START_DATE.month)

        for acc_id in expense_accounts:
            base = base_amounts[acc_id]
            # Inflation + growth
            amount = base * (1 + 0.01 * months_elapsed) * random.uniform(0.85, 1.15)
            budget = base * (1 + 0.01 * months_elapsed)
            variance = amount - budget
            category = "fixed" if acc_id in [19, 24, 25] else ("variable" if acc_id in [17, 21, 22] else "semi-variable")

            rows.append({
                "date_id": d.strftime("%Y-%m-%d"),
                "account_id": acc_id,
                "cost_center_id": random.choice(cost_centers),
                "description": f"Gasto mensual {MONTH_NAMES_ES[d.month]} {d.year}",
                "odoo_move_id": random.randint(20000, 29999),
                "amount": round(amount, 2),
                "budget_amount": round(budget, 2),
                "variance": round(variance, 2),
                "variance_pct": round(variance / budget * 100, 2) if budget else 0,
                "category": category,
                "is_recurring": 1 if category == "fixed" else 0,
                "vendor_id": random.randint(1, 25) if acc_id not in [18, 25, 27] else None,
            })

        # Move to next month
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)

    return pd.DataFrame(rows)


def gen_fact_financials() -> pd.DataFrame:
    """Generate monthly income statement and balance sheet entries."""
    rows = []
    d = START_DATE

    while d <= END_DATE:
        period = f"{d.year}-{d.month:02d}"
        months_elapsed = (d.year - START_DATE.year) * 12 + (d.month - START_DATE.month)
        growth = 1 + 0.015 * months_elapsed

        # Income Statement
        revenue = round(350000 * growth * random.uniform(0.9, 1.1), 2)
        cogs = round(revenue * random.uniform(0.55, 0.65), 2)
        opex = round(80000 * growth * random.uniform(0.9, 1.1), 2)
        fin_expenses = round(6000 * random.uniform(0.9, 1.1), 2)
        tax = round(max(0, (revenue - cogs - opex - fin_expenses) * 0.25), 2)

        is_entries = [
            (15, "4100", "Ingresos por Ventas", "Ingresos", "Ventas", revenue),
            (17, "5100", "Costo de Ventas", "Costos", "CMV", -cogs),
            (18, "6100", "Sueldos y Salarios", "Gastos Operativos", "Personal", -45000 * growth),
            (19, "6200", "Alquiler", "Gastos Operativos", "Infraestructura", -8000),
            (20, "6300", "Servicios Básicos", "Gastos Operativos", "Servicios", -3000 * random.uniform(0.9, 1.1)),
            (21, "6400", "Marketing", "Gastos Operativos", "Marketing", -12000 * growth * random.uniform(0.8, 1.2)),
            (26, "6900", "Gastos Financieros", "Gastos Financieros", "Intereses", -fin_expenses),
            (27, "7100", "IUE", "Impuestos", "IUE", -tax),
        ]

        for acc_id, code, name, parent, sub, amount in is_entries:
            rows.append({
                "period": period,
                "year": d.year,
                "month": d.month,
                "statement_type": "income_statement",
                "account_id": acc_id,
                "account_code": code,
                "account_name": name,
                "parent_group": parent,
                "sub_group": sub,
                "amount": round(amount, 2),
                "prev_period": round(amount * random.uniform(0.92, 1.0), 2),
                "prev_year": round(amount * random.uniform(0.85, 0.95), 2) if months_elapsed >= 12 else None,
                "budget": round(amount * random.uniform(0.95, 1.05), 2),
                "ytd_actual": round(amount * (months_elapsed % 12 + 1), 2),
                "ytd_budget": round(amount * 1.02 * (months_elapsed % 12 + 1), 2),
            })

        # Balance Sheet (simplified)
        total_assets = round(2000000 * growth * random.uniform(0.95, 1.05), 2)
        bs_entries = [
            (1, "1100", "Caja y Bancos", "Activo Corriente", "Efectivo", total_assets * 0.15),
            (2, "1200", "Cuentas por Cobrar", "Activo Corriente", "CxC", total_assets * 0.25),
            (3, "1300", "Inventarios", "Activo Corriente", "Inventarios", total_assets * 0.20),
            (5, "1500", "Activo Fijo", "Activo No Corriente", "Propiedad", total_assets * 0.35),
            (6, "1600", "Depreciación Acum.", "Activo No Corriente", "Depreciación", -total_assets * 0.05),
            (7, "2100", "Cuentas por Pagar", "Pasivo Corriente", "Proveedores", -total_assets * 0.15),
            (8, "2200", "Impuestos por Pagar", "Pasivo Corriente", "Impuestos", -total_assets * 0.03),
            (9, "2300", "Préstamos CP", "Pasivo Corriente", "Préstamos", -total_assets * 0.10),
            (11, "2500", "Préstamos LP", "Pasivo No Corriente", "Préstamos LP", -total_assets * 0.12),
            (12, "3100", "Capital Social", "Patrimonio", "Capital", -total_assets * 0.20),
            (14, "3300", "Resultados Acum.", "Patrimonio", "Resultados", -total_assets * 0.15),
        ]

        for acc_id, code, name, parent, sub, amount in bs_entries:
            rows.append({
                "period": period,
                "year": d.year,
                "month": d.month,
                "statement_type": "balance_sheet",
                "account_id": acc_id,
                "account_code": code,
                "account_name": name,
                "parent_group": parent,
                "sub_group": sub,
                "amount": round(amount, 2),
                "prev_period": round(amount * random.uniform(0.97, 1.0), 2),
                "prev_year": round(amount * random.uniform(0.85, 0.95), 2) if months_elapsed >= 12 else None,
                "budget": round(amount * random.uniform(0.95, 1.05), 2),
                "ytd_actual": None,
                "ytd_budget": None,
            })

        # Next month
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)

    return pd.DataFrame(rows)


def gen_fact_cashflow() -> pd.DataFrame:
    """Generate daily cashflow entries for 24 months."""
    bdays = _business_days(START_DATE, END_DATE)
    rows = []
    running = 500000.0  # Starting cash

    for day in bdays:
        months_elapsed = (day.year - START_DATE.year) * 12 + (day.month - START_DATE.month)
        growth = 1 + 0.015 * months_elapsed

        # Operating: collections and payments
        collections = round(random.gauss(18000, 3000) * growth, 2)
        supplier_pay = round(random.gauss(10000, 2000) * growth, 2)
        payroll = round(2200 * growth, 2) if day.day <= 5 or (25 <= day.day <= 31) else 0
        other_opex = round(random.gauss(1500, 500), 2)

        entries = [
            ("operating", "collections", "Cobros del día", collections, 0),
            ("operating", "suppliers", "Pagos a proveedores", 0, supplier_pay),
        ]
        if payroll > 0:
            entries.append(("operating", "payroll", "Nómina", 0, payroll))
        entries.append(("operating", "other", "Otros gastos operativos", 0, other_opex))

        # Occasional investing/financing
        if random.random() < 0.02:
            entries.append(("investing", "equipment", "Compra de equipo", 0, round(random.uniform(5000, 50000), 2)))
        if random.random() < 0.05:
            entries.append(("financing", "loan_payment", "Cuota préstamo", 0, round(random.uniform(3000, 15000), 2)))

        for cat, subcat, desc, inflow, outflow in entries:
            net = round(inflow - outflow, 2)
            running = round(running + net, 2)
            rows.append({
                "date_id": day.strftime("%Y-%m-%d"),
                "category": cat,
                "sub_category": subcat,
                "description": desc,
                "inflow": inflow,
                "outflow": outflow,
                "net_flow": net,
                "running_balance": running,
                "is_projected": 0,
                "confidence": None,
                "source": "odoo",
            })

    return pd.DataFrame(rows)


# ════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════

def main() -> None:
    logger.info("Generating demo data...")

    # Dimensions
    logger.info("Generating dimensions...")
    dim_time = gen_dim_time()
    dim_products = gen_dim_products()
    dim_customers = gen_dim_customers()
    dim_vendors = gen_dim_vendors()
    dim_sellers = gen_dim_sellers()
    dim_accounts = gen_dim_accounts()
    dim_cost_centers = gen_dim_cost_centers()

    logger.info(f"  dim_time: {len(dim_time)} days")
    logger.info(f"  dim_products: {len(dim_products)} products")
    logger.info(f"  dim_customers: {len(dim_customers)} customers")
    logger.info(f"  dim_vendors: {len(dim_vendors)} vendors")
    logger.info(f"  dim_sellers: {len(dim_sellers)} sellers")
    logger.info(f"  dim_accounts: {len(dim_accounts)} accounts")
    logger.info(f"  dim_cost_centers: {len(dim_cost_centers)} cost centers")

    # Facts
    logger.info("Generating fact_sales (this may take a moment)...")
    fact_sales = gen_fact_sales(dim_products, len(dim_customers))
    logger.info(f"  fact_sales: {len(fact_sales)} line items")

    logger.info("Generating receivables, payables, inventory...")
    fact_receivables = gen_fact_receivables(fact_sales)
    fact_payables = gen_fact_payables()
    fact_inventory = gen_fact_inventory(dim_products, fact_sales)
    logger.info(f"  fact_receivables: {len(fact_receivables)} open items")
    logger.info(f"  fact_payables: {len(fact_payables)} open items")
    logger.info(f"  fact_inventory: {len(fact_inventory)} product snapshots")

    logger.info("Generating expenses, financials, cashflow...")
    fact_expenses = gen_fact_expenses()
    fact_financials = gen_fact_financials()
    fact_cashflow = gen_fact_cashflow()
    logger.info(f"  fact_expenses: {len(fact_expenses)} entries")
    logger.info(f"  fact_financials: {len(fact_financials)} entries")
    logger.info(f"  fact_cashflow: {len(fact_cashflow)} entries")

    # Load into database
    logger.info("Loading into database...")
    tables = [
        ("dim_time", dim_time),
        ("dim_products", dim_products),
        ("dim_customers", dim_customers),
        ("dim_vendors", dim_vendors),
        ("dim_sellers", dim_sellers),
        ("dim_accounts", dim_accounts),
        ("dim_cost_centers", dim_cost_centers),
        ("fact_sales", fact_sales),
        ("fact_receivables", fact_receivables),
        ("fact_payables", fact_payables),
        ("fact_inventory", fact_inventory),
        ("fact_expenses", fact_expenses),
        ("fact_financials", fact_financials),
        ("fact_cashflow", fact_cashflow),
    ]

    for name, df in tables:
        # Clear existing data but keep schema (preserves PKs and indexes)
        execute_script(f"DELETE FROM {name}")
        insert_df(df, name, if_exists="append")
        logger.info(f"  ✅ {name}: {len(df)} rows loaded")

    logger.info("Demo data generation complete!")


if __name__ == "__main__":
    main()
