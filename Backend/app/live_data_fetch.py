import requests

def get_market_data(api_key: str, 
                    output_format: str = 'csv', 
                    limit: int = None, 
                    offset: int = None,
                    state: str = None,
                    district: str = None,
                    market: str = None,
                    commodity: str = None,
                    variety: str = None,
                    grade: str = None):
   
    # The base URL for the API endpoint from your image
    base_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    # Start with the required parameters
    params = {
        'api-key': api_key,
        'format': output_format
    }

    # --- Add optional parameters only if they are provided ---
    if limit is not None:
        params['limit'] = limit
    if offset is not None:
        params['offset'] = offset
    if state is not None:
        params['filters[state.keyword]'] = state
    if district is not None:
        params['filters[district]'] = district
    if market is not None:
        params['filters[market]'] = market
    if commodity is not None:
        params['filters[commodity]'] = commodity
    if variety is not None:
        params['filters[variety]'] = variety
    if grade is not None:
        params['filters[grade]'] = grade
    
    try:
        # Make the GET request to the API
        response = requests.get(base_url, params=params)
        
        # Check if the request was successful (e.g., not a 404 or 500 error)
        response.raise_for_status()  

        # Return the entire response content as text
        return response.text

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API request: {e}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    
    sample_api_key = "579b464db66ec23bdd0000016a01febea78d49c05964acd03b47d136"

    data_csv = get_market_data(api_key=sample_api_key, output_format='csv', limit=100, state="Uttar Pradesh", district="Ghaziabad")
    
    if data_csv:
        print(data_csv)



   


   
