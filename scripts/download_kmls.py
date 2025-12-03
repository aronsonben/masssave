import requests
from bs4 import BeautifulSoup
import os
import time
import zipfile
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://www.masssavedata.com/Public/GoogleEarth/"
OUTPUT_DIR = "data/masssave_kmls"
UNZIPPED_DIR = "data/masssave_kmls_unzipped"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UNZIPPED_DIR, exist_ok=True)

# Use a session to persist cookies
session = requests.Session()

# Fetch the main page to get form data and municipality list
print("Fetching list of municipalities and form data...")
try:
    response = session.get(BASE_URL)
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"Failed to fetch the main page. Error: {e}")
    exit()

soup = BeautifulSoup(response.text, 'html.parser')

# Extract hidden form inputs required for POST requests
viewstate = soup.find('input', {'name': '__VIEWSTATE'}).get('value')
viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'}).get('value')
eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'}).get('value')

# Extract municipality names from the dropdown
municipality_select = soup.find('select', {'id': 'MasterContent_ddlKMZFiles'})
if not municipality_select:
    print("Could not find the municipality dropdown. The page structure may have changed.")
    exit()

municipalities = [option.get('value') for option in municipality_select.find_all('option') if option.get('value')]

print(f"Found {len(municipalities)} municipalities.")

# Download KMZ for each municipality
for i, municipality in enumerate(municipalities):
    filename = f"{municipality}.kmz"
    output_path = os.path.join(OUTPUT_DIR, filename)

    if not os.path.exists(output_path):
        print(f"Downloading KMZ for {municipality}...")

        # Form data for the POST request
        form_data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': viewstategenerator,
            '__EVENTVALIDATION': eventvalidation,
            'ctl00$MasterContent$ddlKMZFiles': municipality,
            'ctl00$MasterContent$btnDownload': 'Download',
            'ctl00$MasterContent$hdnPublic': '1'
        }

        try:
            file_response = session.post(BASE_URL, data=form_data)
            file_response.raise_for_status()

            # Check if the response is HTML, which indicates an error
            if 'text/html' in file_response.headers.get('Content-Type', ''):
                 print(f"  -> Failed to download for {municipality}. The server returned an HTML page instead of a file. The form data might be stale.")
                 # Optionally, re-fetch the page to get new form data and retry
                 continue

            with open(output_path, 'wb') as f:
                f.write(file_response.content)
            print(f"  -> Saved to {output_path}")
            time.sleep(0.5) # Be polite to the server

        except requests.exceptions.RequestException as e:
            print(f"  -> Could not download for {municipality}. Error: {e}")
            continue
    else:
        print(f"Skipping download for {municipality}, file already exists.")

    # Unzip the KMZ file
    try:
        with zipfile.ZipFile(output_path, 'r') as kmz:
            # Find the KML file inside the KMZ archive
            kml_files = [name for name in kmz.namelist() if name.endswith('.kml')]
            if kml_files:
                kml_filename = kml_files[0]
                kml_output_path = os.path.join(UNZIPPED_DIR, f"{municipality}.kml")
                if not os.path.exists(kml_output_path):
                    kmz.extract(kml_filename, path=UNZIPPED_DIR)
                    # Rename the extracted file to match the municipality
                    os.rename(os.path.join(UNZIPPED_DIR, kml_filename), kml_output_path)
                    print(f"  -> Extracted KML to {kml_output_path}")
                else:
                    print(f"  -> Skipping extraction for {municipality}, KML already exists.")
    except zipfile.BadZipFile:
        print(f"  -> Could not unzip {filename}. It may not be a valid zip file.")


print("\nProcess complete.")