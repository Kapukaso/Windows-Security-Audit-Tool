"""
utils/powershell.py

Utility functions for executing PowerShell commands.
"""

import subprocess
import json


def _sanitize_null_bytes(val):
    """Recursively removes NUL (0x00) bytes from strings, dicts, and lists."""
    if isinstance(val, str):
        return val.replace("\x00", "")
    elif isinstance(val, dict):
        return {_sanitize_null_bytes(k): _sanitize_null_bytes(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [_sanitize_null_bytes(item) for item in val]
    return val


def run_powershell(command):
    """
    Execute a PowerShell command and return the raw output.
    """

    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout.strip()
        if output:
            output = output.replace("\x00", "")
        return output

    except subprocess.CalledProcessError as e:
        return None


def run_powershell_json(command):
    """
    Execute a PowerShell command that returns JSON.
    """

    output = run_powershell(command)

    if output is None:
        return {"error": "PowerShell execution failed."}

    try:
        data = json.loads(output)
        return _sanitize_null_bytes(data)

    except json.JSONDecodeError:
        return {"error": "Invalid JSON returned from PowerShell."}