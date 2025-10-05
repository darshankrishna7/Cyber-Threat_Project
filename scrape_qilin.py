#!/usr/bin/env python3
# scrape_qilin.py
from scrape_common import *

GROUP = "qilin"

def main():
    conf = load_sources_yaml().get(GROUP)
    if not conf: print("[qilin] no config"); return
    base = conf.get("base") or ""
    if not base: print("[qilin] empty base"); return

    s = session_tor()
    rows = []
    for path in conf.get("list_paths", ["/"]):
        try:
            html, _ = fetch(s, base, path)
            soup = bs(html)
            for box in soup.select(conf.get("block_selector","")):
                a = box.select_one(conf.get("post_link_selector",""))
                victim = a.get_text(strip=True) if a else ""
                href = a.get("href","") if a else ""
                post_url = urljoin(base, href) if href else ""

                # card fields
                date = ""
                date_icon = box.select_one(conf.get("date_icon_selector",""))
                if date_icon and date_icon.parent:
                    date = clean_space(date_icon.parent.get_text(" ", strip=True))
                website = select_attr(box, conf.get("website_selector",""), "href","")
                size = ""

                # detail page for extras
                if post_url:
                    try:
                        dhtml, _ = fetch(s, post_url)
                        dsoup = bs(dhtml)
                        website = select_attr(dsoup, conf["post_page"].get("website_selector",""), "href","") or website
                        if conf["post_page"].get("size_next_text"):
                            size_el = dsoup.select_one(conf["post_page"].get("size_icon_selector",""))
                            size = size_el.get_text(strip=True) if size_el else ""
                    except Exception:
                        pass

                add_row(rows,
                    group=GROUP, victim=victim, website=website, date=date, size=size,
                    source_path=path, post_url=post_url
                )
        except Exception as e:
            print("[qilin] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[qilin] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()