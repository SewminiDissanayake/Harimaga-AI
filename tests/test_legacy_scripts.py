"""
Runs the older one-file test scripts in scripts/ so they keep being checked.
Each script exits with an error if one of its asserts fails.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

LEGACY = """
test_bus_complaint_noisy_singlish_v1 test_bus_jurisdiction_v2 test_civic_quotes_v8_2
test_clean_professional_v8 test_complaint_draft_fix_v8_3_1 test_complaint_router
test_consumer_complaint_v1 test_deep_island_privacy_v7_2
test_electricity_noisy_singlish_v1 test_electricity_noisy_singlish_v1_1
test_final_safety_disaster_categories_v1 test_harimaga_unified_dependencies_v1
test_issue_classifier test_issue_specific_channel_service test_local_authority_choice_fix
test_local_authority_contact_service test_local_road_channel_service
test_lost_document_id_shortform_v1_2 test_lost_document_precedence_v1_1 test_lost_document_v1
test_road_robustness_ukuwela_v2 test_water_provider_channel_service
test_women_child_safety_noisy_v1_1 test_women_child_safety_noisy_v1_2 test_women_child_safety_noisy_v1_3
""".split()
# Not included: test_deep_island_privacy_v7 (replaced by v7_2, which handles
# Windows keeping a previewed file open) and older scripts that check UI
# versions which no longer exist.


@pytest.mark.parametrize("name", LEGACY)
def test_legacy_script(name):
    # UTF-8 mode: on Windows, printing Sinhala text otherwise crashes the script
    env = dict(os.environ, PYTHONWARNINGS="ignore", PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / f"{name}.py")],
        cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
