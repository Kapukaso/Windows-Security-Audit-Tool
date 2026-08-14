# Phase 8: Network & Open Ports

## 8.1 Academic Overview & Motivation
An open listening port is a direct interface between the operating system's internal services and the external network. Unnecessary open ports exponentially increase a system's attack surface. 

## 8.2 Technical Implementation
To maintain a small footprint, the module bypasses external tools like `netstat` or `nmap` and uses the cross-platform `psutil` library.
It calls `psutil.net_connections()` and filters for sockets where `status == psutil.CONN_LISTEN`.

## 8.3 Vulnerability Assessment Logic
The listening ports are compared against a threat-intelligence dictionary of notoriously vulnerable protocols:

- **CRITICAL (NET-001):** Port 23 (Telnet). Transmits credentials in plaintext.
- **CRITICAL (NET-002):** Port 445 (SMB). The protocol exploited by EternalBlue, WannaCry, and NotPetya. Should never be exposed outside a hardened LAN.
- **HIGH (NET-003):** Port 3389 (RDP). Heavily targeted by brute-force botnets and Initial Access Brokers (IABs).
- **HIGH (NET-004):** Port 21 (FTP). Insecure file transfer.
