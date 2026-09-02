from pathlib import Path
from urllib.parse import quote

import folium
import geopandas as gpd
import pandas as pd


# ---------------------------------------------------
# Project paths
# ---------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

DISTRICT_FILE = DATA_DIR / "GeoAI_District_Risk_Combined.geojson"
COUNTY_FILE = DATA_DIR / "lbr_admin1.geojson"


# ---------------------------------------------------
# Hotspot classification
# ---------------------------------------------------

def classify_hotspot(zscore, pvalue):
    """
    Classify Getis-Ord Gi* hotspot significance.

    Parameters
    ----------
    zscore : float
        Getis-Ord Gi* z-score.
    pvalue : float
        Getis-Ord Gi* p-value.

    Returns
    -------
    str
        Hotspot, Coldspot, Not Significant, or Not Available.
    """

    if pd.isna(zscore) or pd.isna(pvalue):
        return "Not Available"

    if pvalue <= 0.05 and zscore > 1.96:
        return "Hotspot"

    if pvalue <= 0.05 and zscore < -1.96:
        return "Coldspot"

    return "Not Significant"


# ---------------------------------------------------
# Safe numeric formatting
# ---------------------------------------------------

def format_numeric(value, decimals=2, suffix=""):
    """
    Safely format numeric values for Folium tooltips.
    """

    value = pd.to_numeric(value, errors="coerce")

    if pd.isna(value):
        return "Not Available"

    return f"{value:.{decimals}f}{suffix}"


# ---------------------------------------------------
# Validate required fields
# ---------------------------------------------------

def validate_fields(gdf, required_fields, layer_name):
    """
    Raise a clear error if required fields are missing.
    """

    missing_fields = [
        field for field in required_fields
        if field not in gdf.columns
    ]

    if missing_fields:
        raise ValueError(
            f"{layer_name} is missing required fields: "
            f"{', '.join(missing_fields)}"
        )


# ---------------------------------------------------
# Create interactive GeoAI map
# ---------------------------------------------------

def create_geoai_map(carto_basemap_api_key=None):
    """
    Create the operational GeoAI spatial intelligence map.

    The map displays:
    - Relative district outbreak-risk categories
    - Predicted outbreak probabilities
    - Incidence and environmental indicators
    - Getis-Ord Gi* hotspot intelligence
    - Local Moran's I cluster information
    - County boundaries and labels

    Parameters
    ----------
    carto_basemap_api_key : str, optional
        CARTO-issued public basemap key. When omitted, the map uses the
        OpenStreetMap basemap so unauthenticated CARTO watermark tiles are
        never displayed.
    """

    # --------------------------------
    # Confirm source files exist
    # --------------------------------

    if not DISTRICT_FILE.exists():
        raise FileNotFoundError(
            f"District GeoJSON not found: {DISTRICT_FILE}"
        )

    if not COUNTY_FILE.exists():
        raise FileNotFoundError(
            f"County GeoJSON not found: {COUNTY_FILE}"
        )

    # --------------------------------
    # Load final GeoAI layers
    # --------------------------------

    district_gdf = gpd.read_file(DISTRICT_FILE)
    county_gdf = gpd.read_file(COUNTY_FILE)

    # --------------------------------
    # Validate required fields
    # --------------------------------

    required_district_fields = [
        "adm2_pcode",
        "adm2_name",
        "adm1_name",
        "Predicted_Probability",
        "Risk_Level",
        "Rainfall_mm",
        "Temperature_C",
        "Incidence_100k",
        "GiZScore",
        "GiPValue",
        "LISA_cluster",
        "LISA_ZScore",
        "LISA_PValue",
        "geometry"
    ]

    validate_fields(
        district_gdf,
        required_district_fields,
        "District GeoAI layer"
    )

    validate_fields(
        county_gdf,
        ["adm1_name", "geometry"],
        "County boundary layer"
    )

    # --------------------------------
    # Ensure web-map coordinate system
    # --------------------------------

    if district_gdf.crs is None:
        district_gdf = district_gdf.set_crs(
            "EPSG:4326",
            allow_override=True
        )
    elif district_gdf.crs.to_epsg() != 4326:
        district_gdf = district_gdf.to_crs("EPSG:4326")

    if county_gdf.crs is None:
        county_gdf = county_gdf.set_crs(
            "EPSG:4326",
            allow_override=True
        )
    elif county_gdf.crs.to_epsg() != 4326:
        county_gdf = county_gdf.to_crs("EPSG:4326")

    # --------------------------------
    # Standardise text fields
    # --------------------------------

    text_fields = [
        "adm2_pcode",
        "adm2_name",
        "adm1_name",
        "Risk_Level",
        "LISA_cluster"
    ]

    for field in text_fields:
        district_gdf[field] = (
            district_gdf[field]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    district_gdf["Risk_Level"] = (
        district_gdf["Risk_Level"]
        .replace(
            {
                "Low": "Low Risk",
                "Moderate": "Moderate Risk",
                "High": "High Risk"
            }
        )
        .replace("", "Not Available")
    )

    # --------------------------------
    # Convert analytical fields to numeric
    # --------------------------------

    numeric_fields = [
        "Predicted_Probability",
        "Rainfall_mm",
        "Temperature_C",
        "Incidence_100k",
        "GiZScore",
        "GiPValue",
        "LISA_ZScore",
        "LISA_PValue"
    ]

    for field in numeric_fields:
        district_gdf[field] = pd.to_numeric(
            district_gdf[field],
            errors="coerce"
        )

    # --------------------------------
    # Standardise LISA labels
    # --------------------------------

    district_gdf["LISA_cluster"] = (
        district_gdf["LISA_cluster"]
        .replace(
            {
                "": "Not Significant",
                "nan": "Not Significant",
                "None": "Not Significant"
            }
        )
        .fillna("Not Significant")
    )

    lisa_labels = {
        "HH": "High-High Cluster",
        "HL": "High-Low Outlier",
        "LH": "Low-High Outlier",
        "LL": "Low-Low Cluster",
        "High-High": "High-High Cluster",
        "High-Low": "High-Low Outlier",
        "Low-High": "Low-High Outlier",
        "Low-Low": "Low-Low Cluster",
        "Not Significant": "Not Significant"
    }

    district_gdf["LISA_cluster_Display"] = (
        district_gdf["LISA_cluster"]
        .map(lisa_labels)
        .fillna(district_gdf["LISA_cluster"])
    )

    # --------------------------------
    # Create hotspot classification
    # --------------------------------

    district_gdf["Hotspot_Class"] = district_gdf.apply(
        lambda row: classify_hotspot(
            row["GiZScore"],
            row["GiPValue"]
        ),
        axis=1
    )

    # --------------------------------
    # Create display fields
    # --------------------------------

    district_gdf["Predicted_Probability_Display"] = (
        district_gdf["Predicted_Probability"]
        .apply(
            lambda value: format_numeric(
                value,
                decimals=6
            )
        )
    )

    district_gdf["Predicted_Probability_Percent"] = (
        district_gdf["Predicted_Probability"]
        .apply(
            lambda value: format_numeric(
                value * 100
                if pd.notna(value)
                else value,
                decimals=2,
                suffix="%"
            )
        )
    )

    district_gdf["Incidence_100k_Display"] = (
        district_gdf["Incidence_100k"]
        .apply(
            lambda value: format_numeric(
                value,
                decimals=2
            )
        )
    )

    district_gdf["Rainfall_mm_Display"] = (
        district_gdf["Rainfall_mm"]
        .apply(
            lambda value: format_numeric(
                value,
                decimals=2
            )
        )
    )

    district_gdf["Temperature_C_Display"] = (
        district_gdf["Temperature_C"]
        .apply(
            lambda value: format_numeric(
                value,
                decimals=2
            )
        )
    )

    district_gdf["GiZScore_Display"] = (
        district_gdf["GiZScore"]
        .apply(
            lambda value: format_numeric(
                value,
                decimals=4
            )
        )
    )

    district_gdf["GiPValue_Display"] = (
        district_gdf["GiPValue"]
        .apply(
            lambda value: format_numeric(
                value,
                decimals=6
            )
        )
    )

    district_gdf["LISA_ZScore_Display"] = (
        district_gdf["LISA_ZScore"]
        .apply(
            lambda value: format_numeric(
                value,
                decimals=4
            )
        )
    )

    district_gdf["LISA_PValue_Display"] = (
        district_gdf["LISA_PValue"]
        .apply(
            lambda value: format_numeric(
                value,
                decimals=6
            )
        )
    )

    # --------------------------------
    # Clean unsupported object values
    # --------------------------------

    for gdf in [district_gdf, county_gdf]:
        for column in gdf.columns:
            if column == "geometry":
                continue

            gdf[column] = gdf[column].apply(
                lambda value: value.isoformat()
                if hasattr(value, "isoformat")
                else value
            )

    # --------------------------------
    # Create Folium map
    # --------------------------------

    geoai_map = folium.Map(
        location=[6.5, -9.5],
        zoom_start=7,
        tiles=None,
        control_scale=True
    )

    carto_basemap_api_key = str(
        carto_basemap_api_key or ""
    ).strip()

    if carto_basemap_api_key:
        encoded_carto_key = quote(
            carto_basemap_api_key,
            safe="",
        )
        folium.TileLayer(
            tiles=(
                "https://{s}.basemaps.cartocdn.com/"
                "light_all/{z}/{x}/{y}{r}.png"
                f"?key={encoded_carto_key}"
            ),
            attr=(
                '&copy; <a href="https://www.openstreetmap.org/copyright">'
                'OpenStreetMap</a> contributors &copy; '
                '<a href="https://carto.com/attributions">CARTO</a>'
            ),
            name="CARTO Positron",
            subdomains="abcd",
            max_zoom=20,
            overlay=False,
            control=True,
            show=True,
        ).add_to(geoai_map)
    else:
        folium.TileLayer(
            tiles="OpenStreetMap",
            name="OpenStreetMap",
            overlay=False,
            control=True,
            show=True,
        ).add_to(geoai_map)

    # --------------------------------
    # Risk-classification colours
    # --------------------------------

    risk_colors = {
        "Low Risk": "#2ECC71",
        "Moderate Risk": "#F39C12",
        "High Risk": "#E74C3C",
        "Not Available": "#808080"
    }

    # --------------------------------
    # District GeoAI layer
    # --------------------------------

    folium.GeoJson(
        district_gdf,
        name="Relative District Outbreak Risk",
        show=True,
        style_function=lambda feature: {
            "fillColor": risk_colors.get(
                feature["properties"].get(
                    "Risk_Level",
                    "Not Available"
                ),
                "#808080"
            ),
            "color": "#555555",
            "weight": 0.5,
            "fillOpacity": 0.72
        },
        highlight_function=lambda feature: {
            "weight": 2.0,
            "color": "#000000",
            "fillOpacity": 0.88
        },
        tooltip=folium.GeoJsonTooltip(
            fields=[
                "adm2_name",
                "adm1_name",
                "Risk_Level",
                "Predicted_Probability_Display",
                "Predicted_Probability_Percent",
                "Incidence_100k_Display",
                "Rainfall_mm_Display",
                "Temperature_C_Display",
                "Hotspot_Class",
                "LISA_cluster_Display",
                "LISA_ZScore_Display",
                "LISA_PValue_Display",
                "GiZScore_Display",
                "GiPValue_Display"
            ],
            aliases=[
                "District",
                "County",
                "Relative Risk Category",
                "Predicted Probability (0–1)",
                "Predicted Probability (%)",
                "Incidence per 100k",
                "Rainfall (mm)",
                "Temperature (°C)",
                "Getis-Ord Gi* Classification",
                "Local Moran's I Cluster",
                "LISA Z-Score",
                "LISA P-Value",
                "Gi* Z-Score",
                "Gi* P-Value"
            ],
            localize=True,
            sticky=True,
            labels=True,
            style=(
                "background-color: white; "
                "color: #222222; "
                "font-family: Arial; "
                "font-size: 12px; "
                "padding: 8px;"
            )
        )
    ).add_to(geoai_map)

    # --------------------------------
    # County boundary layer
    # --------------------------------

    folium.GeoJson(
        county_gdf,
        name="County Boundaries",
        show=True,
        style_function=lambda feature: {
            "fillColor": "transparent",
            "color": "#5A0000",
            "weight": 1.4,
            "fillOpacity": 0
        },
        interactive=False
    ).add_to(geoai_map)

    # --------------------------------
    # County labels
    # --------------------------------

    county_label_col = "adm1_name"

    for _, row in county_gdf.iterrows():
        if row.geometry is None or row.geometry.is_empty:
            continue

        label_point = row.geometry.representative_point()

        county_name = str(
            row.get(
                county_label_col,
                ""
            )
        ).strip()

        folium.Marker(
            location=[
                label_point.y,
                label_point.x
            ],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-size: 11px;
                    font-weight: bold;
                    color: #5A0000;
                    text-shadow:
                        -1px -1px 0 white,
                         1px -1px 0 white,
                        -1px  1px 0 white,
                         1px  1px 0 white;
                    pointer-events: none;
                    white-space: nowrap;
                    transform: translate(-50%, -50%);
                ">
                    {county_name}
                </div>
                """
            )
        ).add_to(geoai_map)

    # --------------------------------
    # Layer control
    # --------------------------------

    folium.LayerControl(
        collapsed=False
    ).add_to(geoai_map)

    return geoai_map
