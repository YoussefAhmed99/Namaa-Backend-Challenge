"""Memory limit enforcement via active polling."""

import time
import psutil


def monitor_process(
    process,
    memory_limit_mb: int,
    memory_exceeded_callback
) -> None:
    """
    Monitor a multiprocessing.Process for memory limits.
    
    Runs in a separate thread, polls every 100ms.
    Calls callback and kills process if memory limit exceeded.
    Used on both Windows and Linux.
    
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