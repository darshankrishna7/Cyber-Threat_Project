# images_to_csv.py
import os, re, csv, json, base64
from dateutil import parser as dparser
from openai import OpenAI

client = OpenAI()

IN_DIR  = "screenshots/Dragonforce"     # screenshots input dir
OUT_CSV = "csv_output_raw/out_dragonforce.csv"
GROUP   = "dragonforce"

# Canonical taxonomy for data_types
DATA_TYPE_TAXONOMY = [
    "PII/Personal Data",
    "Financial",
    "HR/Payroll",
    "Emails",
    "Customer Data",
    "Databases",
    "Backups/Archives",
    "Source Code",
    "Credentials/Access",
    "Legal",
    "Medical/PHI",
    "Operational",
]

# keyword -> canonical label mapping
DATA_TYPE_KEYWORDS = {
    # PII
    "personal id": "PII/Personal Data",
    "id card": "PII/Personal Data",
    "passport": "PII/Personal Data",
    "drivers license": "PII/Personal Data",
    "ssn": "PII/Personal Data",
    "customer contacts": "PII/Personal Data",
    "contact": "PII/Personal Data",
    "address": "PII/Personal Data",
    # Financial
    "financial": "Financial",
    "accounting": "Financial",
    "invoice": "Financial",
    "bank": "Financial",
    # HR
    "payroll": "HR/Payroll",
    "hr": "HR/Payroll",
    "employee": "HR/Payroll",
    # Emails
    "email": "Emails",
    "mailbox": "Emails",
    # Customer
    "crm": "Customer Data",
    "customer": "Customer Data",
    "client": "Customer Data",
    # DB
    "sql": "Databases",
    "database": "Databases",
    "mongodb": "Databases",
    "postgres": "Databases",
    # Backups
    "backup": "Backups/Archives",
    "archive": "Backups/Archives",
    # Source code
    "source code": "Source Code",
    "git": "Source Code",
    "repository": "Source Code",
    # Credentials
    "credential": "Credentials/Access",
    "password": "Credentials/Access",
    "vpn": "Credentials/Access",
    # Legal
    "contract": "Legal",
    "litigation": "Legal",
    # Medical
    "patient": "Medical/PHI",
    "medical": "Medical/PHI",
    "phi": "Medical/PHI",
    # Operational
    "erp": "Operational",
    "manufactur": "Operational",
    "operations": "Operational",
}

def canonicalize_data_types(items, fallback_text=""):
    found = set()
    # map from provided list
    for it in (items or []):
        s = str(it).lower()
        for k, lab in DATA_TYPE_KEYWORDS.items():
            if k in s:
                found.add(lab)
    # also scan fallback text
    s = (fallback_text or "").lower()
    for k, lab in DATA_TYPE_KEYWORDS.items():
        if k in s:
            found.add(lab)
    # return in canonical ordering
    ordered = [lab for lab in DATA_TYPE_TAXONOMY if lab in found]
    return ordered

SCHEMA = {
  "type":"object",
  "properties":{
    "group":{"type":"string"},
    "victim":{"type":"string"},
    "website":{"type":"string"},
    "date_iso":{"type":"string"},
    "country":{"type":"string"},
    "sector":{"type":"string"},
    "data_types":{"type":"array","items":{"type":"string"}},
    "size_gb":{"type":["number","null"]},
    "notes":{"type":"string"}
  },
  "required":["group","victim"]
}

PROMPT = (
  "You are an information extractor. The input is a screenshot of a single ransomware victim post.\n"
  "Extract fields and return a JSON object EXACTLY matching the schema below.\n"
  "Rules:\n"
  "- Output ONLY JSON (no prose).\n"
  "- If a field is missing in the image, return '' for strings, [] for arrays, null for size_gb.\n"
  "- Normalize dates to YYYY-MM-DD when possible; else ''.\n"
  "- Use ISO-2 for country when obvious (e.g., United States->US, Germany->DE). If flag or GEO present, map it.\n"
  "- Convert sizes like '2.9 TB', '387.6 GB', '700 MB' to numeric size_gb when possible.\n"
  "- Do not invent facts not visible in the image.\n"
  f"- Set group='{GROUP}'.\n"
  "- VERY IMPORTANT: For data_types, choose ZERO OR MORE labels only from this EXACT list (no other words):\n"
  + " | ".join(DATA_TYPE_TAXONOMY) + "\n"
  "Schema:\n" + json.dumps(SCHEMA)
)

NAME2ISO = {
    "united states":"US","usa":"US","germany":"DE","france":"FR","italy":"IT","spain":"ES",
    "netherlands":"NL","singapore":"SG","united kingdom":"GB","uk":"GB","canada":"CA","mexico":"MX",
    "brazil":"BR","australia":"AU","india":"IN","japan":"JP","china":"CN"
}

def to_iso_date(s):
    s = (s or "").strip()
    if not s: return ""
    for dayfirst in (False, True):
        try:
            return dparser.parse(s, fuzzy=True, dayfirst=dayfirst).strftime("%Y-%m-%d")
        except Exception:
            pass
    return ""

def size_to_gb(s):
    if not s: return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB|MB|TiB|GiB|MiB)", s, re.I)
    if not m: return None
    val = float(m.group(1)); unit = m.group(2).upper()
    mult = {"MB":1/1024,"GB":1,"TB":1024,"MIB":1/1024,"GIB":1,"TIB":1024}.get(unit)
    return round(val*mult, 1) if mult else None

def iso2_country(s):
    s = (s or "").strip().lower()
    if len(s)==2 and s.isalpha(): return s.upper()
    return NAME2ISO.get(s, "")

def encode_image(path):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def extract_from_image(img_path):
    img_url = encode_image(img_path)
    resp = client.chat.completions.create(
        model="gpt-5",
        response_format={"type":"json_object"},
        messages=[
            {"role":"system","content":"You output strictly valid JSON object and nothing else."},
            {"role":"user","content":[
                {"type":"text","text":PROMPT},
                {"type":"image_url","image_url":{"url":img_url}}
            ]}
        ],
        # temperature=0
    )
    obj = json.loads(resp.choices[0].message.content)

    # normalize
    o = obj
    o["group"]   = GROUP
    o["victim"]  = (o.get("victim") or "").strip()
    o["website"] = (o.get("website") or "").strip()
    o["notes"]   = (o.get("notes") or "").strip()
    o["date_iso"]= to_iso_date(o.get("date_iso",""))
    o["country"] = iso2_country(o.get("country",""))
    sz = o.get("size_gb")
    if isinstance(sz, str): o["size_gb"] = size_to_gb(sz)
    # normalize data_types to canonical taxonomy
    raw_dt = o.get("data_types")
    if isinstance(raw_dt, str):
        raw_list = [t.strip() for t in re.split(r"[;,/]", raw_dt) if t.strip()]
    else:
        raw_list = list(raw_dt or [])
    o["data_types"] = canonicalize_data_types(raw_list, fallback_text=o.get("notes",""))
    return o

def main():
    rows = []
    for fn in sorted(os.listdir(IN_DIR)):
        if not fn.lower().endswith((".png",".jpg",".jpeg")): continue
        path = os.path.join(IN_DIR, fn)
        try:
            o = extract_from_image(path)
            o["image_file"] = fn
            rows.append(o)
            print("ok:", fn, "->", o.get("victim",""))
        except Exception as e:
            print("fail:", fn, e)

    cols = ["group","victim","website","date_iso","country","sector","data_types","size_gb","notes","image_file"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            r = dict(r)
            r["data_types"] = "; ".join(r.get("data_types") or [])
            w.writerow({k: r.get(k,"") for k in cols})
    print("Wrote", OUT_CSV, "rows:", len(rows))

if __name__ == "__main__":
    main()