"""Tests para analytics.budget_projector y override de presupuesto en expense_analytics."""

from datetime import date, timedelta

import pandas as pd
import pytest

from analytics import budget_projector as bp
from analytics import expense_analytics as ea
from database.db_manager import execute_sql, query_df, insert_df


# ── Helpers ───────────────────────────────────────────────────────────────

def _seed_history(months_back: int = 8, account_id: int = 3, base: float = 4000.0) -> None:
    """Inserta historia mensual con ligera tendencia ascendente para una cuenta."""
    today = date.today()
    rows = []
    for i in range(months_back, 0, -1):
        y, m = today.year, today.month - i
        while m <= 0:
            m += 12
            y -= 1
        amount = base * (1 + 0.02 * (months_back - i))
        rows.append({
            "date_id": f"{y}-{m:02d}-15",
            "account_id": account_id,
            "cost_center_id": 1,
            "description": f"seed {y}-{m:02d}",
            "amount": round(amount, 2),
            "budget_amount": round(amount * 1.05, 2),
            "variance": 0.0,
            "category": "variable",
        })
    insert_df(pd.DataFrame(rows), "fact_expenses")


# ── Projection math ────────────────────────────────────────────────────────

class TestProjectAllAccounts:
    def test_empty_db_returns_empty(self, db):
        result = bp.project_all_accounts(2027, 1, months_ahead=3)
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_projects_n_months_for_each_expense_account(self, seeded_db):
        accounts = query_df(
            "SELECT account_id FROM dim_accounts WHERE account_type='expense'"
        )
        n_accounts = len(accounts)
        months = 4
        result = bp.project_all_accounts(2027, 1, months_ahead=months)
        assert len(result) == n_accounts * months
        assert set(result["source"].unique()) == {"projected"}
        assert result["target_value"].min() >= 0

    def test_projection_follows_recent_trend(self, seeded_db):
        _seed_history(months_back=8, account_id=3, base=4000.0)
        today = date.today()
        next_y, next_m = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)

        value = bp.project_account_budget(3, next_y, next_m, lookback=6)
        # El histórico sembrado es ~4000 creciendo 2% mensual → proyección > base inicial
        assert value > 3500


# ── Assumption multipliers ────────────────────────────────────────────────

class TestAssumptions:
    def test_increase_pct_applied(self, seeded_db):
        _seed_history(months_back=6, account_id=3, base=5000.0)
        today = date.today()
        next_y, next_m = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)

        base_value = bp.project_account_budget(3, next_y, next_m)

        execute_sql(
            "INSERT INTO config_assumptions "
            "(module, description, impact_type, impact_pct, account_id, "
            " start_date, end_date, is_active, created_by) "
            "VALUES ('expenses', 'test +20%', 'increase', 20, 3, '2020-01-01', '2099-12-31', 1, 'test')"
        )

        with_assumption = bp.project_account_budget(3, next_y, next_m)
        assert with_assumption == pytest.approx(base_value * 1.20, rel=0.001)

    def test_replace_overrides_base(self, seeded_db):
        _seed_history(months_back=6, account_id=3, base=5000.0)
        today = date.today()
        next_y, next_m = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)

        execute_sql(
            "INSERT INTO config_assumptions "
            "(module, description, impact_type, impact_value, account_id, "
            " start_date, end_date, is_active, created_by) "
            "VALUES ('expenses', 'fix 9000', 'replace', 9000, 3, '2020-01-01', '2099-12-31', 1, 'test')"
        )
        value = bp.project_account_budget(3, next_y, next_m)
        assert value == pytest.approx(9000.0, rel=0.001)

    def test_inactive_assumption_ignored(self, seeded_db):
        _seed_history(months_back=6, account_id=3, base=5000.0)
        today = date.today()
        next_y, next_m = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)

        base_value = bp.project_account_budget(3, next_y, next_m)

        execute_sql(
            "INSERT INTO config_assumptions "
            "(module, description, impact_type, impact_pct, account_id, "
            " start_date, end_date, is_active, created_by) "
            "VALUES ('expenses', 'inactive +50%', 'increase', 50, 3, '2020-01-01', '2099-12-31', 0, 'test')"
        )
        assert bp.project_account_budget(3, next_y, next_m) == pytest.approx(base_value, rel=0.001)

    def test_category_substring_filter(self, seeded_db):
        # Account 3 name = 'Gastos Admin'
        _seed_history(months_back=6, account_id=3, base=5000.0)
        today = date.today()
        next_y, next_m = (today.year, today.month + 1) if today.month < 12 else (today.year + 1, 1)

        base_value = bp.project_account_budget(3, next_y, next_m)

        # category filter that doesn't match → should NOT apply
        execute_sql(
            "INSERT INTO config_assumptions "
            "(module, description, impact_type, impact_pct, category, "
            " start_date, end_date, is_active, created_by) "
            "VALUES ('expenses', 'marketing +30%', 'increase', 30, 'marketing', '2020-01-01', '2099-12-31', 1, 'test')"
        )
        assert bp.project_account_budget(3, next_y, next_m) == pytest.approx(base_value, rel=0.001)

        # Now a matching one
        execute_sql(
            "INSERT INTO config_assumptions "
            "(module, description, impact_type, impact_pct, category, "
            " start_date, end_date, is_active, created_by) "
            "VALUES ('expenses', 'admin +10%', 'increase', 10, 'admin', '2020-01-01', '2099-12-31', 1, 'test')"
        )
        assert bp.project_account_budget(3, next_y, next_m) == pytest.approx(base_value * 1.10, rel=0.001)


# ── Upsert semantics ──────────────────────────────────────────────────────

class TestSaveBudget:
    def test_insert_then_update(self, seeded_db):
        bp.save_budget(2027, 6, 3, 5000.0, source="manual")
        row = query_df(
            "SELECT target_value, source FROM config_budgets "
            "WHERE year=2027 AND month=6 AND account_id=3 AND module='expenses'"
        )
        assert len(row) == 1
        assert row["target_value"].iloc[0] == 5000.0

        bp.save_budget(2027, 6, 3, 7500.0, source="projected", notes="updated")
        row = query_df(
            "SELECT target_value, source, notes FROM config_budgets "
            "WHERE year=2027 AND month=6 AND account_id=3 AND module='expenses'"
        )
        assert len(row) == 1
        assert row["target_value"].iloc[0] == 7500.0
        assert row["source"].iloc[0] == "projected"
        assert row["notes"].iloc[0] == "updated"

    def test_delete_removes_row(self, seeded_db):
        bp.save_budget(2027, 7, 3, 1234.0)
        bp.delete_budget(2027, 7, 3)
        row = query_df(
            "SELECT 1 FROM config_budgets WHERE year=2027 AND month=7 AND account_id=3"
        )
        assert row.empty

    def test_save_many_skips_nulls(self, seeded_db):
        df = pd.DataFrame([
            {"year": 2027, "month": 1, "account_id": 3, "target_value": 100.0, "source": "manual"},
            {"year": 2027, "month": 2, "account_id": 3, "target_value": None, "source": "manual"},
            {"year": 2027, "month": 3, "account_id": 3, "target_value": 300.0, "source": "manual"},
        ])
        count = bp.save_many(df)
        assert count == 2


# ── expense_analytics override wiring ─────────────────────────────────────

class TestExpenseOverrideWiring:
    def test_override_wins_over_fact_budget(self, seeded_db):
        today = date.today()
        period = f"{today.year}-{today.month:02d}"

        before = ea.by_account(period)
        admin_row = before[before["account"].str.contains("Admin", case=False)]
        assert not admin_row.empty
        original_budget = float(admin_row["budget"].iloc[0])
        assert original_budget > 0

        bp.save_budget(today.year, today.month, 3, 1.0, source="manual")

        after = ea.by_account(period)
        admin_row = after[after["account"].str.contains("Admin", case=False)]
        assert float(admin_row["budget"].iloc[0]) == pytest.approx(1.0, rel=0.01)

    def test_fallback_when_no_override(self, seeded_db):
        today = date.today()
        period = f"{today.year}-{today.month:02d}"
        result = ea.by_account(period)
        # seed_db fixture tiene budget_amount poblado en fact_expenses → debería haber budget > 0
        assert (result["budget"] > 0).any()
