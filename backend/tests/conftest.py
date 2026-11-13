import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_tmp = tempfile.mkdtemp()
os.environ["FORESIGHT_DB"] = str(Path(_tmp) / "test.db")
os.environ["FORESIGHT_DIST"] = str(Path(_tmp) / "no-dist")

from app import db  # noqa: E402
from app.seed import load  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    load.seed()
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


@pytest.fixture
def conn():
    with db.session() as c:
        yield c
