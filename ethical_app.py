import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="Ethical Product Intelligence", page_icon="🌍", layout="wide")

DATA_DIR = Path("data")
FILES = [
    DATA_DIR / "openfoodfacts_germany_clean.csv",
    DATA_DIR / "openfoodfacts_poland_clean.csv",
]

@st.cache_data
def load_data():
    frames = []
    for f in FILES:
        if f.exists():
            df = pd.read_csv(f, low_memory=False)
            frames.append(df)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    needed = [
        "market", "code", "product_name", "brands", "stores", "categories",
        "nutriscore_grade", "nova_group", "ecoscore_grade",
        "energy-kcal_100g", "fat_100g", "saturated-fat_100g",
        "sugars_100g", "proteins_100g", "salt_100g"
    ]

    for col in needed:
        if col not in df.columns:
            df[col] = ""

    for col in ["energy-kcal_100g", "fat_100g", "saturated-fat_100g", "sugars_100g", "proteins_100g", "salt_100g", "nova_group"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["product_name", "brands", "stores", "categories", "nutriscore_grade", "ecoscore_grade", "market"]:
        df[col] = df[col].fillna("").astype(str)

    df["search_text"] = (
        df["product_name"] + " " + df["brands"] + " " + df["stores"] + " " + df["categories"]
    ).str.lower()

    return df

def health_score(row):
    score = 50
    nutri = str(row["nutriscore_grade"]).lower()

    if nutri == "a": score += 35
    elif nutri == "b": score += 25
    elif nutri == "c": score += 10
    elif nutri == "d": score -= 10
    elif nutri == "e": score -= 25

    if pd.notna(row["sugars_100g"]):
        if row["sugars_100g"] <= 5: score += 10
        elif row["sugars_100g"] >= 25: score -= 20

    if pd.notna(row["salt_100g"]):
        if row["salt_100g"] <= 0.3: score += 8
        elif row["salt_100g"] >= 2: score -= 15

    if pd.notna(row["saturated-fat_100g"]) and row["saturated-fat_100g"] >= 10:
        score -= 10

    if pd.notna(row["proteins_100g"]) and row["proteins_100g"] >= 10:
        score += 8

    return max(0, min(100, score))

def environmental_score(row):
    score = 50
    eco = str(row["ecoscore_grade"]).lower()

    if eco == "a": score += 35
    elif eco == "b": score += 25
    elif eco == "c": score += 10
    elif eco == "d": score -= 10
    elif eco == "e": score -= 25

    text = row["search_text"]
    if "bio" in text or "organic" in text or "eko" in text:
        score += 10
    if "palm" in text:
        score -= 15

    return max(0, min(100, score))

def transparency_score(row):
    cols = ["product_name", "brands", "categories", "nutriscore_grade", "nova_group", "ecoscore_grade"]
    filled = sum(str(row[c]).strip() != "" and str(row[c]).lower() != "nan" for c in cols)
    return round(100 * filled / len(cols), 1)

df = load_data()

st.title("🌍 Ethical Product Intelligence Platform")
st.caption("Consumer-facing ESG, health and ethics scoring based on Open Food Facts data")

if df.empty:
    st.error("Brak danych CSV. Streamlit nie widzi folderu data.")
    st.write("Current directory:", Path.cwd())
    st.write("Data folder exists:", DATA_DIR.exists())
    st.write("Files:", list(DATA_DIR.glob('*')) if DATA_DIR.exists() else [])
    st.stop()

df["health_score"] = df.apply(health_score, axis=1)
df["environmental_score"] = df.apply(environmental_score, axis=1)
df["transparency_score"] = df.apply(transparency_score, axis=1)
df["overall_ethical_score"] = (
    df["health_score"] * 0.4 +
    df["environmental_score"] * 0.35 +
    df["transparency_score"] * 0.25
).round(1)

st.sidebar.header("Filters")

markets = st.sidebar.multiselect(
    "Market",
    sorted(df["market"].dropna().unique()),
    default=sorted(df["market"].dropna().unique())
)

filtered = df[df["market"].isin(markets)].copy()

q = st.sidebar.text_input("Search product / brand / category")
if q:
    filtered = filtered[filtered["search_text"].str.contains(q.lower(), na=False)]

min_score = st.sidebar.slider("Minimum ethical score", 0, 100, 0)
filtered = filtered[filtered["overall_ethical_score"] >= min_score]

tab1, tab2, tab3, tab4 = st.tabs([
    "ESG Overview",
    "Product Search",
    "Ethical Ranking",
    "Methodology"
])

with tab1:
    st.subheader("ESG Overview")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Products", f"{len(filtered):,}")
    c2.metric("Avg Overall", round(filtered["overall_ethical_score"].mean(), 1))
    c3.metric("Avg Health", round(filtered["health_score"].mean(), 1))
    c4.metric("Avg Environmental", round(filtered["environmental_score"].mean(), 1))

    summary = filtered.groupby("market")[["overall_ethical_score", "health_score", "environmental_score", "transparency_score"]].mean().reset_index()

    fig = px.bar(summary, x="market", y=["overall_ethical_score", "health_score", "environmental_score", "transparency_score"], barmode="group")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Product Search")

    cols = [
        "market", "code", "product_name", "brands", "stores", "categories",
        "nutriscore_grade", "nova_group", "ecoscore_grade",
        "overall_ethical_score", "health_score", "environmental_score", "transparency_score"
    ]

    st.dataframe(filtered[cols].sort_values("overall_ethical_score", ascending=False).head(1000), use_container_width=True)

with tab3:
    st.subheader("Ethical Ranking")

    ranking = st.selectbox("Ranking", ["Best overall", "Worst overall", "Best health", "Best environmental"])

    if ranking == "Best overall":
        rank = filtered.sort_values("overall_ethical_score", ascending=False)
    elif ranking == "Worst overall":
        rank = filtered.sort_values("overall_ethical_score", ascending=True)
    elif ranking == "Best health":
        rank = filtered.sort_values("health_score", ascending=False)
    else:
        rank = filtered.sort_values("environmental_score", ascending=False)

    cols = [
        "market", "product_name", "brands", "stores",
        "overall_ethical_score", "health_score", "environmental_score",
        "transparency_score", "nutriscore_grade", "ecoscore_grade"
    ]

    st.dataframe(rank[cols].head(100), use_container_width=True)

with tab4:
    st.subheader("Methodology")

    st.markdown("""
This is a lightweight prototype based on the public Open Food Facts fields available in the deployed CSV files.

### Overall Ethical Score

- Health Score: 40%
- Environmental Score: 35%
- Transparency Score: 25%

### Health Score

Uses Nutri-Score, sugar, salt, saturated fat and protein per 100g.

### Environmental Score

Uses Eco-Score where available and simple keyword indicators such as organic/bio/eko and palm oil.

### Transparency Score

Measures whether key product fields are available.
    """)
