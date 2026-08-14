# Phase 12: Reporting Engine

## 12.1 Academic Overview
Enterprise auditing requires static artifacts for compliance frameworks (like ISO 27001 or SOC2). Phase 12 serializes the Python data structures into machine-readable JSON and human-readable HTML reports.

## 12.2 Technical Implementation
- **JSON Serialization:** Uses `json.dumps()` to format the `sys_info` and `findings` lists into `report.json`. This allows the data to be ingested by centralized SIEM platforms.
- **HTML Rendering:** Utilizes the **Jinja2** templating engine. Jinja allows developers to write standard HTML (`templates/report.html`) infused with Python `for` loops. 
```html
{% for finding in findings %}
    <tr class="{{ finding.severity }}">
        <td>{{ finding.id }}</td>
        <td>{{ finding.title }}</td>
    </tr>
{% endfor %}
```
This cleanly decouples the business logic (Python) from the presentation layer (HTML).
