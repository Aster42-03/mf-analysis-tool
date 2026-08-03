import os

import pytest

from app.database import verify_conn


@pytest.fixture
def test_db_conn():
    url = verify_conn(os.getenv("DB_URL"))
    assert url == "postgresql+asyncpg://aster:wrong_password@db:5432/mf_data"


def test_bad_conn():
    with pytest.raises(ValueError):
        verify_conn(os.getenv("BAD_DB_URL"))
