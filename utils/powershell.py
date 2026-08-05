"""
utils/powershell.py

Utility functions for executing PowerShell commands.
"""

import subprocess
import json


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

        return result.stdout.strip()

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
        return json.loads(output)

    except json.JSONDecodeError:
        return {"error": "Invalid JSON returned from PowerShell."}