def get_results(data):
    """
    Generate a dictionary of results based on input data.

    Args:
        data (dict): A dictionary containing keys "scope1", "scope2", "scope3", and "profit".

    Returns:
        dict: A dictionary with the same keys as the input, defaulting to "-" if a key is missing.
    """    
    return {
        "scope1": data.get("scope1", "-"),
        "scope2": data.get("scope2", "-"),
        "scope3": data.get("scope3", "-"),
        "profit": data.get("profit", "-")
    }

def calculate_net_zero_cost(data, cc_method):
    """
    Calculate the cost of achieving net zero emissions using a specific carbon capture method.

    Args:
        data (dict): A dictionary containing "scope1", "scope2", "scope3", and "profit".
        cc_method (dict): A dictionary containing the carbon capture method details, including:
            - "name" (str): The name of the carbon capture method.
            - "cost_per_ton" (float): The cost per ton of carbon removal.

    Returns:
        dict: A dictionary containing:
            - "method" (str): The name of the carbon capture method.
            - "scope1" (int): Emissions from scope 1.
            - "scope2" (int): Emissions from scope 2.
            - "scope3" (int): Emissions from scope 3.
            - "total_emissions" (int): The total emissions from all scopes.
            - "cost_to_offset" (float): The total cost to offset the emissions.
            - "percentage_of_revenue" (float): The percentage of revenue required to offset emissions.
    """
    scope1 = data.get("scope1", 0)
    scope2 = data.get("scope2", 0)
    scope3 = data.get("scope3", 0)
    revenue = data.get("profit")

    total_emissions = scope1 + scope2 + scope3
    cost_to_offset = total_emissions * cc_method['cost_per_ton']
    percentage = (cost_to_offset / (revenue*1000000)) * 100

    return {
        "method": cc_method["name"],
        "scope1": scope1,
        "scope2": scope2,
        "scope3": scope3,
        "total_emissions": total_emissions,
        "cost_to_offset": round(cost_to_offset, 2),
        "percentage_of_revenue": round(percentage, 2)
        
    }