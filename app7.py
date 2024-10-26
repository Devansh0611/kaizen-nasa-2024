import streamlit as st
import geopandas as gpd
import pydeck as pdk
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
import plotly.graph_objects as go
import base64

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
    # Combine all selected GeoDataFrames into one for mapping
    if selected_gdfs:
        combined_gdf = gpd.GeoDataFrame(pd.concat(selected_gdfs, ignore_index=True)).to_crs(epsg=4326)
        layers = [
            pdk.Layer(
                "GeoJsonLayer",
                data=combined_gdf[combined_gdf['color'] == color].__geo_interface__,
                get_fill_color=color[:3],  # Use RGB from the RGBA tuple
                get_line_color=[0, 0, 0, 50],
                opacity=0.6,
                pickable=True,
            )
            for color in color_ranges[layer]
        ]
        
        # Map Display with Pydeck
        st.pydeck_chart(
            pdk.Deck(
                map_style='mapbox://styles/mapbox/light-v10',
                initial_view_state=pdk.ViewState(latitude=20.5937, longitude=78.9629, zoom=3),
                layers=layers,
                tooltip={"text": "{name}: {value_column}"}
            )
        )

        # Display legends below map
        for layer in selected_layers:
            st.write(f"#### {layer} Legend")
            fig, ax = plt.subplots(figsize=(6, 0.2))
            patches = [
                mpatches.Patch(color=[c/255 for c in color[:3]], label=f"{bins[i]} - {bins[i+1]}")
                for i, color in enumerate(color_ranges[layer])
            ]
            ax.legend(handles=patches, loc='center', ncol=len(patches), frameon=False)
            ax.axis('off')
            st.pyplot(fig)

with right_col:
    # Display interactive graphs and charts for each selected layer
    for gdf, layer in zip(selected_gdfs, selected_layers):
        st.write(f"### Data Analysis for {layer}")

        # Show a bar chart for top regions in terms of 'value_column'
        top_regions = gdf.nlargest(10, 'value_column')[['st_nm', 'value_column']]
        fig = px.bar(top_regions, x='st_nm', y='value_column', title=f'Top 10 Regions by {layer}')
        st.plotly_chart(fig)

        # Time-series chart if historical data is available
        if 'year' in gdf.columns:
            region_name = st.selectbox(f"Select Region to view time-series data for {layer}", gdf['st_nm'].unique())
            region_data = gdf[gdf['st_nm'] == region_name]
            fig = px.line(region_data, x='year', y='value_column', title=f'{layer} over Time for {region_name}')
            st.plotly_chart(fig)
