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
    "image_url",
    "energy-kcal_100g", "sugars_100g", "salt_100g", "fat_100g", "proteins_100g"
]

def build_image_url(code, images):
    if not code or not isinstance(images, dict):
        return ""

    image_keys = list(images.keys())

    preferred = [
        "front_de", "front_pl", "front_en", "front",
        "1", "2", "3"
    ]

    selected = None

    for key in preferred:
        if key in images:
            selected = key
            break

    if selected is None:
        for key in image_keys:
            if key.startswith("front"):
                selected = key
                break

    if selected is None and image_keys:
        selected = image_keys[0]

    if selected is None:
        return ""

    img = images.get(selected, {})
    rev = img.get("rev") if isinstance(img, dict) else None

    if not rev:
        return ""

    code = str(code)
    padded = code.zfill(13)

    path = "/".join([padded[i:i+3] for i in range(0, 9, 3)])
    filename = f"{selected}.{rev}.400.jpg"

    return f"https://images.openfoodfacts.org/images/products/{path}/{padded}/{filename}"

for market, infile, outfile in INPUTS:
    if not infile.exists():
        print(f"Missing: {infile}")
        continue

    count = 0
    with_images = 0

    with outfile.open("w", newline="", encoding="utf-8-sig") as fout:
        writer = csv.DictWriter(fout, fieldnames=FIELDS)
        writer.writeheader()

        with infile.open("r", encoding="utf-8", errors="ignore") as fin:
            for line in fin:
                try:
                    p = json.loads(line)
                except:
                    continue

                code = p.get("code")
                image_url = build_image_url(code, p.get("images"))

                if image_url:
                    with_images += 1

                nutr = p.get("nutriments", {})

                row = {
                    "code": code,
                    "market": market,
                    "product_name": p.get("product_name"),
                    "brands": p.get("brands"),
                    "stores": p.get("stores"),
                    "categories": p.get("categories"),
                    "nutriscore_grade": p.get("nutriscore_grade"),
                    "nova_group": p.get("nova_group"),
                    "ecoscore_grade": p.get("ecoscore_grade"),
                    "image_url": image_url,
                    "energy-kcal_100g": nutr.get("energy-kcal_100g"),
                    "sugars_100g": nutr.get("sugars_100g"),
                    "salt_100g": nutr.get("salt_100g"),
                    "fat_100g": nutr.get("fat_100g"),
                    "proteins_100g": nutr.get("proteins_100g"),
                }

                writer.writerow(row)
                count += 1

                if count % 50000 == 0:
                    print(f"{market}: {count:,} | images: {with_images:,}")

    print(f"DONE {market}: {count:,} products | images: {with_images:,} -> {outfile}")
