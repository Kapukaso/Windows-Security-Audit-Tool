# Phase 1 — System Information

## Goal

Collect baseline information about the Windows computer before evaluating security controls. This helps identify the machine being audited and provides context for later findings.

## Files

```text
main.py
modules/
  __init__.py
  system.py
```

## Module responsibility

`modules/system.py` contains `get_system_info()`. It returns a dictionary containing the computer name, signed-in user, Windows version, processor, installed RAM, CPU information, boot time, and IP address.

`main.py` imports the function, calls it once, and passes the returned dictionary to `print_table()` for display.

## Key packages

- `platform` reads Windows and architecture details.
- `socket` supplies the computer name and IP address.
- `getpass` identifies the current user.
- `psutil` reads memory, CPU, and boot-time data.
- `tabulate` formats dictionary data for the terminal.

Install the project dependencies once:

```powershell
pip install psutil tabulate
```

## Expected result

The program prints a System Information table. This phase is informational: it does not assign a security score or change any Windows settings.

## Verification

Run the project from its root folder:

```powershell
python main.py
```

Confirm that the values displayed match the current computer. CPU usage can differ between runs, which is expected.

