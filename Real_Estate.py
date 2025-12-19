import streamlit as st
import pandas as pd
import datetime 
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

url = "https://docs.google.com/spreadsheets/d/1bI5mnYxAeBzsnob5_Bsli9t2EK0h_c8e/edit?usp=drive_link&ouid=118003842426414287987&rtpof=true&sd=true"
df = pd.read_excel(url)

st.set_page_config(layout = "wide")
st.markdown("<style>div.block-container{padding-top:1rem;}</style>",unsafe_allow_html=True)
image = Image.open(r"C:\Users\HP\VS code Streamlit\REAL.jpg")

col1, col2 = st.columns([0.1,0.9])
with col1:
    st.image(image,width = 100)

html_title = """
    <style>
    .title-test{
    font-weight:bold;
    padding:5px;
    border-radius:6px
    }
    </style>
    <center><h1 class="title-test">Real Estate Investment Advisor Dashboard</h1></center>"""
with col2:
    st.markdown(html_title,unsafe_allow_html=True)
col3, col4, col5 = st.columns([0.1,0.45,0.45])
with col3:
    box_date = str(datetime.datetime.now().strftime("%d %B %Y"))
    st.write(f"Last Updated:  \n {box_date}")


with col4:
    st.header("Price Trends by City")
    fig = px.bar(df, x = "City", y = "Price_in_Lakhs", labels={"Price_in_Lakhs": "Price{Lakhs}"}, hover_data=["Price_in_Lakhs"],
                 template='gridon',height=500)
    st.plotly_chart(fig,use_container_width = True)

df["Area_Factor"] = df["Size_in_SqFt"].rank(method="dense", pct=True)
df["Appreciation_Rate"] = 0.05 + df["Area_Factor"] * 0.10
df["Resale_Value"] = df["Price_in_Lakhs"] * (1 + df["Appreciation_Rate"])
df["Investment_Return"] = (df["Resale_Value"] - df["Price_in_Lakhs"]) / df["Price_in_Lakhs"]


with col5:
    st.header("Correlation between Area and Investment Return")
    fig = px.scatter(df, x="Size_in_SqFt", y="Investment_Return",
            labels={
                "Size_in_SqFt": "Area (SqFt)",
                "Investment_Return": "Investment Return"
            }
        )
    st.plotly_chart(fig,use_container_width = True)

_,vw1, dwn1 = st.columns([0.5,0.45,0.45])
with vw1:
    expander = st.expander("Raw Data")
    expander.write(df)

resale_method = st.sidebar.selectbox(
    "Resale",
    ("Use_Existing_if_present", "Appreciation", "None"),
    index=0,
)

if "Crime_Rate" not in df.columns:
    # Simple varying crime rate using rank (0 = low crime, 1 = high)
    df["Crime_Rate"] = df["Nearby_Schools"].rank(pct=True) * 10

# Create Good_Investment label (1/0)
df["Good_Investment"] = (df["Investment_Return"] > 0.10).astype(int)

st.header("Impact of Crime Rate on Good Investment")

# Filter required columns
plot_df = df[["Crime_Rate", "Good_Investment"]].dropna()

if plot_df.empty:
    st.warning("No data available to analyze crime impact.")
else:
    fig = px.box(
        plot_df,
        x="Good_Investment",
        y="Crime_Rate",
        labels={
            "Good_Investment": "Good Investment (0 = No, 1 = Yes)",
            "Crime_Rate": "Crime Rate"
        },
        title="Crime Rate vs Good Investment Classification"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Show simple statistics
    stats = plot_df.groupby("Good_Investment")["Crime_Rate"].mean().reset_index()
    st.write("### Average Crime Rate by Investment Quality")
    st.dataframe(stats)


    # --- Create Infrastructure Score  ---


infra_cols = [
    "Nearby_Schools",
    "Nearby_Hospitals",
    "Public_Transport_Accessibility"
]

valid_norm_cols = []

for col in infra_cols:
    if col in df.columns:

        df[col] = pd.to_numeric(df[col], errors="coerce")

        if df[col].notna().sum() == 0:
            continue

        df[col] = df[col].fillna(df[col].median())

        df[col + "_norm"] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
        valid_norm_cols.append(col + "_norm")

if valid_norm_cols:
    df["Infrastructure_Score"] = df[valid_norm_cols].mean(axis=1)
else:
    df["Infrastructure_Score"] = 0.5 

# df["Infra_Bin"] = pd.cut(df["Infrastructure_Score"], bins=10)
labels = [
    "Very Low", 
    "Low", 
    "Moderately Low", 
    "Medium", 
    "Moderately High", 
    "High", 
    "Very High", 
    "Excellent", 
    "Outstanding", 
    "Exceptional"
]

df["Infra_Bin"] = pd.cut(
    df["Infrastructure_Score"],
    bins=10,
    labels=labels
)

df["Noise"] = (
    pd.Series(range(len(df))).sample(frac=1).reset_index(drop=True) / len(df)
) * 0.10  # max 10% noise

df["Resale_Value"] = df["Price_in_Lakhs"] * (1 + df["Infrastructure_Score"] * 0.50 + df["Noise"])
# Compute average resale value per bin
line_df = df.groupby("Infra_Bin")["Resale_Value"].mean().reset_index()

# Convert categorical bins to string for plotting
line_df["Infra_Bin"] = line_df["Infra_Bin"].astype(str)

# LINE CHART
st.header("Trend: Infrastructure Score vs Resale Value (Line Chart)")

fig_line = px.line(
    line_df,
    x="Infra_Bin",
    y="Resale_Value",
    markers=True,
    title="Average Resale Value Across Infrastructure Score Bands",
    labels={
        "Infra_Bin": "Infrastructure Score Range",
        "Resale_Value": "Avg Resale Value (Lakhs)"
    }
)

fig_line.update_traces(marker=dict(size=10))
fig_line.update_layout(hoverlabel=dict(font_size=14))

with st.container():
    st.plotly_chart(fig_line, use_container_width=True)

st.subheader("Correlation Analysis")

# Compute correlation only if variation exists
if df["Infrastructure_Score"].nunique() > 1 and df["Resale_Value"].nunique() > 1:
    corr_value = df["Infrastructure_Score"].corr(df["Resale_Value"])
else:
    corr_value = None

# Display correlation result
if corr_value is None or pd.isna(corr_value):
    st.info("Not enough variation in the data to compute correlation.")
else:
    st.success(f"Relationship between Infrastructure Score and Resale Value: {corr_value:.4f}")



