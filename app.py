import streamlit as st
import geopandas as gpd
import pydeck as pdk
import pandas as pd

# Load the GeoPackage files
gpkg_files = {
    "Air": "copieddata/states_india_Agri.gpkg",
    "Agriculture": "copieddata/states_india_Agri.gpkg",
    # Add other files here
}

# Sidebar for selecting layers
st.sidebar.title("Select Layers to Display")
selected_layers = st.sidebar.multiselect("Choose layers:", gpkg_files.keys())

# Initialize an empty list to hold selected GeoDataFrames
selected_gdfs = []

# Load selected GeoDataFrames
for layer in selected_layers:
    gdf = gpd.read_file(gpkg_files[layer])
    selected_gdfs.append(gdf)

# Combine all selected GeoDataFrames
if selected_gdfs:
    combined_gdf = gpd.GeoDataFrame(pd.concat(selected_gdfs, ignore_index=True))
    combined_gdf = combined_gdf.to_crs(epsg=4326)  # Convert to WGS84 for mapping
    
    # Map display using Pydeck
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v10',
        initial_view_state=pdk.ViewState(
            latitude=20.5937,
            longitude=78.9629,
            zoom=4,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "GeoJsonLayer",
                data=combined_gdf,
                get_fill_color="[255, 0, 0, 150]",
                get_line_color="[0, 0, 0, 150]",
            )
        ],
    ))
else:
    st.write("Select layers from the sidebar to display them on the map.")
