#!/usr/bin/env python3
# scrape_everest.py
from scrape_common import *

GROUP = "everest"

def main():
    conf = load_sources_yaml().get(GROUP)
    if not conf: print("[everest] no config"); return
    base = conf.get("base") or ""
    if not base: print("[everest] empty base"); return

    s = session_tor()
    rows = []
    try:
        req = conf.get("list_request", {})
        html, _ = fetch(s, base, req.get("path","/controllers/news"),
                        method=req.get("method","POST"),
                        headers=req.get("headers",{}),
                        data=req.get("body",{}))
        soup = bs(html)
        list_sel = conf.get("list_item_selector",".js-open-chat")
        id_attr  = conf.get("list_item_id_attr","data-translit")

        for item in soup.select(list_sel):
            translit = item.get(id_attr, "")
            victim = item.get_text(strip=True)
            date = website = size = desc = ""
            # detail
            try:
                dreq = conf.get("detail_request", {})
                dhtml, _ = fetch(s, base, dreq.get("path","/controllers/news_card"),
                                 method=dreq.get("method","POST"),
                                 headers=dreq.get("headers",{}),
                                 data={"translit": translit})
                dsoup = bs(dhtml)
                victim = select_text(dsoup, conf.get("victim_selector","")) or victim
                date   = select_text(dsoup, conf.get("date_selector",""))
                website= select_attr(dsoup, conf.get("website_selector",""), "href","")
                size   = select_text(dsoup, conf.get("size_selector",""))
                desc   = select_text(dsoup, conf.get("description_selector",""))
            except Exception:
                pass

            add_row(rows,
                group=GROUP, victim=victim, website=website, date=date, size=size,
                source_path=req.get("path","/controllers/news"), post_url="", notes=desc[:160]
            )
    except Exception as e:
        print("[everest] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[everest] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()