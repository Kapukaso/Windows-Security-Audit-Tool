"""
modules/report.py
Generates JSON and HTML reports based on the final audit data.
"""
import json
import os
import datetime
from jinja2 import Environment, FileSystemLoader

def generate_json_report(score_data, all_findings, compliance_report=None, output_dir="reports"):
    """
    Exports the complete audit results to a JSON file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"audit_report_{timestamp}.json")
    
    report_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "score_summary": score_data,
        "findings": all_findings
    }
    
    if compliance_report:
        report_data["compliance"] = compliance_report
    
    with open(filepath, "w") as f:
        json.dump(report_data, f, indent=4)
        
    print(f"[+] JSON Report generated successfully: {filepath}")
    return filepath

def generate_html_report(score_data, all_findings, category_weights, output_dir="reports"):
    """
    Generates a professional HTML report using Jinja2 templates.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
    
    try:
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("report.html")
    except Exception as e:
        print(f"[-] Failed to load HTML template: {e}")
        return None
        
    percentage = (score_data['total_earned'] / score_data['total_possible']) * 100
    
    html_content = template.render(
        total_earned=score_data['total_earned'],
        total_possible=score_data['total_possible'],
        percentage=percentage,
        category_scores=score_data['category_scores'],
        category_weights=category_weights,
        all_findings=all_findings
    )
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"audit_report_{timestamp}.html")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"[+] HTML Report generated successfully: {filepath}")
    return filepath
