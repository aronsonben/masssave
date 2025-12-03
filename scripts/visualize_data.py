import geopandas as gpd
import pandas as pd
import folium

# File path for the GeoJSON data
geojson_path = 'data/rej_with_masssave_participation.geojson'

# Output HTML file name to the data directory
output_map_path = 'data/masssave_participation_map.html'

# Load the GeoJSON data into a GeoDataFrame
try:
    gdf = gpd.read_file(geojson_path)
except Exception as e:
    print(f"Error reading GeoJSON file: {e}")
    exit()

# Ensure numeric types and handle potential missing values
gdf['electric_participation_rate_avg'] = pd.to_numeric(gdf['electric_participation_rate_avg'], errors='coerce').fillna(0)
gdf['gas_participation_rate_avg'] = pd.to_numeric(gdf['gas_participation_rate_avg'], errors='coerce').fillna(0)
# The 'REJ__flag_' is read as a string, which is what we need for filtering.

# Create a base map centered on Massachusetts
m = folium.Map(location=[42.4072, -71.3824], zoom_start=8)

# --- Create Choropleth Layer for Participation Rate ---
# This layer will color all tracts by ELECTRIC participation rate
folium.Choropleth(
    geo_data=gdf,
    name='Electric Participation Rate',
    data=gdf,
    columns=['GeoID', 'electric_participation_rate_avg'],
    key_on='feature.properties.GeoID',
    fill_color='YlGn',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Avg. Electric Participation Rate (%)',
    show=True # This layer is visible by default
).add_to(m)

# This layer will color all tracts by GAS participation rate
folium.Choropleth(
    geo_data=gdf,
    name='Gas Participation Rate',
    data=gdf,
    columns=['GeoID', 'gas_participation_rate_avg'],
    key_on='feature.properties.GeoID',
    fill_color='PuBu',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Avg. Gas Participation Rate (%)',
    show=False # This layer is not visible by default
).add_to(m)

# --- Create layers for toggling MassSave participation rate bins ---

# Layer for Very High Electric Participation (>36%)
very_high_elec_gdf = gdf[gdf['electric_participation_rate_avg'] > 36].copy()
if not very_high_elec_gdf.empty:
    very_high_elec_layer = folium.FeatureGroup(name='Very High Electric Participation (>36%)', show=False)
    very_high_elec_style = {'color': 'darkgreen', 'weight': 2, 'fillOpacity': 0.2, 'fillColor': 'darkgreen'}
    folium.GeoJson(
        very_high_elec_gdf,
        style_function=lambda x: very_high_elec_style
    ).add_to(very_high_elec_layer)
    very_high_elec_layer.add_to(m)

# TODO: Implement the remaining bins once I've processed all of the KML data files for the state.
#       so that I know what the max value is for each MassSave participation rate.

# ...todo here...



# --- Create a separate layer for REJ areas ---

# Filter the GeoDataFrame to get only the REJ tracts
rej_gdf = gdf[gdf['REJ__flag_'] == 'Yes'].copy()

if not rej_gdf.empty:
    # Create a FeatureGroup for REJ areas. This makes it a toggleable layer.
    rej_layer = folium.FeatureGroup(name='REJ Area Boundaries', show=True)

    # Style for the REJ boundaries to make them stand out
    rej_style = {
        'color': 'purple',
        'weight': 2,
        'fillOpacity': 0, # Transparent fill to see choropleth underneath
    }

    # Add the REJ geometries to the FeatureGroup
    folium.GeoJson(
        rej_gdf,
        style_function=lambda x: rej_style
    ).add_to(rej_layer)
    
    # Add the REJ layer to the map
    rej_layer.add_to(m)
else:
    print("Warning: No REJ areas found in the dataset to create a separate layer.")

# --- Create layers for other REJ-related flags ---

# Layer for Zero-Vehicle Households (ZVHH_flag)
zvhh_gdf = gdf[gdf['ZVHH_flag'] == 1].copy()
if not zvhh_gdf.empty:
    zvhh_layer = folium.FeatureGroup(name='Zero-Vehicle Households', show=False)
    zvhh_style = {'color': 'red', 'weight': 2, 'fillOpacity': 0.2, 'fillColor': 'red'}
    folium.GeoJson(
        zvhh_gdf,
        style_function=lambda x: zvhh_style
    ).add_to(zvhh_layer)
    zvhh_layer.add_to(m)

# Layer for Senior Population (Senior_fla)
senior_gdf = gdf[gdf['Senior_fla'] == 1].copy()
if not senior_gdf.empty:
    senior_layer = folium.FeatureGroup(name='High Senior Population', show=False)
    senior_style = {'color': 'orange', 'weight': 2, 'fillOpacity': 0.2, 'fillColor': 'orange'}
    folium.GeoJson(
        senior_gdf,
        style_function=lambda x: senior_style
    ).add_to(senior_layer)
    senior_layer.add_to(m)

# Layer for Disability Flag (Disabili_f)
disability_gdf = gdf[gdf['Disabili_f'] == 1].copy()
if not disability_gdf.empty:
    disability_layer = folium.FeatureGroup(name='Disability Flag', show=False)
    disability_style = {'color': 'blue', 'weight': 2, 'fillOpacity': 0.2, 'fillColor': 'blue'}
    folium.GeoJson(
        disability_gdf,
        style_function=lambda x: disability_style
    ).add_to(disability_layer)
    disability_layer.add_to(m)

# Layer for Percent Non-White (pct_nonwhi)
nonwhite_gdf = gdf[gdf['pct_nonwhi'] == 1].copy()
if not nonwhite_gdf.empty:
    nonwhite_layer = folium.FeatureGroup(name='Percent Non-White Flag', show=False)
    nonwhite_style = {'color': 'brown', 'weight': 2, 'fillOpacity': 0.2, 'fillColor': 'brown'}
    folium.GeoJson(
        nonwhite_gdf,
        style_function=lambda x: nonwhite_style
    ).add_to(nonwhite_layer)
    nonwhite_layer.add_to(m)

# Layer for Limited English Proficiency (pct_lep_fl)
lep_gdf = gdf[gdf['pct_lep_fl'] == 1].copy()
if not lep_gdf.empty:
    lep_layer = folium.FeatureGroup(name='Limited English Proficiency Flag', show=False)
    lep_style = {'color': 'purple', 'weight': 2, 'fillOpacity': 0.2, 'fillColor': 'purple'}
    folium.GeoJson(
        lep_gdf,
        style_function=lambda x: lep_style
    ).add_to(lep_layer)
    lep_layer.add_to(m)

# Layer for Median Income (median_inc)
income_gdf = gdf[gdf['median_inc'] == 1].copy()
if not income_gdf.empty:
    income_layer = folium.FeatureGroup(name='Median Income Flag', show=False)
    income_style = {'color': 'black', 'weight': 2, 'fillOpacity': 0.2, 'fillColor': 'black'}
    folium.GeoJson(
        income_gdf,
        style_function=lambda x: income_style
    ).add_to(income_layer)
    income_layer.add_to(m)


# --- Add Tooltips for all areas ---
# This invisible layer provides tooltips for all tracts when you hover over them
tooltip_layer = folium.features.GeoJson(
    gdf,
    style_function=lambda x: {'fillColor': 'transparent', 'color': 'transparent'},
    control=False,
    tooltip=folium.features.GeoJsonTooltip(
        fields=['GeoID', 'MPO', 'town', 'POPULATION', 'POP20_SQMI', 'REJ__flag_', 'ZVHH_flag', 'Senior_fla', 'Disabili_f', 'pct_nonwhi', 'pct_lep_fl', 'median_inc', 'electric_participation_rate_avg', 'gas_participation_rate_avg', 'block_group_count'],
        aliases=['Census Tract ID:', 'MPO:', 'Town:', 'Population:', 'Population Density:', 'REJ Area:', 'Zero-Vehicle HH:', 'High Senior Pop:', 'Disability Flag:', 'Percent Non-White:', 'Limited English Proficiency:', 'Median Income:', 'Avg. Electric Participation (%):', 'Avg. Gas Participation (%):', 'Block Groups Processed:'],
        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
    )
)
m.add_child(tooltip_layer)
m.keep_in_front(tooltip_layer)

# --- Finalize Map ---
# Add a layer control panel to the map to toggle layers
folium.LayerControl().add_to(m)

# Save the map to an HTML file
m.save(output_map_path)

print(f"Map has been generated and saved to '{output_map_path}'")
print("You can now toggle 'REJ Area Boundaries' in the layer control on the map.")