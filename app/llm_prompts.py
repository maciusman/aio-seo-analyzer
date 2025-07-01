# Moduł do przechowywania szablonów promptów LLM

# Ten prompt jest oparty na przykładzie z dokumentu planistycznego
# FAZA 3: Szczegółowe Specyfikacje Techniczne -> 3.2 ARCHITEKTURA PROMPTÓW LLM
# Został dostosowany, aby oczekiwać konkretnych informacji z `format_serp_for_llm_prompt`
# oraz zwracać JSON zgodny ze schematem bazy danych.

BASE_AI_OVERVIEW_ANALYSIS_PROMPT = """
Przeanalizuj poniższe dane SERP dla zapytania "{query}" dotyczącego domeny klienta "{client_domain}", która działa w branży "{client_industry}".
Twoim celem jest zidentyfikowanie możliwości dla klienta w kontekście AI Overview oraz ogólnej strategii SEO.

Dane SERP:
{formatted_serp_data}

Przeanalizuj powyższe informacje i zwróć odpowiedź WYŁĄCZNIE w formacie JSON.
Nie dodawaj żadnych wyjaśnień ani tekstu przed lub po JSONie.
Struktura JSON powinna być następująca:

{{
  "query_summary": {{
    "query": "{query}",
    "client_domain": "{client_domain}",
    "client_industry": "{client_industry}",
    "client_present_in_ai_overview": boolean, // Czy domena klienta jest w źródłach AI Overview?
    "client_present_in_top_10_organic": boolean // Czy domena klienta jest w top 10 organicznych?
  }},
  "ai_overview_analysis": {{
    "current_sources": [ // Lista domen i tytułów obecnych w AI Overview
      {{ "domain": "example.com", "title": "Example Title" }}
    ],
    "opportunities_for_client": [ // Konkretne, aktywne sugestie dla klienta
      "Sugestia 1: Stwórz szczegółowy artykuł na temat X, ponieważ brakuje go w obecnych źródłach AI Overview.",
      "Sugestia 2: Zaktualizuj istniejący artykuł Y, aby lepiej odpowiadał na potrzeby użytkowników widoczne w PAA."
    ],
    "potential_content_formats": [ // Sugerowane formaty treści
        "Blog post", "FAQ page", "Infographic", "Video tutorial"
    ]
  }},
  "competitive_landscape": {{
    "key_competitors_in_ai_overview": [ // Domeny konkurentów w AI Overview
        "competitor1.com", "competitor2.com"
    ],
    "key_competitors_in_organic": [ // Domeny konkurentów w top 10 organicznych
        "competitor3.com", "competitor4.com"
    ],
    "client_strengths_relative_to_competitors": [], // Jeśli są widoczne
    "client_weaknesses_relative_to_competitors": [] // Jeśli są widoczne
  }},
  "content_gap_analysis": {{
    "unanswered_paa_questions": [ // Pytania z PAA, na które klient mógłby odpowiedzieć
      "Pytanie PAA 1", "Pytanie PAA 2"
    ],
    "related_search_opportunities": [ // Tematy z powiązanych wyszukiwań do pokrycia
      "Temat powiązany 1", "Temat powiązany 2"
    ]
  }},
  "actionable_recommendations": {{
    "priority_1": [ // Najważniejsze działania
      "Stwórz treść X, aby wypełnić lukę w AI Overview."
    ],
    "priority_2": [
      "Zoptymalizuj istniejącą stronę Y pod kątem semantycznym."
    ],
    "priority_3": [
      "Monitoruj domenę Z, która często pojawia się w AI Overview."
    ]
  }},
  "overall_summary": "Krótkie podsumowanie (2-3 zdania) głównych wniosków i najważniejszej rekomendacji."
}}

Instrukcje dotyczące wypełniania JSON:
- `client_present_in_ai_overview`: Ustaw na `true` jeśli `client_domain` znajduje się wśród URLi źródeł AI Overview, w przeciwnym razie `false`.
- `client_present_in_top_10_organic`: Ustaw na `true` jeśli `client_domain` znajduje się wśród URLi top 10 wyników organicznych, w przeciwnym razie `false`.
- `ai_overview_analysis.current_sources`: Wylistuj domeny i tytuły stron, które są aktualnie źródłami dla AI Overview.
- `opportunities_for_client`: Podaj konkretne, aktywne sugestie dla klienta, jak może dostać się do AI Overview lub poprawić swoją pozycję.
- `key_competitors_in_ai_overview`: Wymień domeny konkurentów (inne niż `client_domain`) znalezione w źródłach AI Overview.
- `key_competitors_in_organic`: Wymień domeny konkurentów (inne niż `client_domain`) znalezione w top 10 wyników organicznych.
- `unanswered_paa_questions`: Wylistuj pytania z sekcji "People Also Ask", na które klient mógłby stworzyć wartościowe odpowiedzi.
- `related_search_opportunities`: Wskaż tematy z "Related Searches", które klient mógłby wykorzystać do stworzenia nowych treści lub rozbudowy istniejących.
- `actionable_recommendations`: Podziel rekomendacje na priorytety. Powinny być konkretne i wykonalne.
- `overall_summary`: Krótkie, zwięzłe podsumowanie.

Pamiętaj, aby odpowiedź była TYLKO JSONEM.
"""

# Można tu dodać inne szablony promptów w przyszłości, np.:
# PROMPT_CONTENT_STRATEGY = """..."""
# PROMPT_COMPETITIVE_ANALYSIS = """..."""

def get_ai_overview_analysis_prompt(query, client_domain, client_industry, formatted_serp_data):
    """Formatuj główny prompt analizy AI Overview danymi."""
    return BASE_AI_OVERVIEW_ANALYSIS_PROMPT.format(
        query=query,
        client_domain=client_domain,
        client_industry=client_industry,
        formatted_serp_data=formatted_serp_data
    )

if __name__ == '__main__':
    # Przykład użycia
    example_query = "najlepsze oprogramowanie CRM"
    example_domain = "mojafirma.pl"
    example_industry = "SaaS dla małych firm"
    example_serp_data = """
    Analizuję SERP dla zapytania: "najlepsze oprogramowanie CRM"
    Domena klienta: mojafirma.pl

    Źródła AI Overview:
      1. Tytuł: Co to jest CRM?, URL: crmhero.com/co-to-jest-crm
      2. Tytuł: Ranking CRM 2024, URL: topcrm.pl/ranking

    Top 10 wyników organicznych:
      1. Tytuł: Najlepszy CRM dla Ciebie, URL: crmhero.com/najlepszy-crm
      2. Tytuł: Porównanie CRM, URL: mojafirma.pl/blog/crm (Klient)

    Uwaga: Domena klienta (mojafirma.pl) JEST obecna w top 10 wyników organicznych.

    People Also Ask:
      - Jakie są rodzaje CRM?
      - Ile kosztuje CRM?

    Related Searches:
      - darmowy crm
      - crm dla handlowca
    """

    prompt = get_ai_overview_analysis_prompt(
        example_query,
        example_domain,
        example_industry,
        example_serp_data
    )
    print(prompt)
