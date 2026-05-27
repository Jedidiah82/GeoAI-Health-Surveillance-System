import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
from map_utils import create_geoai_map
from audit_logger import log_event
from streamlit_folium import st_folium
from datetime import datetime

st.set_page_config(
    page_title="GeoAI Surveillance Dashboard",
    layout="wide"
)

st.title("GeoAI Surveillance Dashboard Prototype")
st.caption("Privacy-preserving district-level COVID-19 outbreak risk monitoring system")

st.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

col1, col2, col3 = st.columns(3)

with col1:
    st.success("System Status: Operational")

with col2:
    st.info("API Gateway: Healthy")

with col3:
    st.warning("Audit Logging: Active")

@st.cache_data
def load_data():
    df = pd.read_csv("data/geoai_surveillance_outputs.csv")
    df["Date"] = pd.to_datetime(
        df["Year"].astype(str) + "-" + df["Month"].astype(str) + "-01"
    )
    return df


df = load_data()

# --------------------------------
# Operational Summary Metrics
# --------------------------------

latest_df = (
    df.sort_values(["Year", "Month"])
      .groupby("adm2_name")
      .tail(1)
      .copy()
)

high_risk_count = (latest_df["Risk_Level"] == "High Risk").sum()
avg_risk_score = latest_df["Outbreak_Probability"].mean()

try:
    hotspot_gdf = gpd.read_file("data/geoai_spatial_intelligence.geojson")

    if "Hotspot_Class" in hotspot_gdf.columns:
        active_hotspots = (hotspot_gdf["Hotspot_Class"] == "Hotspot").sum()

    elif "GiZScore" in hotspot_gdf.columns and "GiPValue" in hotspot_gdf.columns:
        active_hotspots = (
            (hotspot_gdf["GiPValue"].astype(float) <= 0.05)
            & (hotspot_gdf["GiZScore"].astype(float) > 1.96)
        ).sum()

    else:
        active_hotspots = "N/A"

except Exception:
    active_hotspots = "N/A"

try:
    audit_log = pd.read_csv("logs/audit_log.csv")
    governance_events = len(audit_log)
except FileNotFoundError:
    governance_events = 0

m1, m2, m3, m4 = st.columns(4)

m1.metric("High-Risk Districts", high_risk_count)
m2.metric("Average Risk Score", f"{avg_risk_score:.4f}")
m3.metric("Active Hotspots", active_hotspots)
m4.metric("Governance Events Logged", governance_events)

st.sidebar.header("District Selection")

districts = sorted(df["adm2_name"].dropna().unique())

selected_district = st.sidebar.selectbox(
    "Select District",
    districts
)

top_risk = (
    df.sort_values(["Year", "Month"])
      .groupby("adm2_name")
      .tail(1)
      .sort_values(by="Outbreak_Probability", ascending=False)
      .head(10)
      .copy()
)

st.subheader("Top Risk Districts")

st.dataframe(
    top_risk.rename(
        columns={
            "adm2_name": "District",
            "adm1_name": "County",
            "Outbreak_Probability": "Risk Score",
            "Risk_Level": "Risk Level"
        }
    )[["District", "County", "Risk Score", "Risk Level"]],
    width="stretch"
)

log_event(
    user_role="analyst",
    action="district_selected",
    district=selected_district
)

start_period = df["Date"].min().strftime("%B %Y")
end_period = df["Date"].max().strftime("%B %Y")

st.caption(f"Dataset Coverage Period: {start_period} – {end_period}")


district_df = df[df["adm2_name"] == selected_district].copy()

latest_record = district_df.sort_values(
    ["Year", "Month"]
).iloc[-1]


# -----------------------------
# KPI Cards
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("District", latest_record["adm2_name"])
col2.metric("County", latest_record["adm1_name"])
col3.metric("Outbreak Probability", round(latest_record["Outbreak_Probability"], 4))
col4.metric("Risk Level", latest_record["Risk_Level"])


# --------------------------------
# Interactive GeoAI Map
# --------------------------------
st.subheader("Operational GeoAI Spatial Intelligence Map")

geoai_map = create_geoai_map()

st_folium(
    geoai_map,
    height=850,
    use_container_width=True
)


# --------------------------------
# Operational Alert Panel
# --------------------------------

st.subheader("Operational Alert Summary")

high_risk_count = latest_df[
    latest_df["Risk_Level"] == "High Risk"
].shape[0]

moderate_risk_count = latest_df[
    latest_df["Risk_Level"] == "Moderate Risk"
].shape[0]

if high_risk_count > 0:
    st.error(
        f"{high_risk_count} district(s) are currently classified as High Risk."
    )

if moderate_risk_count > 0:
    st.warning(
        f"{moderate_risk_count} district(s) are currently classified as Moderate Risk."
    )

if high_risk_count == 0 and moderate_risk_count == 0:
    st.success("No elevated district-level outbreak risk detected.")


# --------------------------------
# Explainable GeoAI Intelligence
# --------------------------------
st.subheader("Explainable GeoAI Intelligence")

st.markdown("""
This section presents explainable AI outputs used to interpret the main
drivers of predicted COVID-19 outbreak risk. The model uses epidemiological,
environmental, temporal, and spatial indicators to estimate district-level
outbreak probability.
""")

col1, col2 = st.columns(2)

if os.path.exists("figures/xgboost_shap_summary_plot.png"):
    with col1:
        st.image(
            "figures/xgboost_shap_summary_plot.png",
            caption="SHAP summary plot for the XGBoost GeoAI model",
            use_container_width=True
        )

if os.path.exists("figures/xgboost_feature_importance.png"):
    with col2:
        st.image(
            "figures/xgboost_feature_importance.png",
            caption="XGBoost feature importance ranking",
            use_container_width=True
        )

st.info("""
Interpretation: Recent case trends, lagged incidence, population density,
rainfall, and temperature help explain variation in predicted outbreak risk.
SHAP values show how each variable contributes positively or negatively to
the model output for individual predictions.
""")


# --------------------------------
# Model Confidence and Validation
# --------------------------------
st.subheader("Model Confidence and Validation")

model_results = pd.read_csv("data/final_geoai_model_comparison.csv")

st.markdown("""
This section summarizes comparative model performance used to validate
the GeoAI prediction engine.
""")

st.dataframe(
    model_results,
    use_container_width=True
)

best_model = model_results.sort_values(
    by=["ROC_AUC", "F1_Score"],
    ascending=False
).iloc[0]

st.success(
    f"Best performing model: {best_model['Model']} "
    f"(ROC-AUC: {best_model['ROC_AUC']:.3f}, "
    f"F1-score: {best_model['F1_Score']:.3f})"
)


# --------------------------------
# Map and Figure Gallery
# --------------------------------
st.subheader("Analytical Map Outputs")

st.markdown("""
The following exported GIS maps summarize the spatial, epidemiological,
environmental, and GeoAI outputs used to support system interpretation.
""")

map_files = {
    "Study Area / Administrative Reference Map": "figures/maps/Study Area - Administrative Reference Map.png",
    "GeoAI-Predicted Outbreak Probability": "figures/maps/GeoAI Outbreak Probability Map.png",
    "GeoAI-Based Risk Classification": "figures/maps/GeoAI Risk Classification Map.png",
    "GeoAI-Derived Spatial Hotspot Intelligence": "figures/maps/GEOAI HOTSPOT MAP.png",
    "Local Moran's I Cluster Analysis": "figures/maps/Local Moran’s I Cluster_Outlier Map.png",
    "Traditional Getis-Ord Gi* Hotspot Analysis": "figures/maps/Traditional Hotspot Analysis Map (Getis-Ord Gi).png",
    "Temperature Distribution": "figures/maps/Temperature Distribution Map.png",
    "Rainfall Distribution": "figures/maps/Rainfall Distribution Map.png",
    "Reported COVID-19 Cases": "figures/maps/COVID-19 Case Count Map.png",
    "Cumulative COVID-19 Incidence": "figures/maps/Cumulative Incidence Map.png",
}

available_maps = {
    name: path for name, path in map_files.items()
    if os.path.exists(path)
}

if available_maps:
    selected_map = st.selectbox(
        "Select analytical map output",
        list(available_maps.keys())
    )

    st.image(
        available_maps[selected_map],
        caption=selected_map,
        use_container_width=True
    )
else:
    st.warning("No map images found. Check the file names inside figures/maps.")


# -----------------------------
# Trend chart
# -----------------------------
st.subheader("Temporal Outbreak Probability Trend")

trend_fig = px.line(
    district_df.sort_values("Date"),
    x="Date",
    y="Outbreak_Probability",
    markers=True,
    title=f"Outbreak Probability Trend: {selected_district}"
)

trend_fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Predicted Outbreak Probability"
)

st.plotly_chart(trend_fig, width="stretch")


# -----------------------------
# Risk Level Distribution
# -----------------------------
st.subheader("Risk Level Distribution")

latest_df = (
    df.sort_values(["Year", "Month"])
      .groupby("adm2_name")
      .tail(1)
)

risk_counts = latest_df["Risk_Level"].value_counts().reset_index()
risk_counts.columns = ["Risk Level", "District Count"]

risk_fig = px.bar(
    risk_counts,
    x="Risk Level",
    y="District Count",
    title="Latest District Risk Classification Summary"
)

risk_fig.update_layout(
    xaxis_title="Risk Level",
    yaxis_title="Number of Districts"
)

st.plotly_chart(risk_fig, width="stretch")


# --------------------------------
# Environmental & Epidemiological Trend Tabs
# --------------------------------

st.subheader("Environmental and Epidemiological Trend")

env_df = district_df.rename(
    columns={
        "COUNT_OBJECTID": "Reported Cases",
        "Incidence_100k": "Incidence per 100k",
        "Rainfall_mm": "Rainfall (mm)",
        "Temperature_C": "Temperature (°C)"
    }
).sort_values("Date")

tab1, tab2, tab3 = st.tabs(
    [
        "Epidemiological Indicators",
        "Environmental Indicators",
        "Normalized Comparison"
    ]
)

with tab1:
    epi_fig = px.line(
        env_df,
        x="Date",
        y=["Reported Cases", "Incidence per 100k"],
        markers=True,
        title=f"Epidemiological Trend: {selected_district}",
        color_discrete_map={
            "Reported Cases": "#E15759",
            "Incidence per 100k": "#59A14F"
        }
    )

    epi_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title="Indicator",
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(epi_fig, width="stretch")


with tab2:
    env_only_fig = px.line(
        env_df,
        x="Date",
        y=["Rainfall (mm)", "Temperature (°C)"],
        markers=True,
        title=f"Environmental Trend: {selected_district}",
        color_discrete_map={
            "Rainfall (mm)": "#4E79A7",
            "Temperature (°C)": "#F28E2B"
        }
    )

    env_only_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title="Indicator",
        template="plotly_white",
        hovermode="x unified"
    )

    st.plotly_chart(env_only_fig, width="stretch")


with tab3:
    normalized_df = env_df.copy()

    indicators = [
        "Reported Cases",
        "Incidence per 100k",
        "Rainfall (mm)",
        "Temperature (°C)"
    ]

    for col in indicators:
        min_val = normalized_df[col].min()
        max_val = normalized_df[col].max()

        if max_val != min_val:
            normalized_df[col] = (
                (normalized_df[col] - min_val) /
                (max_val - min_val)
            )
        else:
            normalized_df[col] = 0

    norm_fig = px.line(
        normalized_df,
        x="Date",
        y=indicators,
        markers=True,
        title=f"Normalized Indicator Comparison: {selected_district}",
        color_discrete_map={
            "Reported Cases": "#E15759",
            "Incidence per 100k": "#59A14F",
            "Rainfall (mm)": "#4E79A7",
            "Temperature (°C)": "#F28E2B"
        }
    )

    norm_fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Normalized Value (0–1)",
        legend_title="Indicator",
        template="plotly_white",
        hovermode="x unified"
    )

    norm_fig.update_traces(
        line=dict(width=3),
        selector=dict(name="Reported Cases")
    )

    norm_fig.update_traces(
        line=dict(width=2, dash="dash"),
        selector=dict(name="Incidence per 100k")
    )

    st.plotly_chart(norm_fig, width="stretch")


# --------------------------------
# Data Table: Aggregated Surveillance Data
# --------------------------------

st.subheader("Aggregated District-Level Surveillance Data")

display_df = district_df[
    [
        "adm2_pcode",
        "adm2_name",
        "adm1_name",
        "Year",
        "Month",
        "COUNT_OBJECTID",
        "Incidence_100k",
        "Rainfall_mm",
        "Temperature_C",
        "Outbreak_Probability",
        "Risk_Level"
    ]
].sort_values(["Year", "Month"])

# Rename fields for operational readability
display_df = display_df.rename(
    columns={
        "adm2_pcode": "District Code",
        "adm2_name": "District",
        "adm1_name": "County",
        "COUNT_OBJECTID": "Reported Cases",
        "Incidence_100k": "Incidence per 100k",
        "Rainfall_mm": "Rainfall (mm)",
        "Temperature_C": "Temperature (°C)",
        "Outbreak_Probability": "Outbreak Probability",
        "Risk_Level": "Risk Level"
    }
)

# Optional formatting
display_df["Outbreak Probability"] = (
    display_df["Outbreak Probability"]
    .astype(float)
    .apply(lambda x: f"{x:.6f}")
)

display_df["Incidence per 100k"] = (
    display_df["Incidence per 100k"]
    .astype(float)
    .apply(lambda x: f"{x:.2f}")
)

display_df["Rainfall (mm)"] = (
    display_df["Rainfall (mm)"]
    .astype(float)
    .apply(lambda x: f"{x:.2f}")
)

display_df["Temperature (°C)"] = (
    display_df["Temperature (°C)"]
    .astype(float)
    .apply(lambda x: f"{x:.2f}")
)

st.dataframe(
    display_df,
    width="stretch"
)


# --------------------------------
# Scheduled Refresh Simulation
# --------------------------------

from refresh_simulator import simulate_refresh

st.subheader("Scheduled Refresh Simulation")

st.markdown("""
This section simulates an operational data refresh workflow. In a production
environment, this process would be scheduled to ingest updated surveillance
records, validate aggregated district-level data, refresh model outputs, and
update the dashboard.
""")

if st.button("Run Simulated Data Refresh"):
    refresh_result = simulate_refresh()

    st.success(refresh_result["message"])
    st.code(refresh_result["backup_file"])
    

# --------------------------------
# Governance and Privacy Controls
# --------------------------------
st.subheader("Governance and Privacy Controls")

st.success("District-level aggregated surveillance data only")

st.info("""
No personally identifiable information (PII) is stored, displayed,
or transmitted within this GeoAI prototype.
""")

st.markdown("""
Security and governance controls implemented or represented in this prototype include:

- JWT authentication
- Role-Based Access Control (RBAC)
- Audit logging
- Secure API mediation
- Aggregated surveillance analytics
- Privacy-preserving spatial intelligence
- Explainable GeoAI outputs
""")