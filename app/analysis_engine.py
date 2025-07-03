# --- START OF FILE analysis_engine.py ---
# Wersja 2.0 - Dostosowano do zmian w utils.py.
# Usunięto wywołanie nieistniejącej funkcji parse_serp_data_for_llm.
# Poprawiono przepływ danych do nowej funkcji format_serp_for_llm_prompt.

import json
from app.serp_client import SerpDataClient
from app.llm_client import OpenRouterClient
from app.db_handler import store_keyword, store_serp_data, store_llm_analysis, get_serp_results_by_keyword, init_db
from app.utils import format_serp_for_llm_prompt # <- Poprawiony import
from app.llm_prompts import get_ai_overview_analysis_prompt

# Inicjalizacja klientów (klucze API są ładowane wewnątrz klas klientów z .env)
try:
    serp_client = SerpDataClient()
    llm_client = OpenRouterClient()
except ValueError as e:
    print(f"Błąd inicjalizacji klientów API: {e}")
    print("Upewnij się, że plik .env istnieje i zawiera poprawne klucze SERPDATA_API_KEY oraz OPENROUTER_API_KEY.")
    serp_client = None
    llm_client = None

DEFAULT_LLM_MODEL = "anthropic/claude-3.5-sonnet" # Domyślny model, jeśli nie zostanie wybrany inny
DEFAULT_TEMPERATURE = 0.5
DEFAULT_MAX_TOKENS = 4096


def run_full_analysis(
    keyword: str,
    client_domain: str,
    client_industry: str,
    lang: str = "pl",
    country_code: str = "PL",
    llm_model_id: str = DEFAULT_LLM_MODEL,
    llm_temperature: float = DEFAULT_TEMPERATURE,
    llm_max_tokens: int = DEFAULT_MAX_TOKENS
    ):
    """
    Orkiestruje cały proces analizy z poprawioną obsługą błędów SerpData:
    1. Pobiera dane z SerpData.
    2. Zapisuje dane SerpData do bazy.
    3. Generuje prompt na podstawie surowych danych.
    4. Wysyła prompt do OpenRouter.
    5. Przetwarza odpowiedź LLM.
    6. Zapisuje analizę LLM do bazy.
    Zwraca wyniki analizy LLM lub None w przypadku błędu.
    """
    if not serp_client or not llm_client:
        print("Klienci API nie są poprawnie skonfigurowani. Przerwanie analizy.")
        return None

    print(f"Rozpoczynanie analizy dla słowa kluczowego: '{keyword}', domena: '{client_domain}'")

    # 1. Pobierz dane z SerpData
    print("Krok 1: Pobieranie danych z SerpData...")
    raw_serp_data_response = serp_client.search(keyword, lang=lang, country_code=country_code)

    # ===== DODANE SZCZEGÓŁOWE LOGI W ANALYSIS ENGINE =====
    print(f"DEBUG: Raw SerpData response type: {type(raw_serp_data_response)}")
    if isinstance(raw_serp_data_response, dict):
        print(f"DEBUG: Raw SerpData response keys: {list(raw_serp_data_response.keys())}")
        
        # Pokaż preview responsea
        response_preview = json.dumps(raw_serp_data_response, indent=2)[:800] + "..."
        print(f"DEBUG: Raw SerpData response preview:\n{response_preview}")
    # ===== KONIEC LOGÓW =====

    # ULEPSZONA OBSŁUGA ODPOWIEDZI Z SERPDATA 
    if not raw_serp_data_response or not isinstance(raw_serp_data_response, dict):
        err_msg = f"Nie udało się pobrać danych lub otrzymano niepoprawny format z SerpData dla słowa kluczowego: {keyword}. Response: {raw_serp_data_response}"
        print(err_msg)
        return {"error": "SerpData API communication failed", "details": err_msg, "raw_response": raw_serp_data_response}

    if raw_serp_data_response.get("error_source"):
        print(f"Błąd klienta SerpData: {raw_serp_data_response.get('message')}. Pełna odpowiedź: {raw_serp_data_response}")
        return {"error": f"SerpData Client Error: {raw_serp_data_response.get('message')}", "details": raw_serp_data_response}

    print("DEBUG: Determining response structure...")
    
    if "data" in raw_serp_data_response:
        data_wrapper = raw_serp_data_response.get('data', {})
        print(f"DEBUG: Found 'data' wrapper with keys: {list(data_wrapper.keys()) if isinstance(data_wrapper, dict) else 'Not a dict'}")
        
        if isinstance(data_wrapper, dict) and data_wrapper.get('success') is True and 'data' in data_wrapper:
            print("DEBUG: Detected OLD broken structure (data.success + data.data)")
            actual_serp_content = data_wrapper.get('data', {})
            serp_results_status = actual_serp_content.get('results', {})
            if not serp_results_status or not serp_results_status.get('query'):
                message = "Invalid or empty SERP results"
                print(f"DEBUG: Old structure search error: {message}")
                return {"error": f"SerpData Search Error: {message}", "details": raw_serp_data_response}
            raw_serp_data_to_process = actual_serp_content
            
        elif isinstance(data_wrapper, dict) and 'status' in data_wrapper:
            print("DEBUG: Detected NEW wrapper structure (data.status + data.results)")
            if data_wrapper.get('status') != 'success':
                message = f"API status: {data_wrapper.get('status')}"
                print(f"DEBUG: New wrapper structure API error: {message}")
                return {"error": f"SerpData API Error: {message}", "details": raw_serp_data_response}
            raw_serp_data_to_process = data_wrapper
            
        else:
            print("DEBUG: Unknown data wrapper structure")
            return {"error": "Unknown SerpData response structure", "details": raw_serp_data_response}
            
    elif "status" in raw_serp_data_response and "results" in raw_serp_data_response:
        print("DEBUG: Detected DIRECT structure (status + results)")
        if raw_serp_data_response.get('status') != 'success':
            message = f"Direct API status: {raw_serp_data_response.get('status')}"
            print(f"DEBUG: Direct structure API error: {message}")
            return {"error": f"SerpData API Error: {message}", "details": raw_serp_data_response}
        raw_serp_data_to_process = raw_serp_data_response
        
    else:
        print("DEBUG: Completely unknown response structure")
        return {"error": "Unrecognized SerpData response structure", "details": raw_serp_data_response}

    print(f"DEBUG: Selected raw_serp_data_to_process keys: {list(raw_serp_data_to_process.keys()) if isinstance(raw_serp_data_to_process, dict) else 'Not a dict'}")
    print("Dane z SerpData pobrane i zweryfikowane pomyślnie.")

    # 2. Zapisz dane SerpData do bazy
    print("Krok 2: Zapisywanie danych SERP do bazy...")
    keyword_id = store_keyword(keyword)

    results_data = raw_serp_data_to_process.get("results", {})
    
    # Ekstrakcja danych do bazy (uproszczona, bo mamy cały JSON)
    ai_overview_sources = []
    organic_results = []
    people_also_ask = []
    related_searches = []
    ads_data = []

    if results_data and isinstance(results_data, dict):
        snippets_data_node = results_data.get("snippets_data", {})
        if isinstance(snippets_data_node, dict):
            ai_overview_node = snippets_data_node.get("ai_overview", {})
            if isinstance(ai_overview_node, dict):
                ai_overview_sources = ai_overview_node.get("sources", [])
            
            paa_node = snippets_data_node.get("people_also_ask", {})
            if isinstance(paa_node, dict):
                people_also_ask = paa_node.get("questions", [])

            related_node = snippets_data_node.get("related_searches", {})
            if isinstance(related_node, dict):
                related_searches = related_node.get("queries", [])
            
            ads_data = snippets_data_node.get("ads", [])
        
        organic_results = results_data.get("organic_results", [])

    serp_db_id = store_serp_data(
        keyword_id,
        raw_serp_data_to_process,
        ai_overview_sources,
        organic_results,
        people_also_ask,
        related_searches,
        ads_data
    )
    print(f"Dane SERP zapisane do bazy z ID: {serp_db_id}")

    # Krok 3 został usunięty, ponieważ jego logikę przejęła nowa funkcja formatująca
    # 3. Wygeneruj prompt
    print("Krok 3 i 4: Generowanie promptu dla LLM...")
    # Przekazujemy surowe dane bezpośrednio do nowej funkcji formatującej
    formatted_prompt_serp_data = format_serp_for_llm_prompt(raw_serp_data_to_process, client_domain)
    final_llm_prompt = get_ai_overview_analysis_prompt(keyword, client_domain, client_industry, formatted_prompt_serp_data)

    # 4. Wyślij prompt do OpenRouter
    print(f"Krok 5: Wysyłanie promptu do OpenRouter (Model: {llm_model_id}, Temp: {llm_temperature}, MaxTokens: {llm_max_tokens})...")
    llm_response = llm_client.analyze_json_with_model(
        prompt_content=final_llm_prompt,
        model=llm_model_id,
        temperature=llm_temperature,
        max_tokens=llm_max_tokens
    )

    if not llm_response or llm_response.get("error"):
        print(f"Nie udało się uzyskać poprawnej odpowiedzi od LLM ({llm_model_id}). Response: {llm_response}")
        return {"error": "LLM analysis failed", "details": llm_response}

    print("Odpowiedź LLM otrzymana.")

    # 5. Przetwórz odpowiedź LLM (zakładamy, że jest już JSON)
    llm_analysis_content = llm_response
    if not isinstance(llm_analysis_content, dict) or "overall_summary" not in llm_analysis_content:
        print(f"Odpowiedź LLM nie jest w oczekiwanym formacie JSON lub brakuje kluczowych pól. Response: {llm_analysis_content}")
        return {"error": "Invalid LLM response format", "details": llm_analysis_content}

    # 6. Zapisz analizę LLM do bazy
    print("Krok 7: Zapisywanie analizy LLM do bazy...")
    analysis_db_id = store_llm_analysis(
        serp_result_id=serp_db_id,
        analysis_type="ai_overview_analysis_v2", # Wersja promptu/analizy
        llm_model=llm_model_id,
        insights=llm_analysis_content,
        recommendations=llm_analysis_content.get("actionable_recommendations", {})
    )
    print(f"Analiza LLM (model: {llm_model_id}) zapisana do bazy z ID: {analysis_db_id}")

    print("Analiza zakończona pomyślnie.")

    if isinstance(llm_analysis_content, dict):
        llm_analysis_content["llm_model_used"] = llm_model_id
        llm_analysis_content["llm_temperature_used"] = llm_temperature
        llm_analysis_content["llm_max_tokens_used"] = llm_max_tokens

    return llm_analysis_content


if __name__ == '__main__':
    init_db()
    test_keyword = "narzędzia do marketingu online"
    test_client_domain = "mojadomena.pl"
    test_client_industry = "Marketing cyfrowy dla MŚP"
    test_llm_model = "anthropic/claude-3-haiku-20240307"

    print(f"Uruchamianie testowej analizy dla: '{test_keyword}', domena: '{test_client_domain}', model LLM: {test_llm_model}")

    if not serp_client or not llm_client:
        print("Nie można uruchomić testu, ponieważ klienci API nie są skonfigurowani.")
    elif not llm_client.get_available_models():
        print(f"Nie można uruchomić testu, brak dostępnych modeli LLM z OpenRouter lub błąd API.")
    else:
        analysis_result = run_full_analysis(test_keyword, test_client_domain, test_client_industry, lang="pl", country_code="pl")

        if analysis_result and not analysis_result.get("error"):
            print("\n--- Wynik Analizy LLM ---")
            print(json.dumps(analysis_result, indent=2, ensure_ascii=False))
        elif analysis_result and analysis_result.get("error"):
            print(f"\n--- Błąd Analizy ---")
            print(f"Szczegóły błędu: {analysis_result.get('details')}")
        else:
            print("\nAnaliza nie zwróciła wyniku lub wystąpił nieoczekiwany błąd.")
