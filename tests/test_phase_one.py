"""Essential tests for Phase 1: Basic execution."""

import pytest
import requests

BASE_URL = "http://localhost:8000"


class TestPhaseOne:
    
    def test_stdout(self):
        """Test print returns stdout."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "print('Hello')"
        })
        assert response.status_code == 200
        assert response.json()["stdout"] == "Hello\n"
    
    def test_stderr(self):
        """Test error returns stderr."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "1 / 0"
        })
        assert response.status_code == 200
        data = response.json()
        assert "stderr" in data
        assert "ZeroDivisionError" in data["stderr"]
    
    def test_no_output(self):
        """Test code with no output."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "x = 5"
        })
        assert response.status_code == 200
        data = response.json()
        # Level 3: id is always present, check only output fields
        assert data.get("stdout") is None
        assert data.get("stderr") is None
        assert data.get("error") is None
        assert "id" in data  # Session ID should always be present
    
    def test_syntax_error(self):
        """Test syntax error returns stderr."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "print('unclosed"
        })
        assert response.status_code == 200
        assert "SyntaxError" in response.json()["stderr"]
    
    def test_empty_code_rejected(self):
        """Test empty code is rejected."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": ""
        })
        assert response.status_code == 422


@pytest.fixture(scope="session", autouse=True)
def check_server():
    """Check server is running."""
    try:
        requests.get(f"{BASE_URL}/")
    except requests.ConnectionError:
        pytest.exit("Server not running! Start with: python run.py")