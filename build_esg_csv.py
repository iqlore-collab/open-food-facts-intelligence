import json
import csv
from pathlib import Path

COUNTRIES = {
    "germany": {
        "input": Path("data/openfoodfacts_germany.jsonl"),
        "output": Path("data/openfoodfacts_germany_esg.csv"),
        "market": "Germany"
    },
    "poland": {
        "input": Path("data/openfoodfacts_poland.jsonl"),
        "output": Path("data/openfoodfacts_poland_esg.csv"),
        "market": "Poland"
    }
}

FIELDS = [
    "code", "market", "product_name", "brands", "stores", "categories",
    "labels", "labels_tags", "ingredients_text",
    "nutriscore_grade", "nova_group", "ecoscore_grade",
    "countries",
    "energy-kcal_100g", "fat_100g", "saturated-fat_100g",
    "carbohydrates_100g", "sugars_100g", "proteins_100g", "salt_100g",
    "packaging", "packaging_tags",
    "traces", "allergens",
    "manufacturing_places",
    "origins",
    "data_quality_errors_tags",
    "data_quality_warnings_tags"
]

def get_nutriment(p, key):
    return p.get("nutriments", {}).get(key)

for name, cfg in COUNTRIES.items():
    input_file = cfg["input"]
    output_file = cfg["output"]

    if not input_file.exists():
        print(f"SKIP missing: {input_file}")
        continue

    count = 0

    with output_file.open("w", newline="", encoding="utf-8-sig") as fout:
        writer = csv.DictWriter(fout, fieldnames=FIELDS)
        writer.writeheader()

        with input_file.open("r", encoding="utf-8", errors="ignore") as fin:
            for line in fin:
                try:
                    p = json.loads(line)
                except:
                    continue

                row = {
                    "code": p.get("code"),
                    "market": cfg["market"],
                    "product_name": p.get("product_name"),
                    "brands": p.get("brands"),
                    "stores": p.get("stores"),
                    "categories": p.get("categories"),
                    "labels": p.get("labels"),
                    "labels_tags": ",".join(p.get("labels_tags", [])) if isinstance(p.get("labels_tags"), list) else p.get("labels_tags"),
                    "ingredients_text": p.get("ingredients_text"),
                    "nutriscore_grade": p.get("nutriscore_grade"),
                    "nova_group": p.get("nova_group"),
                    "ecoscore_grade": p.get("ecoscore_grade"),
                    "countries": p.get("countries"),
                    "energy-kcal_100g": get_nutriment(p, "energy-kcal_100g"),
                    "fat_100g": get_nutriment(p, "fat_100g"),
                    "saturated-fat_100g": get_nutriment(p, "saturated-fat_100g"),
                    "carbohydrates_100g": get_nutriment(p, "carbohydrates_100g"),
                    "sugars_100g": get_nutriment(p, "sugars_100g"),
                    "proteins_100g": get_nutriment(p, "proteins_100g"),
                    "salt_100g": get_nutriment(p, "salt_100g"),
                    "packaging": p.get("packaging"),
                    "packaging_tags": ",".join(p.get("packaging_tags", [])) if isinstance(p.get("packaging_tags"), list) else p.get("packaging_tags"),
                    "traces": p.get("traces"),
                    "allergens": p.get("allergens"),
                    "manufacturing_places": p.get("manufacturing_places"),
                    "origins": p.get("origins"),
                    "data_quality_errors_tags": ",".join(p.get("data_quality_errors_tags", [])) if isinstance(p.get("data_quality_errors_tags"), list) else p.get("data_quality_errors_tags"),
                    "data_quality_warnings_tags": ",".join(p.get("data_quality_warnings_tags", [])) if isinstance(p.get("data_quality_warnings_tags"), list) else p.get("data_quality_warnings_tags"),
                }

                writer.writerow(row)
                count += 1

                if count % 50000 == 0:
                    print(f"{cfg['market']}: {count:,}")

    print(f"DONE {cfg['market']}: {count:,} -> {output_file}")
