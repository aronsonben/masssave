"""
MassSave + REJ Data Processing Script

PURPOSE:
This script processes MassSave energy efficiency program participation data from KML files
and combines it with Regional Environmental Justice (REJ) area data to analyze how program
participation overlaps with environmental justice areas in Massachusetts.

FUNCTION:
1. Reads KML files from the MassSave geotargeting tool (one per municipality)
2. Extracts block group-level participation data from embedded HTML tables in KML descriptions
3. Aggregates block group data up to census tract level (mean participation rates)
4. Performs an attribute join with REJ census tract GeoJSON data
5. Outputs combined dataset for web application visualization

INPUT FILES:
- data/masssave_kmls_unzipped/*.kml - Municipal KML files with block group participation data
- data/REJ_by_Census_Tracts_2025.geojson - REJ areas by census tract

OUTPUT FILES:
- data/masssave_block_groups.csv - Extracted block group data (intermediate output)
- data/rej_with_masssave_participation.geojson - Final combined dataset with REJ areas 
  and aggregated MassSave participation rates by census tract

KEY INSIGHT:
MassSave data is at block group level, REJ data is at census tract level. Block groups
are aggregated to match REJ granularity. Census tract GEOID is derived from the first
11 characters of the block group GEOID.

KML DATA STRUCTURE:
The data in the `data/masssave_kmls_unzipped/` directory is structured as follows:

```
Based on the Abington.kml file, here is a summary of its structure and content:

The KML file is a well-organized XML document that uses nested `<Folder>` elements to group different data layers. The core information is contained within `<Placemark>` elements, which represent specific geographic features.

1.  **Hierarchical Folders:** The data is organized into a hierarchy of folders, much like a table of contents. Key top-level folders include:
    *   Informational sections (`Read Me`, `Definitions`, etc.).
    *   `Overlays`: Contains basic geographic boundaries like the town boundary and zip codes.
    *   `Program Administrator Summary Data`: This is the main data folder, containing participation data for Electric, Gas, and Small Business programs.
    *   Socioeconomic Layers: Folders for `Income Eligible Households`, `Rental Households`, and `English Isolated Households`.

2.  **Geographic Features (`<Placemark>`)**: Each individual geographic shape, such as a census block group or a zip code area, is defined within a `<Placemark>` tag. The actual polygon coordinates are inside a `<MultiGeometry>` tag.

3.  **Data Storage (`<description>`)**: This is the most critical part. The statistical data for each placemark is **not** stored in simple key-value fields. Instead, it is embedded as an **HTML table** within a `CDATA` block inside the `<description>` tag.

4.  **Granularity**:
    *   Residential program data (Electric, Gas, Income, Rental, etc.) is provided at the **Census Block Group** level. Each block group has its own `<Placemark>`.
    *   Small Business data is provided at the **Zip Code** level.

5.  **Key Data Points**: The HTML tables within the descriptions contain valuable metrics, including:
    *   Block Group ID or Zip Code.
    *   Active electric and gas locations/accounts.
    *   Electric and gas location participation rates for different years (e.g., 2017, 2018, 2019).
    *   A cumulative `Unique ... location participation rate 2013 - 2019`.
    *   Socioeconomic data from the American Community Survey (ACS), such as the percentage of income-eligible, renter-occupied, or English-isolated households.
```
"""

import os
import pandas as pd
import geopandas as gpd
import fiona
from bs4 import BeautifulSoup
import re

KML_LAYERS = ['Town Boundary', 'Satellite Mask', 'Zip Code Label', 'Zip Code Boundaries', 'Block Group Boundaries', 'MA 2020 State EJC Layer', 'Electric Program Participation and Population Overview', 'Gas Program Participation and Population Overview', 'Small Business Participation and Population Overview', 'Income Eligible Households', 'Rental Households Layer', 'English Isolated Households']

def parse_html_description(html_content):
    """
    Parses the HTML table in the KML description to extract data.
    This function is designed to be robust to different table structures.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    data = {}
    
    # Find all table rows
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 2:
            key = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            data[key] = value
    return data

def process_masssave_kmls(kml_directory):
    """
    Iterates through KML files, parses them, and returns a clean DataFrame.
    """
    all_block_groups_data = []
    
    # Layers that contain block group participation data
    # These layers have the detailed participation statistics we need
    PARTICIPATION_LAYERS = [
        'Electric Program Participation and Population Overview',
        'Gas Program Participation and Population Overview',
        'Income Eligible Households',
        'Rental Households Layer',
        'English Isolated Households'
    ]

    for filename in os.listdir(kml_directory):
        if filename.endswith(".kml"):
            filepath = os.path.join(kml_directory, filename)
            print(f"\nProcessing {filename}...")
            
            try:
                # Iterate through each relevant layer in the KML file
                for layer_name in PARTICIPATION_LAYERS:
                    print(f"  Reading layer: {layer_name}...")
                    
                    try:
                        gdf = gpd.read_file(filepath, layer=layer_name)
                        
                        if gdf.empty:
                            print(f"    Warning: Layer '{layer_name}' contains no data.")
                            continue
                        
                        print(f"    Success: Layer '{layer_name}' contains {len(gdf)} features.")
                        
                        # The data we want is in the 'Description' column of placemarks
                        # that represent block groups. We can identify them by the GEOID format.
                        for index, row in gdf.iterrows():
                            if pd.notna(row.get('Description')) and 'Block Group ID (Text)' in row['Description']:
                                # Parse the HTML description
                                parsed_data = parse_html_description(row['Description'])
                                
                                # Extract the specific fields we need
                                geoid_raw = parsed_data.get('Block Group ID (Text)')
                                if not geoid_raw:
                                    continue

                                # Clean up GEOID: '15000US250235201001' -> '250235201001'
                                block_group_geoid = geoid_raw.replace('15000US', '')
                                
                                # Derive Census Tract GEOID (first 11 digits)
                                census_tract_geoid = block_group_geoid[:11]

                                # Safely convert participation rates to float
                                try:
                                    elec_rate = float(parsed_data.get('Unique electric location participation rate 2013 - 2019', 0))
                                except (ValueError, TypeError):
                                    elec_rate = 0.0
                                
                                try:
                                    gas_rate = float(parsed_data.get('Unique gas location participation rate 2013 - 2019', 0))
                                except (ValueError, TypeError):
                                    gas_rate = 0.0

                                all_block_groups_data.append({
                                    'block_group_geoid': block_group_geoid,
                                    'census_tract_geoid': census_tract_geoid,
                                    'town': parsed_data.get('Town'),
                                    'electric_participation_rate': elec_rate,
                                    'gas_participation_rate': gas_rate
                                })
                    
                    except Exception as layer_error:
                        print(f"    Error reading layer '{layer_name}': {layer_error}")

            except Exception as e:
                print(f"  Could not process {filename}. Error: {e}")

    return pd.DataFrame(all_block_groups_data)

def main():
    # --- Configuration ---
    # Directory containing the downloaded MassSave KML files
    KML_DIR = 'data/masssave_kmls_unzipped' 
    # Path to the REJ GeoJSON file
    REJ_GEOJSON_PATH = 'data/REJ_by_Census_Tracts_2025.geojson'
    # Path for the final output file
    OUTPUT_GEOJSON_PATH = 'data/rej_with_masssave_participation.geojson'

    # --- Step 1: Process KMLs and create a clean DataFrame ---
    masssave_df = process_masssave_kmls(KML_DIR)
    if masssave_df.empty:
        print("No MassSave data was processed. Exiting.")
        return
        
    print(f"\nSuccessfully extracted data for {len(masssave_df)} block groups.")
    print("MassSave DataFrame head:")
    print(masssave_df.head())

    # Save the DataFrame to CSV for review
    output_csv = 'data/masssave_block_groups.csv'
    masssave_df.to_csv(output_csv, index=False)
    print(f"\nSaved MassSave block group data to {output_csv}")

    
    # --- Step 2: Aggregate MassSave data to Census Tract level ---
    # We group by the tract ID and calculate the mean participation rate.
    # We also aggregate the town names into a comma-separated list.
    tract_agg_df = masssave_df.groupby('census_tract_geoid').agg(
        town=('town', lambda x: (', '.join(x.unique())).capitalize()),
        electric_participation_rate_avg=('electric_participation_rate', 'mean'),
        gas_participation_rate_avg=('gas_participation_rate', 'mean'),
        block_group_count=('block_group_geoid', 'count')
    ).reset_index()

    print(f"\nAggregated data into {len(tract_agg_df)} census tracts.")
    print("Aggregated DataFrame head:")
    print(tract_agg_df.head())

    # Save the Aggregated DataFrame to CSV for review
    output_csv2 = 'data/masssave_tract_groups.csv'
    tract_agg_df.to_csv(output_csv2, index=False)
    print(f"\nSaved MassSave tract group data to {output_csv2}")
    
    # --- Step 3: Load REJ GeoJSON and join with aggregated data ---
    print("\nLoading REJ Census Tract data...")
    rej_gdf = gpd.read_file(REJ_GEOJSON_PATH)
    
    # The GeoID in the REJ file is the key for merging
    print(f"REJ GeoDataFrame has {len(rej_gdf)} features.")
    print("Performing attribute join (merge)...")

    # Perform an inner merge to keep only REJ tracts that have MassSave data
    # final_gdf = rej_gdf.merge(
    #     tract_agg_df,
    #     left_on='GeoID',
    #     right_on='census_tract_geoid',
    #     how='inner'
    # )

    # Perform a left merge to keep all REJ tracts, even if they don't have MassSave data
    final_gdf = rej_gdf.merge(
        tract_agg_df, 
        left_on='GeoID', 
        right_on='census_tract_geoid', 
        how='left'
    )

    # We are having issues where perfectly fine GeoIDs in REJ are one digit off from perfectly fine GeoIDs in the tract_agg_df
    # So after we merge, let's look for the GeoIDs in the REJ set that don't exist in the new final_gdf
    # Use the mapping in the data/missing_tracts_mapping.txt file to fill in those missing GeoIDs
    ##### COPILOT HELP TO FIX MISSING IDS ######
    # # --- Step 3.5: Load and apply missing tracts mapping ---
    # print("\nApplying missing tracts mapping...")
    
    # # Load the mapping file
    # missing_tracts_mapping = {}
    # try:
    #     with open('data/missing_tracts_mapping.txt', 'r') as f:
    #         for line in f:
    #             line = line.strip()
    #             # Skip comments and empty lines
    #             if not line or line.startswith('#'):
    #                 continue
    #             # Parse format: "missing_geoid -> mapped_geoid"
    #             if ' -> ' in line:
    #                 missing_geoid, mapped_geoid = line.split(' -> ')
    #                 missing_tracts_mapping[missing_geoid.strip()] = mapped_geoid.strip()
        
    #     print(f"Loaded {len(missing_tracts_mapping)} mapping entries.")
    # except FileNotFoundError:
    #     print("Warning: missing_tracts_mapping.txt not found. Skipping missing tract mapping.")
    #     missing_tracts_mapping = {}
    
    # # For each row in final_gdf that is missing MassSave data, check the mapping
    # if missing_tracts_mapping:
    #     rows_with_missing_data = final_gdf[final_gdf['town'].isna()].index
    #     print(f"Found {len(rows_with_missing_data)} rows with missing MassSave data.")
        
    #     for idx in rows_with_missing_data:
    #         geoid = final_gdf.at[idx, 'GeoID']
            
    #         # Check if this GeoID has a mapping
    #         if str(geoid) in missing_tracts_mapping:
    #             mapped_geoid = missing_tracts_mapping[str(geoid)]
                
    #             # Look up the data for the mapped GeoID in tract_agg_df
    #             mapped_data = tract_agg_df[tract_agg_df['census_tract_geoid'] == mapped_geoid]
                
    #             if not mapped_data.empty:
    #                 # Use the first match (should only be one)
    #                 data_row = mapped_data.iloc[0]
                    
    #                 # Update the final_gdf row with the mapped data
    #                 final_gdf.at[idx, 'town'] = data_row['town']
    #                 final_gdf.at[idx, 'electric_participation_rate_avg'] = data_row['electric_participation_rate_avg']
    #                 final_gdf.at[idx, 'gas_participation_rate_avg'] = data_row['gas_participation_rate_avg']
    #                 final_gdf.at[idx, 'block_group_count'] = data_row['block_group_count']
        
    #     # Count how many we successfully filled
    #     filled_rows = final_gdf[~final_gdf['town'].isna()].index
    #     print(f"Successfully filled {len(filled_rows) - len(rows_with_missing_data)} additional rows with mapped data.")
    ##### COPILOT HELP TO FIX MISSING IDS ######

    # Clean up the extra geoid column from the merge
    final_gdf = final_gdf.drop(columns=['census_tract_geoid'], errors='ignore')

    # --- Step 4: Save the final combined data ---
    print(f"\nSaving final combined GeoDataFrame with {len(final_gdf)} features to {OUTPUT_GEOJSON_PATH}")
    final_gdf.to_file(OUTPUT_GEOJSON_PATH, driver='GeoJSON')
    
    print("\nProcessing complete.")
    print("Final data head:")
    print(final_gdf.head())


if __name__ == '__main__':
    main()