import pytest
from fastapi.testclient import TestClient

from app.main import app

# Creating Fake Browser
client = TestClient(app)


# Functions to Test The Root Endpoint
def test_root_endpoint_returns_200():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}


def test_get_fund():
    response = client.get("/fund/100034")

    assert response.status_code == 200
    response.json() ==
