#!/usr/bin/env python3
# scrape_safepay.py
from scrape_common import *

GROUP = "safepay"

def main():
    conf = load_sources_yaml().get(GROUP)
    if not conf: print("[safepay] no config"); return
    base = conf.get("base") or ""
    if not base: print("[safepay] empty base"); return

    s = session_tor()
    rows = []
    for path in conf.get("list_paths", ["/blog/"]):
        try:
            html, _ = fetch(s, base, path)
            soup = bs(html)
            for card in soup.select(conf.get("block_selector","")):
                victim = select_text(card, conf.get("victim_selector",""))
                post_href = select_attr(card, conf.get("post_link_selector",""), "href","")
                post_url = urljoin(base, post_href) if post_href else ""
                country = ""
                flag_alt = select_attr(card, conf.get("country_flag_selector",""), conf.get("country_attr","alt"), "")
                if flag_alt: country = flag_alt.upper()
                views = regex_search(conf.get("views_regex", r"(\d+)"), select_text(card, conf.get("views_selector","")))

                date = size = website = desc = ""
                if post_url:
                    try:
                        dhtml, _ = fetch(s, post_url)
                        dsoup = bs(dhtml)
                        meta = select_text(dsoup, conf["post_page"].get("meta_selector",""))
                        date = regex_search(conf["post_page"].get("date_regex", r"(\d{4}-\d{2}-\d{2})"), meta)
                        views2 = regex_search(conf["post_page"].get("views_regex", r"(\d+)"), meta)
                        if views2: views = views2
                        desc = " ".join([p.get_text(strip=True) for p in dsoup.select(conf["post_page"].get("description_selector",""))])
                        website = select_attr(dsoup, "a[href^='http']", "href","")
                    except Exception:
                        pass

                add_row(rows,
                    group=GROUP, victim=victim, country=country, website=website,
                    date=date, size=size, views=views, source_path=path, post_url=post_url, notes=desc[:160]
                )
        except Exception as e:
            print("[safepay] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[safepay] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()