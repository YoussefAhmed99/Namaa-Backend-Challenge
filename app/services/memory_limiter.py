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
    process,
    memory_limit_mb: int,
    memory_exceeded_callback
) -> None:
    """
    Monitor a multiprocessing.Process for memory limits on Windows.
    
    Runs in a separate thread, polls every 100ms.
    Calls callback and kills process if memory limit exceeded.
    
    Args:
        process: The multiprocessing.Process instance to monitor
        memory_limit_mb: Maximum memory allowed in megabytes
        memory_exceeded_callback: Function to call when limit exceeded
    """
    memory_limit_bytes = memory_limit_mb * 1024 * 1024
    
    while process.is_alive():
        try:
            proc = psutil.Process(process.pid)
            memory_usage = proc.memory_info().rss
            
            if memory_usage > memory_limit_bytes:
                # Memory limit exceeded - call callback and kill process
                memory_exceeded_callback()
                process.terminate()
                process.join(timeout=1)
                if process.is_alive():
                    process.kill()
                break
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # Process died or can't access - stop monitoring
            break
        
        time.sleep(0.1)