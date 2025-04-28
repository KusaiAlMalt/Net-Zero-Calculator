import pandas as pd
import json
import os
import colorsys

# Load the CSV file with coordinates
df = pd.read_csv('cdr_suppliers_with_coordinates.csv')

# Define a color mapping function for different methods
def get_method_colors():
    """Generate colors for each unique method"""
    methods = df['Method'].dropna().unique()
    
    # Create a dictionary to store method -> color
    method_colors = {}
    
    # Generate evenly spaced colors based on the number of methods
    for i, method in enumerate(methods):
        # Use HSV color space to generate distinct colors
        # H: evenly space around the color wheel
        # S: high saturation for vivid colors
        # V: high value for brightness
        hue = i / len(methods)
        # Convert HSV to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        
        # Convert RGB to hex
        hex_color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
        method_colors[method] = hex_color
    
    return method_colors

# Generate colors for each method
method_colors = get_method_colors()

# Print the color assignments for reference
print("Method Color Assignments:")
for method, color in method_colors.items():
    print(f"  {method}: {color}")

# Create data structure for suppliers with coordinates
suppliers_with_coords = []

for _, row in df.iterrows():
    # Skip suppliers without coordinates
    if pd.isna(row['location']) or row['location'] == '':
        continue
    
    # Parse latitude and longitude from the location field
    try:
        lat_str, lng_str = row['location'].split(',')
        latitude = float(lat_str)
        longitude = float(lng_str)
        
        # Skip if coordinates are invalid
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            print(f"Warning: Invalid coordinates for {row['Name']}: {row['location']}")
            continue
        
        # Get the color for this method
        method = row['Method']
        color = method_colors.get(method, '#808080')  # Default gray if method not found
        
        # Create supplier data object
        supplier = {
            'name': row['Name'],
            'method': method,
            'tons_delivered': row['Tons Delivered'],
            'tons_sold': row['Tons Sold'],
            'latitude': latitude,
            'longitude': longitude,
            'color': color
        }
        
        # Add Company link if available (but skip CDR link as requested)
        if 'Company_Link' in row and pd.notna(row['Company_Link']):
            supplier['company_link'] = row['Company_Link']
        
        suppliers_with_coords.append(supplier)
    except Exception as e:
        print(f"Error processing {row['Name']}: {e}")

# Ensure the static directory exists
os.makedirs('static', exist_ok=True)

# Write to JSON file
with open('static/suppliers.json', 'w') as f:
    json.dump(suppliers_with_coords, f, indent=2)

print(f"\nCreated suppliers.json with {len(suppliers_with_coords)} entries")
print(f"Included {len(suppliers_with_coords)} out of {len(df)} suppliers (those with valid coordinates)")