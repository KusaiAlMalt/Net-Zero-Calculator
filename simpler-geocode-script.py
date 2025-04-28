import pandas as pd
import requests
import time

def geocode_address(address):
    """
    Convert an address to latitude and longitude using Nominatim API (OpenStreetMap)
    """
    # Respect Nominatim's usage policy with a delay between requests
    time.sleep(1)
    
    try:
        base_url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        headers = {
            'User-Agent': 'CompanyLocationGeocoder/1.0'  # Required by Nominatim
        }
        
        response = requests.get(base_url, params=params, headers=headers)
        data = response.json()
        
        if data and len(data) > 0:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
        else:
            print(f"Could not geocode address: {address}")
            return None, None
    except Exception as e:
        print(f"Error geocoding address {address}: {e}")
        return None, None

# Read the input CSV files
print("Reading CSV files...")
suppliers_df = pd.read_csv('cdr_suppliers_with_links_and_company.csv')
locations_df = pd.read_csv('company_locations.csv')

# Print original column names to verify
print("\nOriginal column names in suppliers CSV:", suppliers_df.columns.tolist())
print("Original column names in locations CSV:", locations_df.columns.tolist())

# Clean up any spaces in column names and standardize case for matching
suppliers_df.columns = suppliers_df.columns.str.strip()
locations_df.columns = locations_df.columns.str.strip()

# Ensure we have a 'Name' column in both DataFrames for merging
# Usually, suppliers has 'Name' and locations has 'name'
if 'name' in locations_df.columns and 'Name' not in locations_df.columns:
    locations_df['Name'] = locations_df['name']

if 'Name' in suppliers_df.columns and 'name' not in suppliers_df.columns:
    suppliers_df['name'] = suppliers_df['Name']

# Verify we have correct columns to proceed
required_cols = {
    'suppliers': ['Name', 'Tons Delivered', 'Tons Sold', 'Method', 'CDR_Link', 'Company_Link'],
    'locations': ['Name', 'geo_address']
}

# Check suppliers columns
missing_supplier_cols = [col for col in required_cols['suppliers'] if col not in suppliers_df.columns]
if missing_supplier_cols:
    print(f"Warning: Missing columns in suppliers CSV: {missing_supplier_cols}")
    # Try case-insensitive matching
    for missing_col in missing_supplier_cols:
        for col in suppliers_df.columns:
            if col.lower() == missing_col.lower():
                print(f"  Found {col} instead of {missing_col}, using this column")
                suppliers_df[missing_col] = suppliers_df[col]
                break

# Check locations columns
missing_location_cols = [col for col in required_cols['locations'] if col not in locations_df.columns]
if missing_location_cols:
    print(f"Warning: Missing columns in locations CSV: {missing_location_cols}")
    # Try case-insensitive matching
    for missing_col in missing_location_cols:
        for col in locations_df.columns:
            if col.lower() == missing_col.lower():
                print(f"  Found {col} instead of {missing_col}, using this column")
                locations_df[missing_col] = locations_df[col]
                break

print("\nUpdated column names in suppliers CSV:", suppliers_df.columns.tolist())
print("Updated column names in locations CSV:", locations_df.columns.tolist())

# Create a dictionary to store geocoded locations to avoid redundant lookups
geocoded_locations = {}

print("\nStarting geocoding process. This may take several minutes...")

# Geocode each address
coordinates = []
for index, row in locations_df.iterrows():
    company_name = row['Name']
    address = row['geo_address']
    
    if pd.isna(address) or address == '':
        print(f"Warning: No address for {company_name}, skipping")
        continue
    
    # Skip if we've already geocoded this address
    if address in geocoded_locations:
        lat, lon = geocoded_locations[address]
    else:
        # Geocode the address
        lat, lon = geocode_address(address)
        geocoded_locations[address] = (lat, lon)
    
    coordinates.append({
        'Name': company_name,
        'latitude': lat,
        'longitude': lon,
        'geo_address': address
    })
    
    # Progress update every 10 entries
    if (index + 1) % 10 == 0:
        print(f"Processed {index + 1}/{len(locations_df)} addresses")

# Convert to DataFrame
coordinates_df = pd.DataFrame(coordinates)

# Merge the suppliers data with the coordinates data
print("\nMerging data...")
result_df = pd.merge(suppliers_df, coordinates_df[['Name', 'latitude', 'longitude', 'geo_address']], 
                     on='Name', how='left')

# Check for suppliers that weren't matched
unmatched = result_df[result_df['latitude'].isna()]['Name'].tolist()
if unmatched:
    print(f"\nWarning: {len(unmatched)} suppliers couldn't be matched to locations:")
    for name in unmatched[:10]:  # Show first 10
        print(f"  - {name}")
    if len(unmatched) > 10:
        print(f"  ... and {len(unmatched) - 10} more")

# Add the location column which combines the coordinates for use in Leaflet
result_df['location'] = result_df.apply(
    lambda row: f"{row['latitude']},{row['longitude']}" if pd.notnull(row['latitude']) and pd.notnull(row['longitude']) else '', 
    axis=1
)

# Reorder columns to match the requested format
try:
    final_df = result_df[['Name', 'Tons Delivered', 'Tons Sold', 'Method', 'CDR_Link', 'Company_Link', 'location']]
except KeyError as e:
    print(f"Error selecting columns: {e}")
    print("Available columns:", result_df.columns.tolist())
    print("Using all available columns instead")
    final_df = result_df

# Save to a new CSV file
output_file = 'cdr_suppliers_with_coordinates.csv'
final_df.to_csv(output_file, index=False)

# Print statistics
total_suppliers = len(final_df)
geocoded_suppliers = final_df['location'].astype(bool).sum()

print(f"\nGeocoding complete!")
print(f"Total suppliers: {total_suppliers}")
print(f"Successfully geocoded: {geocoded_suppliers} ({geocoded_suppliers / total_suppliers * 100:.1f}%)")
print(f"Output saved to: {output_file}")