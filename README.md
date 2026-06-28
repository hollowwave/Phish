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

## Features

- **Page Cloner** — scrapes and saves a target login page with injected form action
- **Credential Harvester** — Flask listener that captures submitted credentials
- **Email Sender** — SMTP campaign sender with per-target tracking tokens
- **Tracking System** — logs email opens, link clicks, and credential submissions
- **CLI Dashboard** — view and export logs per campaign

---

## Setup

```bash
git clone <repo>
cd phishing-tool
pip install -r requirements.txt
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

# Start harvester
python main.py listen --campaign corp_test_01 --port 8080

# Send emails
python main.py send --campaign corp_test_01 --targets targets.txt --template account_alert

# View logs
python main.py logs --campaign corp_test_01

# Export to CSV
python main.py export --campaign corp_test_01
```

---

## Targets File Format

One email per line:
```
alice@company.com
bob@company.com
carol@company.com
```

---

## Email Templates

Place `.html` templates in `data/templates/`. Available placeholders:

| Placeholder | Description |
|---|---|
| `{{TARGET}}` | Target email address |
| `{{TRACKING_URL}}` | Unique link per target |
| `{{PIXEL_URL}}` | Tracking pixel URL |

---

## Project Structure

```
phishing-tool/
├── main.py                  # CLI entry point
├── modules/
│   ├── cloner.py            # Page scraper + asset downloader
│   ├── harvester.py         # Flask listener + credential capture
│   ├── mailer.py            # SMTP campaign sender
│   ├── tracker.py           # SQLite logging + CLI log viewer
│   └── utils.py             # Banner, colors, shared helpers
├── data/
│   ├── cloned_pages/        # Saved cloned sites per campaign
│   ├── templates/           # HTML email templates
│   └── logs/                # Exported CSV reports
├── campaigns.db             # SQLite database
└── requirements.txt
```

---

## Roadmap / Extension Ideas

- [ ] HTTPS support via self-signed cert
- [ ] Multi-page site cloning
- [ ] SMS phishing (smishing) module
- [ ] Redirect chaining
- [ ] Report PDF generation
