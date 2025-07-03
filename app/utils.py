# --- START OF FILE utils.py ---
# Wersja 2.0 - Gruntownie przebudowany w celu implementacji Zadania #1 z planu naprawczego.
# Usunięto zbędną funkcję parse_serp_data_for_llm.
# Funkcja format_serp_for_llm_prompt została przebudowana, aby tworzyć kompletny,
# bogaty w informacje kontekst dla LLM bezpośrednio z surowych danych SERP.

import json
from urllib.parse import urlparse

def get_domain_from_url(url):
    """Pomocnicza funkcja do wyciągania domeny z URL."""
    if not url:
        return "N/A"
    try:
        return urlparse(url).netloc.replace('www.', '')
    except Exception:
        return "N/A"

def format_serp_for_llm_prompt(raw_serp_data: dict, client_domain: str) -> str:
    """
    Formatuje surowe dane SERP w szczegółowy, ustrukturyzowany tekst
    przeznaczony dla zaawansowanego promptu LLM.

    Args:
        raw_serp_data: Słownik zawierający pełne, surowe dane z API SerpData.
        client_domain: Domena klienta do analizy.

    Returns:
        Sformatowany string gotowy do wstawienia do promptu LLM.
    """
    results = raw_serp_data.get("results", {})
    if not results:
        return "Błąd: Brak klucza 'results' w danych SERP."

    # --- Ekstrakcja kluczowych danych z zabezpieczeniami ---
    query = results.get("query", "N/A")
    snippets_data = results.get("snippets_data", {})

    # AI Overview
    ai_overview = snippets_data.get("ai_overview", {}) if isinstance(snippets_data, dict) else {}
    ai_overview_text = ai_overview.get("text", "Brak wygenerowanego tekstu AI Overview.") if isinstance(ai_overview, dict) else "Brak danych AI Overview."
    ai_overview_sources = ai_overview.get("sources", []) if isinstance(ai_overview, dict) else []

    # Organic Results
    organic_results = results.get("organic_results", [])

    # People Also Ask
    paa_data = snippets_data.get("people_also_ask", {}) if isinstance(snippets_data, dict) else {}
    paa_questions = paa_data.get("questions", []) if isinstance(paa_data, dict) else []

    # Related Searches
    related_searches_data = snippets_data.get("related_searches", {}) if isinstance(snippets_data, dict) else {}
    related_searches = related_searches_data.get("queries", []) if isinstance(related_searches_data, dict) else []


    # --- Budowanie stringa dla promptu ---
    prompt_lines = [
        "--- AI OVERVIEW ANALYSIS INPUT ---",
        "",
        f"**Query:** \"{query}\"",
        f"**Client Domain:** \"{client_domain}\"",
        "",
        "---",
        "",
        "**AI Overview Main Text:**",
        ai_overview_text,
        "",
        "**AI Overview Sources (with snippets):**"
    ]

    if ai_overview_sources:
        for i, source in enumerate(ai_overview_sources, 1):
            domain = get_domain_from_url(source.get("url"))
            prompt_lines.append(f"- Source {i}: {{title: \"{source.get('title', 'N/A')}\", domain: \"{domain}\", snippet: \"{source.get('snippet', 'N/A')}\"}}")
    else:
        prompt_lines.append("- Brak źródeł AI Overview.")

    prompt_lines.append("\n**Top 10 Organic Results:**")
    if organic_results:
        for i, res in enumerate(organic_results[:10], 1): # Ogranicz do top 10
            domain = res.get('domain', 'N/A')
            prompt_lines.append(f"- Rank {i}: {{title: \"{res.get('title', 'N/A')}\", domain: \"{domain}\", url: \"{res.get('url', 'N/A')}\"}}")
    else:
        prompt_lines.append("- Brak wyników organicznych.")

    prompt_lines.append("\n**People Also Ask (with answers):**")
    if paa_questions:
        for i, q in enumerate(paa_questions, 1):
            question_text = q.get("text", "Brak tekstu pytania")
            answer_text = q.get("answer", "Brak gotowej odpowiedzi")
            answer_source = q.get("source", {}).get("domain", "N/A")
            prompt_lines.append(f"- Question {i}: \"{question_text}\"")
            prompt_lines.append(f"  - Answer: \"{answer_text}\" (Source: {answer_source})")
    else:
        prompt_lines.append("- Brak pytań w sekcji People Also Ask.")

    prompt_lines.append("\n**Related Searches:**")
    if related_searches:
        for search_term in related_searches:
            prompt_lines.append(f"- \"{search_term}\"")
    else:
        prompt_lines.append("- Brak powiązanych wyszukiwań.")

    prompt_lines.append("\n--- END OF DATA ---")

    return "\n".join(prompt_lines)


if __name__ == '__main__':
    # Przykład użycia z realistycznymi danymi testowymi
    example_serp_json_string = """
    {
      "results": {
        "query": "najlepsze oprogramowanie CRM",
        "snippets_data": {
          "ai_overview": {
            "text": "Najlepsze oprogramowanie CRM dla małych firm to takie, które oferuje zarządzanie kontaktami, automatyzację sprzedaży i wsparcie klienta. Wiele opcji, takich jak CRM Hero i TopCRM, dostarcza rankingi i porównania funkcji, pomagając w podjęciu decyzji.",
            "sources": [
              {"title": "Co to jest CRM i jak działa? Przewodnik 2024", "url": "https://www.crmhero.com/guide", "snippet": "CRM, czyli Customer Relationship Management, to strategia i narzędzia do zarządzania interakcjami z klientami..."},
              {"title": "Ranking CRM 2024 - TOP 10 systemów", "url": "https://www.topcrm.pl/ranking", "snippet": "Nasz ranking CRM na 2024 rok uwzględnia ceny, funkcje i opinie użytkowników..."}
            ]
          },
          "people_also_ask": {
            "questions": [
              {"text": "Ile kosztuje system CRM?", "answer": "Ceny systemów CRM wahają się od darmowych planów do kilkuset złotych miesięcznie.", "source": {"domain": "cennik-crm.com"}},
              {"text": "Czy Excel to CRM?", "answer": "Choć Excel może służyć do przechowywania danych, nie posiada kluczowych funkcji CRM.", "source": {"domain": "crmhero.com"}}
            ]
          },
          "related_searches": {
            "queries": ["darmowy crm dla małej firmy", "ranking crm online"]
          }
        },
        "organic_results": [
          {"rank_inner": 1, "title": "Ranking CRM 2024 - TOP 10 systemów", "domain": "topcrm.pl", "url": "https://www.topcrm.pl/ranking"},
          {"rank_inner": 2, "title": "Porównanie systemów CRM | mojafirma.pl", "domain": "mojafirma.pl", "url": "https://mojafirma.pl/blog/crm-comparison"}
        ]
      }
    }
    """
    example_raw_data = json.loads(example_serp_json_string)
    example_client_domain = "mojafirma.pl"

    # Wywołaj nową funkcję
    formatted_prompt = format_serp_for_llm_prompt(example_raw_data, example_client_domain)

    print("--- Wygenerowany, sformatowany prompt dla LLM ---")
    print(formatted_prompt)

    # Test z brakującymi danymi
    print("\n\n--- Test z brakującymi danymi ---")
    minimal_raw_data = { "results": { "query": "minimal query" } }
    formatted_minimal_prompt = format_serp_for_llm_prompt(minimal_raw_data, "anydomain.com")
    print(formatted_minimal_prompt)
