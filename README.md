# Windows Security Audit Tool

A Python-based Windows security auditing tool that gathers important system-security information and presents it in readable terminal tables. The project is designed to help users understand the security posture of a Windows computer without changing its configuration.

> This tool is read-only. It collects and reports information; it does not modify Windows security settings, firewall rules, users, or services.

## Features

### Completed

- System information audit
  - Computer name, active user, Windows version, CPU, RAM, boot time, and IP address
- Microsoft Defender audit
  - Antivirus, real-time protection, behavior monitoring, download protection, and Network Inspection System status
  - Findings and Defender score out of 10
- Windows Firewall audit
  - Domain, Private, and Public firewall profile status
  - Default inbound and outbound actions
  - Findings and Firewall score out of 10
- Local user account audit
  - Enabled and disabled local accounts
  - Local administrator membership
  - Password-last-set and last-sign-in information
  - Findings and user-account score out of 10

### Planned

- Running services audit
- Startup-program audit
- Installed-software audit
- Password-policy audit
- Windows Update audit
- Open network-port audit
- Event Log summary
- Overall security score
- HTML and PDF reports

## Project Structure

```text
Windows-Security-Audit-Tool/
├── main.py                    # Runs the audit and displays results
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── modules/
│   ├── system.py               # Phase 1: system information
│   ├── defender.py             # Phase 2: Microsoft Defender
│   ├── firewall.py             # Phase 3: Windows Firewall
│   └── users.py                # Phase 4: local user accounts
├── utils/
│   └── powershell.py           # PowerShell execution and JSON parsing
├── documentation/
│   ├── phase1.md
│   ├── phase2.md
│   ├── phase3.md
│   └── phase4.md
├── reports/                    # Generated reports (future phase)
├── templates/                  # HTML report templates (future phase)
└── screenshots/                # Project screenshots
```

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or later
- PowerShell

## Installation

1. Clone or download the project.

2. Open PowerShell in the project folder.

3. Create and activate a virtual environment (recommended):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

## Usage

Run the application from the project root:

```powershell
python main.py
```

The program displays each audit section in the terminal, followed by findings and section scores where available.

## How It Works

Python coordinates the audit modules. For Windows-specific security information, the project uses PowerShell commands and converts their JSON output into Python dictionaries and lists.

```text
main.py
  ├── modules/system.py
  ├── modules/defender.py
  ├── modules/firewall.py
  └── modules/users.py
          ↓
  utils/powershell.py
          ↓
      PowerShell
          ↓
   Windows security data
```

## Security Notes

- Run the tool only on computers you own or are authorized to audit.
- Some information may be restricted by organizational policy or security software.
- A failed data collection does not necessarily indicate an insecure computer; it means the setting could not be verified by the tool.
- Review findings before changing any security configuration.

## Documentation

Detailed notes for each completed phase are stored in the `documentation` directory:

- `phase1.md` — System Information
- `phase2.md` — Microsoft Defender Audit
- `phase3.md` — Windows Firewall Audit
- `phase4.md` — Local User Account Audit

## Future Improvements

- Export results to HTML and PDF
- Add command-line options to run selected audit modules
- Add timestamps and audit history
- Add unit tests for scoring and assessment functions
- Improve findings severity levels and recommendations

## License

This project is intended for educational and portfolio use. Add a license file before distributing it publicly.