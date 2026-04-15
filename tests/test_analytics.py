"""Tests for analytics detail modules — edge cases and data integrity."""

import pytest
import pandas as pd
from analytics import (
    sales_analytics as sa,
    receivables_analytics as ra,
    payables_analytics as pa,
    inventory_analytics as ia,
    expense_analytics as ea,
    financial_analytics as fa,
    cashflow_analytics as ca,
)


class TestSalesAnalytics:
    def test_monthly_trend_returns_dataframe(self, seeded_db):
        result = sa.monthly_trend()
        assert isinstance(result, pd.DataFrame)
        assert "revenue" in result.columns
        assert len(result) >= 1

    def test_by_category(self, seeded_db):
        result = sa.by_category()
        assert not result.empty
        assert set(result["category"]) == {"Cat1", "Cat2"}

    def test_pareto_products_empty(self, db):
        result = sa.pareto_products()
        assert result.empty

    def test_pareto_products_cumulative(self, seeded_db):
        result = sa.pareto_products()
        assert "cumulative_pct" in result.columns
        # Last row cumulative should be ~100%
        assert abs(result["cumulative_pct"].iloc[-1] - 100.0) < 0.1

    def test_seller_performance(self, seeded_db):
        result = sa.seller_performance()
        assert not result.empty
        assert "target_monthly" in result.columns

    def test_rfm_empty(self, db):
        result = sa.rfm_analysis()
        assert result.empty

    def test_rfm_segments(self, seeded_db):
        result = sa.rfm_analysis()
        assert "rfm_segment" in result.columns
        assert all(s in ["Champions", "Loyal", "At Risk", "Lost"] for s in result["rfm_segment"])

    def test_top_products(self, seeded_db):
        result = sa.top_products(n=5)
        assert len(result) <= 5
        assert not result.empty


class TestReceivablesAnalytics:
    def test_aging_summary(self, seeded_db):
        result = ra.aging_summary()
        assert not result.empty
        assert "aging_bucket" in result.columns

    def test_top_debtors(self, seeded_db):
        result = ra.top_debtors(n=5)
        assert not result.empty
        assert result.iloc[0]["balance"] >= result.iloc[-1]["balance"]

    def test_credit_score_empty(self, db):
        result = ra.credit_score()
        assert result.empty

    def test_credit_score_range(self, seeded_db):
        result = ra.credit_score()
        assert not result.empty
        assert all(0 <= s <= 100 for s in result["score"])
        assert all(r in ["Bajo", "Medio", "Alto"] for r in result["risk_level"])

    def test_collection_rate_trend(self, seeded_db):
        result = ra.collection_rate_trend()
        assert isinstance(result, pd.DataFrame)


class TestPayablesAnalytics:
    def test_aging_summary(self, seeded_db):
        result = pa.aging_summary()
        assert not result.empty

    def test_by_vendor(self, seeded_db):
        result = pa.by_vendor()
        assert not result.empty

    def test_payment_priority_empty(self, db):
        result = pa.payment_priority_matrix()
        assert result.empty

    def test_payment_priority_score(self, seeded_db):
        result = pa.payment_priority_matrix()
        assert not result.empty
        assert "urgency_score" in result.columns

    def test_cash_vs_payables(self, seeded_db):
        result = pa.cash_vs_payables()
        assert "cash_available" in result
        assert "coverage_7d" in result
        assert isinstance(result["coverage_7d"], bool)


class TestInventoryAnalytics:
    def test_abc_classification_empty(self, db):
        result = ia.abc_classification()
        assert result.empty

    def test_abc_classification(self, seeded_db):
        result = ia.abc_classification()
        assert not result.empty
        assert "abc_value" in result.columns
        assert all(v in ["A", "B", "C"] for v in result["abc_value"])

    def test_critical_levels(self, seeded_db):
        result = ia.critical_levels()
        assert isinstance(result, dict)
        assert "below_reorder" in result
        assert "zero_stock" in result
        assert "overstock" in result
        assert "dead_stock" in result

    def test_reorder_suggestions(self, seeded_db):
        result = ia.reorder_suggestions()
        assert isinstance(result, pd.DataFrame)

    def test_inventory_value_by_category(self, seeded_db):
        result = ia.inventory_value_by_category()
        assert not result.empty


class TestExpenseAnalytics:
    def test_monthly_trend(self, seeded_db):
        result = ea.monthly_trend()
        assert not result.empty
        assert "actual" in result.columns
        assert "budget" in result.columns

    def test_by_cost_center_empty(self, db):
        result = ea.by_cost_center()
        assert result.empty

    def test_by_cost_center_status(self, seeded_db):
        result = ea.by_cost_center()
        assert not result.empty
        assert "status" in result.columns
        assert all(s in ["🔴", "🟡", "🟢"] for s in result["status"])

    def test_anomalies_empty(self, db):
        result = ea.anomalies()
        assert result.empty

    def test_fixed_vs_variable(self, seeded_db):
        result = ea.fixed_vs_variable()
        assert not result.empty


class TestFinancialAnalytics:
    def test_income_statement(self, seeded_db):
        result = fa.income_statement()
        assert not result.empty
        assert "parent_group" in result.columns

    def test_balance_sheet(self, seeded_db):
        result = fa.balance_sheet()
        assert not result.empty

    def test_common_size_empty(self, db):
        result = fa.common_size_analysis()
        assert result.empty

    def test_common_size_pct(self, seeded_db):
        result = fa.common_size_analysis()
        assert "pct_of_revenue" in result.columns

    def test_efficiency_ratios(self, seeded_db):
        result = fa.efficiency_ratios()
        assert "dso" in result
        assert "dpo" in result
        assert "ccc" in result
        assert result["interpretation"] in ["Eficiente", "Normal", "Lento — capital atrapado"]

    def test_period_comparison_missing_period(self, seeded_db):
        result = fa.period_comparison("2020-01", "2020-02")
        assert result.empty


class TestCashflowAnalytics:
    def test_daily_balance(self, seeded_db):
        result = ca.daily_balance()
        assert not result.empty
        assert "balance" in result.columns

    def test_monthly_summary(self, seeded_db):
        result = ca.monthly_summary()
        assert not result.empty

    def test_waterfall_monthly(self, seeded_db):
        result = ca.waterfall_monthly()
        assert not result.empty
        assert result.iloc[0]["item"] == "Saldo Inicial"
        assert result.iloc[-1]["item"] == "Saldo Final"

    def test_projection_empty(self, db):
        result = ca.projection()
        assert result.empty

    def test_projection_has_scenarios(self, seeded_db):
        result = ca.projection(days=10)
        assert not result.empty
        assert "balance_base" in result.columns
        assert "balance_optimistic" in result.columns
        assert "balance_pessimistic" in result.columns

    def test_breakeven_days_cash_positive(self, seeded_db):
        result = ca.breakeven_days()
        # With positive net flow, should be None
        assert result is None

    def test_seasonal_pattern(self, seeded_db):
        result = ca.seasonal_pattern()
        assert isinstance(result, pd.DataFrame)
