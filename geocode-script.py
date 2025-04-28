import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables (for API keys)
load_dotenv()

def geocode_address(address):
    """
    Convert an address to latitude and longitude using Nominatim API
    (OpenStreetMap's geocoding service)
    
    Note: For production use, consider using a paid service like Google Maps API
    which has better rate limits and more reliable results
    """
    # Respect Nominatim's usage policy with a delay between requests
    time.sleep(1)
    
    try:
        # For a more robust solution in production, consider using Google's Geocoding API
        # with proper error handling, but it requires an API key
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

def google_geocode_address(address, api_key):
    """
    Convert an address to latitude and longitude using Google Maps Geocoding API
    
    This is a more reliable option for production use, but requires an API key
    and may have associated costs
    """
    time.sleep(0.1)  # Respect rate limits
    
    try:
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': api_key
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            print(f"Could not geocode address: {address} (Status: {data['status']})")
            return None, None
    except Exception as e:
        print(f"Error geocoding address {address}: {e}")
        return None, None

def main():
    # Read the input CSV files
    suppliers_df = pd.read_csv('cdr_suppliers_with_links_and_company.csv')
    locations_df = pd.read_csv('company_locations.csv')
    
    # Clean up any spaces in column names
    suppliers_df.columns = suppliers_df.columns.str.strip()
    locations_df.columns = locations_df.columns.str.strip()
    
    # Prepare the geocoding
    google_api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    use_google_api = google_api_key is not None
    
    if use_google_api:
        print("Using Google Maps Geocoding API")
    else:
        print("Using Nominatim (OpenStreetMap) Geocoding API")
        print("For production use, consider using Google Maps API for better results")
    
    # Create a dictionary to store geocoded locations to avoid redundant lookups
    geocoded_locations = {}
    
    # Geocode each address
    coordinates = []
    for _, row in locations_df.iterrows():
        address = row['geo_address']
        
        # Skip if we've already geocoded this address
        if address in geocoded_locations:
            lat, lon = geocoded_locations[address]
        else:
            # Geocode the address using the appropriate service
            if use_google_api:
                lat, lon = google_geocode_address(address, google_api_key)
            else:
                lat, lon = geocode_address(address)
                
            # Store for future use
            geocoded_locations[address] = (lat, lon)
        
        coordinates.append({
            'name': row['name'],
            'latitude': lat,
            'longitude': lon,
            'geo_address': address
        })
    
    # Convert to DataFrame
    coordinates_df = pd.DataFrame(coordinates)
    
    # Merge the suppliers data with the coordinates data
    # First, ensure the name columns match for merging
    coordinates_df['Name'] = coordinates_df['name']
    
    # Merge the dataframes on the company name
    result_df = pd.merge(suppliers_df, coordinates_df[['Name', 'latitude', 'longitude', 'geo_address']], 
                         on='Name', how='left')
    
    # Add the location column which combines the coordinates for use in Leaflet
    result_df['location'] = result_df.apply(
        lambda row: f"{row['latitude']},{row['longitude']}" if pd.notnull(row['latitude']) and pd.notnull(row['longitude']) else '', 
        axis=1
    )
    
    # Reorder columns to match the requested format
    final_df = result_df[['Name', 'Tons Delivered', 'Tons Sold', 'Method', 'CDR_Link', 'Company_Link', 'location', 'geo_address']]
    
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

if __name__ == "__main__":
    main()