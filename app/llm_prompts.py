# --- START OF FILE llm_prompts.py ---

# Wersja 2.0 - Gruntownie przebudowany prompt w celu transformacji LLM
# z "wypełniacza danych" w "stratega SEO" poprzez nadanie roli,
# pogłębienie instrukcji analitycznych i dodanie sekcji strategicznych.

# Moduł do przechowywania szablonów promptów LLM

BASE_AI_OVERVIEW_ANALYSIS_PROMPT = """
JESTEŚ ŚWIATOWEJ KLASY STRATEGIEM SEO I ANALITYKIEM TREŚCI z 10-letnim doświadczeniem.
Twoją specjalizacją jest optymalizacja pod kątem Google AI Overview i identyfikacja luk w treści (content gaps).
Działasz w sposób metodyczny, opierając swoje wnioski WYŁĄCZNIE na dostarczonych poniżej DANYCH SERP. Nie wymyślasz informacji.
Twoim zadaniem jest głęboka synteza i interpretacja danych, aby dostarczyć klientowi precyzyjne, oparte na danych i gotowe do wdrożenia rekomendacje strategiczne.

Przeanalizuj poniższe dane SERP dla zapytania "{query}" dotyczącego domeny klienta "{client_domain}", która działa w branży "{client_industry}".

Dane SERP:
{formatted_serp_data}

Przeanalizuj powyższe informacje i zwróć odpowiedź WYŁĄCZNIE w formacie JSON.
Nie dodawaj żadnych wyjaśnień, komentarzy ani tekstu przed lub po bloku JSON. Odpowiedź musi być surowym, czystym JSONEM.
Struktura JSON powinna być następująca:

{{
  "query_summary": {{
    "query": "{query}",
    "client_domain": "{client_domain}",
    "client_industry": "{client_industry}",
    "client_present_in_ai_overview": boolean, // Ustaw na true, jeśli domena klienta jest w źródłach AI Overview
    "client_present_in_top_10_organic": boolean // Ustaw na true, jeśli domena klienta jest w top 10 organicznych
  }},
  "query_intent_analysis": {{
    "identified_intent": "string", // Określ intencję zapytania jako jedną z: 'Informational', 'Commercial Investigation', 'Transactional', 'Navigational'
    "intent_justification": "string" // Uzasadnij wybór intencji (1-2 zdania) na podstawie sformułowania zapytania i charakteru wyników w SERP.
  }},
  "ai_overview_analysis": {{
    "current_sources": [ // Wylistuj WSZYSTKIE domeny i tytuły stron, które są aktualnie źródłami dla AI Overview
      {{ "domain": "example.com", "title": "Example Title" }}
    ],
    "opportunities_for_client": [ // Przeanalizuj TREŚĆ snippetów ze źródeł AI Overview. Zidentyfikuj kluczowe pojęcia, dane i pytania, na które odpowiadają konkurenci, a których brakuje u klienta. Sformułuj konkretne propozycje rozbudowy treści, np. 'Dodać sekcję H2 «Porównanie X i Y», ponieważ ten temat jest poruszany w snippetach od konkurentów A i B.'
      "Sugestia 1: ...",
      "Sugestia 2: ..."
    ],
    "potential_content_formats": [ // Na podstawie analizy SERP, zasugeruj najbardziej obiecujące formaty treści
        "Blog post with expert quotes", "Detailed FAQ page", "Data-driven infographic", "Comparison table"
    ]
  }},
  "competitive_landscape": {{
    "key_competitors_in_ai_overview": [ // Wymień domeny konkurentów (inne niż client_domain) znalezione w źródłach AI Overview.
        "competitor1.com", "competitor2.com"
    ],
    "key_competitors_in_organic": [ // Wymień domeny konkurentów (inne niż client_domain) znalezione w top 10 organicznych.
        "competitor3.com", "competitor4.com"
    ],
    "client_strengths_relative_to_competitors": [ // Na podstawie TWARDYCH DANYCH z SERP (np. wyższa pozycja, obecność w AIO), wskaż konkretne mocne strony klienta względem konkurencji.
        "Przewaga 1: ..."
    ],
    "client_weaknesses_relative_to_competitors": [ // Na podstawie TWARDYCH DANYCH z SERP (np. brak w AIO, mniej szczegółowy tytuł), wskaż konkretne słabości klienta.
        "Słabość 1: ..."
    ]
  }},
  "content_gap_analysis": {{
    "unanswered_paa_questions": [ // Przejrzyj 'People Also Ask'. Wylistuj pytania, na które klient mógłby odpowiedzieć lepiej. Dla każdego pytania ZAPROPONUJ KRÓTKĄ, zwięzłą odpowiedź (2-3 zdania) w stylu Google, którą klient mógłby wdrożyć.
      {{ "question": "Pytanie PAA 1", "suggested_answer": "Sugerowana odpowiedź na pytanie 1." }},
      {{ "question": "Pytanie PAA 2", "suggested_answer": "Sugerowana odpowiedź na pytanie 2." }}
    ],
    "related_search_opportunities": [ // Przeanalizuj 'Related Searches'. Zidentyfikuj klastry tematyczne i zaproponuj tytuły NOWYCH artykułów lub konkretne sekcje do rozbudowy istniejących treści.
      "Propozycja tematu/tytułu 1", "Propozycja tematu/tytułu 2"
    ]
  }},
  "strategic_advantage_opportunities": {{
      "unique_angle_suggestion": "string", // Zaproponuj unikalny 'haczyk' (angle), który pozwoli klientowi się wyróżnić. Może to być dodanie case study, włączenie opinii eksperta, stworzenie oryginalnej infografiki, odpowiedź na kontrowersyjne pytanie lub zaprezentowanie danych w nowatorski sposób. Bądź kreatywny, ale realistyczny.
      "next_logical_content_piece": "string" // Bazując na intencji zapytania i analizie SERP, jaki jest następny, logiczny artykuł, który klient powinien stworzyć, aby zbudować autorytet tematyczny (topical authority) wokół tego zapytania?
  }},
  "actionable_recommendations": {{
    "priority_1": [ // Najważniejsze działania o największym potencjalnym wpływie, będące syntezą powyższych analiz.
      "Stwórz treść X, aby wypełnić lukę Y zidentyfikowaną w analizie AIO."
    ],
    "priority_2": [ // Działania ważne, ale o mniejszym priorytecie lub bardziej czasochłonne.
      "Zoptymalizuj istniejącą stronę Z, dodając sekcję FAQ z sugerowanymi odpowiedziami."
    ],
    "priority_3": [ // Działania długofalowe lub monitorujące.
      "Stwórz nowy artykuł na temat «...», aby zbudować autorytet tematyczny."
    ]
  }},
  "overall_summary": "string" // Napisz krótkie podsumowanie (2-3 zdania) dla osoby decyzyjnej (np. właściciela firmy), skupiając się na głównym wniosku i najważniejszej rekomendacji strategicznej.
}}
"""

def get_ai_overview_analysis_prompt(query, client_domain, client_industry, formatted_serp_data):
    """
    Formatuje główny, zaawansowany prompt analizy AI Overview, wstawiając dane specyficzne dla zapytania.
    """
    return BASE_AI_OVERVIEW_ANALYSIS_PROMPT.format(
        query=query,
        client_domain=client_domain,
        client_industry=client_industry,
        formatted_serp_data=formatted_serp_data
    )

if __name__ == '__main__':
    # Przykład użycia z nową, bogatszą strukturą danych wejściowych,
    # odzwierciedlającą dane, które prompt jest zaprojektowany, aby analizować.
    example_query = "najlepsze oprogramowanie CRM"
    example_domain = "mojafirma.pl"
    example_industry = "SaaS dla małych firm"
    
    # Ta przykładowa struktura danych odzwierciedla to, co funkcja formatująca
    # powinna przekazywać do promptu - zawiera snippety, odpowiedzi PAA itp.
    example_serp_data = """
--- AI OVERVIEW ANALYSIS INPUT ---

**Query:** "najlepsze oprogramowanie CRM"
**Client Domain:** "mojafirma.pl"
**Client Industry:** "SaaS dla małych firm"

**AI Overview Main Text:**
"Najlepsze oprogramowanie CRM dla małych firm to takie, które oferuje zarządzanie kontaktami, automatyzację sprzedaży i wsparcie klienta. Wiele opcji, takich jak CRM Hero i TopCRM, dostarcza rankingi i porównania funkcji, pomagając w podjęciu decyzji."

**AI Overview Sources (with snippets):**
- Source 1: {title: "Co to jest CRM i jak działa? Przewodnik 2024", domain: "crmhero.com", snippet: "CRM, czyli Customer Relationship Management, to strategia i narzędzia do zarządzania interakcjami z klientami. Kluczowe funkcje to baza kontaktów, historia interakcji i raportowanie."}
- Source 2: {title: "Ranking CRM 2024 - TOP 10 systemów", domain: "topcrm.pl", snippet: "Nasz ranking CRM na 2024 rok uwzględnia ceny, funkcje i opinie użytkowników. Sprawdź, który system CRM najlepiej pasuje do Twojej firmy."}
- Source 3: {title: "Jak wybrać CRM? Poradnik dla początkujących", domain: "innakonkurencja.pl", snippet: "Wybierając CRM, zwróć uwagę na skalowalność, integracje z innymi narzędziami oraz łatwość obsługi interfejsu. Darmowe wersje często mają ograniczenia."}

**Top 10 Organic Results:**
- Rank 1: {title: "Ranking CRM 2024 - TOP 10 systemów", domain: "topcrm.pl", url: "..."}
- Rank 2: {title: "Porównanie systemów CRM | mojafirma.pl", domain: "mojafirma.pl", url: "..."}
- Rank 3: {title: "Co to jest CRM i jak działa? Przewodnik 2024", domain: "crmhero.com", url: "..."}
- ...

**People Also Ask (with answers):**
- Question 1: "Ile kosztuje system CRM?"
  - Answer: "Ceny systemów CRM wahają się od darmowych planów z podstawowymi funkcjami do kilkuset złotych miesięcznie za użytkownika w zaawansowanych wersjach."
  - Source: "cennik-crm.com"
- Question 2: "Czy Excel to CRM?"
  - Answer: "Choć Excel może służyć do przechowywania danych klientów, nie posiada kluczowych funkcji CRM, takich jak automatyzacja, śledzenie interakcji i zaawansowane raportowanie."
  - Source: "crmhero.com"

**Related Searches:**
- "darmowy crm dla małej firmy"
- "ranking crm online"
- "wdrożenie crm krok po kroku"
- "system crm zintegrowany z pocztą"
--- END OF DATA ---
    """

    prompt = get_ai_overview_analysis_prompt(
        example_query,
        example_domain,
        example_industry,
        example_serp_data
    )
    print("--- GENERATED PROMPT FOR LLM ---")
    print(prompt)

# --- END OF FILE llm_prompts.py ---
