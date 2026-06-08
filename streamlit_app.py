import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Open Food Facts Intelligence",
    page_icon="🥫",
    layout="wide"
)

DATA_DIR = Path("data")
GERMANY_FILE = DATA_DIR / "openfoodfacts_germany_clean.csv"
POLAND_FILE = DATA_DIR / "openfoodfacts_poland_clean.csv"

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

    numeric_cols = [
        "energy-kcal_100g", "fat_100g", "saturated-fat_100g",
        "carbohydrates_100g", "sugars_100g",
        "proteins_100g", "salt_100g", "nova_group"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["product_name", "brands", "stores", "categories", "nutriscore_grade", "ecoscore_grade"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)

    df["search_text"] = (
        df["product_name"] + " " +
        df["brands"] + " " +
        df["stores"] + " " +
        df["categories"]
    ).str.lower()

    return df

df = load_data()

st.title("🥫 Open Food Facts Intelligence")
st.caption("Germany / Poland product intelligence dashboard based on Open Food Facts")

if df.empty:
    st.error("Brak danych. Streamlit nie widzi plików CSV.")
    st.write("Current directory:", Path.cwd())
    st.write("Data folder exists:", DATA_DIR.exists())
    st.write("Files:", list(DATA_DIR.glob("*")) if DATA_DIR.exists() else [])
    st.stop()

st.sidebar.header("Filters")

markets = st.sidebar.multiselect(
    "Market",
    sorted(df["market"].dropna().unique()),
    default=sorted(df["market"].dropna().unique())
)

filtered = df[df["market"].isin(markets)].copy()

product_search = st.sidebar.text_input("Product / brand / category contains")
if product_search:
    filtered = filtered[filtered["search_text"].str.contains(product_search.lower(), na=False)]

if "nutriscore_grade" in filtered.columns:
    scores = sorted([x for x in filtered["nutriscore_grade"].dropna().unique() if x != ""])
    selected_scores = st.sidebar.multiselect("Nutri-Score", scores)
    if selected_scores:
        filtered = filtered[filtered["nutriscore_grade"].isin(selected_scores)]

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Overview",
    "Germany vs Poland",
    "Nutrition Explorer",
    "Risk Ranking",
    "Product Table"
])

with tab1:
    st.subheader("Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products", f"{len(filtered):,}")
    c2.metric("Markets", filtered["market"].nunique())
    c3.metric("Brands", filtered["brands"].nunique())
    c4.metric("Stores", filtered["stores"].nunique())

    market_counts = filtered["market"].value_counts().reset_index()
    market_counts.columns = ["market", "products"]

    fig = px.bar(market_counts, x="market", y="products", title="Products by market")
    st.plotly_chart(fig, use_container_width=True)

    nutri = filtered[filtered["nutriscore_grade"] != ""]
    if not nutri.empty:
        nutri_counts = nutri.groupby(["market", "nutriscore_grade"]).size().reset_index(name="products")
        fig = px.bar(
            nutri_counts,
            x="nutriscore_grade",
            y="products",
            color="market",
            barmode="group",
            title="Nutri-Score distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Germany vs Poland")

    numeric_cols = [
        "energy-kcal_100g", "fat_100g", "saturated-fat_100g",
        "carbohydrates_100g", "sugars_100g", "proteins_100g", "salt_100g"
    ]

    available = [c for c in numeric_cols if c in filtered.columns]

    selected_metric = st.selectbox("Metric", available)

    summary = filtered.groupby("market")[selected_metric].mean().reset_index().dropna()

    fig = px.bar(summary, x="market", y=selected_metric, title=f"Average {selected_metric} by market")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(summary, use_container_width=True)

with tab3:
    st.subheader("Nutrition Explorer")

    numeric_cols = [
        "energy-kcal_100g", "fat_100g", "saturated-fat_100g",
        "carbohydrates_100g", "sugars_100g", "proteins_100g", "salt_100g"
    ]

    available = [c for c in numeric_cols if c in filtered.columns]

    selected = st.selectbox("Choose nutrient", available, key="nutrient_hist")

    temp = filtered.dropna(subset=[selected])
    if not temp.empty:
        upper = temp[selected].quantile(0.99)
        temp = temp[(temp[selected] >= 0) & (temp[selected] <= upper)]

        fig = px.histogram(
            temp,
            x=selected,
            color="market",
            nbins=60,
            title=f"Distribution of {selected}"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Risk Ranking")

    ranking_type = st.selectbox(
        "Ranking",
        [
            "Highest sugar",
            "Highest salt",
            "Highest fat",
            "Highest calories",
            "Best Nutri-Score A",
            "Worst Nutri-Score E"
        ]
    )

    rank_df = filtered.copy()

    if ranking_type == "Highest sugar":
        rank_df = rank_df.dropna(subset=["sugars_100g"]).sort_values("sugars_100g", ascending=False)
    elif ranking_type == "Highest salt":
        rank_df = rank_df.dropna(subset=["salt_100g"]).sort_values("salt_100g", ascending=False)
    elif ranking_type == "Highest fat":
        rank_df = rank_df.dropna(subset=["fat_100g"]).sort_values("fat_100g", ascending=False)
    elif ranking_type == "Highest calories":
        rank_df = rank_df.dropna(subset=["energy-kcal_100g"]).sort_values("energy-kcal_100g", ascending=False)
    elif ranking_type == "Best Nutri-Score A":
        rank_df = rank_df[rank_df["nutriscore_grade"].str.lower() == "a"]
    elif ranking_type == "Worst Nutri-Score E":
        rank_df = rank_df[rank_df["nutriscore_grade"].str.lower() == "e"]

    cols = [
        "market", "product_name", "brands", "stores", "categories",
        "nutriscore_grade", "nova_group",
        "energy-kcal_100g", "sugars_100g", "salt_100g", "fat_100g", "proteins_100g"
    ]
    cols = [c for c in cols if c in rank_df.columns]

    st.dataframe(rank_df[cols].head(100), use_container_width=True)

with tab5:
    st.subheader("Product Table")

    cols = [
        "market", "code", "product_name", "brands", "stores", "categories",
        "nutriscore_grade", "nova_group", "ecoscore_grade",
        "energy-kcal_100g", "sugars_100g", "salt_100g", "fat_100g", "proteins_100g"
    ]
    cols = [c for c in cols if c in filtered.columns]

    safe_table = filtered[cols].head(1000).copy()
    safe_table = safe_table.astype(str)
    st.dataframe(safe_table, use_container_width=True)

with tab6:
    st.header("Author")

    from pathlib import Path

    photo = Path("data/1731311789083.jpg")

    if photo.exists():
        st.image(str(photo), width=350)

    st.subheader("Dr. Tomasz Szymusiak")

    st.markdown("""
### AI-Powered Geospatial Investment Intelligence Platform

Researcher, Data Scientist and Project Manager working at the intersection of:

- Artificial Intelligence
- Geospatial Analytics
- Renewable Energy
- Hydrogen Economy
- Maritime Intelligence
- Investment Intelligence

Current flagship projects:

- Namibia Hydrogen Atlas
- Open Food Facts Intelligence
- Ethical Consumer Intelligence Platform

GitHub:
https://github.com/iqlore-collab
""")
