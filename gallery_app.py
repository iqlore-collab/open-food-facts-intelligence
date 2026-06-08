import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Open Food Facts Product Gallery",
    page_icon="🖼️",
    layout="wide"
)

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

    required_cols = [
        "code", "market", "product_name", "brands", "stores", "categories",
        "nutriscore_grade", "nova_group", "ecoscore_grade", "image_url",
        "energy-kcal_100g", "sugars_100g", "salt_100g", "fat_100g", "proteins_100g"
    ]

    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    text_cols = [
        "product_name", "brands", "stores", "categories",
        "nutriscore_grade", "ecoscore_grade", "image_url", "market"
    ]

    for col in text_cols:
        df[col] = df[col].fillna("").astype(str)

    numeric_cols = [
        "energy-kcal_100g", "sugars_100g", "salt_100g", "fat_100g", "proteins_100g"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["search_text"] = (
        df["product_name"] + " " +
        df["brands"] + " " +
        df["stores"] + " " +
        df["categories"]
    ).str.lower()

    df = df[df["image_url"].str.startswith("http", na=False)].copy()

    return df

df = load_data()

st.title("🖼️ Open Food Facts Product Gallery")
st.caption("Visual product explorer for Germany and Poland using Open Food Facts image URLs")

if df.empty:
    st.error("Brak produktów ze zdjęciami.")
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
        image_url = str(row.get("image_url", ""))

        try:
            st.markdown(f"[Open image]({image_url})")
        except Exception as e:
            st.warning("Image could not be loaded.")
            st.caption(image_url)
            st.caption(str(e))

        name = str(row.get("product_name", "Unnamed product"))
        brand_name = str(row.get("brands", ""))
        market = str(row.get("market", ""))
        nutri = str(row.get("nutriscore_grade", ""))
        eco = str(row.get("ecoscore_grade", ""))

        st.markdown(f"**{name[:80] if name else 'Unnamed product'}**")
        st.caption(f"{brand_name[:80]} | {market}")

        st.write(f"Nutri-Score: **{nutri if nutri else 'n/a'}**")
        st.write(f"Eco-Score: **{eco if eco else 'n/a'}**")

        sugars = row.get("sugars_100g")
        salt = row.get("salt_100g")
        kcal = row.get("energy-kcal_100g")

        st.write(f"Sugar: {round(sugars, 2) if pd.notna(sugars) else 'n/a'} g / 100g")
        st.write(f"Salt: {round(salt, 2) if pd.notna(salt) else 'n/a'} g / 100g")
        st.write(f"Calories: {round(kcal, 0) if pd.notna(kcal) else 'n/a'} kcal / 100g")

        st.divider()
