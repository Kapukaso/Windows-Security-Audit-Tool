import winreg

key = winreg.OpenKey(
    winreg.HKEY_LOCAL_MACHINE,
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
)