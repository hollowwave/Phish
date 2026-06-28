import os
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from modules.utils import log_event, color
from modules.tracker import log_event_db
from modules import config

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

    # ── SMTP config — pre-fill from config.yaml if set ────────────────────────
    print(color("\n[*] SMTP Configuration (press Enter to use config.yaml defaults)", "cyan"))

    cfg_host    = config.get("smtp", "host", "")
    cfg_port    = config.get("smtp", "port", 587)
    cfg_sender  = config.get("smtp", "sender", "")
    cfg_pass    = config.get("smtp", "password", "")
    cfg_subject = config.get("smtp", "default_subject", "")
    cfg_port_default = config.get("harvester", "port", 8080)

    smtp_host = input(color(f"[>] SMTP host [{cfg_host or 'smtp.gmail.com'}]: ", "cyan")).strip() or cfg_host or "smtp.gmail.com"
    smtp_port = input(color(f"[>] SMTP port [{cfg_port}]: ", "cyan")).strip()
    smtp_port = int(smtp_port) if smtp_port else cfg_port
    sender    = input(color(f"[>] Sender email [{cfg_sender or 'required'}]: ", "cyan")).strip() or cfg_sender
    password  = input(color(f"[>] App password [{'set' if cfg_pass else 'required'}]: ", "cyan")).strip() or cfg_pass
    subject   = input(color(f"[>] Subject [{cfg_subject or 'required'}]: ", "cyan")).strip() or cfg_subject
    host_url  = input(color(f"[>] Harvester URL [http://localhost:{cfg_port_default}]: ", "cyan")).strip() or f"http://localhost:{cfg_port_default}"

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
