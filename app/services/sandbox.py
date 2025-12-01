"""Sandbox restrictions for code execution environment.

This module implements Python-level sandboxing by replacing dangerous
functions with safe stubs that raise PermissionError.

Restrictions:
- Filesystem: Blocks file I/O operations (open, os.remove, os.mkdir, etc.)
- Network: Blocks all network operations (socket, urllib, http, etc.)
"""

import os
import socket
import pathlib


def _create_safe_stub():
    """
    Create a function that raises PermissionError when called.
    
    Returns:
        A function that blocks execution and raises PermissionError
    """
    def safe_function(*args, **kwargs):
        """Replacement function that raises PermissionError."""
        # Try to extract resource name from first argument
        if args:
            resource = str(args[0])
            raise PermissionError(f"[Errno 13] Permission denied: '{resource}'")
        else:
            raise PermissionError("[Errno 13] Permission denied")
    
    return safe_function


def _create_safe_open():
    """
    Create a safe replacement for open() that allows /proc/ reads for psutil.
    
    We need to allow psutil to read /proc/ files for memory monitoring,
    but block all other file operations.
    """
    # Save reference to real open before we replace it
    import builtins
    real_open = builtins.open
    
    def safe_open(file, mode='r', *args, **kwargs):
        """Replacement open() that only allows /proc/ reads."""
        filepath = str(file)
        
        # Allow reading from /proc/ (needed for psutil memory monitoring)
        if filepath.startswith('/proc/') and ('r' in mode and 'w' not in mode and 'a' not in mode and '+' not in mode):
            return real_open(file, mode, *args, **kwargs)
        
        # Block everything else
        raise PermissionError(f"[Errno 13] Permission denied: '{filepath}'")
    
    return safe_open


def apply_sandbox_to_namespace(namespace: dict):
    """
    Apply all sandboxing restrictions to the execution namespace.
    
    This is called once when the worker process initializes, before any
    user code executes. It modifies the namespace dictionary in-place.
    
    Args:
        namespace: The execution namespace (interpreter.locals)
    """
    _block_filesystem(namespace)
    _block_network(namespace)


def _block_filesystem(namespace: dict):
    """
    Block filesystem I/O operations.
    
    Blocks:
    - Built-in open()
    - os module file operations (remove, mkdir, listdir, etc.)
    - pathlib file operations
    
    Keeps safe:
    - os.getcwd(), os.cpu_count(), os.path.join(), etc.
    
    Args:
        namespace: The execution namespace to modify
    """
    # Block built-in open() but allow /proc/ reads for psutil
    # __builtins__ can be either a dict or a module, handle both cases
    builtins = namespace.get('__builtins__')
    if isinstance(builtins, dict):
        builtins['open'] = _create_safe_open()
    else:
        # It's a module, set attribute
        import builtins as builtins_module
        builtins_module.open = _create_safe_open()
    
    # Block dangerous os module functions
    FILESYSTEM_BLACKLIST = [
        # File deletion
        'remove', 'unlink', 'rmdir', 'removedirs',
        # File/directory creation
        'mkdir', 'makedirs', 'mknod',
        # File modification
        'rename', 'renames', 'replace', 'chmod', 'chown', 'lchown',
        # File I/O
        'open', 'truncate',
        # Directory operations
        'listdir',
        # Links
        'link', 'symlink',
    ]
    
    for func_name in FILESYSTEM_BLACKLIST:
        if hasattr(os, func_name):
            setattr(os, func_name, _create_safe_stub())
    
    # Add patched os to namespace
    namespace['os'] = os
    
    # Block pathlib operations
    # TODO: Implement pathlib blocking
    namespace['pathlib'] = pathlib


def _block_network(namespace: dict):
    """
    Block ALL network operations.
    
    Blocks everything callable in:
    - socket module
    - urllib module
    - http module
    
    Args:
        namespace: The execution namespace to modify
    """
    # Block socket.socket() - the main way to create network connections
    # We can't block everything in socket module as it breaks Python internals
    socket.socket = _create_safe_stub()
    
    if hasattr(socket, 'create_connection'):
        socket.create_connection = _create_safe_stub()
    
    if hasattr(socket, 'create_server'):
        socket.create_server = _create_safe_stub()
    
    namespace['socket'] = socket
    
    # Block urllib module
    try:
        import urllib.request
        
        urllib.request.urlopen = _create_safe_stub()
        if hasattr(urllib.request, 'urlretrieve'):
            urllib.request.urlretrieve = _create_safe_stub()
        
        namespace['urllib'] = urllib
    except ImportError:
        pass  # urllib not available
    
    # Block http module
    try:
        import http.client
        
        http.client.HTTPConnection = _create_safe_stub()
        http.client.HTTPSConnection = _create_safe_stub()
        
        namespace['http'] = http
    except ImportError:
        pass  # http not available