#!/usr/bin/env python3
# scrape_abyss.py
from scrape_common import *
import json, re

GROUP = "abyss"

def main():
    conf = load_sources_yaml().get(GROUP)
    if not conf: print("[abyss] no config"); return
    base = conf.get("base") or ""
    if not base: print("[abyss] empty base"); return

    s = session_tor()
    rows = []
    data_url = conf.get("data_url", "/static/data.js")
    regexes = [re.compile(rx, re.S) for rx in conf.get("js_variable_regexes", [])]
    fmap = conf.get("field_mapping", {})

    try:
        text, _ = fetch(s, base, data_url)
        payload = None
        for rx in regexes:
            m = rx.search(text)
            if m: payload = m.group(1); break
        if not payload:
            print("[abyss] unable to locate data array"); return
        data = json.loads(payload.strip().rstrip(";"))
        for item in data:
            victim = item.get(fmap.get("victim","title"), "")
            website = item.get(fmap.get("links","links"), [])
            website = website[0] if isinstance(website, list) and website else ""
            add_row(rows,
                group=GROUP,
                victim=victim,
                website=website,
                country=item.get(fmap.get("country","country"), ""),
                sector=item.get(fmap.get("sector","sector"), ""),
                data_types=item.get(fmap.get("datatypes","tags"), []),
                date=item.get(fmap.get("date","date"), ""),
                source_path=data_url,
                post_url="",
                notes=item.get(fmap.get("description","text"), "")[:160]
            )
    except Exception as e:
        print("[abyss] error:", e)

    out = f"data/raw/{GROUP}_{datestamp()}.csv"
    write_csv_atomic(rows, out)
    print(f"[abyss] wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()