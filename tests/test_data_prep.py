"""Unit tests for the data-preparation functions."""

import pandas as pd

import data_prep

# Known-good values present in the cleaned dataset.
HADM = 145834
ITEMID = 50893          # Calcium, Total - has abnormal readings for HADM 145834
SUBJECT = 3
MISSING_HADM = -999     # not present -> empty results


def test_get_abnormal_results_returns_only_abnormal():
    result = data_prep.get_abnormal_results(HADM)
    assert not result.empty
    assert list(result.columns) == ["HADM_ID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME", "FLAG"]
    assert (result["FLAG"] == "abnormal").all()


def test_get_latest_lab_value_returns_single_row():
    result = data_prep.get_latest_lab_value(HADM, ITEMID)
    assert len(result) == 1
    assert "VALUENUM" in result.columns


def test_get_lab_trend_is_time_sorted():
    result = data_prep.get_lab_trend(HADM, ITEMID)
    times = pd.to_datetime(result["CHARTTIME"], errors="coerce")
    assert times.is_monotonic_increasing


def test_get_all_lab_tests_columns():
    result = data_prep.get_all_lab_tests(HADM)
    assert not result.empty
    assert list(result.columns) == ["HADM_ID", "ITEMID", "LABEL", "CHARTTIME"]


def test_compare_first_last_difference_is_consistent():
    result = data_prep.compare_first_last_values(HADM, ITEMID)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["Difference"] == row["Last Value"] - row["First Value"]


def test_get_lab_summary_stats_bounds():
    result = data_prep.get_lab_summary_stats(HADM, ITEMID)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["Count"] >= 1
    assert row["Min"] <= row["Max"]


def test_count_abnormal_vs_normal_adds_up():
    result = data_prep.count_abnormal_vs_normal(HADM)
    row = result.iloc[0]
    assert row["Total Tests"] == row["Abnormal"] + row["Normal"]


def test_get_abnormal_results_for_lab_only_abnormal():
    result = data_prep.get_abnormal_results_for_lab(HADM, ITEMID)
    assert not result.empty
    assert (result["FLAG"] == "abnormal").all()


def test_get_abnormal_tests_summary_counts():
    result = data_prep.get_abnormal_tests_summary(HADM)
    assert list(result.columns) == ["HADM_ID", "ITEMID", "LABEL", "Abnormal Count"]
    assert (result["Abnormal Count"] >= 1).all()


def test_get_lab_values_in_range_filters_dates():
    result = data_prep.get_lab_values_in_range(HADM, ITEMID, "2101-10-20", "2101-10-22")
    times = pd.to_datetime(result["CHARTTIME"], errors="coerce")
    assert times.is_monotonic_increasing
    assert (times.dt.date >= pd.Timestamp("2101-10-20").date()).all()


def test_get_patient_admissions_renames_subject():
    result = data_prep.get_patient_admissions(SUBJECT)
    assert not result.empty
    assert "SUBJECT_ID" in result.columns
    assert "DIAGNOSIS" in result.columns


def test_get_abnormal_counts_all_admissions_summary():
    result = data_prep.get_abnormal_counts_all_admissions()
    assert not result.empty
    assert list(result.columns) == ["HADM_ID", "Total Tests", "Abnormal", "Normal"]
    # one row per admission, counts add up, sorted by most abnormal first
    assert result["HADM_ID"].is_unique
    assert (result["Abnormal"] + result["Normal"] == result["Total Tests"]).all()
    assert result["Abnormal"].is_monotonic_decreasing
    # the dataset-wide row for an admission must match the per-admission view (Q7)
    q7 = data_prep.count_abnormal_vs_normal(HADM).iloc[0]
    row = result[result["HADM_ID"] == HADM].iloc[0]
    assert row["Abnormal"] == q7["Abnormal"]
    assert row["Total Tests"] == q7["Total Tests"]


# --- edge cases (no data) ---
def test_abnormal_results_empty_for_missing_admission():
    assert data_prep.get_abnormal_results(MISSING_HADM).empty


def test_summary_stats_empty_for_missing_admission():
    assert data_prep.get_lab_summary_stats(MISSING_HADM, ITEMID).empty


def test_patient_admissions_empty_for_missing_patient():
    assert data_prep.get_patient_admissions(MISSING_HADM).empty
