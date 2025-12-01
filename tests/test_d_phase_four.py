"""Tests for Phase 4: Environment Hardening (Sandboxing)."""

import pytest
import requests

BASE_URL = "http://localhost:8000"


class TestPhaseFour:
    """Test sandboxing restrictions on filesystem and network operations."""
    
    # ============================================
    # Filesystem Restriction Tests
    # ============================================
    
    def test_os_remove_blocked(self):
        """Test os.remove() is blocked (matches PDF example exactly)."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "import os; os.remove('file.txt')"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should have session id
        assert "id" in data
        
        # Should have stderr (not error - it's a Python exception)
        assert "stderr" in data
        assert data["stderr"] is not None
        
        # Verify error details match spec
        assert "PermissionError" in data["stderr"]
        assert "[Errno 13]" in data["stderr"]
        assert "Permission denied" in data["stderr"]
        assert "'file.txt'" in data["stderr"]
    
    def test_builtin_open_blocked(self):
        """Test built-in open() is blocked."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "open('test.txt', 'w')"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "stderr" in data
        assert "PermissionError" in data["stderr"]
        assert "[Errno 13]" in data["stderr"]
        assert "Permission denied" in data["stderr"]
    
    def test_os_mkdir_blocked(self):
        """Test os.mkdir() is blocked."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "import os; os.mkdir('newdir')"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "stderr" in data
        assert "PermissionError" in data["stderr"]
        assert "[Errno 13]" in data["stderr"]
        assert "Permission denied" in data["stderr"]
    
    # ============================================
    # Network Restriction Tests
    # ============================================
    
    def test_socket_blocked(self):
        """Test socket.socket() is blocked."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "import socket; s = socket.socket()"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "stderr" in data
        assert "PermissionError" in data["stderr"]
        assert "[Errno 13]" in data["stderr"]
        assert "Permission denied" in data["stderr"]
    
    def test_urllib_blocked(self):
        """Test urllib.request.urlopen() is blocked."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "import urllib.request; urllib.request.urlopen('http://example.com')"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "stderr" in data
        assert "PermissionError" in data["stderr"]
    
    # ============================================
    # Safe Operations Still Work
    # ============================================
    
    def test_os_getcwd_works(self):
        """Test os.getcwd() still works (safe operation)."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "import os; print(os.getcwd())"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Should have stdout with directory path
        assert "stdout" in data
        assert data["stdout"] is not None
        # Should NOT have error or stderr
        assert data.get("stderr") is None
        assert data.get("error") is None
    
    def test_os_path_join_works(self):
        """Test os.path.join() still works (safe operation)."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "import os; print(os.path.join('a', 'b', 'c'))"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "stdout" in data
        assert "a" in data["stdout"] or "b" in data["stdout"]  # Path separator varies
        assert data.get("stderr") is None
        assert data.get("error") is None
    
    def test_math_works(self):
        """Test math operations still work."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "import math; print(math.sqrt(16))"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "stdout" in data
        assert "4.0" in data["stdout"]
    
    def test_computation_works(self):
        """Test normal computation still works."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "x = [1, 2, 3]; print(sum(x))"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "stdout" in data
        assert "6" in data["stdout"]
    
    # ============================================
    # Sandbox Persists Across Requests
    # ============================================
    
    def test_sandbox_persists_in_session(self):
        """Test sandbox restrictions persist across requests in same session."""
        # First request - create session with normal code
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "x = 5"
        })
        assert response1.status_code == 200
        session_id = response1.json()["id"]
        
        # Second request - try blocked operation in same session
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "open('file.txt', 'w')"
        })
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Sandbox should still be active
        assert "stderr" in data2
        assert "PermissionError" in data2["stderr"]
        
        # Should be same session
        assert data2["id"] == session_id


@pytest.fixture(scope="session", autouse=True)
def check_server():
    """Check server is running."""
    try:
        requests.get(f"{BASE_URL}/")
    except requests.ConnectionError:
        pytest.exit("Server not running! Start with: python run.py")