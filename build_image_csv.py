import json
import csv
from pathlib import Path

INPUTS = [
    ("Germany", Path("data/openfoodfacts_germany.jsonl"), Path("data/openfoodfacts_germany_images.csv")),
    ("Poland", Path("data/openfoodfacts_poland.jsonl"), Path("data/openfoodfacts_poland_images.csv")),
]

FIELDS = [
    "code", "market", "product_name", "brands", "stores", "categories",
    "nutriscore_grade", "nova_group", "ecoscore_grade",
    "image_url", "image_front_url", "image_front_small_url",
    "energy-kcal_100g", "sugars_100g", "salt_100g", "fat_100g", "proteins_100g"
]

for market, infile, outfile in INPUTS:
    if not infile.exists():
        print(f"Missing: {infile}")
        continue

    count = 0

    with outfile.open("w", newline="", encoding="utf-8-sig") as fout:
        writer = csv.DictWriter(fout, fieldnames=FIELDS)
        writer.writeheader()

        with infile.open("r", encoding="utf-8", errors="ignore") as fin:
            for line in fin:
                try:
                    p = json.loads(line)
                except:
                    continue

                nutr = p.get("nutriments", {})

                row = {
                    "code": p.get("code"),
                    "market": market,
                    "product_name": p.get("product_name"),
                    "brands": p.get("brands"),
                    "stores": p.get("stores"),
                    "categories": p.get("categories"),
                    "nutriscore_grade": p.get("nutriscore_grade"),
                    "nova_group": p.get("nova_group"),
                    "ecoscore_grade": p.get("ecoscore_grade"),
                    "image_url": p.get("image_url"),
                    "image_front_url": p.get("image_front_url"),
                    "image_front_small_url": p.get("image_front_small_url"),
                    "energy-kcal_100g": nutr.get("energy-kcal_100g"),
                    "sugars_100g": nutr.get("sugars_100g"),
                    "salt_100g": nutr.get("salt_100g"),
                    "fat_100g": nutr.get("fat_100g"),
                    "proteins_100g": nutr.get("proteins_100g"),
                }

                writer.writerow(row)
                count += 1

                if count % 50000 == 0:
                    print(f"{market}: {count:,}")

    print(f"DONE {market}: {count:,} -> {outfile}")
