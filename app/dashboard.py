from pathlib import Path

import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
import plotly.express as px
from branca.element import MacroElement, Template
from map_utils import create_geoai_map
from audit_logger import log_event
from streamlit_folium import st_folium
from datetime import datetime, timezone

# ---------------------------------------------------
# Project paths
# ---------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "figures"
LOGS_DIR = PROJECT_ROOT / "logs"


def _optional_setting(name):
    """Read an optional setting from Streamlit secrets or the environment."""
    environment_value = os.getenv(name, "").strip()

    try:
        value = st.secrets.get(name, environment_value)
    except (FileNotFoundError, KeyError):
        value = environment_value

    return str(value or "").strip()

st.set_page_config(
    page_title="Liberia GeoAI Outbreak Watch",
    layout="wide"
)

# ---------------------------------------------------
# Accessible visual hierarchy
# ---------------------------------------------------

st.markdown(
    """
    <style>
    :root {
        --geoai-indigo: #4338ca;
        --geoai-blue: #2563eb;
        --geoai-teal: #0f766e;
        --geoai-ink: #172033;
        --geoai-muted: #526078;
        --geoai-line: #dce5f0;
        --geoai-surface: rgba(255, 255, 255, 0.92);
    }
    /* A calm indigo-teal canvas keeps dense analytical content readable. */
    .stApp {
        color: var(--geoai-ink);
        background:
            radial-gradient(circle at 8% 6%, rgba(67, 56, 202, 0.07), transparent 24rem),
            radial-gradient(circle at 92% 12%, rgba(15, 118, 110, 0.07), transparent 26rem),
            linear-gradient(180deg, #f8fbff 0%, #ffffff 24rem, #f8fafc 100%);
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 1180px;
    }
    h1 { font-size: clamp(2rem, 3vw, 2.35rem) !important; line-height: 1.15 !important; }
    h2 {
        color: #172554 !important;
        font-size: clamp(1.55rem, 2.2vw, 1.8rem) !important;
    }
    h3 {
        color: #1e2b4d !important;
        font-size: clamp(1.25rem, 1.8vw, 1.5rem) !important;
        letter-spacing: -0.012em;
    }
    p, li, label, [data-testid="stCaptionContainer"] {
        font-size: 0.94rem !important;
        line-height: 1.55 !important;
    }
    [data-testid="stCaptionContainer"], .stCaption {
        color: #4b5563 !important;
    }
    [data-testid="stMetricLabel"] p {
        color: #374151 !important;
        font-weight: 650 !important;
    }
    [data-testid="stMetricValue"] {
        color: #111827 !important;
    }
    /* Give the four primary analytical KPIs stronger visual priority without
       enlarging every metric used elsewhere in the dashboard. */
    .st-key-primary_kpis [data-testid="stMetricLabel"] {
        align-items: flex-start !important;
        min-height: 2.9rem;
        padding-right: 2.35rem;
        overflow: visible !important;
        white-space: normal !important;
    }
    .st-key-primary_kpis [data-testid="stMetricLabel"] [data-testid="stMarkdownContainer"] {
        flex: 1 1 auto;
        min-width: 0;
        max-width: none !important;
        overflow: visible !important;
    }
    .st-key-primary_kpis [data-testid="stMetricLabel"] p {
        color: #1f2937 !important;
        font-size: clamp(0.92rem, 1.05vw, 1.05rem) !important;
        font-weight: 750 !important;
        line-height: 1.25 !important;
        max-width: none !important;
        overflow: visible !important;
        text-overflow: clip !important;
        white-space: normal !important;
    }
    .st-key-primary_kpis [data-testid="stMetricValue"],
    .st-key-primary_kpis [data-testid="stMetricValue"] > div,
    .st-key-primary_kpis [data-testid="stMetricValue"] p {
        color: #0f172a !important;
        font-size: clamp(2rem, 2.55vw, 2.35rem) !important;
        font-weight: 610 !important;
        line-height: 1.15 !important;
    }
    .st-key-primary_kpis [data-testid="stColumn"] {
        --kpi-accent: #0f766e;
        --kpi-chip: rgba(15, 118, 110, 0.11);
        position: relative;
        min-height: 8.8rem;
        overflow: hidden;
        background: #f5fbfa;
        border: 1px solid #dce3ea;
        border-left: 3px solid var(--kpi-accent);
        border-radius: 0.8rem;
        box-shadow: 0 7px 18px rgba(30, 41, 59, 0.07);
        padding: 0.95rem 1rem 0.8rem;
    }
    .st-key-primary_kpis [data-testid="stColumn"]::after {
        content: "▥";
        position: absolute;
        top: 0.78rem;
        right: 0.75rem;
        display: grid;
        place-items: center;
        width: 1.8rem;
        height: 1.8rem;
        border-radius: 0.55rem;
        background: var(--kpi-chip);
        color: var(--kpi-accent);
        font-size: 0.86rem;
        font-weight: 800;
        line-height: 1;
    }
    .st-key-primary_kpis [data-testid="stColumn"]:nth-child(2) {
        --kpi-accent: #b66a05;
        --kpi-chip: rgba(217, 119, 6, 0.13);
        background: #fffbf2;
    }
    .st-key-primary_kpis [data-testid="stColumn"]:nth-child(2)::after {
        content: "%";
    }
    .st-key-primary_kpis [data-testid="stColumn"]:nth-child(3) {
        --kpi-accent: #d45147;
        --kpi-chip: rgba(220, 38, 38, 0.11);
        background: #fff7f5;
    }
    .st-key-primary_kpis [data-testid="stColumn"]:nth-child(3)::after {
        content: "●";
    }
    .st-key-primary_kpis [data-testid="stColumn"]:nth-child(4) {
        --kpi-accent: #64748b;
        --kpi-chip: rgba(100, 116, 139, 0.12);
        background: #f8fafc;
    }
    .st-key-primary_kpis [data-testid="stColumn"]:nth-child(4)::after {
        content: "◷";
    }
    .st-key-primary_kpis [data-testid="stMetric"] {
        gap: 0.3rem;
    }
    .st-key-primary_kpis [data-testid="stCaptionContainer"] {
        color: #475569 !important;
        margin-top: 0.4rem;
    }
    .st-key-primary_kpis [data-testid="stCaptionContainer"] p {
        color: #475569 !important;
        font-size: 0.78rem !important;
        font-weight: 560 !important;
        line-height: 1.3 !important;
    }
    .geoai-hero {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1.5rem;
        padding: 0.35rem 0.1rem 0.85rem;
        border-bottom: 1px solid #d7e2e8;
    }
    .geoai-brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        min-width: 0;
    }
    .geoai-brand-mark {
        display: grid;
        place-items: center;
        flex: 0 0 auto;
        width: 2.75rem;
        height: 2.75rem;
        border: 1px solid rgba(15, 118, 110, 0.4);
        border-radius: 50%;
        background: linear-gradient(145deg, #ecfdf5, #eef2ff);
        box-shadow: 0 5px 15px rgba(15, 118, 110, 0.09);
    }
    .geoai-brand-mark svg {
        width: 1.75rem;
        height: 1.75rem;
    }
    .geoai-title-block h1 {
        margin: 0 !important;
        color: #162238 !important;
        font-size: clamp(1.65rem, 2.4vw, 2.1rem) !important;
        font-weight: 760 !important;
        line-height: 1.08 !important;
        letter-spacing: -0.025em;
    }
    .geoai-subtitle {
        margin: 0.28rem 0 0;
        color: #617084;
        font-size: 0.88rem;
        line-height: 1.4;
    }
    .geoai-prototype-badge {
        display: inline-block;
        margin-left: 0.25rem;
        padding: 0.08rem 0.42rem;
        border: 1px solid #c7d2fe;
        border-radius: 999px;
        background: #eef2ff;
        color: #3730a3;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        vertical-align: 0.08rem;
    }
    .geoai-updated {
        flex: 0 0 auto;
        text-align: right;
        white-space: nowrap;
    }
    .geoai-updated-label {
        display: block;
        color: #7a8798;
        font-size: 0.66rem;
        font-weight: 700;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }
    .geoai-updated time {
        color: #435166;
        font-size: 0.82rem;
        font-variant-numeric: tabular-nums;
    }
    .geoai-status-strip {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        margin: 0.75rem 0 1rem;
        padding: 0.62rem 0.9rem;
        border: 1px solid #dce5eb;
        border-radius: 0.72rem;
        background: rgba(255, 255, 255, 0.9);
        box-shadow: 0 5px 16px rgba(30, 41, 59, 0.055);
    }
    .geoai-status-items {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 0;
    }
    .geoai-status-item {
        display: inline-flex;
        align-items: center;
        gap: 0.42rem;
        padding: 0 0.85rem;
        border-right: 1px solid #dce5eb;
        color: #415064;
        font-size: 0.82rem;
        line-height: 1.25;
    }
    .geoai-status-item:first-child {
        padding-left: 0;
    }
    .geoai-status-item:last-child {
        border-right: 0;
    }
    .geoai-status-dot {
        width: 0.48rem;
        height: 0.48rem;
        border-radius: 50%;
        background: #16a34a;
        box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.1);
    }
    .governance-event-link {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        flex: 0 0 auto;
        color: #0f5f59 !important;
        font-size: 0.82rem;
        font-weight: 700;
        line-height: 1.2;
        text-decoration: underline;
        text-decoration-color: rgba(15, 95, 89, 0.35);
        text-underline-offset: 0.16rem;
    }
    .governance-event-link:hover {
        color: #0f766e !important;
        text-decoration-color: currentColor;
    }
    .st-key-hotspot_quick_actions {
        margin-bottom: 0.2rem;
    }
    .st-key-hotspot_quick_actions [data-testid="stPopover"] > button {
        width: 100%;
        white-space: nowrap;
    }
    .map-reset-spacer {
        height: 1.55rem;
    }
    @media (max-width: 768px) {
        .geoai-hero {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.65rem;
        }
        .geoai-updated {
            padding-left: 3.6rem;
            text-align: left;
        }
        .geoai-status-strip {
            align-items: flex-start;
            flex-direction: column;
            gap: 0.65rem;
        }
        .geoai-status-item {
            padding: 0 0.55rem;
        }
        .st-key-hotspot_quick_actions [data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }
        .st-key-hotspot_quick_actions [data-testid="stColumn"] {
            flex: 1 1 100% !important;
            width: 100% !important;
        }
        .st-key-primary_kpis [data-testid="stMetricLabel"] p {
            font-size: 0.95rem !important;
        }
        .st-key-primary_kpis [data-testid="stColumn"] {
            min-height: auto;
        }
        .map-reset-spacer {
            height: 0;
        }
    }
    [data-testid="stDataFrame"] { font-size: 0.88rem; }
    .selected-intelligence {
        border-left: 5px solid #4c1d95;
        background: #f5f3ff;
        color: #2e1065;
        padding: 0.8rem 1rem;
        border-radius: 0.35rem;
        margin: 0.6rem 0 0.9rem;
        font-weight: 600;
    }
    .action-panel {
        border-left: 5px solid var(--risk-accent);
        background: #f8fafc;
        color: #1f2937;
        padding: 0.9rem 1.1rem;
        border-radius: 0.35rem;
        margin-bottom: 0.5rem;
    }
    .action-panel ul { margin-bottom: 0.15rem; }
    [data-testid="stExpander"] {
        background: rgba(255,255,255,0.72);
        border-color: var(--geoai-line) !important;
        border-radius: 0.65rem !important;
    }
    [data-testid="stPopover"] button,
    [data-testid="stButton"] button {
        border-radius: 0.6rem;
    }
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #f4f7ff 0%, #f8fbff 52%, #f0fdfa 100%);
        border-right: 1px solid #dfe7f2;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

dashboard_updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
st.markdown(
    f"""
    <header class="geoai-hero" aria-labelledby="geoai-dashboard-title">
        <div class="geoai-brand-lockup">
            <div class="geoai-brand-mark" aria-hidden="true">
                <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 9.5 16 6l8 7-4 10-10-2Z" stroke="#0f766e" stroke-width="1.5"/>
                    <path d="m8 9.5 12 13M16 6l-6 15m14-8-14 8" stroke="#64748b" stroke-width="1"/>
                    <circle cx="8" cy="9.5" r="2.2" fill="#2563eb"/>
                    <circle cx="16" cy="6" r="2.2" fill="#0f766e"/>
                    <circle cx="24" cy="13" r="2.2" fill="#4338ca"/>
                    <circle cx="20" cy="23" r="2.2" fill="#0f766e"/>
                    <circle cx="10" cy="21" r="2.2" fill="#2563eb"/>
                </svg>
            </div>
            <div class="geoai-title-block">
                <h1 id="geoai-dashboard-title">Liberia GeoAI Outbreak Watch</h1>
                <p class="geoai-subtitle">
                    Privacy-preserving district-level COVID-19 outbreak-risk surveillance · Republic of Liberia
                    <span class="geoai-prototype-badge">Research prototype</span>
                </p>
            </div>
        </div>
        <div class="geoai-updated">
            <span class="geoai-updated-label">Last updated</span>
            <time datetime="{dashboard_updated_at}Z">{dashboard_updated_at} UTC</time>
        </div>
    </header>
    """,
    unsafe_allow_html=True,
)

def _first_existing_path(paths):
    """Return the first existing path from a collection of Path objects."""
    for path in paths:
        path = Path(path)

        if path.exists():
            return path

    raise FileNotFoundError(
        "None of the expected data files were found:\n- "
        + "\n- ".join(str(path) for path in paths)
    )


@st.cache_data
def load_data():
    """Load the full leakage-controlled district-month modelling output."""
    data_path = _first_existing_path([
        DATA_DIR / "GeoAI_Modelling_Outputs_All_4760_Observations.csv",
        DATA_DIR / "Corrected_GeoAI_Modelling_Outputs_All_4760_Observations.csv",
    ])

    data = pd.read_csv(data_path)

    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    else:
        data["Date"] = pd.to_datetime(
            {
                "year": data["Year"],
                "month": data["Month"],
                "day": 1,
            },
            errors="coerce",
        )

    required_columns = {
        "adm2_pcode",
        "adm2_name",
        "adm1_name",
        "Year",
        "Month",
        "COUNT_OBJECTID",
        "Incidence_100k",
        "Rainfall_mm",
        "Temperature_C",
        "Predicted_Probability",
    }

    missing = sorted(required_columns.difference(data.columns))
    if missing:
        raise ValueError(
            "The modelling output is missing required columns: "
            + ", ".join(missing)
        )

    return data.sort_values(
        ["adm2_pcode", "Date"]
    ).reset_index(drop=True)


def _normalise_relative_risk_label(value):
    """Return consistent relative-risk terminology for dashboard display."""
    labels = {
        "Low Risk": "Lower Relative Risk",
        "Lower Risk": "Lower Relative Risk",
        "Lower Relative Risk": "Lower Relative Risk",
        "Moderate Risk": "Moderate Relative Risk",
        "Moderate Relative Risk": "Moderate Relative Risk",
        "High Risk": "Higher Relative Risk",
        "Higher Risk": "Higher Relative Risk",
        "Higher Relative Risk": "Higher Relative Risk",
    }
    return labels.get(str(value).strip(), str(value).strip())


def _find_column(frame, candidates):
    """Return the first available column from a list of possible names."""
    lookup = {str(column).casefold(): column for column in frame.columns}
    for candidate in candidates:
        if candidate.casefold() in lookup:
            return lookup[candidate.casefold()]
    return None


def _normalise_text(value):
    """Normalise labels for resilient district and county matching."""
    return " ".join(str(value).strip().casefold().split())


def _harmonise_district_names(frame, spatial_reference):
    """Use district codes to align modelling labels with spatial labels."""
    required_columns = {"adm2_pcode", "adm2_name"}
    if (
        frame.empty
        or spatial_reference.empty
        or not required_columns.issubset(frame.columns)
        or not required_columns.issubset(spatial_reference.columns)
    ):
        return frame

    reference = spatial_reference[["adm2_pcode", "adm2_name"]].copy()
    reference["_district_code"] = (
        reference["adm2_pcode"].astype(str).str.strip()
    )
    reference["_canonical_name"] = (
        reference["adm2_name"].astype(str).str.strip()
    )
    reference = reference[
        reference["_district_code"].ne("")
        & reference["_canonical_name"].ne("")
    ].drop_duplicates("_district_code")
    canonical_names = reference.set_index("_district_code")[
        "_canonical_name"
    ]

    harmonised = frame.copy()
    district_codes = harmonised["adm2_pcode"].astype(str).str.strip()
    matched_names = district_codes.map(canonical_names)
    matched_rows = (
        matched_names.notna()
        & matched_names.astype(str).str.strip().ne("")
    )
    harmonised.loc[matched_rows, "adm2_name"] = matched_names[matched_rows]
    return harmonised


def _classify_hotspot(zscore, pvalue):
    """Classify a district using the study's 95% Getis-Ord Gi* threshold."""
    zscore = pd.to_numeric(zscore, errors="coerce")
    pvalue = pd.to_numeric(pvalue, errors="coerce")

    if pd.isna(zscore) or pd.isna(pvalue):
        return "Not Available"
    if pvalue <= 0.05 and zscore >= 1.960:
        return "Hotspot"
    if pvalue <= 0.05 and zscore <= -1.960:
        return "Coldspot"
    return "Not Significant"


def _hotspot_confidence(zscore, pvalue):
    """Report whether a Gi* result meets the study's 95% threshold."""
    zscore = pd.to_numeric(zscore, errors="coerce")
    pvalue = pd.to_numeric(pvalue, errors="coerce")

    if pd.isna(zscore) or pd.isna(pvalue):
        return "Not available"
    absolute_z = abs(zscore)
    if pvalue <= 0.05 and absolute_z >= 1.960:
        return "95%"
    return "Not significant"


def _hotspot_status_label(hotspot_class, zscore, pvalue):
    """Return an accessible badge using text as well as colour."""
    confidence = _hotspot_confidence(zscore, pvalue)
    if hotspot_class == "Hotspot":
        marker = "🔴"
        return f"{marker} Hotspot — {confidence}"
    if hotspot_class == "Coldspot":
        return f"🔵 Coldspot — {confidence}"
    if hotspot_class == "Not Available":
        return "⚪ Not available"
    return "⚪ Not significant"


@st.cache_data
def load_latest_predictions():
    """Load the latest district predictions used by the maps and dashboard."""
    latest_path = _first_existing_path([
        DATA_DIR / "Latest_District_Risk_Predictions.csv",
        DATA_DIR / "Corrected_Latest_District_Risk_Predictions.csv",
    ])

    latest = pd.read_csv(latest_path)
    latest["Date"] = pd.to_datetime(latest["Date"], errors="coerce")

    required_columns = {
        "adm2_pcode",
        "adm2_name",
        "adm1_name",
        "Predicted_Probability",
        "Risk_Level",
    }

    missing = sorted(required_columns.difference(latest.columns))
    if missing:
        raise ValueError(
            "The latest-predictions file is missing required columns: "
            + ", ".join(missing)
        )

    latest["Relative_Risk_Level"] = latest["Risk_Level"].apply(
        _normalise_relative_risk_label
    )

    return latest.sort_values(
        "Predicted_Probability",
        ascending=False,
    ).reset_index(drop=True)


@st.cache_data
def load_hotspot_intelligence(method_version):
    """Load and standardise GeoAI-derived Getis-Ord Gi* outputs."""
    # The explicit version participates in Streamlit's cache key. Increment it
    # whenever the declared hotspot method or classification threshold changes.
    _ = method_version
    hotspot_path = DATA_DIR / "GeoAI_District_Risk_Combined.geojson"
    if not hotspot_path.exists():
        return gpd.GeoDataFrame()

    hotspot_data = gpd.read_file(hotspot_path)
    if hotspot_data.empty:
        return hotspot_data

    column_candidates = {
        "adm2_pcode": ["adm2_pcode", "ADM2_PCODE", "district_code", "pcode"],
        "adm2_name": ["adm2_name", "District", "district", "ADM2_EN", "NAME_2"],
        "adm1_name": ["adm1_name", "County", "county", "ADM1_EN", "NAME_1"],
        "GiZScore": ["GiZScore", "Gi_ZScore", "GiZ", "z_score", "zscore"],
        "GiPValue": ["GiPValue", "Gi_PValue", "GiP", "p_value", "pvalue"],
        "Hotspot_Class": [
            "Hotspot_Class",
            "HotspotClass",
            "Gi_Bin",
            "GiBin",
            "hotspot_status",
        ],
    }
    source_columns = {
        canonical: _find_column(hotspot_data, candidates)
        for canonical, candidates in column_candidates.items()
    }

    if source_columns["adm2_name"] is None:
        return gpd.GeoDataFrame()

    for canonical in ("adm2_pcode", "adm2_name", "adm1_name"):
        source = source_columns[canonical]
        if source is not None:
            hotspot_data[canonical] = hotspot_data[source].astype(str)
        elif canonical == "adm2_pcode":
            hotspot_data[canonical] = ""
        else:
            hotspot_data[canonical] = "Unavailable"

    for canonical in ("GiZScore", "GiPValue"):
        source = source_columns[canonical]
        hotspot_data[canonical] = (
            pd.to_numeric(hotspot_data[source], errors="coerce")
            if source is not None
            else pd.NA
        )

    if source_columns["GiZScore"] and source_columns["GiPValue"]:
        hotspot_data["Hotspot_Class"] = hotspot_data.apply(
            lambda row: _classify_hotspot(
                row["GiZScore"],
                row["GiPValue"],
            ),
            axis=1,
        )
    elif source_columns["Hotspot_Class"]:
        source_class = hotspot_data[source_columns["Hotspot_Class"]].astype(str)
        hotspot_data["Hotspot_Class"] = source_class.apply(
            lambda value: (
                "Hotspot"
                if "hot" in value.casefold()
                and "not" not in value.casefold()
                and "cold" not in value.casefold()
                else "Coldspot"
                if "cold" in value.casefold()
                else "Not Significant"
            )
        )
    else:
        hotspot_data["Hotspot_Class"] = "Not Available"

    hotspot_data["Confidence"] = hotspot_data.apply(
        lambda row: _hotspot_confidence(
            row["GiZScore"],
            row["GiPValue"],
        ),
        axis=1,
    )
    hotspot_data["Spatial_Hotspot_Status"] = hotspot_data.apply(
        lambda row: _hotspot_status_label(
            row["Hotspot_Class"],
            row["GiZScore"],
            row["GiPValue"],
        ),
        axis=1,
    )

    return hotspot_data


df = load_data()
latest_df = load_latest_predictions()
hotspot_gdf = load_hotspot_intelligence("geoai_gi_95_v1")
df = _harmonise_district_names(df, hotspot_gdf)
latest_df = _harmonise_district_names(latest_df, hotspot_gdf)
if hotspot_gdf.empty:
    detected_hotspots_gdf = gpd.GeoDataFrame()
else:
    # Recompute threshold-derived fields after loading as a safeguard against
    # stale cached labels from an earlier 90%/95%/99% display convention.
    hotspot_gdf = hotspot_gdf.copy()
    hotspot_gdf["Hotspot_Class"] = hotspot_gdf.apply(
        lambda row: _classify_hotspot(
            row["GiZScore"],
            row["GiPValue"],
        ),
        axis=1,
    )
    hotspot_gdf["Confidence"] = hotspot_gdf.apply(
        lambda row: _hotspot_confidence(
            row["GiZScore"],
            row["GiPValue"],
        ),
        axis=1,
    )
    hotspot_gdf["Spatial_Hotspot_Status"] = hotspot_gdf.apply(
        lambda row: _hotspot_status_label(
            row["Hotspot_Class"],
            row["GiZScore"],
            row["GiPValue"],
        ),
        axis=1,
    )
    detected_hotspots_gdf = hotspot_gdf[
        (hotspot_gdf["Hotspot_Class"] == "Hotspot")
        & (hotspot_gdf["Confidence"] == "95%")
    ].copy()
    detected_hotspots_gdf = detected_hotspots_gdf.sort_values(
        ["GiZScore", "adm1_name", "adm2_name"],
        ascending=[False, True, True],
    )
    detected_hotspots_gdf = detected_hotspots_gdf.drop_duplicates(
        subset=["adm2_pcode", "adm2_name", "adm1_name"]
    ).reset_index(drop=True)
    detected_hotspots_gdf["Hotspot_Selector_Label"] = (
        detected_hotspots_gdf["adm2_name"].astype(str)
        + " — "
        + detected_hotspots_gdf["adm1_name"].astype(str)
    )


# --------------------------------
# Operational Summary Metrics
# --------------------------------

avg_risk_score = latest_df["Predicted_Probability"].mean()
avg_risk_score_pct = avg_risk_score * 100

detected_hotspot_count = len(detected_hotspots_gdf)
district_total_count = latest_df["adm2_pcode"].astype(str).nunique()
top_ranked_count = min(10, district_total_count)

try:
    audit_log = pd.read_csv(LOGS_DIR / "audit_log.csv")
    governance_events = len(audit_log)
except FileNotFoundError:
    governance_events = 0

latest_date = latest_df["Date"].max()
latest_data_period = (
    latest_date.strftime("%b %Y")
    if pd.notna(latest_date)
    else "Unavailable"
)
hotspot_analysis_period = "Latest Available Spatial Analysis"

governance_event_noun = "event" if governance_events == 1 else "events"
st.markdown(
    f"""
    <div class="geoai-status-strip" role="status" aria-label="Operational status">
        <div class="geoai-status-items">
            <span class="geoai-status-item">
                <span class="geoai-status-dot" aria-hidden="true"></span>
                Prototype services available
            </span>
            <span class="geoai-status-item">
                <span class="geoai-status-dot" aria-hidden="true"></span>
                API gateway healthy
            </span>
            <span class="geoai-status-item">
                <span class="geoai-status-dot" aria-hidden="true"></span>
                Audit logging active
            </span>
        </div>
        <a class="governance-event-link"
           href="#governance-and-privacy-controls"
           title="Open governance and privacy controls">
            {governance_events} governance {governance_event_noun} logged →
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

primary_kpi_container = st.container(key="primary_kpis")
m1, m2, m3, m4 = primary_kpi_container.columns(4)

with m1:
    st.metric(
        "Top Ranked Districts",
        f"{top_ranked_count} of {district_total_count}",
        help=(
            "The ten districts with the highest latest predicted outbreak "
            "probabilities, ranked for operational prioritisation, out of all "
            "districts in the latest national dataset."
        ),
    )
    st.caption("probability-ranked districts")

with m2:
    st.metric(
        "Mean Predicted Probability",
        f"{avg_risk_score_pct:.2f}%",
        help=(
            "Average predicted outbreak probability across the latest district "
            "records, displayed as a percentage."
        ),
    )
    st.caption("mean model probability")

with m3:
    st.metric(
        "GeoAI-Derived Spatial Hotspots",
        (
            f"{detected_hotspot_count} of {district_total_count}"
            if not hotspot_gdf.empty
            else "N/A"
        ),
        help=(
            "Districts identified by Getis-Ord Gi* as significant spatial "
            "concentrations in the model-derived risk surface at 95% confidence, "
            "out of all districts in the latest national dataset."
        ),
    )
    st.caption("Gi* spatial hotspots")

with m4:
    st.metric(
        "Latest Data",
        latest_data_period,
        help="Most recent surveillance period represented in the dashboard.",
    )
    st.caption("latest analytical period")

HOTSPOT_SELECTOR_PLACEHOLDER = "— Select a GeoAI-derived hotspot —"


def _focus_hotspot(source_key="hotspot_drilldown"):
    """Synchronise the dashboard selectors and map with a hotspot choice."""
    hotspot_label = st.session_state.get(source_key)
    if not hotspot_label or hotspot_label.startswith("—"):
        return

    match = detected_hotspots_gdf[
        detected_hotspots_gdf["Hotspot_Selector_Label"] == hotspot_label
    ]
    if match.empty:
        return

    selected = match.iloc[0]
    selected_pcode = str(selected.get("adm2_pcode", "")).strip()
    prediction_match = latest_df[
        latest_df["adm2_pcode"].astype(str).str.strip() == selected_pcode
    ]
    if prediction_match.empty:
        selected_district = selected["adm2_name"]
        selected_county = selected["adm1_name"]
    else:
        selected_district = prediction_match.iloc[0]["adm2_name"]
        selected_county = prediction_match.iloc[0]["adm1_name"]

    st.session_state["active_hotspot_label"] = hotspot_label
    counterpart_key = (
        "sidebar_hotspot_focus"
        if source_key == "hotspot_drilldown"
        else "hotspot_drilldown"
    )
    st.session_state[counterpart_key] = hotspot_label
    st.session_state["pending_county_selector"] = selected_county
    st.session_state["pending_district_selector"] = selected_district
    st.session_state["map_focus_district"] = selected_district
    st.session_state["map_focus_county"] = selected_county
    quick_focus_labels = globals().get("visible_hotspot_labels", [])
    st.session_state["hotspot_quick_focus"] = (
        hotspot_label if hotspot_label in quick_focus_labels else None
    )


def _focus_sidebar_hotspot():
    """Synchronise from the persistent sidebar hotspot selector."""
    _focus_hotspot("sidebar_hotspot_focus")


def _focus_drilldown_hotspot():
    """Synchronise from the hotspot drill-down selector."""
    _focus_hotspot("hotspot_drilldown")


def _focus_hotspot_label(hotspot_label):
    """Focus the dashboard and map from a known hotspot label."""
    st.session_state["hotspot_quick_focus"] = hotspot_label
    st.session_state["hotspot_drilldown"] = hotspot_label
    _focus_hotspot("hotspot_drilldown")


def _focus_hotspot_chip():
    """Focus the dashboard and map from a visible hotspot chip."""
    hotspot_label = st.session_state.get("hotspot_quick_focus")
    if hotspot_label:
        _focus_hotspot_label(hotspot_label)


def _clear_map_focus():
    """Return the spatial-intelligence map to its national extent."""
    st.session_state.pop("map_focus_district", None)
    st.session_state.pop("map_focus_county", None)
    st.session_state.pop("active_hotspot_label", None)
    st.session_state["hotspot_quick_focus"] = None


def _clear_hotspot_focus():
    """Clear the hotspot workflow before its widgets are instantiated."""
    _clear_map_focus()
    st.session_state["sidebar_hotspot_focus"] = (
        HOTSPOT_SELECTOR_PLACEHOLDER
    )


def _focus_selected_location():
    """Zoom the map to a district chosen through the location selectors."""
    district = st.session_state.get("district_selector")
    county = st.session_state.get("county_selector")
    if not district or not county:
        return

    st.session_state["map_focus_district"] = district
    st.session_state["map_focus_county"] = county
    st.session_state.pop("active_hotspot_label", None)
    st.session_state["hotspot_quick_focus"] = None


hotspot_names = (
    detected_hotspots_gdf["adm2_name"].tolist()
    if not detected_hotspots_gdf.empty
    else []
)
hotspot_labels = (
    detected_hotspots_gdf["Hotspot_Selector_Label"].tolist()
    if not detected_hotspots_gdf.empty
    else []
)
hotspot_summary_table = pd.DataFrame(
    columns=[
        "District",
        "County",
        "Spatial Hotspot Status",
        "Gi* z-score",
        "p-value",
        "Confidence",
    ]
)

if hotspot_names:
    st.subheader(
        f"GeoAI-Derived Spatial Hotspots — {hotspot_analysis_period}",
        help=(
            "Method: XGBoost predicted outbreak probabilities → Getis-Ord Gi* "
            "spatial analysis → GeoAI-derived hotspot intelligence. Predicted "
            "probability estimates an individual district-month; relative risk groups "
            "the latest probabilities into national tertiles; GeoAI-derived Gi* "
            "hotspots identify significant spatial concentrations in model-derived "
            "risk; and traditional Gi* hotspots use observed cumulative incidence. "
            "Interpret these complementary outputs together, not as interchangeable "
            "classifications."
        ),
    )
    visible_hotspot_labels = hotspot_labels[:5]
    hotspot_summary_table = detected_hotspots_gdf[
        [
            "adm2_name",
            "adm1_name",
            "Spatial_Hotspot_Status",
            "GiZScore",
            "GiPValue",
            "Confidence",
        ]
    ].rename(
        columns={
            "adm2_name": "District",
            "adm1_name": "County",
            "Spatial_Hotspot_Status": "Spatial Hotspot Status",
            "GiZScore": "Gi* z-score",
            "GiPValue": "p-value",
        }
    )
    hotspot_summary_table["Gi* z-score"] = (
        hotspot_summary_table["Gi* z-score"].round(3)
    )
    hotspot_summary_table["p-value"] = (
        hotspot_summary_table["p-value"].round(4)
    )

    with st.container(key="hotspot_quick_actions"):
        quick_focus_col, hotspot_directory_col = st.columns(
            [6, 2.1],
            gap="small",
            vertical_alignment="center",
        )

        with quick_focus_col:
            if hasattr(st, "pills"):
                st.pills(
                    "Quick-focus hotspot districts",
                    visible_hotspot_labels,
                    format_func=lambda label: label.split(" — ", 1)[0],
                    key="hotspot_quick_focus",
                    help="Select a district chip to focus the dashboard and map.",
                    on_change=_focus_hotspot_chip,
                    label_visibility="collapsed",
                )
            else:
                hotspot_chip_columns = st.columns(len(visible_hotspot_labels))
                for chip_column, hotspot_label in zip(
                    hotspot_chip_columns,
                    visible_hotspot_labels,
                ):
                    with chip_column:
                        st.button(
                            hotspot_label.split(" — ", 1)[0],
                            key=f"hotspot_chip::{hotspot_label}",
                            on_click=_focus_hotspot_label,
                            args=(hotspot_label,),
                            width="stretch",
                        )

        with hotspot_directory_col:
            hotspot_details_panel = (
                st.popover(
                    f"View all {detected_hotspot_count}",
                    help="Open the full GeoAI-derived hotspot district directory.",
                    width="stretch",
                )
                if hasattr(st, "popover")
                else st.expander(
                    f"View all {detected_hotspot_count} hotspot districts"
                )
            )
            with hotspot_details_panel:
                st.dataframe(
                    hotspot_summary_table,
                    hide_index=True,
                    width="stretch",
                )
                st.selectbox(
                    "Select a hotspot district",
                    hotspot_labels,
                    key="hotspot_drilldown",
                    on_change=_focus_drilldown_hotspot,
                )
                hotspot_action_col, national_view_col = st.columns(2)
                with hotspot_action_col:
                    st.button(
                        "Focus dashboard and map",
                        on_click=_focus_drilldown_hotspot,
                        width="stretch",
                    )
                with national_view_col:
                    st.button(
                        "Return map to national view",
                        on_click=_clear_map_focus,
                        width="stretch",
                    )
else:
    st.warning(
        "No statistically significant GeoAI-derived Gi* hotspot districts "
        "are available in the current spatial-intelligence output."
    )

# Render the primary decision-support regions in a map-first sequence. Data
# preparation continues below, but content written into these containers appears
# here: signal -> location -> temporal context -> action -> prioritisation.
map_slot = st.container()
decision_slot = st.container()
trend_slot = st.container()
action_slot = st.container()
ranking_slot = st.container()

st.sidebar.header("District Exploration")

with st.sidebar.expander("About this dashboard", expanded=False):
    st.markdown(
        "Use this dashboard to explore:\n\n"
        "* District-level predicted outbreak probabilities and relative-risk "
        "categories\n"
        "* Spatial hotspot intelligence\n"
        "* Explainable AI insights\n"
        "* Model performance summaries\n"
        "* Environmental and epidemiological trends\n"
        "* Governance and privacy controls\n\n"
        "Use the two workflows below to explore locations or focus directly "
        "on a statistically significant GeoAI hotspot."
    )

sidebar_hotspot_options = [
    HOTSPOT_SELECTOR_PLACEHOLDER,
    *hotspot_labels,
]
st.sidebar.markdown("### Focus on GeoAI Hotspot")
st.sidebar.selectbox(
    "Hotspot District",
    sidebar_hotspot_options,
    key="sidebar_hotspot_focus",
    on_change=_focus_sidebar_hotspot,
    help=(
        "Select a GeoAI-derived Getis-Ord Gi* hotspot to "
        "synchronise the county, district, and map."
    ),
)

st.sidebar.button(
    "Clear hotspot focus",
    width="stretch",
    on_click=_clear_hotspot_focus,
)

st.sidebar.markdown("### Explore by Location")

# --------------------------------

# County Selection

# --------------------------------

counties = sorted(df["adm1_name"].dropna().unique())

if "pending_county_selector" in st.session_state:
    st.session_state["county_selector"] = st.session_state.pop(
        "pending_county_selector"
    )

if st.session_state.get("county_selector") not in counties:
    st.session_state["county_selector"] = counties[0]

selected_county = st.sidebar.selectbox(
    "County",
    counties,
    key="county_selector",
    on_change=_clear_map_focus,
)

# --------------------------------

# District Selection (filtered by county)

# --------------------------------

county_districts = sorted(
    df.loc[
        df["adm1_name"] == selected_county,
        "adm2_name"
    ]
    .dropna()
    .unique()
)

if "pending_district_selector" in st.session_state:
    st.session_state["district_selector"] = st.session_state.pop(
        "pending_district_selector"
    )

if st.session_state.get("district_selector") not in county_districts:
    st.session_state["district_selector"] = county_districts[0]

selected_district = st.sidebar.selectbox(
    "District",
    county_districts,
    key="district_selector",
    on_change=_focus_selected_location,
)

top_ranked = (
    latest_df
      .sort_values(by="Predicted_Probability", ascending=False)
      .head(10)
      .copy()
)

hotspot_result_columns = [
    "Hotspot_Class",
    "GiZScore",
    "GiPValue",
    "Spatial_Hotspot_Status",
]
if not hotspot_gdf.empty:
    usable_pcodes = (
        hotspot_gdf["adm2_pcode"].fillna("").astype(str).str.strip().ne("")
    )
    if usable_pcodes.any():
        hotspot_lookup = hotspot_gdf[
            ["adm2_pcode", *hotspot_result_columns]
        ].drop_duplicates("adm2_pcode")
        top_ranked = top_ranked.merge(
            hotspot_lookup,
            on="adm2_pcode",
            how="left",
        )
    else:
        hotspot_lookup = hotspot_gdf[
            ["adm2_name", "adm1_name", *hotspot_result_columns]
        ].copy()
        hotspot_lookup["_district_key"] = hotspot_lookup["adm2_name"].map(
            _normalise_text
        )
        hotspot_lookup["_county_key"] = hotspot_lookup["adm1_name"].map(
            _normalise_text
        )
        hotspot_lookup = hotspot_lookup.drop_duplicates(
            ["_district_key", "_county_key"]
        )
        top_ranked["_district_key"] = top_ranked["adm2_name"].map(
            _normalise_text
        )
        top_ranked["_county_key"] = top_ranked["adm1_name"].map(
            _normalise_text
        )
        top_ranked = top_ranked.merge(
            hotspot_lookup[
                ["_district_key", "_county_key", *hotspot_result_columns]
            ],
            on=["_district_key", "_county_key"],
            how="left",
        )
else:
    for column in hotspot_result_columns:
        top_ranked[column] = pd.NA

ranking_slot.subheader(
    "Top Ranked Districts by Predicted Probability",
    help=(
        "Ranks the ten districts with the highest latest predicted outbreak "
        "probabilities. Relative-risk and hotspot columns show how this ranking "
        "compares with the complementary analytical outputs."
    ),
)

top_ranked_display = top_ranked.rename(
    columns={
        "adm2_name": "District",
        "adm1_name": "County",
        "Predicted_Probability": "Predicted Outbreak Probability (0-1)",
        "Relative_Risk_Level": "Relative Risk Category",
        "Spatial_Hotspot_Status": "Spatial Hotspot Status",
        "GiZScore": "Gi* z-score",
        "GiPValue": "Gi* p-value",
    }
)[[
    "District",
    "County",
    "Predicted Outbreak Probability (0-1)",
    "Relative Risk Category",
    "Spatial Hotspot Status",
    "Gi* z-score",
    "Gi* p-value",
]]

top_ranked_display["Predicted Outbreak Probability (%)"] = (
    top_ranked_display["Predicted Outbreak Probability (0-1)"] * 100
).round(2)
top_ranked_display["Gi* z-score"] = top_ranked_display["Gi* z-score"].round(4)
top_ranked_display["Gi* p-value"] = top_ranked_display["Gi* p-value"].round(6)
top_ranked_display["Spatial Hotspot Status"] = (
    top_ranked_display["Spatial Hotspot Status"].fillna(
        "⚪ Not significant"
    )
)
top_ranked_display.insert(
    0,
    "Rank",
    range(1, len(top_ranked_display) + 1),
)

ranking_slot.dataframe(
    top_ranked_display[
        [
            "Rank",
            "District",
            "County",
            "Predicted Outbreak Probability (%)",
            "Relative Risk Category",
            "Spatial Hotspot Status",
        ]
    ],
    hide_index=True,
    width="stretch"
)

log_event(
    user_role="analyst",
    action="district_selected",
    district=selected_district
)

start_period = df["Date"].min().strftime("%B %Y")
end_period = df["Date"].max().strftime("%B %Y")

ranking_slot.caption(f"Dataset Coverage Period: {start_period} – {end_period}")

district_df = (
    df[
        (df["adm2_name"] == selected_district)
        & (df["adm1_name"] == selected_county)
    ]
    .sort_values("Date")
    .copy()
)

latest_record = latest_df[
    (latest_df["adm2_name"] == selected_district)
    & (latest_df["adm1_name"] == selected_county)
].iloc[0]


# -----------------------------
# KPI Cards
# -----------------------------
decision_slot.subheader("Selected District Intelligence")
col1, col2, col3, col4 = decision_slot.columns(4)

col1.metric("District", latest_record["adm2_name"])
col2.metric("County", latest_record["adm1_name"])
col3.metric("Predicted Probability", f"{latest_record['Predicted_Probability'] * 100:.2f}%")
col4.metric("Relative Risk Category", latest_record["Relative_Risk_Level"])


with decision_slot.expander("How are the GeoAI risk outputs interpreted?"):

    st.markdown("""
### GeoAI Risk Outputs

The dashboard presents the model outputs in three complementary ways:

- **Predicted Outbreak Probability**
  - A model-estimated probability ranging from 0 to 1.
  - It represents the estimated likelihood that a district-month observation belongs to the outbreak-risk class.

- **Relative Risk Category**
  - Districts are grouped into **Lower Relative Risk**, **Moderate Relative Risk**, and **Higher Relative Risk** categories using tertiles of the latest predicted probabilities across all 136 districts.
  - These categories indicate relative position within the national probability distribution and are not fixed epidemiological outbreak thresholds.

- **Top Ranked Districts**
  - Districts are ordered by their latest predicted probabilities.
  - This ranking supports comparative surveillance prioritisation and resource allocation.

### Operational Interpretation

#### Higher Relative Risk
- Prioritise review of current surveillance indicators and hotspot intelligence.
- Consider enhanced monitoring and field verification where supported by additional evidence.

#### Moderate Relative Risk
- Continue enhanced review of trends and recent surveillance indicators.
- Prepare escalation if probability, case activity, or hotspot evidence increases.

#### Lower Relative Risk
- Continue routine surveillance and periodic review.
- Reassess if new case activity or spatial hotspot signals emerge.
""")

# --------------------------------
# Recommended Actions
# --------------------------------

action_slot.subheader("Recommended Actions")

selected_risk_level = latest_record["Relative_Risk_Level"]

if selected_risk_level == "Higher Relative Risk":
    action_slot.markdown("""
    <div class="action-panel" style="--risk-accent:#dc2626">
    <strong>Higher Relative Risk</strong>
    <ul>
      <li><strong>Review</strong> current surveillance indicators.</li>
      <li><strong>Compare</strong> GeoAI hotspot intelligence and recent trends.</li>
      <li><strong>Consider</strong> field verification where corroborating evidence exists.</li>
      <li><strong>Increase</strong> monitoring if elevated signals persist.</li>
      <li><strong>Prepare</strong> targeted resource allocation where operationally justified.</li>
    </ul></div>
    """, unsafe_allow_html=True)

elif selected_risk_level == "Moderate Relative Risk":
    action_slot.markdown("""
    <div class="action-panel" style="--risk-accent:#d97706">
    <strong>Moderate Relative Risk</strong>
    <ul>
      <li><strong>Continue</strong> enhanced surveillance monitoring.</li>
      <li><strong>Review</strong> district trends and hotspot indicators.</li>
      <li><strong>Monitor</strong> recent case activity and incidence changes.</li>
      <li><strong>Prepare</strong> escalation if risk indicators increase.</li>
    </ul></div>
    """, unsafe_allow_html=True)

else:
    action_slot.markdown("""
    <div class="action-panel" style="--risk-accent:#16a34a">
    <strong>Lower Relative Risk</strong>
    <ul>
      <li><strong>Continue</strong> routine surveillance.</li>
      <li><strong>Maintain</strong> periodic monitoring.</li>
      <li><strong>Review</strong> trends if new cases or hotspot signals emerge.</li>
    </ul></div>
    """, unsafe_allow_html=True)

action_slot.caption(
    f"Current relative-risk category: {latest_record['Relative_Risk_Level']} "
    f"(latest predicted outbreak probability = "
    f"{latest_record['Predicted_Probability']*100:.2f}%). "
    "The category reflects the district's relative position within the national distribution."
)

# -----------------------------
# Temporal trend
# -----------------------------
trend_slot.subheader("Temporal Outbreak Probability Trend")

latest_two = district_df.sort_values("Date").tail(2)

if len(latest_two) == 2:
    previous = latest_two.iloc[0]["Predicted_Probability"]
    current = latest_two.iloc[1]["Predicted_Probability"]

    if current > previous * 1.05:
        trend_status = "Increasing"
    elif current < previous * 0.95:
        trend_status = "Decreasing"
    else:
        trend_status = "Stable"

    trend_col1, trend_col2 = trend_slot.columns(2)

    with trend_col1:
        st.metric(
            "Current Predicted Probability",
            f"{latest_record['Predicted_Probability']*100:.2f}%"
        )

    with trend_col2:
        st.metric(
            "Trend Direction",
            trend_status
        )

with trend_slot.expander("About this trend chart"):
    st.markdown("""
    This chart shows how predicted outbreak probability changes over time
    for the selected district, supporting retrospective trend monitoring and comparative surveillance review.
    """)

trend_fig = px.line(
    district_df.sort_values("Date"),
    x="Date",
    y="Predicted_Probability",
    markers=True,
    title=f"Outbreak Probability Trend: {selected_district}"
)

trend_fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Predicted Outbreak Probability"
)

trend_slot.plotly_chart(trend_fig, width="stretch")

# --------------------------------
# Relative Risk Summary
# --------------------------------

st.subheader("Relative Risk Summary")

higher_relative_count = latest_df[
    latest_df["Relative_Risk_Level"] == "Higher Relative Risk"
].shape[0]

moderate_relative_count = latest_df[
    latest_df["Relative_Risk_Level"] == "Moderate Relative Risk"
].shape[0]

lower_relative_count = latest_df[
    latest_df["Relative_Risk_Level"] == "Lower Relative Risk"
].shape[0]

risk_summary_cards = [
    ("Lower Relative Risk", lower_relative_count, "#2ECC71", "#ecfdf5"),
    ("Moderate Relative Risk", moderate_relative_count, "#F39C12", "#fffbeb"),
    ("Higher Relative Risk", higher_relative_count, "#E74C3C", "#fef2f2"),
]

risk_summary_columns = st.columns(3)
for column, (label, count, accent, background) in zip(
    risk_summary_columns, risk_summary_cards
):
    column.markdown(
        f"""
        <div style="
            border:1px solid #e5e7eb;
            border-top:4px solid {accent};
            border-radius:0.65rem;
            background:{background};
            padding:0.9rem 1rem;
            min-height:6.1rem;
        ">
          <div style="color:#374151;font-size:0.92rem;font-weight:650;">
            {label}
          </div>
          <div style="color:#111827;font-size:1.65rem;font-weight:750;line-height:1.25;">
            {count}
          </div>
          <div style="color:#4b5563;font-size:0.82rem;">districts</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("""
The categories summarise the latest relative-risk classification derived from the
national distribution of predicted probabilities. They support comparative
prioritisation and do not represent fixed epidemiological thresholds.
""")

risk_total = max(
    lower_relative_count + moderate_relative_count + higher_relative_count,
    1,
)
risk_segments = [
    ("Lower", lower_relative_count, "#2ECC71"),
    ("Moderate", moderate_relative_count, "#F39C12"),
    ("Higher", higher_relative_count, "#E74C3C"),
]
risk_segment_html = "".join(
    f"""
    <div title="{label} Relative Risk: {count} districts"
         style="width:{(count / risk_total) * 100:.4f}%;background:{colour};
                height:0.75rem;min-width:2px;"></div>
    """
    for label, count, colour in risk_segments
)
risk_distribution_labels = "".join(
    f"""
    <span style="display:inline-flex;align-items:center;gap:0.35rem;white-space:nowrap;">
      <span style="width:0.65rem;height:0.65rem;border-radius:2px;background:{colour};
                   display:inline-block;"></span>
      {label} {count}
    </span>
    """
    for label, count, colour in risk_segments
)

st.markdown(
    f"""
    <div style="margin:0.35rem 0 0.9rem 0;">
      <div style="color:#374151;font-size:0.9rem;font-weight:650;margin-bottom:0.45rem;">
        Relative Risk Category Distribution
      </div>
      <div style="display:flex;overflow:hidden;border-radius:999px;
                  border:1px solid #d1d5db;background:#f3f4f6;">
        {risk_segment_html}
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:0.7rem 1.2rem;margin-top:0.45rem;
                  color:#4b5563;font-size:0.82rem;">
        {risk_distribution_labels}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.info(
    "The Top Ranked Districts table is a probability-based ranking and should not be "
    "interpreted as equivalent to the tertile-based relative-risk categories displayed "
    "on the classification map."
)

# --------------------------------
# Interactive GeoAI Map
# --------------------------------
map_slot.subheader(
    "GeoAI Decision-Support Spatial Intelligence Map",
    help=(
        "This map combines model-based relative-risk information with GeoAI-derived "
        "Getis-Ord Gi* hotspot intelligence. The hotspot layer shows significant "
        "spatial concentrations in model-derived outbreak risk, not the traditional "
        "Gi* analysis of observed cumulative incidence. Use Spatial focus to show "
        "all districts, GeoAI-derived hotspots, or the ten highest predicted-"
        "probability districts. The district selected in the sidebar is always "
        "highlighted; selecting it directly or through the hotspot workflow also "
        "zooms the map to its boundary."
    ),
)

map_focus_col, map_reset_col = map_slot.columns([5, 1])
with map_focus_col:
    map_filter = st.radio(
        "Spatial focus",
        [
            "All districts",
            "GeoAI-derived hotspots",
            "Top-ranked districts only",
        ],
        horizontal=True,
        help=(
            "Controls the analytical outline displayed over the underlying "
            "relative-risk classification map."
        ),
    )
with map_reset_col:
    st.markdown(
        '<div class="map-reset-spacer"></div>',
        unsafe_allow_html=True,
    )
    st.button(
        "Reset view",
        key="reset_spatial_map_view",
        on_click=_clear_map_focus,
        help=(
            "Return the map to the national extent while retaining the selected "
            "district outline."
        ),
        width="stretch",
    )

map_focus_district = st.session_state.get("map_focus_district")
map_focus_county = st.session_state.get("map_focus_county")
selected_map_district = selected_district
selected_map_county = selected_county
focus_prediction = latest_df[
    (latest_df["adm2_name"] == selected_map_district)
    & (latest_df["adm1_name"] == selected_map_county)
]
selected_pcode = (
    str(focus_prediction.iloc[0]["adm2_pcode"]).strip()
    if not focus_prediction.empty
    else ""
)
focus_spatial = gpd.GeoDataFrame()
if selected_pcode and "adm2_pcode" in hotspot_gdf.columns:
    focus_spatial = hotspot_gdf[
        hotspot_gdf["adm2_pcode"].astype(str).str.strip()
        == selected_pcode
    ]
if (
    focus_spatial.empty
    and {"adm2_name", "adm1_name"}.issubset(hotspot_gdf.columns)
):
    focus_spatial = hotspot_gdf[
        (
            hotspot_gdf["adm2_name"].map(_normalise_text)
            == _normalise_text(selected_map_district)
        )
        & (
            hotspot_gdf["adm1_name"].map(_normalise_text)
            == _normalise_text(selected_map_county)
        )
    ]
focus_probability = (
    f"{focus_prediction.iloc[0]['Predicted_Probability'] * 100:.2f}%"
    if not focus_prediction.empty else "Unavailable"
)
focus_risk = (
    focus_prediction.iloc[0]["Relative_Risk_Level"]
    if not focus_prediction.empty else "Unavailable"
)
focus_risk_display = str(focus_risk).replace(" Relative Risk", "")
if focus_spatial.empty:
    focus_spatial_summary = "GeoAI Gi* status: Spatial result unavailable"
else:
    focus_hotspot_class = str(focus_spatial.iloc[0]["Hotspot_Class"])
    focus_confidence = str(focus_spatial.iloc[0]["Confidence"])
    if focus_hotspot_class == "Hotspot":
        focus_spatial_summary = (
            f"🔴 GeoAI Gi* hotspot — {focus_confidence} confidence"
        )
    elif focus_hotspot_class == "Coldspot":
        focus_spatial_summary = (
            f"🔵 GeoAI Gi* coldspot — {focus_confidence} confidence"
        )
    else:
        focus_spatial_summary = "⚪ GeoAI Gi* status: Not significant"
map_slot.markdown(
    f"""
    <div class="selected-intelligence">
    Selected district: {selected_map_district} — {selected_map_county}<br>
    {focus_spatial_summary} · Predicted outbreak probability: {focus_probability}
    · Relative risk: {focus_risk_display}
    </div>
    """,
    unsafe_allow_html=True,
)

geoai_map = create_geoai_map(
    carto_basemap_api_key=_optional_setting(
        "CARTO_BASEMAP_API_KEY"
    )
)

# The shared map utility adds its layer control before dashboard-specific
# overlays exist. Remove it here and recreate one after every overlay has
# been registered so Leaflet never receives references to undefined layers.
for child_key, child in list(geoai_map._children.items()):
    if isinstance(child, folium.map.LayerControl):
        del geoai_map._children[child_key]

# Suppress the underlying risk choropleth in hotspot-only mode so the
# GeoAI-derived hotspot pattern remains visually distinct from both the
# relative-risk classification and traditional incidence hotspot maps.
for child in geoai_map._children.values():
    if (
        getattr(child, "layer_name", None)
        == "Relative District Outbreak Risk"
    ):
        child.show = map_filter != "GeoAI-derived hotspots"

# Add comparison overlays without changing the shared map utility.
hotspot_map_gdf = detected_hotspots_gdf.copy()
if not hotspot_map_gdf.empty and hotspot_map_gdf.crs is None:
    hotspot_map_gdf = hotspot_map_gdf.set_crs(
        "EPSG:4326",
        allow_override=True,
    )
elif (
    not hotspot_map_gdf.empty
    and hotspot_map_gdf.crs.to_epsg() != 4326
):
    hotspot_map_gdf = hotspot_map_gdf.to_crs("EPSG:4326")

if not hotspot_map_gdf.empty:
    folium.GeoJson(
        hotspot_map_gdf,
        name="GeoAI-Derived Gi* Hotspots",
        show=map_filter != "Top-ranked districts only",
        style_function=lambda feature: {
            "fillColor": "#F44336",
            "color": "#B91C1C",
            "weight": 1,
            "fillOpacity": 0.44,
            "dashArray": "4, 3",
            "lineCap": "butt",
        },
        highlight_function=lambda feature: {
            "color": "#7F1D1D",
            "weight": 1.5,
            "fillOpacity": 0.58,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "adm2_name",
                "adm1_name",
                "Spatial_Hotspot_Status",
                "GiZScore",
                "GiPValue",
                "Confidence",
            ],
            aliases=[
                "District",
                "County",
                "Gi* status",
                "Gi* z-score",
                "Gi* p-value",
                "Confidence",
            ],
            sticky=True,
        ),
    ).add_to(geoai_map)

top_ranked_map_gdf = gpd.GeoDataFrame()
if not hotspot_gdf.empty:
    usable_pcodes = (
        hotspot_gdf["adm2_pcode"].fillna("").astype(str).str.strip().ne("")
    )
    if usable_pcodes.any():
        top_ranked_codes = set(top_ranked["adm2_pcode"])
        top_ranked_map_gdf = hotspot_gdf[
            hotspot_gdf["adm2_pcode"].isin(top_ranked_codes)
        ].copy()
    else:
        top_ranked_keys = {
            (
                _normalise_text(row["adm2_name"]),
                _normalise_text(row["adm1_name"]),
            )
            for _, row in top_ranked.iterrows()
        }
        top_ranked_map_gdf = hotspot_gdf[
            hotspot_gdf.apply(
                lambda row: (
                    _normalise_text(row["adm2_name"]),
                    _normalise_text(row["adm1_name"]),
                )
                in top_ranked_keys,
                axis=1,
            )
        ].copy()

if not top_ranked_map_gdf.empty and top_ranked_map_gdf.crs is None:
    top_ranked_map_gdf = top_ranked_map_gdf.set_crs(
        "EPSG:4326",
        allow_override=True,
    )
elif (
    not top_ranked_map_gdf.empty
    and top_ranked_map_gdf.crs.to_epsg() != 4326
):
    top_ranked_map_gdf = top_ranked_map_gdf.to_crs("EPSG:4326")

if not top_ranked_map_gdf.empty:
    folium.GeoJson(
        top_ranked_map_gdf,
        name="Top 10 Probability-Ranked Districts",
        show=map_filter == "Top-ranked districts only",
        style_function=lambda feature: {
            "fillColor": "transparent",
            "color": "#1565C0",
            "weight": 3,
            "fillOpacity": 0,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "adm2_name",
                "adm1_name",
                "Spatial_Hotspot_Status",
            ],
            aliases=[
                "District",
                "County",
                "Gi* status",
            ],
            sticky=True,
        ),
    ).add_to(geoai_map)

selected_gdf = focus_spatial.copy()

if not selected_gdf.empty and selected_gdf.crs is None:
    selected_gdf = selected_gdf.set_crs(
        "EPSG:4326",
        allow_override=True,
    )
elif (
    not selected_gdf.empty
    and selected_gdf.crs.to_epsg() != 4326
):
    selected_gdf = selected_gdf.to_crs("EPSG:4326")

if not selected_gdf.empty:
    selected_row = selected_gdf.iloc[0]
    prediction_match = latest_df[
        latest_df["adm2_pcode"].astype(str)
        == str(selected_row["adm2_pcode"])
    ]
    if prediction_match.empty:
        prediction_match = latest_df[
            latest_df["adm2_name"].map(_normalise_text)
            == _normalise_text(selected_map_district)
        ]

    predicted_probability = (
        f"{prediction_match.iloc[0]['Predicted_Probability'] * 100:.2f}%"
        if not prediction_match.empty
        else "Unavailable"
    )
    relative_risk = (
        prediction_match.iloc[0]["Relative_Risk_Level"]
        if not prediction_match.empty
        else "Unavailable"
    )
    z_text = (
        f"{float(selected_row['GiZScore']):.3f}"
        if pd.notna(selected_row["GiZScore"])
        else "Unavailable"
    )
    p_text = (
        f"{float(selected_row['GiPValue']):.4f}"
        if pd.notna(selected_row["GiPValue"])
        else "Unavailable"
    )
    popup_html = f"""
    <b>{selected_map_district}</b><br>
    County: {selected_map_county}<br>
    Predicted probability: {predicted_probability}<br>
    Relative-risk category: {relative_risk}<br>
    GeoAI spatial status: {selected_row['Spatial_Hotspot_Status']}<br>
    Gi* z-score: {z_text}<br>
    p-value: {p_text}<br>
    Confidence: {selected_row['Confidence']}
    """

    selected_district_layer = folium.FeatureGroup(
        name=f"Selected District: {selected_map_district}",
        show=True,
    )

    # A white halo keeps the selected boundary legible over every risk
    # class and analytical overlay without obscuring the underlying fill.
    folium.GeoJson(
        selected_gdf,
        style_function=lambda feature: {
            "fillColor": "transparent",
            "color": "#FFFFFF",
            "weight": 9,
            "opacity": 0.95,
            "fillOpacity": 0,
        },
        interactive=False,
    ).add_to(selected_district_layer)

    folium.GeoJson(
        selected_gdf,
        style_function=lambda feature: {
            "fillColor": "transparent",
            "color": "#4C1D95",
            "weight": 5,
            "opacity": 1,
            "fillOpacity": 0,
        },
        tooltip=folium.Tooltip(
            f"Selected district: {selected_map_district} "
            f"({selected_map_county})"
        ),
        popup=folium.Popup(popup_html, max_width=360),
    ).add_to(selected_district_layer)
    selected_district_layer.add_to(geoai_map)

if (
    not selected_gdf.empty
    and map_focus_district == selected_map_district
    and map_focus_county == selected_map_county
):
    min_x, min_y, max_x, max_y = selected_gdf.total_bounds
    geoai_map.fit_bounds(
        [[min_y, min_x], [max_y, max_x]],
        padding=(35, 35),
    )

else:
    # Keep the default and reset state tightly framed around Liberia instead
    # of exposing an unnecessarily broad West African extent.
    geoai_map.fit_bounds(
        [[4.25, -11.35], [8.60, -7.40]],
        padding=(20, 20),
    )

if map_filter == "GeoAI-derived hotspots":
    risk_legend_items = """
<b>GeoAI-Derived Spatial Hotspots</b><br>
<small>Gi* analysis of model-derived outbreak risk</small><br><br>
"""
else:
    risk_legend_items = """
<b>Relative District Risk Classification</b><br>
<small>Tertile-based relative category</small><br><br>
<span style="background:#2ECC71;width:12px;height:12px;display:inline-block;margin-right:8px;"></span>Lower Relative Risk<br>
<span style="background:#F39C12;width:12px;height:12px;display:inline-block;margin-right:8px;"></span>Moderate Relative Risk<br>
<span style="background:#E74C3C;width:12px;height:12px;display:inline-block;margin-right:8px;"></span>Higher Relative Risk<br><br>
"""

legend_template = f"""
{{% macro html(this, kwargs) %}}
<div style="
    position: absolute;
    bottom: 70px;
    left: 40px;
    width: 225px;
    background-color: white;
    border: 2px solid grey;
    z-index: 9999;
    font-size: 14px;
    padding: 10px;
    border-radius: 5px;
">
{risk_legend_items}
<span style="background:#F44336;border:1px dashed #B91C1C;width:18px;height:10px;display:inline-block;margin-right:8px;"></span>GeoAI-derived Gi* hotspots<br>
<span style="border:3px solid #1565C0;width:15px;height:10px;display:inline-block;margin-right:8px;"></span>Top-ranked districts<br>
<span style="background:linear-gradient(135deg,#2ECC71 0 50%,#F39C12 50%);border:3px solid #4C1D95;box-shadow:0 0 0 2px #FFFFFF,0 0 0 3px #4C1D95;width:16px;height:10px;display:inline-block;margin:3px 10px 3px 3px;vertical-align:middle;"></span>Selected district
</div>
{{% endmacro %}}
"""

legend = MacroElement()
legend._template = Template(legend_template)
geoai_map.get_root().add_child(legend)
folium.LayerControl(collapsed=True).add_to(geoai_map)

with map_slot:
    st_folium(
        geoai_map,
        key=(
            f"geoai_map::{map_filter}::"
            f"{selected_map_county}::{selected_map_district}::"
            f"{map_focus_county or 'none'}::"
            f"{map_focus_district or 'none'}"
        ),
        height=760,
        width="stretch",
        returned_objects=[],
    )

st.subheader(
    "GeoAI-Derived Hotspot Statistics",
    help=(
        "Positive Getis-Ord Gi* results from the model-derived outbreak-risk "
        "surface, classified at 95% confidence (z ≥ 1.96 and p ≤ 0.05). "
        "These differ from incidence-based Gi* hotspots."
    ),
)
if hotspot_summary_table.empty:
    st.info(
        "No statistically significant GeoAI-derived Gi* hotspot "
        "statistics are available."
    )
else:
    st.dataframe(
        hotspot_summary_table,
        hide_index=True,
        width="stretch",
    )


# --------------------------------
# Environmental & Epidemiological Trend Tabs
# --------------------------------

st.subheader("Environmental and Epidemiological Trend")

with st.expander("About environmental and epidemiological trends"):
    st.markdown("""
    This section presents epidemiological indicators alongside environmental
    variables to support interpretation of potential drivers of outbreak risk.
    """)

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
# Explainable GeoAI Intelligence
# --------------------------------
st.subheader("Explainable GeoAI Intelligence")

with st.expander("About explainable GeoAI intelligence"):
    st.markdown("""
    This section explains why districts are classified as higher or lower outbreak risk.

    The dashboard identifies the main factors influencing outbreak predictions,
    including recent disease activity, population characteristics, and environmental conditions.

    These explanations support transparency and help users understand the reasons
    behind GeoAI-generated predictions.
    """)

col1, col2 = st.columns(2)

shap_summary_path = next(
    (
        path for path in [
            FIGURES_DIR / "Figure_4_12_Corrected_SHAP_Summary.png",
            FIGURES_DIR / "Figure_4_12_SHAP_Summary.png",
            FIGURES_DIR / "xgboost_shap_summary_plot.png",
        ]
        if path.exists()
    ),
    None,
)

shap_importance_path = next(
    (
        path for path in [
            FIGURES_DIR / "Figure_4_11_Corrected_SHAP_Feature_Importance.png",
            FIGURES_DIR / "Figure_4_11_SHAP_Feature_Importance.png",
            FIGURES_DIR / "xgboost_feature_importance.png",
        ]
        if path.exists()
    ),
    None,
)

if shap_summary_path:
    with col1:
        st.image(
            shap_summary_path,
            caption="SHAP summary of feature effects on XGBoost predictions",
            width="stretch",
        )

if shap_importance_path:
    with col2:
        st.image(
            shap_importance_path,
            caption="Mean absolute SHAP importance for the selected XGBoost model",
            width="stretch",
        )

if not shap_summary_path and not shap_importance_path:
    st.warning(
        "Explainability figures were not found. Check the files in the figures folder."
    )

st.info("""
Interpretation: Temperature, population density, and previous-period case activity
were the leading influences on the selected XGBoost model. Higher population density
and elevated previous-period case counts generally increased predicted risk, while
temperature and rainfall effects were non-linear. These associations are explanatory
model patterns and should not be interpreted as causal effects.
""")


# --------------------------------
# Model Confidence and Validation
# --------------------------------
st.subheader("Model Confidence and Validation")

model_results_path = _first_existing_path([
    DATA_DIR / "Table_4_4_Corrected_Model_Performance.csv",
    DATA_DIR / "final_geoai_model_comparison.csv",
    DATA_DIR / "demo_final_geoai_model_comparison.csv",
])

model_results = pd.read_csv(model_results_path)

model_results_display = model_results.rename(
    columns={
        "ROC_AUC": "Overall Prediction Performance (ROC-AUC)",
        "Precision": "Positive Alert Precision",
        "Recall": "Ability to Detect Outbreaks (Recall)",
        "F1_Score": "Overall Detection Balance (F1-Score)"
    }
)

with st.expander("About model confidence and validation"):
    st.markdown("""
    This section presents the performance of the evaluated prediction models.

    The results demonstrate how accurately the GeoAI framework identifies
    outbreak-risk observations within the internal test dataset and provide
    proof-of-concept evidence for comparative model evaluation.
    """)

st.dataframe(
    model_results_display,
    width="stretch"
)

best_model = model_results.sort_values(
    by=["F1_Score", "Recall", "ROC_AUC"],
    ascending=False,
).iloc[0]

st.success(
    f"Selected model: {best_model['Model']}. "
    f"It provided the strongest balance of F1-score, recall, and overall discrimination "
    f"for district-level outbreak-risk classification."
)

st.caption("""
Metric guide: Overall Prediction Performance shows how well the model separates outbreak-risk
from non-outbreak observations. Positive Alert Precision indicates the proportion of positive classifications that were correct.
Ability to Detect Outbreaks shows how well the model identifies outbreak-risk cases.
Overall Detection Balance combines alert reliability and outbreak detection.
""")

st.caption("""
Note: Model confidence is represented through validation metrics such as ROC-AUC,
Precision, Recall, and F1-Score. A district-level uncertainty or confidence interval
was not estimated in this prototype and is recommended for future enhancement.
""")


# --------------------------------
# Map and Figure Gallery
# --------------------------------
st.subheader("Analytical Map Outputs")

with st.expander("About analytical map outputs"):
    st.markdown("""
    This gallery provides access to spatial and epidemiological maps generated
    during analysis. The maps support interpretation of disease patterns,
    environmental conditions, hotspot activity, and GeoAI predictions.
    """)

# --------------------------------
# Analytical maps
# --------------------------------

MAPS_DIR = FIGURES_DIR / "maps"

map_files = {
    "Study Area / Administrative Reference Map":
        MAPS_DIR / "Study Area - Administrative Reference Map.png",

    "Predicted COVID-19 Outbreak Probability":
        MAPS_DIR / "GeoAI Outbreak Probability Map.png",

    "Relative COVID-19 Outbreak Risk Classification":
        MAPS_DIR / "GeoAI Risk Classification Map.png",

    "GeoAI-Derived Spatial Hotspot Intelligence":
        MAPS_DIR / "GEOAI HOTSPOT MAP.png",

    "Local Moran's I Cluster Analysis":
        MAPS_DIR / "Local Moran’s I Cluster_Outlier Map.png",

    "Traditional Getis-Ord Gi* Hotspot Analysis":
        MAPS_DIR / "Traditional Hotspot Analysis Map (Getis-Ord Gi).png",

    "Temperature Distribution":
        MAPS_DIR / "Temperature Distribution Map.png",

    "Rainfall Distribution":
        MAPS_DIR / "Rainfall Distribution Map.png",

    "Reported COVID-19 Cases":
        MAPS_DIR / "COVID-19 Case Count Map.png",

    "Cumulative COVID-19 Incidence":
        MAPS_DIR / "Cumulative Incidence Map.png",

    "Population Density (2022)":
        MAPS_DIR / "population_density_2022.png",
}

available_maps = {
    name: path
    for name, path in map_files.items()
    if path.exists()
}

if available_maps:

    selected_map = st.selectbox(
        "Select analytical map output",
        list(available_maps.keys())
    )

    st.image(
        available_maps[selected_map],
        caption=selected_map,
        width="stretch"
    )

else:

    st.warning(
        "No map images found. Check the file names inside figures/maps."
    )

# --------------------------------
# Data Table: Aggregated Surveillance Data
# --------------------------------

st.subheader("Aggregated District-Level Surveillance Data")

with st.expander("About this surveillance data table"):
    st.markdown("""
    This table presents privacy-preserving, district-level surveillance records
    used by the GeoAI framework. No personally identifiable information is displayed.

    Predicted outbreak probability values range from 0 to 1, where higher values
    indicate greater predicted outbreak risk.
    """)

st.caption(
    f"Current relative-risk category for {selected_district}: "
    f"{latest_record['Relative_Risk_Level']}."
)

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
        "Predicted_Probability",
        "Predicted_Class"
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
        "Predicted_Probability": "Predicted Outbreak Probability (0–1)"
    }
)

# Optional formatting
display_df["Predicted Outbreak Probability (0–1)"] = (
    display_df["Predicted Outbreak Probability (0–1)"]
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

with st.expander("About scheduled refresh simulation"):
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

with st.expander("About governance and privacy controls"):
    st.markdown("""
    This section summarises the governance and privacy safeguards implemented
    within the surveillance system to support secure, transparent, and accountable use.
    """)

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
