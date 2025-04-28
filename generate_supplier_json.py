import pandas as pd
import json
import os
import random  # For demonstration purposes only

# Load the CSV file
df = pd.read_csv('cdr_suppliers_full.csv')

# In a real application, you would use a geocoding service to get actual coordinates
# For this example, we'll generate random coordinates for demonstration
suppliers_with_coords = []

for _, row in df.iterrows():
    # Skip suppliers with zero tons delivered and sold
    if row['Tons Delivered'] == 0 and row['Tons Sold'] == 0:
        continue
        
    # Generate random coordinates (this is for demonstration only)
    # In a real application, you would geocode company addresses
    latitude = random.uniform(-65, 65)
    longitude = random.uniform(-180, 180)
    
    supplier = {
        'name': row['Name'],
        'method': row['Method'],
        'tons_delivered': row['Tons Delivered'],
        'tons_sold': row['Tons Sold'],
        'latitude': latitude,
        'longitude': longitude
    }
    
    suppliers_with_coords.append(supplier)

# Ensure the static directory exists
os.makedirs('static', exist_ok=True)

# Write to JSON file
with open('static/suppliers.json', 'w') as f:
    json.dump(suppliers_with_coords, f, indent=2)

print(f"Created suppliers.json with {len(suppliers_with_coords)} entries")