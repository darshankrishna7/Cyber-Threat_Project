#!/usr/bin/env python3
# scrape_killsec.py
from scrape_common import *
import re

GROUP = "killsec"

def main():
    conf = load_sources_yaml().get(GROUP)
    if not conf: print("[killsec] no config"); return
    base = conf.get("base") or ""
    if not base: print("[killsec] empty base"); return

    s = session_tor()
    rows = []
    for path in conf.get("list_paths", ["/index.php"]):
        try:
            html, _ = fetch(s, base, path)
            soup = bs(html)
            for a in soup.select(conf.get("block_selector","")):
                pid   = a.get(conf.get("post_id_attr","id"), "")
                href  = a.get(conf.get("post_href_attr","href"), "")
                stat  = a.get(conf.get("status_attr","stat"), "")
                pinned= a.get(conf.get("pinned_attr","pinned"), "")
                title_attr=a.get(conf.get("title_attr","title"), "")

                victim = select_text(a, conf.get("victim_selector",""))
                domain = select_text(a, conf.get("domain_selector",""))
                flag_src = select_attr(a, conf.get("country_flag_selector",""), "src","")
                m = re.search(r"/locales/([a-z]{2})\.svg", flag_src or "", re.I)
                country = (m.group(1).upper() if m else "")
                timer = select_text(a, conf.get("countdown_selector",""))
                price = select_text(a, conf.get("price_selector",""))
                disclosures = select_text(a, conf.get("disclosures_selector",""))

                add_row(rows,
                    group=GROUP, victim=victim, domain=domain, country=country,
                    source_path=path, post_url=urljoin(base, href) if href else "",
                    notes=f"status={stat} pinned={pinned} title={title_attr} timer={timer} price={price} disclosures={disclosures}"
                )
        except Exception as e:
            print("[killsec] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[killsec] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()