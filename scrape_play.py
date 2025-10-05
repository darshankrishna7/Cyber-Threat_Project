#!/usr/bin/env python3
# scrape_play.py
from scrape_common import *

GROUP = "play"

def main():
    conf = load_sources_yaml().get(GROUP)
    if not conf: print("[play] no config"); return
    base = conf.get("base") or ""
    if not base: print("[play] empty base"); return

    s = session_tor()
    rows = []
    for path in conf.get("list_paths", ["/index.php"]):
        try:
            html, _ = fetch(s, base, path)
            soup = bs(html)
            for th in soup.select(conf.get("block_selector","th.News")):
                text = th.get_text(" ", strip=True)
                onclick = th.get(conf.get("onclick_id_attr","onclick"), "")
                pid = regex_search(conf.get("onclick_id_regex", r"viewtopic\('(.*?)'\)"), onclick)
                # country/domain are shown after icons; if not in DOM, you can leave blank
                country = select_text(th, conf.get("country_icon_selector",""))
                domain = select_text(th, conf.get("domain_icon_selector",""))
                views = regex_search(conf.get("views_regex", r"views:\s*(\d+)"), text)
                added = regex_search(conf.get("added_regex", r"added:\s*([0-9-]+)"), text)
                pub = regex_search(conf.get("publication_regex", r"publication date:\s*([0-9-]+)"), text)
                status = select_text(th, conf.get("status_selector",""))
                victim = th.contents[0].strip() if th.contents and isinstance(th.contents[0], str) else ""

                post_url = urljoin(base, f"topic.php?id={pid}") if pid else ""
                size = sector = ""
                if post_url:
                    try:
                        dhtml, _ = fetch(s, post_url, allow_redirects=True)
                        dtxt = bs(dhtml).get_text("\n", strip=True)
                        size = regex_search(conf["post_page"]["size_regex"], dtxt)
                        sector = regex_search(conf["post_page"]["info_regex"], dtxt)
                    except Exception:
                        pass

                add_row(rows,
                    group=GROUP, victim=victim, domain=domain, country=country,
                    sector=sector, date=(pub or added), size=size, views=views,
                    source_path=path, post_url=post_url, notes=status
                )
        except Exception as e:
            print("[play] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[play] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()