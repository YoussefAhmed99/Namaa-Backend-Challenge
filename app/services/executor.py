import subprocess
from typing import Tuple, Optional


class CodeExecutor:
    """Executes Python code with resource limits (Level 2)."""
    
    TIMEOUT_SECONDS = 2
    MEMORY_LIMIT_MB = 100
    
    def execute(self, code: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Execute Python code with timeout and memory limits.
        
        Args:
            code: Python code string to execute
            
        Returns:
            Tuple of (stdout, stderr, error)
        """
        try:
            from .platform_utils import is_linux
            
            if is_linux():
                return self._execute_linux(code)
            else:
                return self._execute_windows(code)
                
        except Exception as e:
            return None, None, "Internal server error"
    
    def _execute_linux(self, code: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Execute on Linux with kernel-enforced memory limit.
        
        Strategy:
        - Use preexec_fn to set memory limit before code runs
        - Kernel kills process automatically if limit exceeded
        - subprocess.run handles timeout
        
        Returns:
            Tuple of (stdout, stderr, error)
        """
        try:
            from .memory_limiter import set_limit_linux
            
            def set_limits():
                set_limit_linux(self.MEMORY_LIMIT_MB)
            
            result = subprocess.run(
                ['python', '-c', code],
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
                preexec_fn=set_limits
            )
            
            stdout = result.stdout if result.stdout else None
            stderr = result.stderr if result.stderr else None
            
            return stdout, stderr, None
            
        except subprocess.TimeoutExpired:
            return None, None, "execution timeout"
            
        except Exception as e:
            error_msg = str(e).lower()
            if "memory" in error_msg or "killed" in error_msg:
                return None, None, "memory limit exceeded"
            return None, None, "Internal server error"
    
    def _execute_windows(self, code: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Execute on Windows with reactive memory monitoring.
        
        Strategy:
        - Spawn subprocess and delegate monitoring to memory_limiter
        - Monitor handles timeout and memory checks
        
        Returns:
            Tuple of (stdout, stderr, error)
        """
        try:
            from .memory_limiter import monitor_process_windows
            
            process = subprocess.Popen(
                ['python', '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return monitor_process_windows(
                process,
                self.MEMORY_LIMIT_MB,
                self.TIMEOUT_SECONDS
            )
            
        except Exception as e:
            return None, None, "Internal server error"