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

def run_full_analysis(keyword: str, client_domain: str, client_industry: str, lang: str = "pl", country_code: str = "PL"):
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
    raw_serp_data = serp_client.search(keyword, lang=lang, country_code=country_code)
    if not raw_serp_data or raw_serp_data.get("status") != "success":
        print(f"Nie udało się pobrać danych z SerpData dla słowa kluczowego: {keyword}. Response: {raw_serp_data}")
        return None
    print("Dane z SerpData pobrane pomyślnie.")

    # 2. Zapisz dane SerpData do bazy
    print("Krok 2: Zapisywanie danych SERP do bazy...")
    keyword_id = store_keyword(keyword)

    # Ekstrakcja specyficznych części JSONa do osobnych kolumn (zgodnie z db_handler)
    # Te funkcje powinny być bardziej rozbudowane w utils.py lub tutaj, aby wyciągnąć dokładnie te dane
    results_data = raw_serp_data.get("results", {})
    ai_overview_sources = results_data.get("ai_overview", {}).get("sources", []) if results_data.get("ai_overview") else []
    organic_results = results_data.get("organic_results", [])
    people_also_ask = results_data.get("people_also_ask", {}).get("questions", []) if results_data.get("people_also_ask") else []
    related_searches = results_data.get("related_searches", {}).get("queries", []) if results_data.get("related_searches") else []
    ads_data = results_data.get("snippets_data", {}).get("ads", []) if results_data.get("snippets_data") else []

    serp_db_id = store_serp_data(
        keyword_id,
        raw_serp_data, # Przechowujemy cały JSON
        ai_overview_sources,
        organic_results,
        people_also_ask,
        related_searches,
        ads_data
    )
    print(f"Dane SERP zapisane do bazy z ID: {serp_db_id}")

    # 3. Przetwórz dane SerpData dla LLM
    print("Krok 3: Przetwarzanie danych SERP dla LLM...")
    # Używamy pełnego raw_serp_data, ponieważ parse_serp_data_for_llm oczekuje stringa JSON
    parsed_serp_for_llm = parse_serp_data_for_llm(json.dumps(raw_serp_data))

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
    llm_response = llm_client.analyze_json_with_model(final_llm_prompt)

    if not llm_response or llm_response.get("error"):
        print(f"Nie udało się uzyskać poprawnej odpowiedzi od LLM. Response: {llm_response}")
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
        llm_model=llm_client.analyze_json_with_model.__defaults__[0], # Pobiera domyślny model z sygnatury funkcji
        insights=llm_analysis_content, # Cały sparsowany JSON jako insights
        recommendations=llm_analysis_content.get("actionable_recommendations", {}) # Lub konkretna część
    )
    print(f"Analiza LLM zapisana do bazy z ID: {analysis_db_id}")

    print("Analiza zakończona pomyślnie.")
    return llm_analysis_content


if __name__ == '__main__':
    # Upewnij się, że baza danych jest zainicjowana
    init_db()

    # Przykładowe użycie - Pamiętaj o ustawieniu kluczy API w .env!
    # Te wartości powinny być pobierane z interfejsu użytkownika w aplikacji Streamlit
    test_keyword = "narzędzia do marketingu online"
    test_client_domain = "mojadomena.pl" # Zmień na domenę, którą chcesz analizować
    test_client_industry = "Marketing cyfrowy dla MŚP"

    print(f"Uruchamianie testowej analizy dla: '{test_keyword}', domena: '{test_client_domain}'")

    if not serp_client or not llm_client:
        print("Nie można uruchomić testu, ponieważ klienci API nie są skonfigurowani.")
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
