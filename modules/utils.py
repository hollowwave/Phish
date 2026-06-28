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


def log_event(campaign: str, event: str, detail: str = ""):
    """Print a timestamped event to the CLI."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    event_colors = {
        "HIT":     "green",
        "EVENT":   "cyan",
        "INFO":    "blue",
        "WARN":    "yellow",
        "ERROR":   "red",
    }
    clr = event_colors.get(event, "white")
    tag = color(f"[{event}]", clr)
    print(f"{color(ts, 'white')} {tag} {color(campaign, 'magenta')} | {detail}")
