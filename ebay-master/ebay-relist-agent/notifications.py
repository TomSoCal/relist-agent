import os
import smtplib
import ssl
import subprocess
import sys
from email.mime.text import MIMEText

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def format_subject(date_str: str) -> str:
    return f"Relist Agent Report — {date_str}"


def format_report(relisted: list[dict], ended_zero_qty: list[dict], failures: list[dict]) -> str:
    lines = [f"Relisted ({len(relisted)}):"]
    if relisted:
        for r in relisted:
            lines.append(f"  - [{r['old_id']} -> {r['new_id']}] {r['title']}")
    else:
        lines.append("  (none)")

    lines += ["", f"Zero-Quantity Ended ({len(ended_zero_qty)}):"]
    if ended_zero_qty:
        for r in ended_zero_qty:
            lines.append(f"  - [{r['item_id']}] {r['title']}")
    else:
        lines.append("  (none)")

    lines += ["", f"Failures ({len(failures)}):"]
    if failures:
        for r in failures:
            lines.append(f"  - [{r['item_id']}] {r['title']} -- {r['reason']}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


def format_report_html(relisted: list[dict], ended_zero_qty: list[dict], failures: list[dict]) -> str:
    """Generate HTML email report with professional styling"""

    relisted_rows = ""
    for r in relisted:
        relisted_rows += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 12px; text-align: left;">{r['title']}</td>
            <td style="padding: 12px; text-align: center; font-family: monospace; font-size: 12px;">{r['old_id']}</td>
            <td style="padding: 12px; text-align: center; font-family: monospace; font-size: 12px;">{r['new_id']}</td>
        </tr>
        """

    if not relisted:
        relisted_rows = '<tr><td colspan="3" style="padding: 12px; text-align: center; color: #999;">(none)</td></tr>'

    zero_qty_rows = ""
    for r in ended_zero_qty:
        zero_qty_rows += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 12px; text-align: left;">{r['title']}</td>
            <td style="padding: 12px; text-align: center; font-family: monospace; font-size: 12px;">{r['item_id']}</td>
        </tr>
        """

    if not ended_zero_qty:
        zero_qty_rows = '<tr><td colspan="2" style="padding: 12px; text-align: center; color: #999;">(none)</td></tr>'

    failure_rows = ""
    for r in failures:
        failure_rows += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 12px; text-align: left;">{r['title']}</td>
            <td style="padding: 12px; text-align: center; font-family: monospace; font-size: 12px;">{r['item_id']}</td>
            <td style="padding: 12px; text-align: left; color: #d9534f;">{r.get('reason', 'Unknown error')}</td>
        </tr>
        """

    if not failures:
        failure_rows = '<tr><td colspan="3" style="padding: 12px; text-align: center; color: #999;">(none)</td></tr>'

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; color: #333;">
        <div style="max-width: 900px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px;">

            <!-- Logo -->
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="https://thetrashedpanda.com/wp-content/uploads/2026/06/ERA_Logo-2.png" alt="Relist Agent" width="200" style="max-width: 100%;">
            </div>

            <!-- Headline -->
            <h2 style="text-align: center; color: #2c3e50; margin-bottom: 30px;">Daily Relist Report</h2>

            <!-- Summary Stats -->
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; text-align: center;">
                <div style="background-color: #d4edda; padding: 15px; border-radius: 6px;">
                    <div style="font-size: 24px; font-weight: bold; color: #155724;">{len(relisted)}</div>
                    <div style="color: #155724; font-size: 14px;">Relisted</div>
                </div>
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 6px;">
                    <div style="font-size: 24px; font-weight: bold; color: #856404;">{len(ended_zero_qty)}</div>
                    <div style="color: #856404; font-size: 14px;">Zero-Qty Ended</div>
                </div>
                <div style="background-color: #f8d7da; padding: 15px; border-radius: 6px;">
                    <div style="font-size: 24px; font-weight: bold; color: #721c24;">{len(failures)}</div>
                    <div style="color: #721c24; font-size: 14px;">Failures</div>
                </div>
            </div>

            <!-- Relisted Section -->
            <h3 style="color: #2c3e50; border-bottom: 3px solid #5cb85c; padding-bottom: 10px; margin-bottom: 15px;">✓ Successfully Relisted ({len(relisted)})</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: #f9f9f9; border-bottom: 2px solid #ddd;">
                        <th style="padding: 12px; text-align: left; font-weight: bold;">Title</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Old ID</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">New ID</th>
                    </tr>
                </thead>
                <tbody>
                    {relisted_rows}
                </tbody>
            </table>

            <!-- Zero-Qty Section -->
            <h3 style="color: #2c3e50; border-bottom: 3px solid #f0ad4e; padding-bottom: 10px; margin-bottom: 15px;">— Zero-Quantity Ended ({len(ended_zero_qty)})</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: #f9f9f9; border-bottom: 2px solid #ddd;">
                        <th style="padding: 12px; text-align: left; font-weight: bold;">Title</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Item ID</th>
                    </tr>
                </thead>
                <tbody>
                    {zero_qty_rows}
                </tbody>
            </table>

            <!-- Failures Section -->
            <h3 style="color: #2c3e50; border-bottom: 3px solid #d9534f; padding-bottom: 10px; margin-bottom: 15px;">✗ Failures ({len(failures)})</h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: #f9f9f9; border-bottom: 2px solid #ddd;">
                        <th style="padding: 12px; text-align: left; font-weight: bold;">Title</th>
                        <th style="padding: 12px; text-align: center; font-weight: bold;">Item ID</th>
                        <th style="padding: 12px; text-align: left; font-weight: bold;">Reason</th>
                    </tr>
                </thead>
                <tbody>
                    {failure_rows}
                </tbody>
            </table>

            <!-- Footer -->
            <div style="background-color: #bdd253; padding: 20px; border-radius: 6px; text-align: center; margin-top: 30px;">
                <p style="margin: 0 0 15px 0; font-weight: bold;">Questions? Contact us:</p>
                <p style="margin: 0 0 10px 0;"><strong>support@thetrashedpanda.com</strong></p>
                <p style="margin: 0; font-size: 12px; color: #666;">
                    Powered by <img src="https://thetrashedpanda.com/wp-content/uploads/2026/06/TrshedPanda-Logo-250px.png" alt="The Trashed Panda" width="100" style="vertical-align: middle; margin-top: 5px;">
                </p>
            </div>

        </div>
    </body>
    </html>
    """

    return html


def send_email(gmail_app_password: str, subject: str, body: str, sender: str, recipient: str, is_html: bool = False) -> None:
    subtype = "html" if is_html else "plain"
    msg = MIMEText(body, subtype)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
        server.login(sender, gmail_app_password)
        server.sendmail(sender, [recipient], msg.as_string())


def notify_toast(title: str, body: str) -> None:
    # Check if running in an interactive session by looking for SESSIONNAME env var
    session_name = os.environ.get("SESSIONNAME", "").lower()
    if session_name == "services" or session_name == "console" and not sys.stdin.isatty():
        # Running from Task Scheduler (SESSIONNAME='Services') or non-interactive - skip toast
        return

    title = title.replace("'", "''").replace('"', '`"')
    body = body.replace("'", "''").replace('"', '`"')
    ps = (
        "[reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null;"
        "[reflection.assembly]::loadwithpartialname('System.Drawing') | Out-Null;"
        "$n = New-Object System.Windows.Forms.NotifyIcon;"
        "$n.Icon = [System.Drawing.SystemIcons]::Information;"
        "$n.Visible = $true;"
        f"$n.ShowBalloonTip(8000, '{title}', '{body}', [System.Windows.Forms.ToolTipIcon]::Info);"
        "Start-Sleep -Seconds 9; $n.Dispose()"
    )
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    try:
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-NonInteractive", "-Command", ps],
            creationflags=flags,
        )
    except Exception:
        pass
