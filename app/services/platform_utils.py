"""Platform detection utilities."""

import platform


def is_linux() -> bool:
    """
    Check if running on Linux.
    
    Returns:
        True if platform is Linux, False otherwise
    """
    return platform.system() == "Linux"


def is_windows() -> bool:
    """
    Check if running on Windows.
    
    Returns:
        True if platform is Windows, False otherwise
    """
    return platform.system() == "Windows"


def get_platform_name() -> str:
    """
    Get the platform name.
    
    Returns:
        Platform name as string (e.g., 'Linux', 'Windows', 'Darwin')
    """
    return platform.system()