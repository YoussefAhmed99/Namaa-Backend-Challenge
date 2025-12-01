import uuid
import time
import threading
from typing import Dict, Tuple, Optional
from .session_process import SessionProcess


class SessionManager:
    """Manages persistent Python interpreter sessions (Singleton)."""
    
    _instance = None
    _lock = threading.Lock()
    
    MAX_SESSIONS = 40
    IDLE_TIMEOUT_SECONDS = 60
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize only once."""
        # Only initialize if not already initialized
        if hasattr(self, 'initialized'):
            return
        
        self.sessions: Dict[str, 'SessionProcess'] = {}
        self.locks: Dict[str, threading.Lock] = {}
        self.manager_lock = threading.Lock()
        
        # Start background cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
        
        self.initialized = True
    
    def execute(
        self, 
        code: str, 
        session_id: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
        """
        Execute code in a session.
        
        Args:
            code: Python code to execute
            session_id: Optional session ID (None = create new session)
            
        Returns:
            Tuple of (stdout, stderr, error, session_id)
        """
        # Case 1: No session_id provided → create new session
        if session_id is None:
            session_id = self._create_session()
            if session_id is None:
                return None, None, "max sessions reached", ""
        
        # Case 2: session_id provided but doesn't exist → error
        if session_id not in self.sessions:
            return None, None, "session not found", session_id
        
        # Case 3: session_id exists → use that session
        session = self.sessions[session_id]
        session_lock = self.locks[session_id]
        
        # Lock this session (one execution at a time per session)
        with session_lock:
            # Update last accessed time
            session.last_accessed = time.time()
            
            # Execute in the session
            stdout, stderr, error = session.execute(code)
            
            return stdout, stderr, error, session_id
    
    def _create_session(self) -> Optional[str]:
        """
        Create new session.
        
        Returns:
            New session UUID, or None if max sessions reached
        """
        with self.manager_lock:
            # Check if we've hit the limit
            if len(self.sessions) >= self.MAX_SESSIONS:
                return None
            
            # Generate new UUID
            session_id = str(uuid.uuid4())
            
            # Create SessionProcess (assumes it exists)
            session = SessionProcess()
            
            # Store session and its lock
            self.sessions[session_id] = session
            self.locks[session_id] = threading.Lock()
            
            return session_id
    
    def _cleanup_loop(self):
        """Background thread that removes stale sessions."""
        while True:
            time.sleep(self.IDLE_TIMEOUT_SECONDS)
            self._cleanup_stale_sessions()
    
    def _cleanup_stale_sessions(self):
        """Remove sessions idle longer than IDLE_TIMEOUT_SECONDS."""
        now = time.time()
        
        with self.manager_lock:
            stale_sessions = [
                sid for sid, session in self.sessions.items()
                if now - session.last_accessed > self.IDLE_TIMEOUT_SECONDS
            ]
            
            for sid in stale_sessions:
                self._remove_session(sid)
    
    def _remove_session(self, session_id: str):
        """
        Remove a session and clean up resources.
        
        Args:
            session_id: Session ID to remove
        """
        if session_id in self.sessions:
            # Terminate the session process
            session = self.sessions[session_id]
            session.terminate()
            
            # Remove from dictionaries
            del self.sessions[session_id]
            del self.locks[session_id]