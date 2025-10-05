#!/usr/bin/env python3
# scrape_rhysida.py
from scrape_common import *

GROUP = "rhysida"

def main():
    conf = load_sources_yaml().get(GROUP)
    if not conf: print("[rhysida] no config"); return
    base = conf.get("base") or ""
    if not base: print("[rhysida] empty base"); return

    s = session_tor()
    rows = []
    try:
        lreq = conf.get("list_request", {})
        html, _ = fetch(s, base, lreq.get("path","/archive.php"),
                        method=lreq.get("method","GET"))
        soup = bs(html)
        id_attr = conf.get("list_item_id_attr","data-company")
        for btn in soup.select(conf.get("list_item_selector","button[data-company]")):
            cid = btn.get(id_attr,"")
            dreq = conf.get("detail_request", {})
            try:
                dhtml, _ = fetch(s, base, dreq.get("path_template","/archive.php?company={{id}}").replace("{{id}}", cid),
                                 method=dreq.get("method","GET"))
                dsoup = bs(dhtml)
                title = select_text(dsoup, conf.get("title_selector",""))
                website = select_attr(dsoup, conf.get("website_selector",""), "href","")
                dtxt = dsoup.get_text(" ", strip=True)
                size = regex_search(conf.get("size_regex", r"([0-9.]+\s*(?:TB|GB|MB))"), dtxt)
                date = regex_search(conf.get("date_regex", r"(\d{4}-\d{2}-\d{2})"), dtxt)
                desc = select_text(dsoup, conf.get("description_selector",""))
            except Exception:
                title=website=size=date=desc=""

            add_row(rows,
                group=GROUP, victim=title, website=website, date=date, size=size,
                source_path=lreq.get("path","/archive.php"), post_url="", notes=desc[:160]
            )
    except Exception as e:
        print("[rhysida] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[rhysida] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()