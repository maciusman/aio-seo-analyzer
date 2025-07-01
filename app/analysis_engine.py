import json
from app.serp_client import SerpDataClient
from app.llm_client import OpenRouterClient
from app.db_handler import store_keyword, store_serp_data, store_llm_analysis, get_serp_results_by_keyword, init_db
from app.utils import parse_serp_data_for_llm, format_serp_for_llm_prompt
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
    Orkiestruje cały proces analizy:
    1. Pobiera dane z SerpData.
    2. Zapisuje dane SerpData do bazy.
    3. Przetwarza dane SerpData dla LLM.
    4. Generuje prompt.
    5. Wysyła prompt do OpenRouter.
    6. Przetwarza odpowiedź LLM.
    7. Zapisuje analizę LLM do bazy.
    Zwraca wyniki analizy LLM lub None w przypadku błędu.
    """
    if not serp_client or not llm_client:
        print("Klienci API nie są poprawnie skonfigurowani. Przerwanie analizy.")
        return None

    print(f"Rozpoczynanie analizy dla słowa kluczowego: '{keyword}', domena: '{client_domain}'")

    # 1. Pobierz dane z SerpData
    print("Krok 1: Pobieranie danych z SerpData...")
    raw_serp_data_response = serp_client.search(keyword, lang=lang, country_code=country_code)

    # --- ULEPSZONA OBSŁUGA ODPOWIEDZI Z SERPDATA ---
    if not raw_serp_data_response or not isinstance(raw_serp_data_response, dict):
        err_msg = f"Nie udało się pobrać danych lub otrzymano niepoprawny format z SerpData dla słowa kluczowego: {keyword}. Response: {raw_serp_data_response}"
        print(err_msg)
        return {"error": "SerpData API communication failed", "details": err_msg, "raw_response": raw_serp_data_response}

    # Sprawdzamy, czy nie ma błędu zwróconego przez SerpDataClient (np. HTTPError, RequestException)
    if raw_serp_data_response.get("error_source"): # Klucz dodany w proponowanej modyfikacji SerpDataClient
        print(f"Błąd klienta SerpData: {raw_serp_data_response.get('message')}. Pełna odpowiedź: {raw_serp_data_response}")
        return {"error": f"SerpData Client Error: {raw_serp_data_response.get('message')}", "details": raw_serp_data_response}

    # Analiza struktury odpowiedzi (na podstawie Twojego logu z błędem 'Out of proxy')
    # Oczekiwana struktura sukcesu (nawet jeśli wyniki wyszukiwania mają wewnętrzny błąd)
    # {'data': {'success': True, 'data': { 'results': {'success': True/False, ... }}}}

    serp_api_meta = raw_serp_data_response.get('data', {})
    actual_serp_content = serp_api_meta.get('data', {}) # To jest właściwa treść SERP

    if not isinstance(serp_api_meta, dict) or not isinstance(actual_serp_content, dict):
        err_msg = f"Nieoczekiwana główna struktura odpowiedzi z SerpData. Słowo kluczowe: {keyword}. Response: {raw_serp_data_response}"
        print(err_msg)
        return {"error": "Unexpected SerpData response structure", "details": err_msg, "raw_response": raw_serp_data_response}

    if serp_api_meta.get('success') is not True:
        message = serp_api_meta.get('message', 'Nieznany błąd na poziomie API SerpData (zewnętrzny success: false)')
        print(f"Błąd API SerpData: {message}. Słowo kluczowe: {keyword}. Pełna odpowiedź: {raw_serp_data_response}")
        return {"error": f"SerpData API error: {message}", "details": raw_serp_data_response}

    # Sprawdzamy wewnętrzny obiekt 'results' w 'actual_serp_content'
    serp_results_status = actual_serp_content.get('results', {})
    if not isinstance(serp_results_status, dict):
        err_msg = f"Brak obiektu 'results' w danych SERP lub niepoprawny typ. Słowo kluczowe: {keyword}. Response: {raw_serp_data_response}"
        print(err_msg)
        return {"error": "Missing or invalid 'results' object in SerpData", "details": err_msg, "raw_response": raw_serp_data_response}

    if serp_results_status.get('success') is not True:
        message = serp_results_status.get('message', 'Nieznany błąd wyszukiwania (wewnętrzny results.success: false)')
        print(f"SerpData zgłosiło błąd wyszukiwania: \"{message}\". Słowo kluczowe: {keyword}. Pełna odpowiedź: {raw_serp_data_response}")
        # Zwracamy konkretny błąd, aby UI mogło go wyświetlić
        return {"error": f"SerpData Search Error: {message}", "details": raw_serp_data_response}

    # Jeśli doszliśmy tutaj, to zarówno API SerpData odpowiedziało poprawnie,
    # jak i wewnętrzne wyniki wyszukiwania wskazują na sukces.
    # actual_serp_content zawiera teraz dane, które wcześniej były w raw_serp_data
    raw_serp_data_to_process = actual_serp_content
    print("Dane z SerpData pobrane i zweryfikowane pomyślnie.")
    # --- KONIEC ULEPSZONEJ OBSŁUGI ODPOWIEDZI Z SERPDATA ---

    # 2. Zapisz dane SerpData do bazy
    print("Krok 2: Zapisywanie danych SERP do bazy...")
    keyword_id = store_keyword(keyword)

    results_data = raw_serp_data_to_process.get("results", {}) # Używamy zweryfikowanych danych
    ai_overview_sources = results_data.get("ai_overview", {}).get("sources", []) if results_data.get("ai_overview") else []
    organic_results = results_data.get("organic_results", [])
    people_also_ask_data = results_data.get("people_also_ask", {})
    people_also_ask = people_also_ask_data.get("questions", []) if isinstance(people_also_ask_data, dict) else []

    related_searches_data = results_data.get("related_searches", {})
    related_searches = related_searches_data.get("queries", []) if isinstance(related_searches_data, dict) else []

    # Sprawdzenie czy snippets_data istnieje przed próbą dostępu
    snippets_data_node = results_data.get("snippets_data", {})
    ads_data = snippets_data_node.get("ads", []) if isinstance(snippets_data_node, dict) else []


    serp_db_id = store_serp_data(
        keyword_id,
        raw_serp_data_to_process, # Przechowujemy zweryfikowany i poprawny fragment JSON
        ai_overview_sources,
        organic_results,
        people_also_ask,
        related_searches,
        ads_data
    )
    print(f"Dane SERP zapisane do bazy z ID: {serp_db_id}")

    # 3. Przetwórz dane SerpData dla LLM
    print("Krok 3: Przetwarzanie danych SERP dla LLM...")
    # Używamy zweryfikowanych danych, przekształcając je z powrotem na string JSON dla parse_serp_data_for_llm
    parsed_serp_for_llm = parse_serp_data_for_llm(json.dumps(raw_serp_data_to_process))

    # 4. Wygeneruj prompt
    print("Krok 4: Generowanie promptu dla LLM...")
    formatted_prompt_serp_data = format_serp_for_llm_prompt(parsed_serp_for_llm, client_domain)
    final_llm_prompt = get_ai_overview_analysis_prompt(keyword, client_domain, client_industry, formatted_prompt_serp_data)
    # print("\n--- Final LLM Prompt ---")
    # print(final_llm_prompt[:500] + "...") # For debugging, print start of prompt
    # print("--- End of Final LLM Prompt ---")


    # 5. Wyślij prompt do OpenRouter
    print("Krok 5: Wysyłanie promptu do OpenRouter...")
    # Użyjemy `analyze_json_with_model` oczekując odpowiedzi JSON
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
    # W tym miejscu llm_response powinien być już sparsowanym JSONem (słownikiem Python)
    # jeśli analyze_json_with_model zadziałało poprawnie

    # 6. Przetwórz odpowiedź LLM (zakładamy, że jest już JSON)
    # W tym przypadku, jeśli nie ma błędu, llm_response jest już słownikiem.
    # Można dodać walidację schematu odpowiedzi LLM tutaj, np. używając Pydantic.
    llm_analysis_content = llm_response
    # Sprawdzenie czy odpowiedź zawiera oczekiwane klucze z promptu
    if not isinstance(llm_analysis_content, dict) or "overall_summary" not in llm_analysis_content:
        print(f"Odpowiedź LLM nie jest w oczekiwanym formacie JSON lub brakuje kluczowych pól. Response: {llm_analysis_content}")
        return {"error": "Invalid LLM response format", "details": llm_analysis_content}


    # 7. Zapisz analizę LLM do bazy
    print("Krok 7: Zapisywanie analizy LLM do bazy...")
    analysis_db_id = store_llm_analysis(
        serp_result_id=serp_db_id,
        analysis_type="ai_overview_analysis_v1", # Wersjonowanie typu analizy
        llm_model=llm_model_id, # Zapisujemy faktycznie użyty model
        insights=llm_analysis_content, # Cały sparsowany JSON jako insights
        recommendations=llm_analysis_content.get("actionable_recommendations", {}) # Lub konkretna część
    )
    print(f"Analiza LLM (model: {llm_model_id}) zapisana do bazy z ID: {analysis_db_id}")

    print("Analiza zakończona pomyślnie.")

    # Dodajemy informację o użytym modelu do zwracanych wyników
    # Można to zrobić lepiej, np. poprzez dedykowany obiekt odpowiedzi, ale na razie proste dodanie do słownika
    if isinstance(llm_analysis_content, dict):
        llm_analysis_content["llm_model_used"] = llm_model_id
        llm_analysis_content["llm_temperature_used"] = llm_temperature
        llm_analysis_content["llm_max_tokens_used"] = llm_max_tokens
        # Można też dodać datę analizy itp.
        # llm_analysis_content["analysis_timestamp"] = datetime.now().isoformat()

    return llm_analysis_content


if __name__ == '__main__':
    # Upewnij się, że baza danych jest zainicjowana
    init_db()

    # Przykładowe użycie - Pamiętaj o ustawieniu kluczy API w .env!
    # Te wartości powinny być pobierane z interfejsu użytkownika w aplikacji Streamlit
    test_keyword = "narzędzia do marketingu online"
    test_client_domain = "mojadomena.pl" # Zmień na domenę, którą chcesz analizować
    test_client_industry = "Marketing cyfrowy dla MŚP"
    test_llm_model = "anthropic/claude-3-haiku-20240307" # Przykładowy, inny model do testów
    # test_llm_model = DEFAULT_LLM_MODEL # Można też testować z domyślnym

    print(f"Uruchamianie testowej analizy dla: '{test_keyword}', domena: '{test_client_domain}', model LLM: {test_llm_model}")

    if not serp_client or not llm_client:
        print("Nie można uruchomić testu, ponieważ klienci API nie są skonfigurowani.")
        print("Upewnij się, że masz plik .env z SERPDATA_API_KEY i OPENROUTER_API_KEY.")
    elif not llm_client.get_available_models(): # Sprawdzenie czy są dostępne modele
        print(f"Nie można uruchomić testu, brak dostępnych modeli LLM z OpenRouter lub błąd API.")
        print("Upewnij się, że masz plik .env z SERPDATA_API_KEY i OPENROUTER_API_KEY.")
    else:
        analysis_result = run_full_analysis(test_keyword, test_client_domain, test_client_industry, lang="pl", country_code="PL")

        if analysis_result and not analysis_result.get("error"):
            print("\n--- Wynik Analizy LLM ---")
            print(json.dumps(analysis_result, indent=2, ensure_ascii=False))

            # Przykład pobrania zapisanych danych
            # retrieved_serps = get_serp_results_by_keyword(test_keyword)
            # if retrieved_serps:
            #     print(f"\nOstatni zapisany SERP dla '{test_keyword}':")
            #     # print(json.dumps(json.loads(retrieved_serps[0]['raw_serp_data']), indent=2, ensure_ascii=False))
            # else:
            #     print(f"Nie znaleziono zapisanych SERP dla {test_keyword}")

        elif analysis_result and analysis_result.get("error"):
            print(f"\n--- Błąd Analizy ---")
            print(f"Szczegóły błędu: {analysis_result.get('details')}")
        else:
            print("\nAnaliza nie zwróciła wyniku lub wystąpił nieoczekiwany błąd.")
