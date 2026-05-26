import geopandas as gpd
import folium


def classify_hotspot(zscore, pvalue):
    """
    Classify Getis-Ord Gi* hotspot significance
    """

    if pvalue <= 0.05 and zscore > 1.96:
        return "Hotspot"

    elif pvalue <= 0.05 and zscore < -1.96:
        return "Coldspot"

    else:
        return "Not Significant"


def create_geoai_map():

    # --------------------------------
    # Load GeoAI layers
    # --------------------------------

    district_gdf = gpd.read_file(
        "data/geoai_spatial_intelligence.geojson"
    )

    county_gdf = gpd.read_file(
        "data/lbr_admin1.geojson"
    )

    # --------------------------------
    # Clean timestamp/object fields
    # --------------------------------

    for gdf in [district_gdf, county_gdf]:

        for col in gdf.columns:

            if col != "geometry":

                gdf[col] = gdf[col].apply(
                    lambda x: str(x)
                    if hasattr(x, "isoformat")
                    else x
                )

    # --------------------------------
    # Standardize LISA labels
    # --------------------------------

    district_gdf["LISA_cluster"] = (
        district_gdf["LISA_cluster"]
        .replace("", "Not Significant")
        .fillna("Not Significant")
    )

    lisa_labels = {
        "HH": "High-High Cluster",
        "HL": "High-Low Outlier",
        "LH": "Low-High Outlier",
        "LL": "Low-Low Cluster",
        "Not Significant": "Not Significant"
    }

    district_gdf["LISA_cluster_Display"] = (
        district_gdf["LISA_cluster"]
        .map(lisa_labels)
        .fillna("Not Significant")
    )

    # --------------------------------
    # Create hotspot intelligence field
    # --------------------------------

    if (
        "GiZScore" in district_gdf.columns
        and "GiPValue" in district_gdf.columns
    ):

        district_gdf["Hotspot_Class"] = district_gdf.apply(
            lambda row: classify_hotspot(
                float(row["GiZScore"]),
                float(row["GiPValue"])
            ),
            axis=1
        )

        district_gdf["GiZScore_Display"] = (
            district_gdf["GiZScore"]
            .astype(float)
            .apply(lambda x: f"{x:.4f}")
        )

        district_gdf["GiPValue_Display"] = (
            district_gdf["GiPValue"]
            .astype(float)
            .apply(lambda x: f"{x:.6f}")
        )

    else:

        district_gdf["Hotspot_Class"] = "Not Available"
        district_gdf["GiZScore_Display"] = "Not Available"
        district_gdf["GiPValue_Display"] = "Not Available"

    # --------------------------------
    # Format display fields
    # --------------------------------

    district_gdf["Outbreak_Probability_Display"] = (
        district_gdf["Outbreak_Probability"]
        .astype(float)
        .apply(lambda x: f"{x:.6f}")
    )

    district_gdf["Cum_Incidence_100k_Display"] = (
        district_gdf["Cum_Incidence_100k"]
        .astype(float)
        .apply(lambda x: f"{x:.6f}")
    )

    district_gdf["Rainfall_mm_Display"] = (
        district_gdf["Rainfall_mm"]
        .astype(float)
        .apply(lambda x: f"{x:.2f}")
    )

    district_gdf["Temperature_C_Display"] = (
        district_gdf["Temperature_C"]
        .astype(float)
        .apply(lambda x: f"{x:.2f}")
    )

    # --------------------------------
    # Format LISA statistics
    # --------------------------------

    if "LISA_ZScore" in district_gdf.columns:

        district_gdf["LISA_ZScore_Display"] = (
            district_gdf["LISA_ZScore"]
            .astype(float)
            .apply(lambda x: f"{x:.4f}")
        )

    else:

        district_gdf["LISA_ZScore_Display"] = "Not Available"

    if "LISA_PValue" in district_gdf.columns:

        district_gdf["LISA_PValue_Display"] = (
            district_gdf["LISA_PValue"]
            .astype(float)
            .apply(lambda x: f"{x:.6f}")
        )

    else:

        district_gdf["LISA_PValue_Display"] = "Not Available"

    # --------------------------------
    # Create Folium map
    # --------------------------------

    m = folium.Map(
        location=[6.5, -9.5],
        zoom_start=7,
        tiles="CartoDB positron"
    )

    # --------------------------------
    # Risk classification colors
    # --------------------------------

    risk_colors = {
        "Low Risk": "#2ECC71",
        "Moderate Risk": "#F39C12",
        "High Risk": "#E74C3C"
    }

    # --------------------------------
    # District GeoAI layer
    # --------------------------------

    folium.GeoJson(
        district_gdf,
        name="District Risk Layer",

        style_function=lambda feature: {

            "fillColor": risk_colors.get(
                feature["properties"].get("Risk_Level"),
                "#808080"
            ),

            "color": "#555555",

            "weight": 0.4,

            "fillOpacity": 0.72,
        },

        highlight_function=lambda feature: {

            "weight": 2,

            "color": "#000000",

            "fillOpacity": 0.85,
        },

        tooltip=folium.GeoJsonTooltip(

            fields=[
                "adm2_name",
                "adm1_name",
                "Risk_Level",
                "Outbreak_Probability_Display",
                "Cum_Incidence_100k_Display",
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
                "Risk Level",
                "Outbreak Probability",
                "Cumulative Incidence per 100k",
                "Rainfall (mm)",
                "Temperature (°C)",
                "Hotspot Intelligence",
                "Local Moran's I Cluster",
                "LISA Z-Score",
                "LISA P-Value",
                "Gi* Z-Score",
                "Gi* P-Value"
            ],

            localize=True,
            sticky=True
        )

    ).add_to(m)

    # --------------------------------
    # County boundary layer
    # --------------------------------

    folium.GeoJson(

        county_gdf,

        name="County Boundaries",

        style_function=lambda feature: {

            "fillColor": "transparent",

            "color": "#5A0000",

            "weight": 1.4,

            "fillOpacity": 0,
        },

        interactive=False

    ).add_to(m)

    # --------------------------------
    # County labels
    # --------------------------------

    county_label_col = "adm1_name"

    for _, row in county_gdf.iterrows():

        centroid = row.geometry.centroid

        folium.Marker(

            location=[centroid.y, centroid.x],

            icon=folium.DivIcon(

                html=f"""
                <div style="
                    font-size: 11px;
                    font-weight: bold;
                    color: #5A0000;
                    text-shadow: 1px 1px 2px white;
                    pointer-events: none;
                    white-space: nowrap;
                    ">
                    {row[county_label_col]}
                </div>
                """
            )

        ).add_to(m)

    # --------------------------------
    # Layer controls
    # --------------------------------

    folium.LayerControl(
        collapsed=False
    ).add_to(m)

    return m