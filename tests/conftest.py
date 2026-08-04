import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings


async def _ping_db():
    temp_engine = create_async_engine( settings.db_url )
    try:
        async with temp_engine.connect() as conn:
            await conn.execute( text( "SELECT 1" ) )
    finally:
        await temp_engine.dispose()


@pytest.fixture( scope = 'session', autouse = True )
def test_db_conn():
    try:
        asyncio.run( _ping_db() )
    except Exception as e:
        pytest.fail( f"Connection To DataBase Failed. Error: {e}" )


# Creating Fake Browser
@pytest.fixture( scope = "module" )
def client():
    with TestClient( app ) as test_client:
        yield test_client
