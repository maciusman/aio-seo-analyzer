import requests
import os
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
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()  # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from SerpData: {e}")
            # Consider more sophisticated error handling/logging
            return None

if __name__ == '__main__':
    # Example usage (for testing purposes)
    if not SERPDATA_API_KEY:
        print("Please set your SERPDATA_API_KEY in a .env file to run this test.")
    else:
        client = SerpDataClient()
        keyword_to_search = "real estate software companies"
        print(f"Searching for: {keyword_to_search}")
        results = client.search(keyword_to_search, lang="en", country_code="us")
        if results:
            print("Successfully fetched results.")
            # print(results) # Uncomment to see the full JSON response
            if results.get("results") and results["results"].get("organic_results"):
                 print(f"Found {len(results['results']['organic_results'])} organic results.")
            if results.get("results") and results["results"].get("ai_overview"):
                print("AI Overview found.")
        else:
            print("Failed to fetch results.")
