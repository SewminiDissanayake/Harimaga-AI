"""
Shared pytest setup for HariMaga.

Run all tests from the project folder:
    pytest
"""
import os
import sys
import tempfile
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "webapp" / "backend"))

# Tests must never touch real evidence, and must not be rate limited.
os.environ["HARIMAGA_RUNTIME_DIR"] = tempfile.mkdtemp(prefix="harimaga_test_")
os.environ["HARIMAGA_RATE_LIMIT"] = "0"

warnings.filterwarnings("ignore", message=".*Trying to unpickle.*")


@pytest.fixture(scope="session")
def harimaga():
    import app as harimaga_app
    return harimaga_app


@pytest.fixture()
def client(harimaga):
    return harimaga.app.test_client()


@pytest.fixture(scope="session")
def classifier():
    from nlp.robust_issue_classifier import RobustIssueClassifier
    return RobustIssueClassifier()
