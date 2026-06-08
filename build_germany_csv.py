import json
import csv
from pathlib import Path

INPUT_FILE = Path("data/openfoodfacts_germany.jsonl")
OUTPUT_FILE = Path("data/openfoodfacts_germany_clean.csv")

FIELDS = [
    "code",
    "product_name",
    "brands",
    "stores",
    "categories",
    "nutriscore_grade",
    "nova_group",
    "ecoscore_grade",
    "countries",
    "energy-kcal_100g",
    "fat_100g",
    "saturated-fat_100g",
    "carbohydrates_100g",
    "sugars_100g",
    "proteins_100g",
    "salt_100g"
]

count = 0

with OUTPUT_FILE.open("w", newline="", encoding="utf-8-sig") as fout:
    writer = csv.DictWriter(fout, fieldnames=FIELDS)
    writer.writeheader()

    with INPUT_FILE.open("r", encoding="utf-8", errors="ignore") as fin:

        for line in fin:

            try:
                p = json.loads(line)
            except:
                continue

            nutriments = p.get("nutriments", {})

            row = {
                "code": p.get("code"),
                "product_name": p.get("product_name"),
                "brands": p.get("brands"),
                "stores": p.get("stores"),
                "categories": p.get("categories"),
                "nutriscore_grade": p.get("nutriscore_grade"),
                "nova_group": p.get("nova_group"),
                "ecoscore_grade": p.get("ecoscore_grade"),
                "countries": p.get("countries"),
                "energy-kcal_100g": nutriments.get("energy-kcal_100g"),
                "fat_100g": nutriments.get("fat_100g"),
                "saturated-fat_100g": nutriments.get("saturated-fat_100g"),
                "carbohydrates_100g": nutriments.get("carbohydrates_100g"),
                "sugars_100g": nutriments.get("sugars_100g"),
                "proteins_100g": nutriments.get("proteins_100g"),
                "salt_100g": nutriments.get("salt_100g"),
            }

            writer.writerow(row)

            count += 1

            if count % 50000 == 0:
                print(f"Processed {count:,}")

print("DONE")
print(f"Saved: {OUTPUT_FILE}")
print(f"Products: {count:,}")
