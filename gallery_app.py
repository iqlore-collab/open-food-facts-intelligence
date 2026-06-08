import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Open Food Facts Product Gallery", page_icon="🖼️", layout="wide")

DATA_DIR = Path("data")
GERMANY_FILE = DATA_DIR / "openfoodfacts_germany_images.csv"
POLAND_FILE = DATA_DIR / "openfoodfacts_poland_images.csv"

@st.cache_data
def load_data():
    frames = []

    if GERMANY_FILE.exists():
        de = pd.read_csv(GERMANY_FILE, low_memory=False)
        de["market"] = "Germany"
        frames.append(de)

    if POLAND_FILE.exists():
        pl = pd.read_csv(POLAND_FILE, low_memory=False)
        pl["market"] = "Poland"
        frames.append(pl)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    for col in ["product_name", "brands", "stores", "categories", "image_url", "image_front_url", "image_front_small_url", "nutriscore_grade", "ecoscore_grade"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    for col in ["energy-kcal_100g", "sugars_100g", "salt_100g", "fat_100g", "proteins_100g"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["best_image"] = df["image_front_url"]
    df.loc[df["best_image"] == "", "best_image"] = df["image_url"]
    df.loc[df["best_image"] == "", "best_image"] = df["image_front_small_url"]

    df["search_text"] = (
        df["product_name"] + " " +
        df["brands"] + " " +
        df["stores"] + " " +
        df["categories"]
    ).str.lower()

    df = df[df["best_image"].str.startswith("http", na=False)]

    return df

df = load_data()

st.title("🖼️ Open Food Facts Product Gallery")
st.caption("Visual product explorer for Germany and Poland using Open Food Facts image URLs")

if df.empty:
    st.error("Brak danych obrazów.")
    st.write("Current directory:", Path.cwd())
    st.write("Data folder exists:", DATA_DIR.exists())
    st.write("Files in data:", list(DATA_DIR.glob("*")) if DATA_DIR.exists() else [])
    st.stop()

st.sidebar.header("Filters")

markets = st.sidebar.multiselect(
    "Market",
    sorted(df["market"].dropna().unique()),
    default=sorted(df["market"].dropna().unique())
)

filtered = df[df["market"].isin(markets)].copy()

query = st.sidebar.text_input("Search product / brand / category", value="chocolate")
if query:
    filtered = filtered[filtered["search_text"].str.contains(query.lower(), na=False)]

brand = st.sidebar.text_input("Brand contains")
if brand:
    filtered = filtered[filtered["brands"].str.contains(brand, case=False, na=False)]

store = st.sidebar.text_input("Store contains")
if store:
    filtered = filtered[filtered["stores"].str.contains(store, case=False, na=False)]

max_items = st.sidebar.slider("Number of products", 12, 96, 24, step=12)

st.subheader(f"Products found: {len(filtered):,}")

show = filtered.head(max_items).reset_index(drop=True)

cols = st.columns(4)

for i, row in show.iterrows():
    with cols[i % 4]:
        st.image(row["best_image"], use_container_width=True)
        st.markdown(f"**{row.get('product_name', 'Unnamed product')[:80]}**")
        st.caption(f"{row.get('brands', '')[:80]} | {row.get('market', '')}")

        st.write(f"Nutri-Score: **{row.get('nutriscore_grade', 'n/a')}**")
        st.write(f"Eco-Score: **{row.get('ecoscore_grade', 'n/a')}**")

        sugars = row.get("sugars_100g")
        salt = row.get("salt_100g")
        kcal = row.get("energy-kcal_100g")

        st.write(f"Sugar: {round(sugars, 2) if pd.notna(sugars) else 'n/a'} g / 100g")
        st.write(f"Salt: {round(salt, 2) if pd.notna(salt) else 'n/a'} g / 100g")
        st.write(f"Calories: {round(kcal, 0) if pd.notna(kcal) else 'n/a'} kcal / 100g")
        st.divider()
