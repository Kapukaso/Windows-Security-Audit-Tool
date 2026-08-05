"""
modules/system.py

Collects basic system information for the audit.
"""

import platform
import socket
import getpass
import psutil
from datetime import datetime


def get_system_info():
    """
    Collects system information.

    Returns:
        dict
    """

    memory = psutil.virtual_memory()

    info = {
        "Computer Name": socket.gethostname(),
        "Current User": getpass.getuser(),
        "Operating System": platform.system(),
        "OS Release": platform.release(),
        "OS Version": platform.version(),
        "Architecture": platform.machine(),
        "Processor": platform.processor(),
        "RAM (GB)": round(memory.total / (1024 ** 3), 2),
        "CPU Cores": psutil.cpu_count(logical=False),
        "Logical Processors": psutil.cpu_count(logical=True),
        "CPU Usage (%)": psutil.cpu_percent(interval=1),
        "Boot Time": datetime.fromtimestamp(
            psutil.boot_time()
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "IP Address": socket.gethostbyname(socket.gethostname())
    }

    return info