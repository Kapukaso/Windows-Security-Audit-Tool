# Phase 4 — Local User Account Audit

## Objective

Phase 4 reviews local Windows accounts to identify enabled users, administrator privileges, password information, and recent sign-in activity.

This phase is read-only. It does not change users, passwords, permissions, or group membership.

## Files used

```text
main.py
modules/users.py
utils/powershell.py
```

## Data collected

| Field | Meaning |
| --- | --- |
| Username | Local Windows account name |
| Enabled | Whether the account can sign in |
| Administrator | Whether the account belongs to the local Administrators group |
| Password Last Set | When the account password was last changed |
| Last Sign-in | Most recent local sign-in recorded for the account |

## How it works

The module uses PowerShell to retrieve local accounts with `Get-LocalUser`.

It also locates the built-in Administrators group using its fixed Windows security identifier, `S-1-5-32-544`. This works even when Windows uses a language other than English.

The module then checks whether each local user belongs to that group.

## Findings

The audit reports:

- Whether the built-in Guest account is enabled.
- Each enabled local administrator account.
- Disabled accounts.
- The number of enabled local administrator accounts.

## Score

The score starts at 10/10.

- An enabled Guest account reduces the score by 4 points.
- More than two enabled local administrator accounts reduces the score by 2 points.
- A PowerShell or data-collection error returns 0/10 because the configuration could not be verified.

## Verification

Run the application from the project root:

```powershell
python main.py
```

The output should contain a Local User Accounts table, user-account findings, and a User Account Security Score.
