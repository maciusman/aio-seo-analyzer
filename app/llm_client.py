import requests
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class OpenRouterClient:
    def __init__(self, api_key=OPENROUTER_API_KEY):
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found. Please set it in your .env file.")
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"

    def analyze_with_model(self, prompt_content, model="anthropic/claude-3.5-sonnet", max_tokens=2048, temperature=0.7):
        """
        Sends a prompt to a specified model via OpenRouter and returns the analysis.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt_content}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data)
            response.raise_for_status()

            # Attempt to parse JSON directly
            try:
                return response.json()
            except requests.exceptions.JSONDecodeError:
                print("Error decoding JSON response from OpenRouter.")
                print("Raw response text:", response.text)
                return {"error": "JSONDecodeError", "raw_response": response.text}

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error communicating with OpenRouter: {e}")
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
            # Consider more sophisticated error handling/logging
            return {"error": "HTTPError", "status_code": e.response.status_code, "message": str(e), "raw_response": e.response.text}
        except requests.exceptions.RequestException as e:
            print(f"Request error communicating with OpenRouter: {e}")
            return {"error": "RequestException", "message": str(e)}
        except Exception as e:
            print(f"An unexpected error occurred in OpenRouterClient: {e}")
            return {"error": "UnexpectedException", "message": str(e)}

    def analyze_json_with_model(self, prompt_content, model="anthropic/claude-3.5-sonnet", max_tokens=4096, temperature=0.5):
        """
        Sends a prompt to a specified model via OpenRouter expecting a JSON response.
        Includes basic retry logic for JSON parsing errors.
        """
        # Add instruction for JSON output if not already present (simple check)
        # This is a fallback, ideally the prompt itself should strongly enforce JSON.
        if "JSON" not in prompt_content[-200:]: # Check last 200 chars for JSON instruction
            prompt_content += "\n\nZawsze odpowiadaj TYLKO w formacie JSON."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter specific header to request JSON mode if model supports it
            "HTTP-Referer": "http://localhost", # Can be your app URL
            "X-Title": "AI Overview Analyzer" # Can be your app name
        }

        # Some models support a dedicated JSON mode via response_format
        # This is a common way, but check OpenRouter docs for specific models
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt_content}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            # "response_format": {"type": "json_object"} # Uncomment if model supports it via OpenAI spec
        }

        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data)
            response.raise_for_status()

            raw_response_text = response.text
            # Try to find JSON within ```json ... ``` if present
            if "```json" in raw_response_text:
                json_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_response_text)
                if json_match:
                    raw_response_text = json_match.group(1)

            try:
                return json.loads(raw_response_text)
            except json.JSONDecodeError:
                print("Error decoding JSON response from OpenRouter.")
                print("Raw response text (after potential ```json extraction):", raw_response_text)
                # Fallback: Return the raw text wrapped in an error structure
                return {"error": "JSONDecodeError", "message": "Failed to decode JSON from model response.", "raw_response": response.text}

        except requests.exceptions.HTTPError as e:
            print(f"HTTP error communicating with OpenRouter: {e.response.status_code} - {e.response.text}")
            return {"error": "HTTPError", "status_code": e.response.status_code, "message": str(e), "raw_response": e.response.text if e.response else str(e)}
        except requests.exceptions.RequestException as e:
            print(f"Request error communicating with OpenRouter: {e}")
            return {"error": "RequestException", "message": str(e)}
        except Exception as e:
            print(f"An unexpected error occurred in OpenRouterClient: {e}")
            return {"error": "UnexpectedException", "message": str(e)}


    def compare_models(self, prompt_content, models=["anthropic/claude-3.5-sonnet", "google/gemini-pro"]):
        """
        Sends the same prompt to multiple models and returns their responses for comparison.
        """
        results = {}
        for model in models:
            print(f"Querying model: {model}")
            results[model] = self.analyze_with_model(prompt_content, model=model)
        return results

if __name__ == '__main__':
    # Example usage (for testing purposes)
    if not OPENROUTER_API_KEY:
        print("Please set your OPENROUTER_API_KEY in a .env file to run this test.")
    else:
        client = OpenRouterClient()
        sample_prompt = "What are the key benefits of using AI in SEO analysis?"

        print(f"\n--- Testing single model analysis (Claude 3.5 Sonnet) ---")
        single_analysis = client.analyze_with_model(sample_prompt)
        if single_analysis and single_analysis.get("choices"):
            print("Successfully received analysis:")
            print(single_analysis["choices"][0]["message"]["content"][:200] + "...") # Print first 200 chars
        else:
            print("Failed to get analysis or unexpected response format.")
            if single_analysis:
                print("Response received:", single_analysis)

        # print(f"\n--- Testing model comparison ---")
        # comparison_results = client.compare_models(sample_prompt)
        # for model, result in comparison_results.items():
        #     print(f"\nResponse from {model}:")
        #     if result and result.get("choices"):
        #         print(result["choices"][0]["message"]["content"][:200] + "...") # Print first 200 chars
        #     else:
        #         print("Failed to get analysis or unexpected response format for this model.")
        #         if result:
        #             print("Response received:", result)
