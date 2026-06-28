import os
import sys
from datetime import datetime

RESET  = "\033[0m"
COLORS = {
    "red":     "\033[91m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "cyan":    "\033[96m",
    "white":   "\033[97m",
}


def color(text: str, clr: str) -> str:
    return f"{COLORS.get(clr, '')}{text}{RESET}"


def banner():
    print(color(r"""
 ██████╗ ██╗  ██╗██╗███████╗██╗  ██╗
 ██╔══██╗██║  ██║██║██╔════╝██║  ██║
 ██████╔╝███████║██║███████╗███████║
 ██╔═══╝ ██╔══██║██║╚════██║██╔══██║
 ██║     ██║  ██║██║███████║██║  ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝
    Phishing Simulation Framework
    [ For authorized use only ]
""", "cyan"))


def menu():
    print(color("─" * 40, "blue"))
    print(color(" [1]", "green") + " Clone a page")
    print(color(" [2]", "green") + " Start harvester listener")
    print(color(" [3]", "green") + " Send campaign emails")
    print(color(" [4]", "green") + " View logs")
    print(color(" [5]", "green") + " Export logs (CSV)")
    print(color(" [0]", "red")   + " Exit")
    print(color("─" * 40, "blue"))


# ── File logger setup ──────────────────────────────────────────────────────────

_log_file = None

def _get_log_file():
    """Lazy-load log file path from config, open once."""
    global _log_file
    if _log_file is not None:
        return _log_file

    try:
        from modules import config
        enabled  = config.get("logging", "log_to_file", False)
        log_path = config.get("logging", "log_file", "data/logs/session.log")
    except Exception:
        return None

    if not enabled:
        return None

    base = os.path.join(os.path.dirname(__file__), "..")
    full_path = os.path.join(base, log_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    _log_file = open(full_path, "a", encoding="utf-8")
    return _log_file


def log_event(campaign: str, event: str, detail: str = ""):
    """Print a timestamped event to CLI and optionally write to log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    event_colors = {
        "HIT":   "green",
        "EVENT": "cyan",
        "INFO":  "blue",
        "WARN":  "yellow",
        "ERROR": "red",
    }
    clr = event_colors.get(event, "white")
    tag = color(f"[{event}]", clr)

    # CLI output (with color)
    print(f"{color(ts, 'white')} {tag} {color(campaign, 'magenta')} | {detail}")

    # File output (no ANSI codes)
    f = _get_log_file()
    if f:
        f.write(f"{ts} [{event}] {campaign} | {detail}\n")
        f.flush()
