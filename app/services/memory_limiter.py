"""Memory limit enforcement for processes."""

import time
import subprocess
from typing import Tuple, Optional

# Only import psutil (Windows will use this)
import psutil

# Don't import resource at module level - import inside function instead


def set_limit_linux(memory_mb: int) -> None:
    """
    Set memory limit on Linux using kernel-level resource limits.
    
    This function must be called inside the child process (via preexec_fn)
    before the code execution begins. The kernel will automatically kill
    the process if it exceeds this limit.
    
    Args:
        memory_mb: Maximum memory allowed in megabytes
    """
    import resource  # Import here, only when function is called on Linux
    
    memory_bytes = memory_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))


def monitor_process_windows(
    process: subprocess.Popen,
    memory_limit_mb: int,
    timeout_seconds: float
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Monitor a Windows process for memory and timeout limits.
    
    Polls the process every 100ms to check:
    - If timeout exceeded -> kill and return timeout error
    - If memory exceeded -> kill and return memory error
    - If process completes -> return stdout/stderr
    
    Args:
        process: The subprocess.Popen instance to monitor
        memory_limit_mb: Maximum memory allowed in megabytes
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        Tuple of (stdout, stderr, error)
    """
    start_time = time.time()
    memory_limit_bytes = memory_limit_mb * 1024 * 1024
    
    while process.poll() is None:
        elapsed = time.time() - start_time
        
        # Check timeout
        if elapsed > timeout_seconds:
            process.kill()
            process.wait()
            return None, None, "execution timeout"
        
        # Check memory usage
        try:
            proc = psutil.Process(process.pid)
            memory_usage = proc.memory_info().rss
            if memory_usage > memory_limit_bytes:
                process.kill()
                process.wait()
                return None, None, "memory limit exceeded"
        except psutil.NoSuchProcess:
            break
        
        time.sleep(0.1)
    
    # Process finished naturally
    stdout, stderr = process.communicate()
    
    stdout = stdout if stdout else None
    stderr = stderr if stderr else None
    
    return stdout, stderr, None