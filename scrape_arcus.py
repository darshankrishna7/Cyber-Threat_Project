#!/usr/bin/env python3
# scrape_arcus.py
from scrape_common import *

GROUP = "arcus"

def main():
    confs = load_sources_yaml()
    conf = confs.get(GROUP)
    if not conf: 
        print("[arcus] no config"); return
    base = conf.get("base") or ""
    if not base: 
        print("[arcus] empty base"); return

    s = session_tor()
    rows = []
    for path in conf.get("list_paths", ["/"]):
        try:
            html, url = fetch(s, base, path)
            soup = bs(html)
            for art in soup.select(conf.get("block_selector", "")):
                title_el = art.select_one(conf.get("victim_selector",""))
                victim = title_el.get_text(strip=True) if title_el else ""
                href = select_attr(art, conf.get("post_link_selector",""), "href", "")
                post_url = urljoin(base, href) if href else ""
                d_el = art.select_one(conf.get("date_selector",""))
                date = (d_el.get("datetime") if d_el and d_el.has_attr("datetime") 
                        else (d_el.get_text(strip=True) if d_el else ""))
                sector = ", ".join([a.get_text(strip=True) for a in art.select(conf.get("category_selector",""))])
                excerpt = select_text(art, conf.get("excerpt_selector",""))

                add_row(rows,
                    group=GROUP, victim=victim, sector=sector, date=date,
                    source_path=path, post_url=post_url, notes=excerpt
                )
        except Exception as e:
            print("[arcus] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[arcus] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()