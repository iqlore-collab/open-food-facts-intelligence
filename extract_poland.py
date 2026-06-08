import json
from pathlib import Path

INFILE = Path("data/openfoodfacts-products.jsonl")
OUTFILE = Path("data/openfoodfacts_poland.jsonl")

def is_poland_product(p):
    text = " ".join([
        str(p.get("countries", "")),
        str(p.get("countries_tags", "")),
        str(p.get("countries_en", "")),
        str(p.get("stores", "")),
    ]).lower()

    return (
        "poland" in text
        or "polska" in text
        or "pologne" in text
        or "en:poland" in text
        or "pl:" in text
    )

count_total = 0
count_pl = 0

with INFILE.open("r", encoding="utf-8", errors="ignore") as f_in, OUTFILE.open("w", encoding="utf-8") as f_out:
    for line in f_in:
        count_total += 1

        if count_total % 100000 == 0:
            print(f"Checked: {count_total:,} | Poland: {count_pl:,}")

        try:
            product = json.loads(line)
        except Exception:
            continue

        if is_poland_product(product):
            f_out.write(json.dumps(product, ensure_ascii=False) + "\n")
            count_pl += 1

print("DONE")
print(f"Total checked: {count_total:,}")
print(f"Poland products: {count_pl:,}")
print(f"Saved to: {OUTFILE}")
