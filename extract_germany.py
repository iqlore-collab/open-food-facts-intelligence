import json
from pathlib import Path

INFILE = Path("data/openfoodfacts-products.jsonl")
OUTFILE = Path("data/openfoodfacts_germany.jsonl")

def is_germany_product(p):
    text = " ".join([
        str(p.get("countries", "")),
        str(p.get("countries_tags", "")),
        str(p.get("countries_en", "")),
        str(p.get("stores", "")),
    ]).lower()

    return (
        "germany" in text
        or "deutschland" in text
        or "en:germany" in text
        or "de:" in text
    )

count_total = 0
count_de = 0

with INFILE.open("r", encoding="utf-8", errors="ignore") as f_in, OUTFILE.open("w", encoding="utf-8") as f_out:
    for line in f_in:
        count_total += 1

        if count_total % 100000 == 0:
            print(f"Checked: {count_total:,} | Germany: {count_de:,}")

        try:
            product = json.loads(line)
        except Exception:
            continue

        if is_germany_product(product):
            f_out.write(json.dumps(product, ensure_ascii=False) + "\n")
            count_de += 1

print("DONE")
print(f"Total checked: {count_total:,}")
print(f"Germany products: {count_de:,}")
print(f"Saved to: {OUTFILE}")
