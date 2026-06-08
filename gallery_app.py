import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Gallery Diagnostics", page_icon="🖼️", layout="wide")

DATA_DIR = Path("data")
GERMANY_FILE = DATA_DIR / "openfoodfacts_germany_images.csv"
POLAND_FILE = DATA_DIR / "openfoodfacts_poland_images.csv"

st.title("🖼️ Open Food Facts Product Gallery - Diagnostics")

st.write("Current directory:", Path.cwd())
st.write("Data folder exists:", DATA_DIR.exists())
st.write("Files:", list(DATA_DIR.glob("*")) if DATA_DIR.exists() else [])

frames = []

for market, file in [("Germany", GERMANY_FILE), ("Poland", POLAND_FILE)]:
    st.subheader(market)
    st.write("File:", file)
    st.write("Exists:", file.exists())

    if file.exists():
        df = pd.read_csv(file, low_memory=False)
        df["market"] = market
        st.write("Shape:", df.shape)
        st.write("Columns:", df.columns.tolist())

        for col in ["image_url", "image_front_url", "image_front_small_url"]:
            if col in df.columns:
                st.write(col, "non-empty:", df[col].notna().sum())
                st.dataframe(df[[col]].dropna().head(5))
            else:
                st.write(col, "MISSING")

        frames.append(df)

if frames:
    df = pd.concat(frames, ignore_index=True)

    for col in ["image_front_url", "image_url", "image_front_small_url"]:
        if col not in df.columns:
            df[col] = ""

    df["image_front_url"] = df["image_front_url"].fillna("").astype(str)
    df["image_url"] = df["image_url"].fillna("").astype(str)
    df["image_front_small_url"] = df["image_front_small_url"].fillna("").astype(str)

    df["best_image"] = df["image_front_url"]
    df.loc[df["best_image"] == "", "best_image"] = df["image_url"]
    df.loc[df["best_image"] == "", "best_image"] = df["image_front_small_url"]

    st.subheader("Combined")
    st.write("Combined shape:", df.shape)
    st.write("Best image starts with http:", df["best_image"].str.startswith("http", na=False).sum())
    st.dataframe(df[["product_name", "brands", "market", "best_image"]].head(20))

    sample = df[df["best_image"].str.startswith("http", na=False)].head(12)

    st.subheader("Image preview")
    if sample.empty:
        st.warning("No valid http image URLs found.")
    else:
        cols = st.columns(4)
        for i, row in sample.iterrows():
            with cols[i % 4]:
                st.write(row["best_image"])

        try:
            st.image(str(row["best_image"]), use_container_width=True)
        except Exception as e:
            st.error(str(e))
                st.write(row.get("product_name", ""))
