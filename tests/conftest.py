import os

import pytest
from fastapi.testclient import TestClient
from app.database import engine, verify_conn
from app.main import app


@pytest.fixture( scope = 'session', autouse = True )
def test_db_conn():
    url = verify_conn( os.getenv( 'DB_URL' ) )
    assert url == "postgresql+asyncpg://aster:aster42@localhost:5434/mf_data"


# Creating Fake Browser
@pytest.fixture( scope = "module" )
def client():
    with TestClient( app ) as test_client:
        yield test_client
