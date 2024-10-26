import streamlit as st
import geopandas as gpd
import pydeck as pdk
import pandas as pd

# Load the GeoPackage files and specify the exact layers
gpkg_files = {
    "Air Quality": ("copieddata/states_india_air.gpkg", "states_india_air"),
    "Agriculture": ("copieddata/states_india_Agri.gpkg", "states_india_Agri"),
    "Electricity": ("copieddata/states_india_electricity.gpkg", "states_india_electricity"),
    "Population": ("copieddata/states_india_population.gpkg", "states_india_population"),
    "Water": ("copieddata/states_india_water.gpkg", "states_india_water"),
}

# Set color ranges for gradation (based on 5 classes)
color_ranges = {
    "Air Quality": [
        (255, 247, 236, 150),   # 15-28 - Light Beige
        (254, 232, 200, 150),   # 28-78 - Light Orange
        (253, 187, 132, 150),   # 78-109 - Orange
        (252, 141, 89, 150),    # 109-144 - Dark Orange
        (215, 48, 31, 150)      # 144-176 - Red
    ],
    "Agriculture": [
        (237, 248, 233, 150),   # 1-2246 - Light Green
        (199, 233, 192, 150),   # 2246-6770 - Medium Light Green
        (161, 217, 155, 150),   # 6770-12777 - Green
        (116, 196, 118, 150),   # 12777-20751 - Darker Green
        (35, 139, 69, 150)      # 20751-25493 - Dark Green
    ],
    "Electricity": [
        (255, 245, 235, 150),   # 0-20 - Light Yellow
        (254, 230, 206, 150),   # 20-40 - Light Gold
        (253, 208, 162, 150),   # 40-60 - Gold
        (253, 174, 107, 150),   # 60-80 - Orange-Gold
        (230, 85, 13, 150)      # 80-100 - Burnt Orange
    ],
    "Population": [
        (255, 245, 240, 150),   # 0-20 - Light Pink
        (254, 224, 210, 150),   # 20-40 - Peach
        (252, 187, 161, 150),   # 40-60 - Coral
        (252, 146, 114, 150),   # 60-80 - Orange-Pink
        (222, 45, 38, 150)      # 80-100 - Red
    ],
    "Water": [
        (240, 249, 255, 150),   # 0-20 - Light Blue
        (198, 219, 239, 150),   # 20-40 - Sky Blue
        (158, 202, 225, 150),   # 40-60 - Blue
        (107, 174, 214, 150),   # 60-80 - Ocean Blue
        (33, 113, 181, 150)     # 80-100 - Deep Blue
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
    
    # Convert the relevant column to numeric, handling errors by coercing them to NaN
    if layer == "Air Quality":
        gdf['value_column'] = pd.to_numeric(gdf['india_states_aqi_no_latlong_AQI-US'], errors='coerce')
        bins = [15, 28, 78, 109, 144, 176]
        gdf['color'] = pd.cut(gdf['value_column'], bins=bins, labels=color_ranges[layer])
    elif layer == "Agriculture":
        gdf['value_column'] = pd.to_numeric(gdf['state_agricultural_land_Agricultural Land (in thousand hectares)'], errors='coerce')
        bins = [1, 2246, 6770, 12777, 20751, 25493]
        gdf['color'] = pd.cut(gdf['value_column'], bins=bins, labels=color_ranges[layer])
    elif layer == "Electricity":
        gdf['value_column'] = pd.to_numeric(gdf['state_electricity_consumption_2020_21_Electricity Consumption (GWh) 2020-21'], errors='coerce')
        bins = [53, 11225, 24108, 64888, 94592, 126423]
        gdf['color'] = pd.cut(gdf['value_column'], bins=bins, labels=color_ranges[layer])
    elif layer == "Population":
        gdf['value_column'] = pd.to_numeric(gdf['state_population_Population'], errors='coerce')
        bins = [64473, 10086292, 41974219, 72626809, 112374333, 199812341]
        gdf['color'] = pd.cut(gdf['value_column'], bins=bins, labels=color_ranges[layer])
    elif layer == "Water":
        gdf['value_column'] = pd.to_numeric(gdf['Safe_drinking_2011 Total'], errors='coerce')
        bins = [23, 34, 54, 70, 88, 99]
        gdf['color'] = pd.cut(gdf['value_column'], bins=bins, labels=color_ranges[layer])
    
    selected_gdfs.append(gdf)

# Combine all selected GeoDataFrames
if selected_gdfs:
    combined_gdf = gpd.GeoDataFrame(pd.concat(selected_gdfs, ignore_index=True))
    combined_gdf = combined_gdf.to_crs(epsg=4326)  # Convert to WGS84 for mapping
    
    # Map display using Pydeck
    layers = []
    for _, row in combined_gdf.iterrows():
        if pd.notnull(row['color']):  # Ensure color is defined
            layers.append(
                pdk.Layer(
                    "GeoJsonLayer",
                    data=row.geometry.__geo_interface__,
                    get_fill_color=list(row['color']),
                    get_line_color=[0, 0, 0, 100],
                )
            )
        
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v10',
        initial_view_state=pdk.ViewState(
            latitude=20.5937,
            longitude=78.9629,
            zoom=3,
            pitch=0,
        ),
        layers=layers,
    ))
else:
    st.write("Select layers from the sidebar to display them on the map.")
