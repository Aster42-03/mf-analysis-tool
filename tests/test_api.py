import pytest
from fastapi.testclient import TestClient

from app.main import app


# Creating Fake Browser
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


# Functions to Test The Root Endpoint
def test_root_endpoint_returns_200(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello"}


def test_get_fund(client):
    response = client.get("/fund/100034")

    assert response.status_code == 200
    assert response.json() == {
        "House": "Aditya Birla Sun Life Mutual Fund",
        "Type": "Open Ended Schemes",
        "Category": "Equity Scheme - Large & Mid Cap Fund",
        "Code": 100034,
        "Name": "Aditya Birla Sun Life Large & Mid Cap Fund -Regular - IDCW",
        "Start Date": "2006-04-03",
    }


def test_get_fund_not_found(client):
    response = client.get("/fund/999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Fund not Found"}
