import streamlit as st
import geopandas as gpd
import pydeck as pdk
import pandas as pd

# Load the GeoPackage files and specify the exact layers
gpkg_files = {
    "Air Quality": ("copieddata/states_india_air.gpkg", "states_india_air"),
    "Agriculture": ("copieddata/states_india_Agri.gpkg", "states_india_Agri"),
}

# Set color ranges for gradation (based on 5 classes)
color_ranges = {
    "Air Quality": [
        [255, 255, 178, 150],   # 15-28
        [254, 204, 92, 150],    # 28-78
        [253, 141, 60, 150],    # 78-109
        [240, 59, 32, 150],     # 109-144
        [189, 0, 38, 150]       # 144-176
    ],
    "Agriculture": [
        [239, 243, 255, 150],   # 1-2246
        [189, 215, 231, 150],   # 2246-6770
        [107, 174, 214, 150],   # 6770-12777
        [49, 130, 189, 150],    # 12777-20751
        [8, 81, 156, 150]       # 20751-25493
    ]
}

# Sidebar for selecting layers
st.sidebar.title("Select Layers to Display")
selected_layers = st.sidebar.multiselect("Choose layers:", gpkg_files.keys())

# Initialize an empty list to hold selected GeoDataFrames
selected_gdfs = []

# Load selected GeoDataFrames and apply color ranges
for layer in selected_layers:
    filepath, gpkg_layer = gpkg_files[layer]
    gdf = gpd.read_file(filepath, layer=gpkg_layer)
    
    # Determine color ranges based on values for each layer
    if layer == "Air Quality":
        bins = [15, 28, 78, 109, 144, 176]
        gdf['color'] = pd.cut(
            gdf['india_states_aqi_no_latlong_AQI-US'],
            bins=bins,
            labels=color_ranges[layer]
        )
    elif layer == "Agriculture":
        bins = [1, 2246, 6770, 12777, 20751, 25493]
        gdf['color'] = pd.cut(
            gdf['state_agricultural_land_Agricultural Land (in thousand hectares)'],
            bins=bins,
            labels=color_ranges[layer]
        )
    
    selected_gdfs.append(gdf)

# Combine all selected GeoDataFrames
if selected_gdfs:
    combined_gdf = gpd.GeoDataFrame(pd.concat(selected_gdfs, ignore_index=True))
    combined_gdf = combined_gdf.to_crs(epsg=4326)  # Convert to WGS84 for mapping
    
    # Map display using Pydeck
    layers = []
    for _, row in combined_gdf.iterrows():
        layers.append(
            pdk.Layer(
                "GeoJsonLayer",
                data=row.geometry.__geo_interface__,
                get_fill_color=row['color'],
                get_line_color=[0, 0, 0, 100],
            )
        )
        
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v10',
        initial_view_state=pdk.ViewState(
            latitude=20.5937,
            longitude=78.9629,
            zoom=4,
            pitch=0,
        ),
        layers=layers,
    ))
else:
    st.write("Select layers from the sidebar to display them on the map.")
