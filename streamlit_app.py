import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Ethical Product Intelligence",
    page_icon="🌍",
    layout="wide"
)

DATA_DIR = Path("data")
GERMANY_FILE = DATA_DIR / "openfoodfacts_germany_esg.csv"
POLAND_FILE = DATA_DIR / "openfoodfacts_poland_esg.csv"

@st.cache_data
def load_data():
    frames = []

    if GERMANY_FILE.exists():
        frames.append(pd.read_csv(GERMANY_FILE, low_memory=False))

    if POLAND_FILE.exists():
        frames.append(pd.read_csv(POLAND_FILE, low_memory=False))

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    numeric_cols = [
        "energy-kcal_100g", "fat_100g", "saturated-fat_100g",
        "carbohydrates_100g", "sugars_100g", "proteins_100g", "salt_100g",
        "nova_group"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = [
        "product_name", "brands", "stores", "categories", "labels",
        "labels_tags", "ingredients_text", "ecoscore_grade",
        "nutriscore_grade", "packaging", "packaging_tags",
        "origins", "manufacturing_places"
    ]

    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    df["search_text"] = (
        df["product_name"] + " " +
        df["brands"] + " " +
        df["stores"] + " " +
        df["categories"] + " " +
        df["labels"] + " " +
        df["labels_tags"] + " " +
        df["ingredients_text"]
    ).str.lower()

    return df

def map_grade(value, mapping):
    v = str(value).lower().strip()
    return mapping.get(v, 50)

def environmental_score(row):
    score = 50

    eco = str(row.get("ecoscore_grade", "")).lower()
    eco_map = {"a": 95, "b": 80, "c": 60, "d": 40, "e": 20}
    if eco in eco_map:
        score = eco_map[eco]

    text = row.get("search_text", "")

    if "organic" in text or "bio" in text or "ekologicz" in text:
        score += 8
    if "rainforest" in text:
        score += 5
    if "palm oil" in text or "huile de palme" in text or "olej palmowy" in text:
        score -= 15
    if "plastic" in str(row.get("packaging_tags", "")).lower():
        score -= 5

    return max(0, min(100, score))

def health_score(row):
    score = 50

    nutri = str(row.get("nutriscore_grade", "")).lower()
    nutri_map = {"a": 95, "b": 80, "c": 60, "d": 40, "e": 20}
    if nutri in nutri_map:
        score = nutri_map[nutri]

    nova = row.get("nova_group")
    if pd.notna(nova):
        if nova == 1:
            score += 10
        elif nova == 4:
            score -= 20

    sugar = row.get("sugars_100g")
    salt = row.get("salt_100g")
    satfat = row.get("saturated-fat_100g")
    protein = row.get("proteins_100g")

    if pd.notna(sugar):
        if sugar <= 5:
            score += 7
        elif sugar >= 25:
            score -= 15

    if pd.notna(salt):
        if salt <= 0.3:
            score += 5
        elif salt >= 2:
            score -= 10

    if pd.notna(satfat):
        if satfat >= 10:
            score -= 10

    if pd.notna(protein):
        if protein >= 10:
            score += 5

    return max(0, min(100, score))

def social_ethics_score(row):
    score = 50
    text = row.get("search_text", "")

    positive = [
        "fairtrade", "fair trade", "rainforest alliance", "utz",
        "vegan", "vegetarian", "animal welfare", "msc", "asc",
        "free range", "bio", "organic", "eko"
    ]

    negative = [
        "palm oil", "huile de palme", "olej palmowy"
    ]

    for p in positive:
        if p in text:
            score += 7

    for n in negative:
        if n in text:
            score -= 10

    return max(0, min(100, score))

def transparency_score(row):
    important = [
        "product_name", "brands", "categories", "labels",
        "ingredients_text", "nutriscore_grade", "ecoscore_grade",
        "nova_group", "packaging", "origins"
    ]

    filled = 0
    for col in important:
        val = row.get(col)
        if pd.notna(val) and str(val).strip() != "":
            filled += 1

    return round(100 * filled / len(important), 1)

def overall_score(row):
    return round(
        row["environmental_score"] * 0.30 +
        row["health_score"] * 0.25 +
        row["social_ethics_score"] * 0.25 +
        row["transparency_score"] * 0.20,
        1
    )

df = load_data()

st.title("🌍 Ethical Product Intelligence Platform")
st.caption("Consumer-facing ESG, health and ethics scoring based on Open Food Facts data")

if df.empty:
    st.error("Brak plików ESG CSV. Uruchom najpierw build_esg_csv.py.")
    st.stop()

df["environmental_score"] = df.apply(environmental_score, axis=1)
df["health_score"] = df.apply(health_score, axis=1)
df["social_ethics_score"] = df.apply(social_ethics_score, axis=1)
df["transparency_score"] = df.apply(transparency_score, axis=1)
df["overall_ethical_score"] = df.apply(overall_score, axis=1)

st.sidebar.header("Filters")

markets = st.sidebar.multiselect(
    "Market",
    sorted(df["market"].dropna().unique()),
    default=sorted(df["market"].dropna().unique())
)

filtered = df[df["market"].isin(markets)].copy()

query = st.sidebar.text_input("Search product / brand / label")
if query:
    filtered = filtered[filtered["search_text"].str.contains(query.lower(), na=False)]

brand = st.sidebar.text_input("Brand contains")
if brand:
    filtered = filtered[filtered["brands"].str.contains(brand, case=False, na=False)]

min_score = st.sidebar.slider("Minimum overall ethical score", 0, 100, 0)
filtered = filtered[filtered["overall_ethical_score"] >= min_score]

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "ESG Overview",
    "Product Search",
    "Compare Products",
    "Ethical Ranking",
    "Brand Intelligence",
    "Score Methodology"
])

with tab1:
    st.subheader("ESG Overview")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Products", f"{len(filtered):,}")
    c2.metric("Avg Overall", round(filtered["overall_ethical_score"].mean(), 1))
    c3.metric("Avg Environmental", round(filtered["environmental_score"].mean(), 1))
    c4.metric("Avg Health", round(filtered["health_score"].mean(), 1))
    c5.metric("Avg Transparency", round(filtered["transparency_score"].mean(), 1))

    score_summary = filtered.groupby("market")[
        ["overall_ethical_score", "environmental_score", "health_score", "social_ethics_score", "transparency_score"]
    ].mean().reset_index()

    fig = px.bar(
        score_summary,
        x="market",
        y=["overall_ethical_score", "environmental_score", "health_score", "social_ethics_score", "transparency_score"],
        barmode="group",
        title="Average ESG / Ethics scores by market"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.histogram(
        filtered,
        x="overall_ethical_score",
        color="market",
        nbins=50,
        title="Overall ethical score distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Product Search")

    cols = [
        "market", "code", "product_name", "brands", "stores",
        "nutriscore_grade", "ecoscore_grade", "nova_group",
        "overall_ethical_score", "environmental_score", "health_score",
        "social_ethics_score", "transparency_score"
    ]

    cols = [c for c in cols if c in filtered.columns]

    st.dataframe(
        filtered.sort_values("overall_ethical_score", ascending=False)[cols].head(1000),
        use_container_width=True
    )

with tab3:
    st.subheader("Compare Products")

    compare_query = st.text_input("Type product name to compare, e.g. Nutella, yogurt, chocolate, coffee")

    compare_df = filtered.copy()

    if compare_query:
        compare_df = compare_df[compare_df["search_text"].str.contains(compare_query.lower(), na=False)]

    compare_df = compare_df.sort_values("overall_ethical_score", ascending=False).head(30)

    cols = [
        "market", "product_name", "brands",
        "overall_ethical_score", "environmental_score", "health_score",
        "social_ethics_score", "transparency_score",
        "nutriscore_grade", "ecoscore_grade", "nova_group"
    ]

    cols = [c for c in cols if c in compare_df.columns]
    st.dataframe(compare_df[cols], use_container_width=True)

    if not compare_df.empty:
        fig = px.bar(
            compare_df.head(15),
            x="product_name",
            y="overall_ethical_score",
            color="market",
            title="Best matching products by overall ethical score"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Ethical Ranking")

    ranking = st.selectbox(
        "Ranking type",
        [
            "Best overall",
            "Worst overall",
            "Best environmental",
            "Best health",
            "Best social / ethics",
            "Best transparency"
        ]
    )

    sort_map = {
        "Best overall": ("overall_ethical_score", False),
        "Worst overall": ("overall_ethical_score", True),
        "Best environmental": ("environmental_score", False),
        "Best health": ("health_score", False),
        "Best social / ethics": ("social_ethics_score", False),
        "Best transparency": ("transparency_score", False),
    }

    sort_col, asc = sort_map[ranking]

    cols = [
        "market", "product_name", "brands", "stores",
        "overall_ethical_score", "environmental_score", "health_score",
        "social_ethics_score", "transparency_score",
        "nutriscore_grade", "ecoscore_grade", "labels"
    ]

    cols = [c for c in cols if c in filtered.columns]

    st.dataframe(
        filtered.sort_values(sort_col, ascending=asc)[cols].head(100),
        use_container_width=True
    )

with tab5:
    st.subheader("Brand Intelligence")

    brand_df = filtered[filtered["brands"].str.strip() != ""].copy()

    summary = (
        brand_df
        .groupby("brands")
        .agg(
            products=("code", "count"),
            avg_overall=("overall_ethical_score", "mean"),
            avg_environmental=("environmental_score", "mean"),
            avg_health=("health_score", "mean"),
            avg_ethics=("social_ethics_score", "mean"),
            avg_transparency=("transparency_score", "mean")
        )
        .reset_index()
    )

    summary = summary[summary["products"] >= 5]
    summary = summary.sort_values("avg_overall", ascending=False)

    st.dataframe(summary.head(100), use_container_width=True)

    fig = px.scatter(
        summary.head(300),
        x="avg_environmental",
        y="avg_health",
        size="products",
        hover_name="brands",
        title="Brand map: environmental vs health"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab6:
    st.subheader("Score Methodology")

    st.markdown("""
This is a first rule-based prototype.

### Overall Ethical Score

- Environmental Score: 30%
- Health Score: 25%
- Social / Ethics Score: 25%
- Transparency Score: 20%

### Environmental Score

Uses:
- Eco-Score
- organic / bio labels
- Rainforest Alliance labels
- palm oil indicators
- packaging indicators

### Health Score

Uses:
- Nutri-Score
- NOVA group
- sugar per 100g
- salt per 100g
- saturated fat per 100g
- protein per 100g

### Social / Ethics Score

Uses:
- Fairtrade
- Rainforest Alliance
- Vegan / vegetarian
- MSC / ASC
- animal welfare indicators
- palm oil penalty

### Transparency Score

Measures how complete the product information is:
- product name
- brand
- category
- labels
- ingredients
- Nutri-Score
- Eco-Score
- NOVA
- packaging
- origin

Important: this is not a final scientific ESG rating. It is a transparent prototype scoring system.
    """)
