"""
Error in processing:
- Mount Washington.kml
- Worthington.kml

Missing from Block & Tract Group Output:
- Charlemont
- Monroe
- Worthington

Total count of final tract group towns: 348

Regex for getting town names from list: ([a-z]*(\s?[a-z]*)?)
"""
import geopandas as gpd 

# Path to the REJ GeoJSON file
TRACT_GROUP_PATH = 'data/masssave_tract_groups.csv'
REJ_GEOJSON_PATH = 'data/REJ_by_Census_Tracts_2025.geojson'
REJ_AGGR_PATH = "data/rej_with_masssave_participation_table.csv"

def main():
  # Declare town lists pulled from various CSV files
  missing_towns = [
    "Ayer",
    "Belchertown",
    "Bellingham",
    "Blandford",
    "Charlemont",
    "Chester",
    "Chesterfield",
    "Cohasset",
    "Douglas",
    "Goshen",
    "Granville",
    "Great Barrington",
    "Harvard",
    "Lincoln",
    "Middleton",
    "Millis",
    "Monroe",
    "Montgomery",
    "North Reading",
    "Plainville",
    "Royalston",
    "Rutland",
    "Templeton",
    "Tolland",
    "Williamsburg",
    "Worthington"
  ]
  block_group_towns = [
    'UXBRIDGE',
    'MILLBURY',
    'WALES',
    'CONWAY',
    'NORWELL',
    'MILLIS',
    'GOSNOLD',
    'HAVERHILL',
    'WESTON',
    'ERVING',
    'SALEM',
    'WEST BROOKFIELD',
    'RUSSELL',
    'SHUTESBURY',
    'SHEFFIELD',
    'MELROSE',
    'SAVOY',
    'WATERTOWN',
    'NORFOLK',
    'HOPKINTON',
    'BLACKSTONE',
    'LUDLOW',
    'FITCHBURG',
    'PROVINCETOWN',
    'TEWKSBURY',
    'COLRAIN',
    'BLANDFORD',
    'HOLBROOK',
    'HUDSON',
    'SALISBURY',
    'NAHANT',
    'RAYNHAM',
    'PELHAM',
    'NORTH ADAMS',
    'BREWSTER',
    'MEDFORD',
    'DUDLEY',
    'BERKLEY',
    'LONGMEADOW',
    'CANTON',
    'FLORIDA',
    'WESTFIELD',
    'MANCHESTER',
    'BOXBOROUGH',
    'BELCHERTOWN',
    'HOLYOKE',
    'STERLING',
    'PRINCETON',
    'ABINGTON',
    'CHELMSFORD',
    'WHATELY',
    'ROCKPORT',
    'HULL',
    'MONSON',
    'MALDEN',
    'WILMINGTON',
    'READING',
    'BERNARDSTON',
    'OAKHAM',
    'AGAWAM',
    'PLAINFIELD',
    'ROCHESTER',
    'MANSFIELD',
    'NORTHAMPTON',
    'GRANVILLE',
    'STOUGHTON',
    'ESSEX',
    'HOLLISTON',
    'WARREN',
    'MONTEREY',
    'WALPOLE',
    'ROCKLAND',
    'NEWTON',
    'EVERETT',
    'LINCOLN',
    'ASHLAND',
    'PETERSHAM',
    'KINGSTON',
    'HATFIELD',
    'NEEDHAM',
    'WEST BOYLSTON',
    'SUDBURY',
    'SPRINGFIELD',
    'MARBLEHEAD',
    'WEST SPRINGFIELD',
    'EAST LONGMEADOW',
    'HUBBARDSTON',
    'RICHMOND',
    'MERRIMAC',
    'FRANKLIN',
    'TEMPLETON',
    'COHASSET',
    'CHICOPEE',
    'BILLERICA',
    'WEYMOUTH',
    'PERU',
    'BEVERLY',
    'BRIMFIELD',
    'SANDWICH',
    'CHILMARK',
    'WENHAM',
    'LAWRENCE',
    'HANOVER',
    'UPTON',
    'IPSWICH',
    'MILFORD',
    'GARDNER',
    'WAREHAM',
    'CLARKSBURG',
    'FALL RIVER',
    'SOUTHBOROUGH',
    'WEST TISBURY',
    'PLAINVILLE',
    'LEVERETT',
    'SOMERSET',
    'ALFORD',
    'AUBURN',
    'DALTON',
    'GEORGETOWN',
    'DEDHAM',
    'HUNTINGTON',
    'CHELSEA',
    'PEABODY',
    'NATICK',
    'WINCHESTER',
    'MIDDLETON',
    'BUCKLAND',
    'ROWE',
    'CHARLTON',
    'ASHFIELD',
    'AYER',
    'MEDFIELD',
    'HADLEY',
    'WILBRAHAM',
    'WELLFLEET',
    'EDGARTOWN',
    'GREAT BARRINGTON',
    'REHOBOTH',
    'GRAFTON',
    'WESTHAMPTON',
    'LENOX',
    'MASHPEE',
    'FREETOWN',
    'NORTH ATTLEBORO',
    'SPENCER',
    'RUTLAND',
    'NEW ASHFORD',
    'LUNENBURG',
    'SOUTHAMPTON',
    'DENNIS',
    'LYNN',
    'WEST NEWBURY',
    'ASHBURNHAM',
    'PAXTON',
    'ORANGE',
    'CONCORD',
    'BOSTON',
    'CHESTERFIELD',
    'EGREMONT',
    'WAKEFIELD',
    'WOBURN',
    'MAYNARD',
    'TAUNTON',
    'AQUINNAH',
    'AVON',
    'BOYLSTON',
    'WEBSTER',
    'WAYLAND',
    'BURLINGTON',
    'ATHOL',
    'SWAMPSCOTT',
    'LEE',
    'YARMOUTH',
    'ANDOVER',
    'SWANSEA',
    'WEST STOCKBRIDGE',
    'TOLLAND',
    'CARLISLE',
    'WESTMINSTER',
    'STOCKBRIDGE',
    'MONTGOMERY',
    'WINDSOR',
    'SHARON',
    'NEW SALEM',
    'PHILLIPSTON',
    'HANSON',
    'LEYDEN',
    'HOLDEN',
    'ATTLEBORO',
    'EASTON',
    'LANESBOROUGH',
    'HINSDALE',
    'ADAMS',
    'NORTH ANDOVER',
    'NORTON',
    'ASHBY',
    'BRAINTREE',
    'CLINTON',
    'DANVERS',
    'SHELBURNE',
    'BOXFORD',
    'SOUTH HADLEY',
    'GOSHEN',
    'LAKEVILLE',
    'NORTHBOROUGH',
    'BEDFORD',
    'STONEHAM',
    'HAWLEY',
    'WEST BRIDGEWATER',
    'AMHERST',
    'SHREWSBURY',
    'OAK BLUFFS',
    'DEERFIELD',
    'BRIDGEWATER',
    'DARTMOUTH',
    'SOMERVILLE',
    'NORTHBRIDGE',
    'BELLINGHAM',
    'HAMPDEN',
    'DRACUT',
    'WILLIAMSTOWN',
    'WENDELL',
    'ROYALSTON',
    'WESTBOROUGH',
    'LEICESTER',
    'MARION',
    'ARLINGTON',
    'NEWBURY',
    'MENDON',
    'MATTAPOISETT',
    'WINTHROP',
    'GROVELAND',
    'METHUEN',
    'PLYMPTON',
    'TRURO',
    'HARDWICK',
    'GLOUCESTER',
    'WILLIAMSBURG',
    'WORCESTER',
    'LEOMINSTER',
    'DUXBURY',
    'TOPSFIELD',
    'BARRE',
    'BROCKTON',
    'REVERE',
    'BOLTON',
    'RANDOLPH',
    'PITTSFIELD',
    'FRAMINGHAM',
    'WELLESLEY',
    'BARNSTABLE',
    'BERLIN',
    'LANCASTER',
    'MARSHFIELD',
    'WARWICK',
    'CHESHIRE',
    'BROOKLINE',
    'EASTHAMPTON',
    'MARLBOROUGH',
    'ACUSHNET',
    'HINGHAM',
    'NEWBURYPORT',
    'GRANBY',
    'NEW MARLBOROUGH',
    'CUMMINGTON',
    'MIDDLEFIELD',
    'SANDISFIELD',
    'TISBURY',
    'NANTUCKET',
    'TYRINGHAM',
    'HALIFAX',
    'SAUGUS',
    'OXFORD',
    'ACTON',
    'WESTWOOD',
    'WINCHENDON',
    'TYNGSBOROUGH',
    'HOLLAND',
    'WESTFORD',
    'DOVER',
    'LEXINGTON',
    'WASHINGTON',
    'HOPEDALE',
    'STURBRIDGE',
    'TOWNSEND',
    'NEW BRAINTREE',
    'HARWICH',
    'BECKET',
    'SUNDERLAND',
    'MONTAGUE',
    'PEPPERELL',
    'WALTHAM',
    'LYNNFIELD',
    'SHERBORN',
    'MILTON',
    'PEMBROKE',
    'NORTH READING',
    'MOUNT WASHINGTON',
    'STOW',
    'DUNSTABLE',
    'WESTPORT',
    'CHESTER',
    'FOXBOROUGH',
    'SEEKONK',
    'GREENFIELD',
    'ORLEANS',
    'FAIRHAVEN',
    'EAST BROOKFIELD',
    'SOUTHBRIDGE',
    'MILLVILLE',
    'NEW BEDFORD',
    'HAMILTON',
    'OTIS',
    'MEDWAY',
    'WRENTHAM',
    'SHIRLEY',
    'NORTH BROOKFIELD',
    'NORWOOD',
    'HEATH',
    'PALMER',
    'FALMOUTH',
    'SCITUATE',
    'HANCOCK',
    'QUINCY',
    'DIGHTON',
    'SUTTON',
    'CAMBRIDGE',
    'EAST BRIDGEWATER',
    'NORTHFIELD',
    'EASTHAM',
    'WHITMAN',
    'WARE',
    'DOUGLAS',
    'MIDDLEBOROUGH',
    'AMESBURY',
    'ROWLEY',
    'PLYMOUTH',
    'SOUTHWICK',
    'LOWELL',
    'HARVARD',
    'BROOKFIELD',
    'BOURNE',
    'CARVER',
    'GROTON',
    'CHATHAM',
    'GILL',
    'BELMONT',
    'LITTLETON'
  ]
  tract_group_multitowns = ["Savoy, florida",
    "Peru, windsor",
    "Washington, becket",
    "Monterey, tyringham",
    "Sandisfield, otis",
    "Alford, egremont, mount washington",
    "Richmond, new ashford, hancock",
    "Gosnold, chilmark, west tisbury, aquinnah",
    "Colrain, rowe, hawley, heath",
    "Bernardston, leyden, gill",
    "Erving, wendell, warwick",
    "Shutesbury, leverett, new salem",
    "Whately, sunderland",
    "Conway, ashfield",
    "Buckland, shelburne",
    "Russell, blandford, granville, tolland, montgomery, chester",
    "Wales, holland",
    "Goshen, williamsburg",
    "Plainfield, cummington, middlefield",
    "Petersham, phillipston",
    "Hardwick, new braintree"
  ]
  tract_group_towns = ["Provincetown","Wellfleet","Truro","Eastham","Orleans","Chatham","Brewster","Harwich","Dennis","Yarmouth","Barnstable","Sandwich","Bourne","Falmouth","Mashpee","Pittsfield","Lanesborough","Dalton","Lenox","Lee","Williamstown","North adams","Adams","Cheshire","Stockbridge","Great barrington","Sheffield","Clarksburg","Hinsdale","New marlborough","West stockbridge","Easton","Mansfield","Norton","Raynham","Taunton","Dighton","Berkley","Freetown","North attleboro","Attleboro","Seekonk","Rehoboth","Fall river","Somerset","Swansea","Westport","New bedford","Dartmouth","Acushnet","Fairhaven","Tisbury","Oak bluffs","Edgartown","Nahant","Swampscott","Marblehead","Salem","Lynn","Saugus","Lynnfield","Peabody","Danvers","Middleton","Boxford","Topsfield","Hamilton","Wenham","Beverly","Manchester","Rockport","Gloucester","Essex","Ipswich","Lawrence","Methuen","North andover","Andover","Haverhill","Merrimac","West newbury","Groveland","Georgetown","Amesbury","Salisbury","Newburyport","Newbury","Rowley","Northfield","Orange","Montague","Deerfield","Greenfield","Springfield","Palmer","Ludlow","Chicopee","Holyoke","West springfield","Westfield","Southwick","Agawam","Longmeadow","East longmeadow","Hampden","Wilbraham","Monson","Brimfield","Ware","Pelham","Belchertown","Amherst","Granby","South hadley","Hadley","Hatfield","Northampton","Easthampton","Southampton","Huntington","Westhampton","Chesterfield","Ashby","Townsend","Lowell","Tyngsborough","Dracut","Tewksbury","Billerica","Chelmsford","Westford","Hopkinton","Marlborough","Hudson","Stow","Littleton","Ayer","Groton","Pepperell","Dunstable","North reading","Wilmington","Burlington","Woburn","Reading","Wakefield","Melrose","Stoneham","Winchester","Medford","Malden","Everett","Somerville","Cambridge","Arlington","Belmont","Lexington","Bedford","Lincoln","Concord","Carlisle","Acton","Maynard","Sudbury","Wayland","Weston","Waltham","Watertown","Newton","Natick","Framingham","Ashland","Sherborn","Holliston","Boxborough","Shirley","Nantucket","Brookline","Dedham","Needham","Wellesley","Dover","Medfield","Millis","Medway","Norfolk","Foxborough","Walpole","Westwood","Norwood","Sharon","Canton","Milton","Quincy","Braintree","Randolph","Holbrook","Weymouth","Cohasset","Plainville","Wrentham","Franklin","Bellingham","Stoughton","Avon","Hull","Hingham","Rockland","Hanover","Norwell","Scituate","Marshfield","Duxbury","Pembroke","Kingston","Brockton","Abington","Whitman","Hanson","East bridgewater","West bridgewater","Bridgewater","Halifax","Plymouth","Lakeville","Rochester","Middleborough","Plympton","Carver","Wareham","Mattapoisett","Marion","Boston","Chelsea","Revere","Winthrop","Ashburnham","Winchendon","Royalston","Athol","Templeton","Hubbardston","Gardner","Westminster","Leominster","Fitchburg","Lunenburg","Lancaster","Bolton","Clinton","Berlin","Boylston","Sterling","Princeton","Oakham","Rutland","Barre","West brookfield","North brookfield","Spencer","Paxton","Holden","West boylston","Worcester","Leicester","Auburn","Millbury","Grafton","Shrewsbury","Northborough","Southborough","Westborough","Upton","Milford","Hopedale","Mendon","Blackstone","Millville","Uxbridge","Northbridge","Sutton","Douglas","Oxford","Webster","Dudley","Charlton","Southbridge","Sturbridge","East brookfield","Brookfield","Warren","Harvard"]

  # Track the missing towns
  truly_missing_block = []
  truly_missing_tract = []

  # Add multitown towns to tract_group_towns
  for multitown in tract_group_multitowns:
    split_towns = list(map(str.lower, multitown.split(", ")))
    # print(split_towns)
    for st in split_towns:
      if st not in map(str.lower, tract_group_towns):
        # print(f"Adding {st.capitalize()} to tract group towns")
        tract_group_towns.append(st.capitalize())

  # Search for missing towns in block & tract group lists
  for missing in missing_towns:
    # Search in block list
    if missing.lower() in map(str.lower, block_group_towns):
      print(f"[Block] Found {missing}.")
    else:
      truly_missing_block.append(missing)
    # Search in tract list
    if missing.lower() not in map(str.lower, tract_group_towns):
      truly_missing_tract.append(missing)
    else:
      print(f"[Tract] Found {missing}.")

  # Print some info  
  print(f"The BLOCK GROUP list is missing these towns:\n{truly_missing_block}")
  print(f"The TRACT GROUP list is missing these towns:\n{truly_missing_tract}")
  print(f"Total count of tract group towns is: {len(tract_group_towns)}")

  # ----------------------------------------
  # Now try to see whether the REJ has each town in the tract_group_towns array
  rej_csv_df = gpd.read_file(REJ_AGGR_PATH)
  rej_df = gpd.read_file(REJ_GEOJSON_PATH)

  # Drop the geometry column from orig REJ data for easier processing
  rej_df = rej_df.drop(columns='geometry')

  # Get all unique towns in the REJ aggregate file
  rej_towns = rej_csv_df['town'].unique().tolist()

  # Identify which towns from tract_group_towns are missing in the REJ towns
  missing_in_rej = []
  for town in tract_group_towns:
    if town.upper() not in map(str.upper, rej_towns):
      missing_in_rej.append(town)

  print(f"The REJ list is missing these towns:\n{missing_in_rej}\n{len(missing_in_rej)} Total")


  # ------------------------
  # Since the original REJ file (REJ_by_Census_Tracts_2025.geojson) doesn't have town names
  # we're going to instead use GEOIDs from data/masssave_tract_groups.csv to check:
  # - Which Census Tract GEOIDs exist in the original REJ geojson file that DO NOT exist
  #   in the masssave_tract_groups.csv file 
  #   (which is pulled directly from KML files after aggregating census blocks)
  # ------------------------

  # First, get all GEOIDs from masssave_tract_groups.csv
  masssave_tracts_df = gpd.read_file(TRACT_GROUP_PATH)
  masssave_geoids = masssave_tracts_df['census_tract_geoid'].unique().tolist()

  # Get all unique GEOIDs in the REJ geojson file
  rej_geoids = rej_df['GeoID'].unique().tolist()

  # Now identify which GEOIDs from masssave_tracts are missing in the REJ geojson GEOIDs
  missing_geoids = []
  for geoid in masssave_geoids:
    if geoid not in rej_geoids:
      missing_geoids.append(geoid)

  print(f"The REJ geojson file is missing these GEOIDs:\n{missing_geoids}")

  # Now to get actually helpful insight, map the missing GEOIDs to towns

if __name__ == '__main__':
  main()