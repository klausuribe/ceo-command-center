"""Tests for analytics/kpi_calculator.py — KPI functions with edge cases."""

import pytest
from analytics.kpi_calculator import (
    sales_kpis, receivables_kpis, payables_kpis, inventory_kpis,
    expense_kpis, financial_kpis, cashflow_kpis, all_kpis,
)


class TestSalesKpis:
    def test_returns_expected_keys(self, seeded_db):
        result = sales_kpis()
        assert "revenue" in result
        assert "gross_profit" in result
        assert "mom_change_pct" in result
        assert "yoy_change_pct" in result
        assert "daily_velocity" in result

    def test_revenue_matches_data(self, seeded_db):
        result = sales_kpis()
        assert result["revenue"] == 2000.0  # 10 sales × 200

    def test_mom_change(self, seeded_db):
        result = sales_kpis()
        # Current: 2000, Previous: 800 → +150%
        assert result["mom_change_pct"] == 150.0

    def test_empty_db_returns_zeros(self, db):
        result = sales_kpis()
        assert result["revenue"] == 0
        assert result["mom_change_pct"] == 0
        assert result["yoy_change_pct"] == 0
        assert result["daily_velocity"] == 0


class TestReceivablesKpis:
    def test_returns_expected_keys(self, seeded_db):
        result = receivables_kpis()
        assert "total_balance" in result
        assert "dso" in result
        assert "aging" in result
        assert "top5_concentration_pct" in result

    def test_total_balance(self, seeded_db):
        result = receivables_kpis()
        assert result["total_balance"] == 2500.0  # 500 + 2000

    def test_empty_db(self, db):
        result = receivables_kpis()
        assert result["total_balance"] == 0
        assert result["top5_concentration_pct"] == 0


class TestPayablesKpis:
    def test_returns_expected_keys(self, seeded_db):
        result = payables_kpis()
        assert "total_balance" in result
        assert "dpo" in result
        assert "critical_count" in result
        assert "due_next_7d" in result

    def test_critical_count(self, seeded_db):
        result = payables_kpis()
        assert result["critical_count"] == 1

    def test_empty_db(self, db):
        result = payables_kpis()
        assert result["total_balance"] == 0
        assert result["critical_count"] == 0


class TestInventoryKpis:
    def test_returns_expected_keys(self, seeded_db):
        result = inventory_kpis()
        assert "total_value" in result
        assert "total_skus" in result
        assert "stockout_risk" in result
        assert "abc_distribution" in result

    def test_total_value(self, seeded_db):
        result = inventory_kpis()
        assert result["total_value"] == 1025.0  # 1000 + 25

    def test_stockout_risk(self, seeded_db):
        result = inventory_kpis()
        assert result["stockout_risk"] == 1  # Product B has 2.5 days < 7

    def test_empty_db(self, db):
        result = inventory_kpis()
        assert result["total_value"] == 0
        assert result["stockout_risk"] == 0


class TestExpenseKpis:
    def test_returns_expected_keys(self, seeded_db):
        result = expense_kpis()
        assert "total_expenses" in result
        assert "total_budget" in result
        assert "variance_pct" in result
        assert "by_category" in result

    def test_variance_calculation(self, seeded_db):
        result = expense_kpis()
        # total_variance = 500 + (-300) = 200
        # total_budget = 4500 + 1500 = 6000
        assert result["variance_pct"] == round(200 / 6000 * 100, 1)

    def test_empty_db_no_division_by_zero(self, db):
        result = expense_kpis()
        assert result["total_budget"] == 0
        assert result["variance_pct"] == 0


class TestFinancialKpis:
    def test_returns_expected_keys(self, seeded_db):
        result = financial_kpis()
        assert "revenue" in result
        assert "gross_margin_pct" in result
        assert "current_ratio" in result
        assert "roe" in result

    def test_margin_calculations(self, seeded_db):
        result = financial_kpis()
        assert result["revenue"] == 2000.0
        assert result["cogs"] == 1000.0
        assert result["gross_profit"] == 1000.0
        assert result["gross_margin_pct"] == 50.0

    def test_empty_db_no_division_by_zero(self, db):
        result = financial_kpis()
        assert result["revenue"] == 0
        assert result["gross_margin_pct"] == 0
        assert result["current_ratio"] == 0
        assert result["roe"] == 0
        assert result["debt_to_equity"] == 0


class TestCashflowKpis:
    def test_returns_expected_keys(self, seeded_db):
        result = cashflow_kpis()
        assert "current_balance" in result
        assert "month_inflow" in result
        assert "month_outflow" in result
        assert "avg_daily_net" in result
        assert "runway_days" in result

    def test_cash_positive_runway_none(self, seeded_db):
        result = cashflow_kpis()
        # Net flow is positive (500/day), so runway should be None
        assert result["runway_days"] is None

    def test_empty_db(self, db):
        result = cashflow_kpis()
        assert result["current_balance"] == 0
        assert result["runway_days"] is None


class TestAllKpis:
    def test_returns_all_modules(self, seeded_db):
        result = all_kpis()
        assert set(result.keys()) == {
            "sales", "receivables", "payables",
            "inventory", "expenses", "financial", "cashflow",
        }

    def test_each_module_is_dict(self, seeded_db):
        result = all_kpis()
        for module in result.values():
            assert isinstance(module, dict)
