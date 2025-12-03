"""
Thinking of a way to find GeoIDs from the tract_groups output that are *close* but not exactly the same as GeoIDs in the original REJ data.

Example: Belchertown
- Original REJ GEOID Sample: 25015820207
- Confirmed via Live Online Map: 25015820207 (with tract id: 8,202.07)
- block_groups aggregate set: 25015820203 and 25015820204 

Updated Idea for Script - To be run one time and then store mappings:
- Comb through final set of map viz data in rej_with_masssave_participation.csv (eventually in geojson too but csv easier to test for now)
  - Get a list of all the geoids
- Now compare that list to the original REJ set
  - Get a list of all the geoids that exist in original REJ set but not in final set

- For each missing geoid, perform the "close_match" algo

closest_match( missing_geoid ):
  - Strip final digit from given missing_geoid
  - Get subset of geoids from final set that are in same metro region as missing_geoid is in original dataset
  - identify if missing_geoid starts with '2500', '2501', or '2502'
    - get subset of final set geoids based on that too
  - perform search
"""
import geopandas as gpd 
import difflib as dl
from collections import defaultdict

# Path to the REJ GeoJSON file
TRACT_GROUP_PATH = 'data/masssave_tract_groups.csv'
REJ_GEOJSON_PATH = 'data/REJ_by_Census_Tracts_2025.geojson'
REJ_AGGR_PATH = "data/rej_with_masssave_participation_table.csv"

def group_sequential_geoids(missing_geoids, rej_gdf):
  """
  Group missing GeoIDs that are sequential within the same geographic area.
  
  Args:
    missing_geoids: Set of missing GeoID strings
    rej_gdf: Original REJ GeoDataFrame to get MPO and other location info
  
  Returns:
    List of lists, where each inner list contains sequential GeoIDs
  """
  # Convert to list and sort for easier processing
  missing_list = sorted(list(missing_geoids))
  
  # Group by base pattern (removing last 2 digits) and MPO
  base_groups = defaultdict(list)
  
  for geoid in missing_list:
    # Get MPO for this GeoID
    mpo = rej_gdf.loc[rej_gdf['GeoID'] == geoid, 'MPO'].values[0]
    
    # Create base pattern (remove last 2 digits for grouping)
    base_pattern = geoid[:-2]
    
    # Use combination of base pattern and MPO as key
    key = (base_pattern, mpo)
    base_groups[key].append(geoid)
  
  # Now identify sequential groups within each base group
  sequential_groups = []
  
  for (base_pattern, mpo), geoids in base_groups.items():
    geoids.sort()  # Ensure they're in order
    
    # Split into sequential sub-groups
    current_group = [geoids[0]]
    
    for i in range(1, len(geoids)):
      # Check if current geoid is sequential to the previous one
      prev_suffix = int(geoids[i-1][-2:])  # Last 2 digits
      curr_suffix = int(geoids[i][-2:])    # Last 2 digits
      
      if curr_suffix == prev_suffix + 1:
        # Sequential - add to current group
        current_group.append(geoids[i])
      else:
        # Not sequential - start new group
        sequential_groups.append(current_group)
        current_group = [geoids[i]]
    
    # Don't forget the last group
    sequential_groups.append(current_group)
  
  return sequential_groups

def find_best_match(missing_geoid_group, representative_geoid, final_geoids, rej_gdf):
  """
  Find the best match for a group of missing GeoIDs using multi-strategy matching.
  Implements pattern-based matching based on identified Census tract boundary shifts.
  
  Args:
    missing_geoid_group: List of sequential missing GeoIDs
    representative_geoid: First GeoID in the group to use as representative
    final_geoids: Set of available GeoIDs in the final aggregated dataset
    rej_gdf: Original REJ GeoDataFrame
  
  Returns:
    Tuple of (best_candidate, confidence_score, match_strategy)
  """
  
  # Extract components
  county_code = representative_geoid[:5]      # e.g., '25017'
  tract_base = representative_geoid[5:-2]     # e.g., '3301' from '2501733301'
  last_two = representative_geoid[-2:]        # e.g., '05' 
  last_one = representative_geoid[-1]         # e.g., '5'
  
  # Get MPO for context
  mpo = rej_gdf.loc[rej_gdf['GeoID'] == representative_geoid, 'MPO'].values[0]
  
  # Filter candidates to same county and MPO for efficiency
  county_candidates = [g for g in final_geoids if g[:5] == county_code]
  
  best_candidates = []
  
  # Strategy 1: Exact base match with different last 2 digits
  # Pattern: REJ ...01, ...02, ...03, ...04 → MassSave ...00, ...01
  base_without_suffix = representative_geoid[:6]  # First 6 chars (county + first tract digit)
  strategy1_matches = [g for g in county_candidates 
                       if g[:6] == base_without_suffix and g[-2:] in ['00', '01', '02']]
  if strategy1_matches:
    best_candidates.extend([(g, 95, "strategy1_exact_base_match") for g in strategy1_matches])
  
  # Strategy 2: Last 3 digits transformation
  # Try progressively shorter suffix matches (full suffix, -1, -2 digits)
  for suffix_len in [4, 3, 2]:
    test_suffix = representative_geoid[5:5+suffix_len]
    strategy2_matches = [g for g in county_candidates 
                         if g[5:5+suffix_len] == test_suffix and g[-2:] in ['00', '01', '02']]
    if strategy2_matches:
      confidence = 90 - (suffix_len - 2) * 5  # Slightly lower confidence for shorter matches
      best_candidates.extend([(g, confidence, f"strategy2_suffix_match_{suffix_len}") for g in strategy2_matches])
      break
  
  # Strategy 3: Multiple REJ GeoIDs mapping to one MassSave GEOID
  # This handles consolidation cases where many variants map to a single base tract
  # Look for tracts with same base but ending in 00 or 01 (consolidation patterns)
  base_consolidation = representative_geoid[:7]  # e.g., '2501733'
  strategy3_matches = [g for g in county_candidates 
                       if g[:7] == base_consolidation and g[-2:] in ['00', '01']]
  if strategy3_matches:
    best_candidates.extend([(g, 85, "strategy3_consolidation_match") for g in strategy3_matches])
  
  # Strategy 4: Non-sequential mapping (last-resort, lower confidence)
  # Match on longer base with some digit flexibility
  base_partial = representative_geoid[:6]
  strategy4_matches = [g for g in county_candidates if g[:6] == base_partial]
  if strategy4_matches and not best_candidates:
    best_candidates.extend([(g, 70, "strategy4_base_match_only") for g in strategy4_matches])
  
  # Strategy 5: Fallback - any county match with similar structure
  if not best_candidates:
    # Look for candidates with base pattern similarity
    base_4digit = representative_geoid[5:9]
    strategy5_matches = [g for g in county_candidates if g[5:9] == base_4digit]
    if strategy5_matches:
      best_candidates.extend([(g, 60, "strategy5_partial_base_match") for g in strategy5_matches])
  
  # Return the single best match (highest confidence, fewest digits off)
  if best_candidates:
    # Sort by confidence descending, then by candidate GEOID for consistency
    best_candidates.sort(key=lambda x: (-x[1], x[0]))
    return best_candidates[0]
  
  return (None, 0, "no_match_found")

def main():
  # Get list of all geoids in final aggregated dataset
  rej_aggr_df = gpd.read_file(REJ_AGGR_PATH)
  final_geoids = set(rej_aggr_df['GeoID'].astype(str).values)

  # Get list of all geoids in original REJ dataset
  rej_gdf = gpd.read_file(REJ_GEOJSON_PATH)
  original_geoids = set(rej_gdf['GeoID'].astype(str).values)

  # Identify missing geoids
  missing_geoids = original_geoids - final_geoids
  print(f"Found {len(missing_geoids)} missing GeoIDs.\n")

  # Group missing GeoIDs by sequential patterns
  # This identifies sets of missing GeoIDs that are sequential (e.g., 25023506205, 25023506206)
  missing_geoid_groups = group_sequential_geoids(missing_geoids, rej_gdf)
  
  print(f"Grouped {len(missing_geoids)} missing GeoIDs into {len(missing_geoid_groups)} groups\n")

  # Multi-strategy matching ----------------------------------
  all_mappings = {}  # Dictionary to store geoid -> close_match mappings
  strategy_counts = defaultdict(int)  # Track which strategies are most effective
  
  # Process each group of missing geoids
  for group_idx, missing_geoid_group in enumerate(missing_geoid_groups):
    # Use the first geoid in the group as representative for finding matches
    representative_geoid = missing_geoid_group[0]
    
    # Get 'MPO' value from original REJ data for representative geoid
    missing_geoid_mpo = rej_gdf.loc[rej_gdf['GeoID'] == representative_geoid, 'MPO'].values[0]

    print(f"--- Processing Group {group_idx + 1}: {missing_geoid_group} ---")
    print(f"    Representative: {representative_geoid} | MPO: {missing_geoid_mpo}")

    # Use the new multi-strategy matching function
    best_match, confidence, strategy = find_best_match(
        missing_geoid_group, 
        representative_geoid, 
        final_geoids, 
        rej_gdf
    )
    
    if best_match:
      print(f"    ✓ MATCH FOUND: {best_match} (confidence: {confidence}%, strategy: {strategy})")
      strategy_counts[strategy] += 1
      
      # Map all GeoIDs in this group to the best match
      # This handles consolidation: multiple REJ tracts → one MassSave tract
      for geoid in missing_geoid_group:
        all_mappings[geoid] = best_match
    else:
      print(f"    ✗ NO MATCH FOUND for group {missing_geoid_group}")
      for geoid in missing_geoid_group:
        all_mappings[geoid] = None
    print()
      
  # Save mappings to file for future use
  with open('data/missing_tracts_mapping.txt', 'w') as f:
      f.write("# Mapping of missing REJ GeoIDs to closest MassSave GeoIDs\n")
      f.write("# Format: missing_geoid -> closest_match_geoid\n")
      f.write("# Generated by find_geoids.py using multi-strategy pattern matching\n\n")
      for missing_geoid, match in sorted(all_mappings.items()):
          f.write(f"{missing_geoid} -> {match}\n")
  
  # Summary statistics
  successful_mappings = len([m for m in all_mappings.values() if m is not None])
  print(f"\n{'='*70}")
  print(f"SUMMARY STATISTICS")
  print(f"{'='*70}")
  print(f"Total missing GeoIDs: {len(all_mappings)}")
  print(f"Successfully mapped: {successful_mappings} ({100*successful_mappings/len(all_mappings):.1f}%)")
  print(f"Failed to map: {len(all_mappings) - successful_mappings}")
  print(f"\nStrategy Effectiveness:")
  for strategy, count in sorted(strategy_counts.items(), key=lambda x: -x[1]):
    print(f"  {strategy}: {count} mappings")
  print(f"\nMappings saved to: data/missing_tracts_mapping.txt")
  print(f"{'='*70}\n")

  return all_mappings

if __name__ == '__main__':
  main()