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
            # "response_format": {"type": "json_object"} # Uncomment if model supports it via OpenAI spec, some models might need this
        }

        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data)
            response.raise_for_status()

            # POPRAWKA: Najpierw sparsuj OpenRouter API response, potem wyciągnij content
            try:
                api_response = response.json()
                raw_response_text = api_response['choices'][0]['message']['content']
                
                print(f"DEBUG: OpenRouter API response structure OK")
                print(f"DEBUG: Model content length: {len(raw_response_text)} chars")
                
            except (KeyError, IndexError, json.JSONDecodeError) as parse_error:
                print(f"Error parsing OpenRouter API response structure: {parse_error}")
                print("Raw response text:", response.text[:500] + "...")
                return {"error": "APIResponseParseError", "message": f"Failed to parse OpenRouter response: {str(parse_error)}", "raw_response": response.text}

            # Handle markdown-wrapped JSON (```json ... ```)
            if "```json" in raw_response_text:
                json_match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_response_text)
                if json_match:
                    print("DEBUG: Found ```json wrapper, extracting content")
                    raw_response_text = json_match.group(1)
                else:
                    print("DEBUG: ```json found but regex didn't match")
            else:
                print("DEBUG: No ```json wrapper found, using content directly")

            # Parse the actual JSON content
            try:
                parsed_json = json.loads(raw_response_text)
                print("DEBUG: Successfully parsed JSON from model response")
                return parsed_json
            except json.JSONDecodeError as json_error:
                print(f"Error decoding JSON response from OpenRouter for model {model}.")
                print(f"JSON decode error: {json_error}")
                print("Raw response text (after potential ```json extraction):", raw_response_text[:500] + "...")
                return {"error": "JSONDecodeError", "message": "Failed to decode JSON from model response.", "raw_response": raw_response_text}

        except requests.exceptions.HTTPError as e:
            error_message = f"HTTP error {e.response.status_code} for model {model}: {e.response.text if e.response else str(e)}"
            print(error_message)
            return {"error": "HTTPError", "status_code": e.response.status_code, "message": str(e), "raw_response": e.response.text if e.response else str(e)}
        except requests.exceptions.RequestException as e:
            print(f"Request error communicating with OpenRouter for model {model}: {e}")
            return {"error": "RequestException", "message": str(e)}
        except Exception as e:
            print(f"An unexpected error occurred in OpenRouterClient for model {model}: {e}")
            return {"error": "UnexpectedException", "message": str(e)}

    def get_available_models(self):
        """
        Fetches the list of available models from OpenRouter.
        Caches the result to avoid frequent API calls.
        """
        if hasattr(self, "_available_models") and self._available_models:
            return self._available_models

        try:
            response = requests.get(f"{self.base_url}/models")
            response.raise_for_status()
            models_data = response.json()
            # We are interested in model IDs, and perhaps their names for display
            # Example structure of a model entry: {'id': '...', 'name': '...', ...}
            self._available_models = models_data.get("data", [])
            return self._available_models
        except requests.exceptions.RequestException as e:
            print(f"Error fetching available models from OpenRouter: {e}")
            return [] # Return empty list on error
        except Exception as e:
            print(f"An unexpected error occurred while fetching models: {e}")
            return []


    # def compare_models(self, prompt_content, models=["anthropic/claude-3.5-sonnet", "google/gemini-pro"]):
    #     """
    #     Sends the same prompt to multiple models and returns their responses for comparison.
    #     This method might be less used if users pick one model.
    #     """
    #     results = {}
    #     for model_id in models: # Changed from 'model' to 'model_id' for clarity
    #         print(f"Querying model: {model_id}")
    #         # Assuming analyze_with_model is the general purpose one, not analyze_json_with_model
    #         results[model_id] = self.analyze_with_model(prompt_content, model=model_id)
    #     return results

if __name__ == '__main__':
    if not OPENROUTER_API_KEY:
        print("Please set your OPENROUTER_API_KEY in a .env file to run this test.")
    else:
        client = OpenRouterClient()

        print("\n--- Testing fetching available models ---")
        models = client.get_available_models()
        if models:
            print(f"Successfully fetched {len(models)} models.")
            # Print details of a few models
            for m in models[:3]:
                 print(f"  ID: {m.get('id')}, Name: {m.get('name')}, Context Length: {m.get('context_length')}")
            # Example: find a specific model
            default_model_id = "anthropic/claude-3.5-sonnet"
            # Check if our default model is in the list
            if any(m.get('id') == default_model_id for m in models):
                print(f"\nDefault model '{default_model_id}' is available.")
            else:
                # If default is not available, pick the first one from the list for testing analyze_json_with_model
                if models:
                    default_model_id = models[0].get('id')
                    print(f"\nDefault model not found, using first available model for testing: '{default_model_id}'")
                else:
                    print("\nNo models available to test analyze_json_with_model.")
                    default_model_id = None

            if default_model_id:
                sample_prompt_json = """
                Przeanalizuj poniższy tekst i zwróć informacje o sentymencie oraz kluczowych encjach.
                Tekst: "Uwielbiam pracować z API OpenRouter, jest szybkie i niezawodne!"
                Odpowiedz TYLKO w formacie JSON:
                {
                  "sentiment": "pozytywny" | "negatywny" | "neutralny",
                  "entities": ["OpenRouter API"]
                }
                """
                print(f"\n--- Testing single model JSON analysis ({default_model_id}) ---")
                json_analysis = client.analyze_json_with_model(sample_prompt_json, model=default_model_id)

                if json_analysis and not json_analysis.get("error"):
                    print("Successfully received JSON analysis:")
                    print(json.dumps(json_analysis, indent=2, ensure_ascii=False))
                else:
                    print("Failed to get JSON analysis or error in response.")
                    if json_analysis:
                        print("Response/Error details:", json_analysis)
        else:
            print("Failed to fetch models or no models available.")
