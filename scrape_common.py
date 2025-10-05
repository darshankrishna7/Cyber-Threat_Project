# scrape_common.py
import csv, re, time, yaml, os, sys
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

TOR_PROXIES = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; rv:115.0) "
                   "Gecko/20100101 Firefox/115.0"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.7",
    "Connection": "close",
}
COLUMNS = [
    "group", "victim", "domain", "website", "country", "sector",
    "data_types", "date", "size", "views", "source_path", "post_url", "notes"
]

def session_tor():
    s = requests.Session()
    s.proxies.update(TOR_PROXIES)
    s.headers.update(HEADERS)
    return s

def load_sources_yaml(path="sources.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        y = yaml.safe_load(f)
    confs = {src["group"]: src for src in y.get("sources", []) if "group" in src}
    return confs

def fetch(session, base, path="/", method="GET", headers=None, data=None, timeout=45, allow_redirects=True):
    url = urljoin(base, path)
    h = dict(HEADERS)
    if headers: h.update(headers)
    if method.upper() == "POST":
        r = session.post(url, headers=h, data=data or {}, timeout=timeout)
    else:
        r = session.get(url, headers=h, timeout=timeout, allow_redirects=allow_redirects)
    r.raise_for_status()
    return r.text, url

def bs(html):  # shorthand
    return BeautifulSoup(html, "html.parser")

def select_text(node, sel, default=""):
    el = node.select_one(sel) if sel else None
    return (el.get_text(strip=True) if el else default)

def select_attr(node, sel, attr, default=""):
    el = node.select_one(sel) if sel else None
    return (el.get(attr, default) if el and el.has_attr(attr) else default)

def regex_search(pattern, text, flags=0, group=1, default=""):
    m = re.search(pattern, text or "", flags)
    return (m.group(group) if m else default)

def clean_space(s):
    return re.sub(r"\s+", " ", (s or "")).strip()

def add_row(rows, **kw):
    row = {k: kw.get(k, "") for k in COLUMNS}
    for k in row:
        v = row[k]
        if isinstance(v, (list, tuple, set)):
            v = ", ".join(map(str, v))
        row[k] = clean_space("" if v is None else str(v))
    rows.append(row)

def write_csv_atomic(rows, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, out_path)  # atomic move

def datestamp():
    return datetime.now().strftime("%Y%m%d")