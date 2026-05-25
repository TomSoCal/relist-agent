import smtplib
import ssl
import subprocess
from email.mime.text import MIMEText

SENDER = "tomnissley@gmail.com"
RECIPIENT = "tomnissley@gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465


def format_subject(date_str: str) -> str:
    return f"eBay Relist Report — {date_str}"


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


def send_email(gmail_app_password: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
        server.login(SENDER, gmail_app_password)
        server.sendmail(SENDER, [RECIPIENT], msg.as_string())


def notify_toast(title: str, body: str) -> None:
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
