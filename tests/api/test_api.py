from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "db_row_counts" in data


def test_companies_endpoint():
    response = client.get("/api/v1/companies/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_company_profile():
    response = client.get("/api/v1/companies/HDFCBANK")

    assert response.status_code == 200

    data = response.json()
    assert data["ticker"] == "HDFCBANK"
    assert data["name"] == "HDFC Bank Ltd"
    assert "latest_kpis" in data


def test_company_not_found():
    response = client.get("/api/v1/companies/NOTACOMPANY")

    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"


def test_company_pl():
    response = client.get(
        "/api/v1/companies/HDFCBANK/pl",
        params={"from_year": 2020, "to_year": 2024}
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0
    assert data[0]["year"] == 2020
    assert data[-1]["year"] == 2024


def test_company_ratios():
    response = client.get(
        "/api/v1/companies/HDFCBANK/ratios",
        params={"year": 2024}
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["year"] == 2024
    assert "roe" in data[0]
    assert "pe" in data[0]


def test_screener_endpoint():
    response = client.get(
        "/api/v1/screener/",
        params={"min_roe": 10}
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sectors_endpoint():
    response = client.get("/api/v1/sectors/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0