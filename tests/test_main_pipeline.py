"""Tests for the end-to-end template pipeline, including the demo typo injection."""

import main_pipeline

HADM = 107521
ITEMID = 51221  # Hematocrit for HADM 107521


def test_run_pipeline_normal_has_no_correction():
    result = main_pipeline.run_pipeline(3, {"hadm_id": HADM, "itemid": ITEMID})
    assert result["success"]
    assert not result["correction_applied"]
    assert len(result["attempts"]) == 1


def test_run_pipeline_inject_typo_triggers_correction():
    result = main_pipeline.run_pipeline(
        3, {"hadm_id": HADM, "itemid": ITEMID}, inject_typo=True
    )
    assert result["success"]
    assert result["correction_applied"]
    assert len(result["attempts"]) == 2
    # The first attempt used the misspelled name and failed; the second was fixed.
    assert not result["attempts"][0]["execution"]["success"]
    assert "get_lab_trends" in result["attempts"][0]["code"]
    assert "get_lab_trend(" in result["final_code"]
