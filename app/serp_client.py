import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

SERPDATA_API_KEY = os.getenv("SERPDATA_API_KEY")

class SerpDataClient:
    def __init__(self, api_key=SERPDATA_API_KEY):
        if not api_key:
            raise ValueError("SERPDATA_API_KEY not found. Please set it in your .env file.")
        self.api_key = api_key
        self.base_url = "https://api.serpdata.io/v1/search"

    def search(self, keyword, lang="pl", country_code="PL"):
        """
        Fetches search results from serpdata.io API.
        Returns structured response with improved error handling.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        params = {
            "keyword": keyword,
            "hl": lang,
            "gl": country_code
        }
        
        try:
            print(f"SerpData request: {self.base_url}")
            print(f"SerpData params: {params}")
            response = requests.get(self.base_url, headers=headers, params=params, timeout=30)
            
            # Log response details for debugging
            print(f"SerpData response status: {response.status_code}")
            
            # Check HTTP status
            response.raise_for_status()
            
            # Parse JSON response
            try:
                json_response = response.json()
                
                # ===== DODANE SZCZEGÓŁOWE LOGI =====
                print(f"SerpData JSON keys: {list(json_response.keys()) if isinstance(json_response, dict) else 'Not a dict'}")
                
                # Pokaż pierwszych kilka znaków responsea dla debug
                response_preview = json.dumps(json_response, indent=2)[:500] + "..."
                print(f"SerpData response preview:\n{response_preview}")
                
                # Sprawdź czy jest struktura z 'data' wrapper
                if 'data' in json_response:
                    data_section = json_response['data']
                    print(f"Found 'data' section with keys: {list(data_section.keys()) if isinstance(data_section, dict) else 'Not a dict'}")
                    
                    # Sprawdź czy jest nested data.data
                    if isinstance(data_section, dict) and 'data' in data_section:
                        nested_data = data_section['data']
                        print(f"Found nested 'data.data' with keys: {list(nested_data.keys()) if isinstance(nested_data, dict) else 'Not a dict'}")
                
                # Sprawdź czy jest bezpośrednia struktura (bez data wrapper)
                if 'results' in json_response:
                    print(f"Found direct 'results' section")
                    
                if 'status' in json_response:
                    print(f"Found 'status' field: {json_response['status']}")
                    
                # ===== KONIEC LOGÓW =====
                
                # Validate response structure
                if not isinstance(json_response, dict):
                    return {
                        "error_source": "SerpDataClient",
                        "message": "Invalid JSON response - not a dictionary",
                        "raw_response": response.text
                    }
                
                return json_response
                
            except ValueError as json_error:
                return {
                    "error_source": "SerpDataClient",
                    "message": f"JSON decode error: {str(json_error)}",
                    "raw_response": response.text
                }
                
        except requests.exceptions.HTTPError as e:
            return {
                "error_source": "SerpDataClient",
                "message": f"HTTP error {e.response.status_code}: {e.response.text if e.response else str(e)}",
                "status_code": e.response.status_code if e.response else None,
                "raw_response": e.response.text if e.response else str(e)
            }
        except requests.exceptions.RequestException as e:
            return {
                "error_source": "SerpDataClient", 
                "message": f"Request error: {str(e)}",
                "raw_response": str(e)
            }
        except Exception as e:
            return {
                "error_source": "SerpDataClient",
                "message": f"Unexpected error: {str(e)}",
                "raw_response": str(e)
            }

    def test_different_locations(self, keyword="test"):
        """Test z różnymi lokalizacjami - niektóre proxy mogą działać lepiej"""
        locations = [
            ("en", "us"),
            ("en", "gb"), 
            ("pl", "pl"),
            ("de", "de")
        ]
        
        print(f"Testing keyword '{keyword}' with different locations...")
        for lang, country in locations:
            print(f"\nTesting with {lang}/{country}...")
            result = self.search(keyword, lang, country)
            
            if result and not result.get("error_source"):
                # Sprawdź strukturę zgodnie z nowym formatem
                data_wrapper = result.get("data", {})
                if data_wrapper.get("success"):
                    actual_data = data_wrapper.get("data", {})
                    results = actual_data.get("results", {})
                    if results.get("success"):
                        print(f"✅ SUCCESS with {lang}/{country}")
                        return lang, country
                    else:
                        print(f"❌ Search failed: {results.get('message', 'Unknown error')}")
                else:
                    print(f"❌ API wrapper failed")
            else:
                print(f"❌ Client error: {result.get('message', 'Unknown error')}")
        
        print("❌ All locations failed")
        return None, None

if __name__ == '__main__':
    # Example usage (for testing purposes)
    if not SERPDATA_API_KEY:
        print("Please set your SERPDATA_API_KEY in a .env file to run this test.")
    else:
        client = SerpDataClient()
        
        print("=== Testing basic search ===")
        keyword_to_search = "test"
        print(f"Searching for: {keyword_to_search}")
        results = client.search(keyword_to_search, lang="en", country_code="us")
        
        if results:
            if results.get("error_source"):
                print(f"❌ Error: {results.get('message')}")
            else:
                print("✅ Basic search successful")
        else:
            print("❌ No response received")
