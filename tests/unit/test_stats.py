"""Tests for statistical drift detection — PSI, KS-test, type mismatch."""
import pytest
from backend.stats import (
    population_stability_index,
    ks_test,
    feature_drift_score,
    type_mismatch_check,
)


class TestPSI:
    def test_no_drift_identical_distributions(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = population_stability_index(data, data)
        assert result.drifted is False
        assert result.value < 0.01

    def test_drift_shifted_distribution(self):
        reference = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        current = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        result = population_stability_index(reference, current)
        assert result.drifted is True
        assert result.value > 0.2

    def test_empty_data(self):
        result = population_stability_index([], [1, 2, 3])
        assert result.drifted is False
        assert "Insufficient" in result.detail

    def test_zero_variance(self):
        result = population_stability_index([5, 5, 5, 5], [5, 5, 5, 5])
        assert result.drifted is False


class TestKS:
    def test_no_drift_identical(self):
        data = [1, 2, 3, 4, 5]
        result = ks_test(data, data)
        assert result.drifted is False
        assert result.value == 0.0

    def test_drift_shifted(self):
        reference = [1, 2, 3, 4, 5]
        current = [10, 11, 12, 13, 14]
        result = ks_test(reference, current)
        assert result.drifted is True
        assert result.value > 0.5

    def test_empty_data(self):
        result = ks_test([], [1, 2, 3])
        assert result.drifted is False


class TestFeatureDriftScore:
    def test_no_drift(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = feature_drift_score(data, data)
        assert result["drifted"] is False
        assert result["combined_score"] < 0.1

    def test_drift(self):
        reference = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        current = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
        result = feature_drift_score(reference, current)
        assert result["drifted"] is True
        assert result["combined_score"] > 0.5

    def test_returns_metrics(self):
        data = [1, 2, 3, 4, 5]
        result = feature_drift_score(data, data)
        assert "psi" in result
        assert "ks" in result
        assert "combined_score" in result


class TestTypeMismatchCheck:
    def test_no_mismatch(self):
        ref = [{"name": "a", "type": "INT"}, {"name": "b", "type": "STRING"}]
        cur = [{"name": "a", "type": "INT"}, {"name": "b", "type": "STRING"}]
        result = type_mismatch_check(ref, cur)
        assert result["drifted"] is False
        assert result["count"] == 0

    def test_type_changed(self):
        ref = [{"name": "age", "type": "INT"}]
        cur = [{"name": "age", "type": "STRING"}]
        result = type_mismatch_check(ref, cur)
        assert result["drifted"] is True
        assert result["count"] == 1
        assert result["mismatches"][0]["reference_type"] == "INT"
        assert result["mismatches"][0]["current_type"] == "STRING"

    def test_column_missing(self):
        ref = [{"name": "a", "type": "INT"}, {"name": "b", "type": "STRING"}]
        cur = [{"name": "a", "type": "INT"}]
        result = type_mismatch_check(ref, cur)
        assert result["drifted"] is True
        assert result["mismatches"][0]["current_type"] == "MISSING"

    def test_new_column(self):
        ref = [{"name": "a", "type": "INT"}]
        cur = [{"name": "a", "type": "INT"}, {"name": "new_col", "type": "FLOAT"}]
        result = type_mismatch_check(ref, cur)
        assert result["drifted"] is True
        assert result["mismatches"][0]["reference_type"] == "MISSING"
