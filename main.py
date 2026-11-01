#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wolfer Web Tools - Web structure and source code extraction suite.

Developer : Arman Hossen
YouTube   : @wolfertools0692
Repository: https://github.com/ravexadmain-png/wolfer-web-tools

Fetches the main HTML of a page, finds every external CSS and JavaScript
file, downloads them into output/<host>/assets/, and rewrites the saved
index.html so it points at the local copies.

Use it only on sites you own or have permission to copy.
"""

import hashlib
import os
import re
import sys
import time
from urllib.parse import unquote, urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("[-] Missing dependencies. Run: pip install -r requirements.txt")
    sys.exit(1)

VERSION = "1.0.0"
DEVELOPER = "Arman Hossen"
YOUTUBE = "@wolfertools0692"
REPO = "https://github.com/ravexadmain-png/wolfer-web-tools"

OUTPUT_ROOT = "output"
TIMEOUT = 20
MAX_BYTES = 25 * 1024 * 1024
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13; Termux) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
)


# --------------------------------------------------------------------------
# Terminal styling
# --------------------------------------------------------------------------
class C:
    _on = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
    RED = "\033[91m" if _on else ""
    GREEN = "\033[92m" if _on else ""
    YELLOW = "\033[93m" if _on else ""
    CYAN = "\033[96m" if _on else ""
    GREY = "\033[90m" if _on else ""
    WHITE = "\033[97m" if _on else ""
    BOLD = "\033[1m" if _on else ""
    END = "\033[0m" if _on else ""


WOLF = r"""
       /\                  /\
      /  \________________/  \
     /   /                \   \
    |   |   <o>      <o>   |   |
     \   \       /\       /   /
      \   \_____/  \_____/   /
       \         \/         /
        \     /\    /\     /
         \___/  \__/  \___/
              \  vv  /
               \_/\_/
"""

TITLE = r"""
__        __ ___   _      _____  _____  ____
\ \      / // _ \ | |    |  ___|| ____||  _ \
 \ \ /\ / / | | | || |    | |_   |  _|  | |_) |
  \ V  V /  | |_| || |___ |  _|  | |___ |  _ <
   \_/\_/   \___/ |_____||_|    |_____||_| \_\
"""


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def banner():
    print(C.RED + C.BOLD + WOLF + C.END)
    print(C.CYAN + C.BOLD + TITLE + C.END)
    print(C.RED + "  " + "=" * 46 + C.END)
    print(C.WHITE + "  W E B   S T R U C T U R E   E X T R A C T O R" + C.END)
    print(C.RED + "  " + "=" * 46 + C.END)
    print(f"  {C.GREY}developer {C.END}: {C.GREEN}{DEVELOPER}{C.END}")
    print(f"  {C.GREY}youtube   {C.END}: {C.GREEN}{YOUTUBE}{C.END}")
    print(f"  {C.GREY}version   {C.END}: {C.GREEN}{VERSION}{C.END}")
    print()


def info(msg):
    print(f"  {C.CYAN}[*]{C.END} {msg}")


def ok(msg):
    print(f"  {C.GREEN}[+]{C.END} {msg}")


def warn(msg):
    print(f"  {C.YELLOW}[!]{C.END} {msg}")


def fail(msg):
    print(f"  {C.RED}[-]{C.END} {msg}")


def prompt(label="wolfer@termux"):
    return input(f"  {C.RED}{label}{C.END}{C.GREY}:~${C.END} ").strip()


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def normalize_url(raw):
    raw = raw.strip()
    if not raw:
        return None
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = "https://" + raw
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return raw


def build_session():
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/css,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def fetch(session, url):
    """Download a URL with a size cap. Returns (response, bytes)."""
    resp = session.get(url, timeout=TIMEOUT, stream=True)
    resp.raise_for_status()
    chunks, size = [], 0
    for chunk in resp.iter_content(chunk_size=16384):
        size += len(chunk)
        if size > MAX_BYTES:
            raise ValueError("file exceeds the size limit")
        chunks.append(chunk)
    return resp, b"".join(chunks)


def human_size(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0


def local_name(url, ext, used):
    """Build a safe, unique filename for a remote asset."""
    path = unquote(urlparse(url).path)
    name = os.path.basename(path) or "file"
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    if not name.lower().endswith(ext):
        name += ext
    if name in used:
        stem, dot, suffix = name.rpartition(".")
        tag = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
        name = f"{stem}_{tag}.{suffix}" if dot else f"{name}_{tag}"
    used.add(name)
    return name


_CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)
_CSS_IMPORT = re.compile(r"@import\s+(['\"])(.+?)\1", re.IGNORECASE)


def absolutize_css(text, css_url):
    """Point relative url() and @import references at the original host."""

    def fix_url(match):
        quote, value = match.group(1), match.group(2).strip()
        if not value or value.startswith(("data:", "#")):
            return match.group(0)
        return f"url({quote}{urljoin(css_url, value)}{quote})"

    def fix_import(match):
        quote, value = match.group(1), match.group(2).strip()
        return f"@import {quote}{urljoin(css_url, value)}{quote}"

    text = _CSS_URL.sub(fix_url, text)
    return _CSS_IMPORT.sub(fix_import, text)


def collect_assets(soup, base_url):
    """Return a list of (tag, attribute, kind, absolute_url)."""
    found = []
    for tag in soup.find_all("link", href=True):
        rel = [r.lower() for r in (tag.get("rel") or [])]
        if "stylesheet" in rel:
            found.append((tag, "href", "css", urljoin(base_url, tag["href"].strip())))
    for tag in soup.find_all("script", src=True):
        found.append((tag, "src", "js", urljoin(base_url, tag["src"].strip())))
    return [item for item in found if urlparse(item[3]).scheme in ("http", "https")]


# --------------------------------------------------------------------------
# Core extraction
# --------------------------------------------------------------------------
def extract(target):
    session = build_session()
    started = time.time()

    info(f"target   : {C.WHITE}{target}{C.END}")
    info("fetching main document ...")
    try:
        resp, body = fetch(session, target)
    except requests.exceptions.SSLError:
        fail("SSL error. The certificate could not be verified.")
        return
    except requests.exceptions.ConnectionError:
        fail("Connection failed. Check the URL and your network.")
        return
    except requests.exceptions.Timeout:
        fail("Request timed out.")
        return
    except requests.exceptions.HTTPError as exc:
        fail(f"Server returned an error: {exc}")
        return
    except (requests.exceptions.RequestException, ValueError) as exc:
        fail(f"Could not fetch the page: {exc}")
        return

    final_url = resp.url
    ctype = resp.headers.get("Content-Type", "")
    if "html" not in ctype.lower():
        warn(f"Content-Type is '{ctype or 'unknown'}', expected HTML.")

    host = urlparse(final_url).netloc.replace(":", "_")
    out_dir = os.path.join(OUTPUT_ROOT, host)
    css_dir = os.path.join(out_dir, "assets", "css")
    js_dir = os.path.join(out_dir, "assets", "js")
    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)

    with open(os.path.join(out_dir, "index.original.html"), "wb") as fh:
        fh.write(body)
    ok(f"main document received ({human_size(len(body))})")

    soup = BeautifulSoup(body, "html.parser")
    base_tag = soup.find("base", href=True)
    base_url = urljoin(final_url, base_tag["href"]) if base_tag else final_url

    assets = collect_assets(soup, base_url)
    css_count = sum(1 for a in assets if a[2] == "css")
    js_count = sum(1 for a in assets if a[2] == "js")
    info(f"located  : {C.WHITE}{css_count}{C.END} stylesheet(s), "
         f"{C.WHITE}{js_count}{C.END} script(s)")
    print()

    used = {"css": set(), "js": set()}
    saved = {}  # absolute url -> relative local path
    stats = {"ok": 0, "failed": 0, "bytes": len(body)}

    for tag, attr, kind, url in assets:
        if url in saved:
            tag[attr] = saved[url]
            continue

        info(f"{kind:<3} {C.GREY}{url}{C.END}")
        try:
            aresp, data = fetch(session, url)
        except (requests.exceptions.RequestException, ValueError) as exc:
            fail(f"failed: {exc}")
            stats["failed"] += 1
            tag[attr] = url  # keep the page working online
            continue

        ext = ".css" if kind == "css" else ".js"
        name = local_name(url, ext, used[kind])
        folder = css_dir if kind == "css" else js_dir

        if kind == "css":
            encoding = aresp.encoding or "utf-8"
            text = data.decode(encoding, errors="replace")
            data = absolutize_css(text, url).encode("utf-8")

        with open(os.path.join(folder, name), "wb") as fh:
            fh.write(data)

        rel = f"assets/{kind}/{name}"
        saved[url] = rel
        tag[attr] = rel
        for junk in ("integrity", "crossorigin"):
            if junk in tag.attrs:
                del tag.attrs[junk]

        stats["ok"] += 1
        stats["bytes"] += len(data)
        ok(f"saved {C.GREEN}{rel}{C.END} ({human_size(len(data))})")

    if base_tag:
        base_tag.decompose()  # local paths must not resolve against the remote base

    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(str(soup))

    elapsed = time.time() - started
    print()
    print(C.RED + "  " + "-" * 46 + C.END)
    print(f"  {C.GREY}output    {C.END}: {C.WHITE}{os.path.abspath(out_dir)}{C.END}")
    print(f"  {C.GREY}downloaded{C.END}: {C.GREEN}{stats['ok']}{C.END} asset(s)")
    print(f"  {C.GREY}failed    {C.END}: "
          f"{(C.RED if stats['failed'] else C.GREEN)}{stats['failed']}{C.END}")
    print(f"  {C.GREY}total size{C.END}: {C.WHITE}{human_size(stats['bytes'])}{C.END}")
    print(f"  {C.GREY}time      {C.END}: {C.WHITE}{elapsed:.1f}s{C.END}")
    print(C.RED + "  " + "-" * 46 + C.END)
    ok("extraction complete")


# --------------------------------------------------------------------------
# Menu
# --------------------------------------------------------------------------
def about():
    print(f"  {C.WHITE}Wolfer Web Tools{C.END} v{VERSION}")
    print(f"  {C.GREY}developer  :{C.END} {DEVELOPER}")
    print(f"  {C.GREY}youtube    :{C.END} {YOUTUBE}")
    print(f"  {C.GREY}repository :{C.END} {REPO}")
    print()
    warn("Use this tool only on websites you own or have written permission to copy.")


def run_extract(url=None):
    if url is None:
        info("enter the target website URL (example.com or https://example.com)")
        url = prompt("target")
    target = normalize_url(url)
    if not target:
        fail("Invalid URL.")
        return
    print()
    extract(target)


def menu():
    print(f"  {C.RED}[1]{C.END} Extract website (HTML, CSS, JS)")
    print(f"  {C.RED}[2]{C.END} About")
    print(f"  {C.RED}[0]{C.END} Exit")
    print()


def main():
    if len(sys.argv) > 1:
        clear()
        banner()
        run_extract(sys.argv[1])
        return

    while True:
        clear()
        banner()
        menu()
        choice = prompt()
        print()
        if choice == "1":
            run_extract()
        elif choice == "2":
            about()
        elif choice in ("0", "q", "exit"):
            print(f"  {C.RED}Stay sharp. Wolfer out.{C.END}")
            break
        else:
            fail("Unknown option.")
        print()
        input(f"  {C.GREY}Press Enter to continue ...{C.END}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  {C.RED}[-] Interrupted. Exiting.{C.END}")
        sys.exit(130)
