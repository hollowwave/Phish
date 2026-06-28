import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from modules.utils import log_event, color
from modules.tracker import log_event_db

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "templates")


def send_campaign(campaign: str, targets_file: str, template_name: str):
    """Send phishing emails to all targets in the targets file."""

    # ── Load targets ───────────────────────────────────────────────────────────
    if not os.path.exists(targets_file):
        print(color(f"[-] Targets file not found: {targets_file}", "red"))
        return

    with open(targets_file) as f:
        targets = [line.strip() for line in f if line.strip() and "@" in line]

    if not targets:
        print(color("[-] No valid email addresses found in targets file.", "red"))
        return

    # ── Load template ──────────────────────────────────────────────────────────
    template_path = os.path.join(TEMPLATES_DIR, f"{template_name}.html")
    txt_path      = os.path.join(TEMPLATES_DIR, f"{template_name}.txt")

    if not os.path.exists(template_path) and not os.path.exists(txt_path):
        print(color(f"[-] Template '{template_name}' not found in {TEMPLATES_DIR}", "red"))
        _show_available_templates()
        return

    # ── SMTP config ────────────────────────────────────────────────────────────
    print(color("\n[*] SMTP Configuration", "cyan"))
    smtp_host = input(color("[>] SMTP host (e.g. smtp.gmail.com): ", "cyan")).strip()
    smtp_port = int(input(color("[>] SMTP port (587 / 465): ", "cyan")).strip() or "587")
    sender    = input(color("[>] Sender email: ", "cyan")).strip()
    password  = input(color("[>] Sender password (app password): ", "cyan")).strip()
    subject   = input(color("[>] Email subject: ", "cyan")).strip()
    host_url  = input(color("[>] Your harvester URL (e.g. http://1.2.3.4:8080): ", "cyan")).strip()

    # ── Send loop ──────────────────────────────────────────────────────────────
    print(color(f"\n[*] Sending to {len(targets)} target(s)...\n", "cyan"))

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(sender, password)
    except Exception as e:
        print(color(f"[-] SMTP connection failed: {e}", "red"))
        return

    sent = 0
    for target in targets:
        token = str(uuid.uuid4())[:8]
        tracking_url = f"{host_url}/?t={token}"
        pixel_url    = f"{host_url}/track/open"

        # Build email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = target

        # Load and inject token into template
        html_body = _load_template(template_path or txt_path, tracking_url, pixel_url, target)
        msg.attach(MIMEText(html_body, "html"))

        try:
            server.sendmail(sender, target, msg.as_string())
            log_event_db(campaign, token, "email_sent")
            log_event(campaign, "INFO", f"Sent → {target} | Token: {token}")
            sent += 1
        except Exception as e:
            log_event(campaign, "ERROR", f"Failed → {target} | {e}")

    server.quit()
    print(color(f"\n[✓] Campaign sent: {sent}/{len(targets)} emails delivered\n", "green"))


def _load_template(path: str, tracking_url: str, pixel_url: str, target: str) -> str:
    """Load template and replace placeholders."""
    with open(path) as f:
        content = f.read()

    content = content.replace("{{TRACKING_URL}}", tracking_url)
    content = content.replace("{{PIXEL_URL}}", pixel_url)
    content = content.replace("{{TARGET}}", target)
    return content


def _show_available_templates():
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    templates = os.listdir(TEMPLATES_DIR)
    if templates:
        print(color("\n[*] Available templates:", "cyan"))
        for t in templates:
            print(f"    - {t}")
    else:
        print(color("[!] No templates found. Create one in data/templates/", "yellow"))
        print(color("    Example: data/templates/gmail_alert.html\n", "yellow"))
