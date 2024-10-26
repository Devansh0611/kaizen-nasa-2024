import streamlit as st
import geopandas as gpd
import pydeck as pdk
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
import plotly.graph_objects as go
import base64
from io import BytesIO
from datetime import datetime

# Function to get base64 encoded image for the logo
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

logo_base64 = get_base64_image("logo.png")  

# Display logo and title
st.markdown(
    f"""
    <div style="display: flex; align-items: center;">
        <img src="data:image/png;base64,{logo_base64}" width="50" style="margin-right: 10px;">
        <h1 style="display: inline;">UrbanSphere</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Load the GeoPackage files and specify the exact layers
gpkg_files = {
    "Air Quality": ("copieddata/states_india_air.gpkg", "states_india_air"),
    "Agriculture": ("copieddata/states_india_Agri.gpkg", "states_india_Agri"),
    "Electricity": ("copieddata/states_india_electricity.gpkg", "states_india_electricity"),
    "Population": ("copieddata/states_india_population.gpkg", "states_india_population"),
    "Water": ("copieddata/states_india_water.gpkg", "states_india_water"),
}

# Sidebar for selecting layers
st.sidebar.title("📌 Select Layers to Display")
st.sidebar.write("Choose one or more data layers to visualize on the map.")
selected_layers = st.sidebar.multiselect("Choose layers:", gpkg_files.keys())
selected_gdfs = []  # List to hold selected GeoDataFrames

# Color ranges for layers
color_ranges = {
    "Air Quality": [(255, 247, 236, 150), (254, 232, 200, 150), (253, 187, 132, 150), (252, 141, 89, 150), (215, 48, 31, 150)],
    "Agriculture": [(237, 248, 233, 150), (199, 233, 192, 150), (161, 217, 155, 150), (116, 196, 118, 150), (35, 139, 69, 150)],
    "Electricity": [(255, 245, 235, 150), (254, 230, 206, 150), (253, 208, 162, 150), (253, 174, 107, 150), (230, 85, 13, 150)],
    "Population": [(255, 245, 240, 150), (254, 224, 210, 150), (252, 187, 161, 150), (252, 146, 114, 150), (222, 45, 38, 150)],
    "Water": [(240, 249, 255, 150), (198, 219, 239, 150), (158, 202, 225, 150), (107, 174, 214, 150), (33, 113, 181, 150)]
}

# Sidebar search for a specific region
st.sidebar.subheader("Search for Specific Region")
search_region = st.sidebar.text_input("Enter region name (e.g., Maharashtra)")

# Load selected GeoDataFrames and apply color gradation based on data ranges
for layer in selected_layers:
    filepath, gpkg_layer = gpkg_files[layer]
    gdf = gpd.read_file(filepath, layer=gpkg_layer)
    
    # Define columns and bins for each layer
    if layer == "Air Quality":
        gdf['value_column'] = pd.to_numeric(gdf['india_states_aqi_no_latlong_AQI-US'], errors='coerce')
        bins = [15, 28, 78, 109, 144, 176]
    elif layer == "Agriculture":
        gdf['value_column'] = pd.to_numeric(gdf['state_agricultural_land_Agricultural Land (in thousand hectares)'], errors='coerce')
        bins = [1, 2246, 6770, 12777, 20751, 25493]
    elif layer == "Electricity":
        gdf['value_column'] = pd.to_numeric(gdf['state_electricity_consumption_2020_21_Electricity Consumption (GWh) 2020-21'], errors='coerce')
        bins = [53, 11225, 24108, 64888, 94592, 126423]
    elif layer == "Population":
        gdf['value_column'] = pd.to_numeric(gdf['state_population_Population'], errors='coerce')
        bins = [64473, 10086292, 41974219, 72626809, 112374333, 199812341]
    elif layer == "Water":
        gdf['value_column'] = pd.to_numeric(gdf['Safe_drinking_2011 Total'], errors='coerce')
        bins = [23, 34, 54, 70, 88, 99]
        
    gdf['color'] = pd.cut(gdf['value_column'], bins=bins, labels=color_ranges[layer])
    selected_gdfs.append(gdf)

# Layout setup for map and interactive content
left_col, right_col = st.columns([3, 2])

with left_col:
    if selected_gdfs:
        combined_gdf = gpd.GeoDataFrame(pd.concat(selected_gdfs, ignore_index=True)).to_crs(epsg=4326)

        # Add latitude and longitude columns for Streamlit map
        combined_gdf["latitude"] = combined_gdf.geometry.centroid.y
        combined_gdf["longitude"] = combined_gdf.geometry.centroid.x

        # Map display
        if search_region:
            highlight_gdf = combined_gdf[combined_gdf['st_nm'].str.contains(search_region, case=False, na=False)]
            st.map(highlight_gdf)
        else:
            st.map(combined_gdf)

    st.sidebar.subheader("Map Layer Options")
    map_layer_type = st.sidebar.radio("Choose Map Type:", ["Choropleth", "Heatmap"])

    layers = []
    if map_layer_type == "Choropleth":
        for layer in selected_layers:
            for color in color_ranges[layer]:
                layers.append(
                    pdk.Layer(
                        "GeoJsonLayer",
                        data=combined_gdf[combined_gdf['color'] == color].__geo_interface__,
                        get_fill_color=color[:3],
                        get_line_color=[0, 0, 0, 50],
                        opacity=0.6,
                        pickable=True,
                    )
                )
    elif map_layer_type == "Heatmap":
        layers.append(
            pdk.Layer(
                "HeatmapLayer",
                data=combined_gdf,
                get_position="['longitude', 'latitude']",
                get_weight="value_column",
                radius=200,
                intensity=1,
                threshold=0.1,
            )
        )
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v10",
        initial_view_state=pdk.ViewState(latitude=20.5937, longitude=78.9629, zoom=3),
        layers=layers
    ))

# Interactive Layer Comparison (Split View)
st.sidebar.subheader("Compare Layers Side-by-Side")
compare_layers = st.sidebar.multiselect("Select two layers to compare", gpkg_files.keys(), default=None)

if len(compare_layers) == 2:
    with st.columns([1, 1]):
        for idx, layer in enumerate(compare_layers):
            st.write(f"### {layer} Map")
            st.map(gpkg_files[layer])

# Export Filtered Data as CSV
st.sidebar.subheader("Export Data")
if st.sidebar.button("Download Filtered Data"):
    csv = combined_gdf.to_csv().encode('utf-8')
    st.sidebar.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"filtered_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv",
        mime='text/csv',
    )

# Additional Interactivity in Data Analysis
for gdf, layer in zip(selected_gdfs, selected_layers):
    st.write(f"### Data Analysis for {layer}")

    top_regions = gdf.nlargest(10, 'value_column')[['st_nm', 'value_column']]
    fig = px.bar(top_regions, x='st_nm', y='value_column', title=f'Top 10 Regions by {layer}')
    fig.update_traces(marker_color='blue', marker_line_color='blue', marker_line_width=1.5)
    st.plotly_chart(fig)
