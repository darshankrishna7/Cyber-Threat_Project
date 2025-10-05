#!/usr/bin/env python3
# scrape_sarcoma.py
from scrape_common import *

GROUP = "sarcoma"

def main():
    conf = load_sources_yaml().get(GROUP)
    if not conf: print("[sarcoma] no config"); return
    base = conf.get("base") or ""
    if not base: print("[sarcoma] empty base"); return

    s = session_tor()
    rows = []
    for path in conf.get("list_paths", ["/"]):
        try:
            html, _ = fetch(s, base, path)
            soup = bs(html)
            for card in soup.select(conf.get("block_selector","")):
                title_block = card.select_one(conf.get("card_title_selector",""))
                views = regex_search(conf.get("views_regex", r"^(\d+)"), title_block.get_text(" ", strip=True) if title_block else "")
                # victim name appears after the first <hr> within the title area
                victim = ""
                if title_block:
                    parts = [t.strip() for t in title_block.stripped_strings]
                    if parts: victim = parts[-1]

                facts = select_text(card, conf.get("facts_selector",""))
                website = regex_search(conf.get("site_regex", r"Site:\s*([^\n<]+)"), facts)
                sector  = regex_search(conf.get("industry_regex", r"Industry:\s*([^\n<]+)"), facts)
                country = regex_search(conf.get("country_regex", r"GEO:\s*([^\n<]+)"), facts)

                # modal detail present in same page
                btn = card.select_one(conf.get("list_item_selector",""))
                size = data_types = desc = ""
                if btn and btn.has_attr(conf.get("list_item_id_attr","data-bs-target")):
                    target = btn.get(conf.get("list_item_id_attr","data-bs-target"))
                    mid = regex_search(conf.get("list_item_id_regex", r"#company_(\d+)"), target)
                    if mid:
                        modal_sel = conf.get("detail_container_template","").replace("{{id}}", mid)
                        modal = soup.select_one(modal_sel)
                        if modal:
                            desc = select_text(modal, conf.get("detail_description_selector",""))
                            txt = modal.get_text(" ", strip=True)
                            size = regex_search(conf.get("detail_size_regex", r"Leak size:\s*([^\n<]+)"), txt)
                            contains = regex_search(conf.get("detail_contains_regex", r"Contains:\s*([^\n<]+)"), txt)
                            if contains: data_types = contains

                add_row(rows,
                    group=GROUP, victim=victim, website=website, sector=sector, country=country,
                    size=size, views=views, data_types=data_types, source_path=path, post_url="", notes=desc[:160]
                )
        except Exception as e:
            print("[sarcoma] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[sarcoma] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()