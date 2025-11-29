import time
import sys
import io
import threading
import multiprocessing
from multiprocessing import Process, Queue
from code import InteractiveInterpreter
from typing import Tuple, Optional
from .platform_utils import is_linux
from .memory_limiter import set_limit_linux, monitor_process_windows

# Import psutil for Windows monitoring
try:
    import psutil
except ImportError:
    psutil = None


class SessionProcess:
    """Manages a single persistent interpreter session in a separate process."""
    
    TIMEOUT_SECONDS = 2
    MEMORY_LIMIT_MB = 100
    
    def __init__(self):
        """Initialize session and spawn worker process."""
        self.last_accessed = time.time()
        self.memory_exceeded = False
        
        # Create communication queues
        self.input_queue = Queue()
        self.output_queue = Queue()
        
        # Spawn worker process
        self.process = Process(
            target=worker_function,
            args=(self.input_queue, self.output_queue, self.MEMORY_LIMIT_MB)
        )
        self.process.start()
        
        # Start memory monitoring thread on Windows
        if not is_linux() and psutil:
            def on_memory_exceeded():
                self.memory_exceeded = True
            
            self.monitor_thread = threading.Thread(
                target=monitor_process_windows,
                args=(self.process, self.MEMORY_LIMIT_MB, on_memory_exceeded),
                daemon=True
            )
            self.monitor_thread.start()
            
    def execute(self, code: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Execute code in the persistent interpreter.
        
        Args:
            code: Python code to execute
            
        Returns:
            Tuple of (stdout, stderr, error)
        """
        # Check if memory was exceeded (Windows monitoring)
        if self.memory_exceeded:
            return None, None, "memory limit exceeded"
        
        # Check if worker process is still alive
        if not self.process.is_alive():
            return None, None, "session crashed"
        
        try:
            # Send code to worker
            self.input_queue.put(code)
            
            # Wait for results with timeout
            try:
                result = self.output_queue.get(timeout=self.TIMEOUT_SECONDS)
                stdout, stderr, error = result
                return stdout, stderr, error
                
            except Exception as timeout_ex:
                # Timeout - kill the worker process
                if "Empty" in timeout_ex.__class__.__name__:
                    self.process.terminate()
                    self.process.join(timeout=1)
                    if self.process.is_alive():
                        self.process.kill()
                    
                    # Check if it was actually memory exceeded (Windows race condition)
                    if self.memory_exceeded:
                        return None, None, "memory limit exceeded"
                    
                    return None, None, "execution timeout"
                else:
                    raise
                
        except Exception as e:
            return None, None, "Internal server error"
           
    def terminate(self):
        """Terminate the worker process and clean up resources."""
        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=1)
            if self.process.is_alive():
                self.process.kill()
        
        # Close queues
        self.input_queue.close()
        self.output_queue.close()


def worker_function(input_queue: Queue, output_queue: Queue, memory_limit_mb: int):
    """
    Worker process that runs the persistent interpreter.
    
    Runs in a separate process. Waits for code via input_queue,
    executes it in InteractiveInterpreter, sends results via output_queue.
    
    Args:
        input_queue: Queue to receive code from SessionProcess
        output_queue: Queue to send results back to SessionProcess
        memory_limit_mb: Memory limit in megabytes
    """
    # Set memory limit on Linux
    if is_linux():
        try:
            set_limit_linux(memory_limit_mb)
        except Exception:
            pass  # Continue even if we can't set limits
    
    # Create persistent interpreter
    interpreter = InteractiveInterpreter()
    
    # Main loop - wait for code and execute
    while True:
        try:
            # Wait for code to execute
            code = input_queue.get()
            
            # Capture stdout and stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            try:
                # Execute code in interpreter using exec
                exec(code, interpreter.locals)
                
                # Get captured output
                stdout_output = stdout_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                # Restore stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                # Send results back
                stdout_result = stdout_output if stdout_output else None
                stderr_result = stderr_output if stderr_output else None
                
                output_queue.put((stdout_result, stderr_result, None))
                
            except Exception as e:
                # Restore stdout/stderr first
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                # Get any stderr that was captured before exception
                stderr_output = stderr_capture.getvalue()
                
                # If no stderr captured, format the exception as stderr
                if not stderr_output:
                    import traceback
                    stderr_output = traceback.format_exc()
                
                # Send error as stderr (not as error field)
                output_queue.put((None, stderr_output, None))
                
        except Exception as e:
            # Worker loop crashed - this will cause is_alive() to return False
            break