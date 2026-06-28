# Phishing Simulation Framework

A CLI-based phishing simulation tool built for security awareness training and
educational red team portfolio purposes.

---

## ⚠️ Legal Disclaimer

This tool is intended **strictly for authorized security awareness training**.

- Only use against systems and individuals you have **explicit written permission** to test
- Unauthorized phishing is illegal under computer fraud laws in most jurisdictions
- The author assumes no liability for misuse

See `authorization_template.md` for a sample authorization form.

---

## Project Structure

```
phishing-tool/
├── main.py                        # CLI entry point (interactive + argparse)
├── config.yaml                    # Central configuration file
├── requirements.txt
├── authorization_template.md      # Sample authorization form
│
├── modules/
│   ├── __init__.py
│   ├── config.py                  # Config loader (reads config.yaml)
│   ├── cloner.py                  # Page scraper + asset downloader
│   ├── harvester.py               # Flask listener + credential capture
│   ├── mailer.py                  # SMTP campaign sender
│   ├── tracker.py                 # SQLite logging + CLI log viewer
│   └── utils.py                   # Banner, colors, file logging
│
└── data/
    ├── cloned_pages/              # Saved cloned sites per campaign
    │   └── <campaign_name>/
    │       ├── index.html         # Cloned page with injected form action
    │       └── assets/            # Downloaded CSS, JS, images
    ├── templates/                 # HTML email templates
    │   └── account_alert.html     # Sample template
    └── logs/                      # Exported CSVs + session log
        ├── session.log            # Full CLI output log (plain text)
        ├── <campaign>_credentials.csv
        └── <campaign>_events.csv
```

---

## Setup

```bash
git clone <repo>
cd phishing-tool
pip install -r requirements.txt
```

---

## Configuration

Edit `config.yaml` before running any campaign:

```yaml
harvester:
  port: 8080
  redirect_url: "https://www.google.com"   # Where victim lands after submit

smtp:
  host: "smtp.gmail.com"
  port: 587
  sender: "you@gmail.com"
  password: "your-app-password"
  default_subject: "Action Required: Verify Your Account"

logging:
  log_to_file: true
  log_file: "data/logs/session.log"
  db_path: "campaigns.db"
```

---

## Usage

### Interactive menu
```bash
python main.py
```

### Argparse mode
```bash
# Clone a page
python main.py clone --url https://target.com/login --campaign corp_test_01

# Start harvester listener
python main.py listen --campaign corp_test_01 --port 8080

# Send phishing emails
python main.py send --campaign corp_test_01 --targets targets.txt --template account_alert

# View logs
python main.py logs --campaign corp_test_01

# Export logs to CSV
python main.py export --campaign corp_test_01
```

---

## Full Flow

```
[1] Edit config.yaml
        ↓
[2] Clone a login page
    python main.py clone --url <url> --campaign <name>
        ↓
[3] Start harvester listener
    python main.py listen --campaign <name>
        ↓
[4] Send campaign emails
    python main.py send --campaign <name> --targets targets.txt --template account_alert
        ↓
[5] Victim receives email → clicks link → sees cloned page → submits credentials
        ↓
[6] CLI prints live hit, DB logs full token timeline
        ↓
[7] View or export logs
    python main.py logs --campaign <name>
    python main.py export --campaign <name>
```

---

## Targets File Format

One email per line:
```
alice@company.com
bob@company.com
```

---

## Email Templates

Place `.html` templates in `data/templates/`. Available placeholders:

| Placeholder | Description |
|---|---|
| `{{TARGET}}` | Target email address |
| `{{TRACKING_URL}}` | Unique tracking link per target |
| `{{PIXEL_URL}}` | 1x1 tracking pixel URL |

---

## How Token Tracking Works

Each target gets a unique UUID token embedded in their link (`/?t=a3f9bc12`).
Every action is tied to that token in the database:

```
email_sent → email_opened → visited → credentials_submitted
```

This lets you trace one person's complete journey through the campaign.

---

## Modules Overview

| Module | Responsibility |
|---|---|
| `config.py` | Loads `config.yaml`, exposes `get(section, key, fallback)` |
| `cloner.py` | Fetches page, downloads assets + CSS @imports, injects form action, warns if no login form |
| `harvester.py` | Flask server — serves cloned page, catches POST, logs credentials, fires tracking pixel |
| `mailer.py` | SMTP sender — generates tokens per target, pre-fills prompts from config |
| `tracker.py` | SQLite CRUD — logs credentials + events, CLI viewer, CSV export |
| `utils.py` | ANSI colors, banner, menu, dual CLI+file logging |

---

## Roadmap

- [ ] HTTPS support via self-signed cert
- [ ] Configurable redirect URL per campaign
- [ ] Plain text email fallback template
- [ ] Rate limiting between sends
- [ ] Sender name spoofing
- [ ] Campaign summary stats (open rate %, click rate %, submission rate %)
- [ ] PDF report generation
- [ ] Multi-page cloning
