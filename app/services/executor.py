import subprocess
from typing import Tuple, Optional


class CodeExecutor:
    """Executes Python code in a subprocess."""
    
    def execute(self, code: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Execute Python code.
        
        Args:
            code: Python code string to execute
            
        Returns:
            Tuple of (stdout, stderr, error)
        """
        try:
            # Run Python code as subprocess
            result = subprocess.run(
                ['python', '-c', code],
                capture_output=True,
                text=True
            )
            
            # Extract output
            stdout = result.stdout if result.stdout else None
            stderr = result.stderr if result.stderr else None
            
            return stdout, stderr, None
            
        except Exception as e:
            return None, None, "Internal server error"