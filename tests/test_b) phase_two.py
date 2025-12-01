"""Essential tests for Phase 2: Resource limits."""

import pytest
import requests
import time

BASE_URL = "http://localhost:8000"


class TestPhaseTwo:
    
    def test_timeout(self):
        """Test infinite loop triggers timeout."""
        start = time.time()
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "while True: pass"
        })
        elapsed = time.time() - start

        assert response.status_code == 200
        
        # DEBUG: Print full response
        print(f"\nDEBUG - Full response: {response.json()}")
        print(f"DEBUG - Elapsed time: {elapsed}")
        
        assert response.json()["error"] == "execution timeout"
    
    def test_memory_limit(self):
        """Test large allocation triggers memory limit."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "x = bytearray(150 * 1024 * 1024); x[0] = 1"
        })
        assert response.status_code == 200
        assert response.json()["error"] == "memory limit exceeded"
    
    def test_normal_with_limits(self):
        """Test normal code works with limits active."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "print('ok')"
        })
        assert response.status_code == 200
        assert response.json()["stdout"] == "ok\n"
    
    def test_sleep_within_limit(self):
        """Test short sleep works."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "import time; time.sleep(1); print('done')"
        })
        assert response.status_code == 200
        assert response.json()["stdout"] == "done\n"
    
    def test_small_memory_allocation(self):
        """Test small allocation works."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "x = bytearray(10 * 1024 * 1024); print('ok')"
        })
        assert response.status_code == 200
        assert response.json()["stdout"] == "ok\n"


@pytest.fixture(scope="session", autouse=True)
def check_server():
    """Check server is running."""
    try:
        requests.get(f"{BASE_URL}/")
    except requests.ConnectionError:
        pytest.exit("Server not running! Start with: python run.py")