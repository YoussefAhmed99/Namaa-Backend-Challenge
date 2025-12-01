"""Essential tests for Phase 3: Session persistence."""

import pytest
import requests
import time

BASE_URL = "http://localhost:8000"


class TestPhaseThree:
    
    def test_session_id_returned(self):
        """Test that every execution returns a session ID."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "x = 1"
        })
        assert response.status_code == 200
        data = response.json()
        print(f"DEBUG: Full response = {data}")  # ADD THIS
        assert "id" in data
        assert data["id"] is not None
        assert len(data["id"]) > 0
    
    def test_variable_persistence(self):
        """Test that variables persist within a session."""
        # Create session and set variable
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "my_var = 42"
        })
        assert response1.status_code == 200
        session_id = response1.json()["id"]
        
        # Access variable in same session
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "print(my_var)"
        })
        assert response2.status_code == 200
        assert response2.json()["stdout"] == "42\n"
        assert response2.json()["id"] == session_id
    
    def test_import_persistence(self):
        """Test that imports persist within a session."""
        # Import module
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "import math"
        })
        session_id = response1.json()["id"]
        
        # Use imported module
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "print(math.pi)"
        })
        assert response2.status_code == 200
        assert "3.14159" in response2.json()["stdout"]
    
    def test_function_persistence(self):
        """Test that function definitions persist within a session."""
        # Define function
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "def add(a, b):\n    return a + b"
        })
        session_id = response1.json()["id"]
        
        # Call function
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "print(add(10, 20))"
        })
        assert response2.status_code == 200
        assert response2.json()["stdout"] == "30\n"
    
    def test_session_not_found(self):
        """Test error when session ID doesn't exist."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "id": "nonexistent-session-id-12345",
            "code": "print('test')"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "session not found"
        assert data.get("stdout") is None
        assert data.get("stderr") is None
    
    def test_session_isolation(self):
        """Test that different sessions are isolated from each other."""
        # Create first session
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "session_var = 'session1'"
        })
        session1_id = response1.json()["id"]
        
        # Create second session
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "code": "session_var = 'session2'"
        })
        session2_id = response2.json()["id"]
        
        # Verify they have different IDs
        assert session1_id != session2_id
        
        # Check first session variable
        response3 = requests.post(f"{BASE_URL}/execute", json={
            "id": session1_id,
            "code": "print(session_var)"
        })
        assert response3.json()["stdout"] == "session1\n"
        
        # Check second session variable
        response4 = requests.post(f"{BASE_URL}/execute", json={
            "id": session2_id,
            "code": "print(session_var)"
        })
        assert response4.json()["stdout"] == "session2\n"
    
    def test_session_cannot_access_other_session_variables(self):
        """Test that one session cannot access another session's variables."""
        # Create session 1 with variable
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "secret = 'session1_secret'"
        })
        session1_id = response1.json()["id"]
        
        # Create session 2 and try to access session 1's variable
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "code": "print(secret)"
        })
        session2_id = response2.json()["id"]
        
        # Should get NameError
        assert session2_id != session1_id
        assert response2.json().get("stderr") is not None
        assert "NameError" in response2.json()["stderr"]
    
    def test_crashed_session_isolated(self):
        """Test that crashing one session doesn't affect others."""
        # Create session 1
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "safe_var = 'safe'"
        })
        session1_id = response1.json()["id"]
        
        # Create session 2 and crash it
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "code": "import os; os._exit(1)"
        })
        session2_id = response2.json()["id"]
        
        # Session 1 should still work
        response3 = requests.post(f"{BASE_URL}/execute", json={
            "id": session1_id,
            "code": "print(safe_var)"
        })
        assert response3.status_code == 200
        assert response3.json()["stdout"] == "safe\n"
    
    def test_session_survives_errors(self):
        """Test that a session survives exceptions and can continue."""
        # Create session
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "counter = 0"
        })
        session_id = response1.json()["id"]
        
        # Cause an error
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "1 / 0"
        })
        assert "ZeroDivisionError" in response2.json()["stderr"]
        
        # Session should still work
        response3 = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "counter += 1; print(counter)"
        })
        assert response3.json()["stdout"] == "1\n"
    
    def test_multiple_executions_in_session(self):
        """Test multiple sequential executions in same session."""
        # Create session
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "numbers = []"
        })
        session_id = response1.json()["id"]
        
        # Add to list multiple times
        for i in range(5):
            response = requests.post(f"{BASE_URL}/execute", json={
                "id": session_id,
                "code": f"numbers.append({i})"
            })
            assert response.status_code == 200
        
        # Verify all additions
        response_final = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "print(numbers)"
        })
        assert response_final.json()["stdout"] == "[0, 1, 2, 3, 4]\n"
    
    def test_concurrent_sessions(self):
        """Test that multiple sessions can be created concurrently."""
        session_ids = []
        
        # Create 5 sessions concurrently
        for i in range(5):
            response = requests.post(f"{BASE_URL}/execute", json={
                "code": f"value = {i * 10}"
            })
            assert response.status_code == 200
            session_ids.append(response.json()["id"])
        
        # Verify all sessions are unique
        assert len(session_ids) == len(set(session_ids))
        
        # Verify each session has its own value
        for i, sid in enumerate(session_ids):
            response = requests.post(f"{BASE_URL}/execute", json={
                "id": sid,
                "code": "print(value)"
            })
            assert response.json()["stdout"] == f"{i * 10}\n"
    
    def test_session_with_timeout_still_returns_id(self):
        """Test that even timeout errors return a session ID."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "while True: pass"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "execution timeout"
        assert "id" in data
        assert data["id"] is not None
    
    def test_session_with_memory_limit_still_returns_id(self):
        """Test that even memory errors return a session ID."""
        response = requests.post(f"{BASE_URL}/execute", json={
            "code": "x = bytearray(150 * 1024 * 1024); x[0] = 1"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["error"] == "memory limit exceeded"
        assert "id" in data
        assert data["id"] is not None
    
    def test_class_persistence(self):
        """Test that class definitions persist in sessions."""
        # Define class
        response1 = requests.post(f"{BASE_URL}/execute", json={
            "code": "class Counter:\n    def __init__(self):\n        self.count = 0\n    def increment(self):\n        self.count += 1"
        })
        session_id = response1.json()["id"]
        
        # Create instance
        response2 = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "c = Counter()"
        })
        assert response2.status_code == 200
        
        # Use instance
        response3 = requests.post(f"{BASE_URL}/execute", json={
            "id": session_id,
            "code": "c.increment(); c.increment(); print(c.count)"
        })
        assert response3.json()["stdout"] == "2\n"


@pytest.fixture(scope="session", autouse=True)
def check_server():
    """Check server is running."""
    try:
        requests.get(f"{BASE_URL}/")
    except requests.ConnectionError:
        pytest.exit("Server not running! Start with: python run.py")