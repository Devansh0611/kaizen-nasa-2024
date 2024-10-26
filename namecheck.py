import geopandas as gpd

# Load the GeoPackage files
gdf_air = gpd.read_file("copieddata/states_india_Agri.gpkg")
gdf_agri = gpd.read_file("copieddata/states_india_Agri.gpkg")

# Display column names to identify the one containing the values
print("Air Quality GPKG columns:", gdf_air.columns)
print("Agriculture GPKG columns:", gdf_agri.columns)
