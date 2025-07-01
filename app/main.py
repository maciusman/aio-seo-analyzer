import streamlit as st
import pandas as pd
import json
import sys
import os

# Dodaj główny katalog projektu (nadrzędny do 'app') do sys.path
# aby umożliwić importy z 'app.'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.analysis_engine import run_full_analysis, init_db, DEFAULT_LLM_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
from app.db_handler import get_serp_results_by_keyword # Do wyświetlania historii

# Inicjalizacja bazy danych przy starcie aplikacji (jeśli nie istnieje)
try:
    init_db()
except Exception as e:
    st.error(f"Błąd inicjalizacji bazy danych: {e}")

def display_analysis_results(results):
    """Wyświetla wyniki analizy LLM w sposób ustrukturyzowany."""
    if not results or not isinstance(results, dict):
        st.error("Brak wyników do wyświetlenia lub wyniki w nieprawidłowym formacie.")
        return

    if results.get("error"):
        st.error(f"Błąd podczas analizy: {results.get('error')}")
        if results.get("details"):
            st.json(results.get("details"))
        return

    st.subheader("Podsumowanie Zapytania")
    query_summary = results.get("query_summary", {})
    st.write(f"**Zapytanie:** {query_summary.get('query', 'N/A')}")
    st.write(f"**Domena Klienta:** {query_summary.get('client_domain', 'N/A')}")
    st.write(f"**Branża Klienta:** {query_summary.get('client_industry', 'N/A')}")

    if results.get("llm_model_used"):
        st.write(f"**Model LLM:** {results.get('llm_model_used')}")
        st.write(f"**Temperatura:** {results.get('llm_temperature_used', 'N/A')}")
        st.write(f"**Maks. tokenów:** {results.get('llm_max_tokens_used', 'N/A')}")

    st.write(f"**Klient w AI Overview:** {'Tak' if query_summary.get('client_present_in_ai_overview') else 'Nie'}")
    st.write(f"**Klient w Top 10 Organicznych:** {'Tak' if query_summary.get('client_present_in_top_10_organic') else 'Nie'}")

    st.subheader("Analiza AI Overview")
    ai_overview_analysis = results.get("ai_overview_analysis", {})
    if ai_overview_analysis.get("current_sources"):
        st.write("**Aktualne źródła w AI Overview:**")
        for i, source in enumerate(ai_overview_analysis["current_sources"], 1):
            st.write(f"{i}. {source.get('title', 'N/A')} ({source.get('domain', 'N/A')})")
    else:
        st.write("Brak zidentyfikowanych źródeł w AI Overview.")

    if ai_overview_analysis.get("opportunities_for_client"):
        st.write("**Możliwości dla klienta w AI Overview:**")
        for opp in ai_overview_analysis["opportunities_for_client"]:
            st.markdown(f"- {opp}")

    if ai_overview_analysis.get("potential_content_formats"):
        st.write("**Sugerowane formaty treści:**")
        st.markdown(", ".join(ai_overview_analysis["potential_content_formats"]))


    st.subheader("Krajobraz Konkurencji")
    competitive_landscape = results.get("competitive_landscape", {})
    if competitive_landscape.get("key_competitors_in_ai_overview"):
        st.write("**Kluczowi konkurenci w AI Overview:**")
        st.markdown(", ".join(competitive_landscape["key_competitors_in_ai_overview"]))
    if competitive_landscape.get("key_competitors_in_organic"):
        st.write("**Kluczowi konkurenci w wynikach organicznych:**")
        st.markdown(", ".join(competitive_landscape["key_competitors_in_organic"]))

    st.subheader("Analiza Luk w Treści")
    content_gap_analysis = results.get("content_gap_analysis", {})
    if content_gap_analysis.get("unanswered_paa_questions"):
        st.write("**Pytania z PAA do zaadresowania:**")
        for q in content_gap_analysis["unanswered_paa_questions"]:
            st.markdown(f"- {q}")
    if content_gap_analysis.get("related_search_opportunities"):
        st.write("**Możliwości z powiązanych wyszukiwań:**")
        for rs in content_gap_analysis["related_search_opportunities"]:
            st.markdown(f"- {rs}")

    st.subheader("Rekomendacje Działań")
    actionable_recommendations = results.get("actionable_recommendations", {})
    for priority in ["priority_1", "priority_2", "priority_3"]:
        if actionable_recommendations.get(priority):
            st.markdown(f"**{priority.replace('_', ' ').capitalize()}:**")
            for rec in actionable_recommendations[priority]:
                st.markdown(f"- {rec}")

    st.subheader("Ogólne Podsumowanie")
    st.write(results.get("overall_summary", "Brak podsumowania."))

    return results # Zwracamy wyniki, aby można było je użyć do generowania raportu


def generate_text_report(analysis_results):
    """Generuje raport tekstowy/markdown na podstawie wyników analizy."""
    if not analysis_results or not isinstance(analysis_results, dict) or analysis_results.get("error"):
        return "Nie można wygenerować raportu: Brak poprawnych wyników analizy."

    report_lines = []

    report_lines.append(f"# Raport Analizy AI Overview & SERP")
    report_lines.append(f"Data wygenerowania: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\n---\n")

    query_summary = analysis_results.get("query_summary", {})
    report_lines.append(f"## Podsumowanie Zapytania")
    report_lines.append(f"- **Zapytanie:** {query_summary.get('query', 'N/A')}")
    report_lines.append(f"- **Domena Klienta:** {query_summary.get('client_domain', 'N/A')}")
    report_lines.append(f"- **Branża Klienta:** {query_summary.get('client_industry', 'N/A')}")
    # Dodajemy informację o użytym modelu, jeśli jest dostępna w wynikach.
    # Zakładając, że `llm_model_id` będzie dostępne w `query_summary` lub bezpośrednio w `analysis_results`
    # Ta informacja jest teraz dodawana w `run_full_analysis`
    if analysis_results.get("llm_model_used"):
        report_lines.append(f"- **Model LLM użyty:** {analysis_results.get('llm_model_used')}")
        report_lines.append(f"- **Temperatura:** {analysis_results.get('llm_temperature_used', 'N/A')}")
        report_lines.append(f"- **Maks. tokenów:** {analysis_results.get('llm_max_tokens_used', 'N/A')}")
    report_lines.append(f"- **Klient w AI Overview:** {'Tak' if query_summary.get('client_present_in_ai_overview') else 'Nie'}")
    report_lines.append(f"- **Klient w Top 10 Organicznych:** {'Tak' if query_summary.get('client_present_in_top_10_organic') else 'Nie'}")
    report_lines.append("\n")

    ai_overview_analysis = analysis_results.get("ai_overview_analysis", {})
    report_lines.append(f"## Analiza AI Overview")
    if ai_overview_analysis.get("current_sources"):
        report_lines.append("**Aktualne źródła w AI Overview:**")
        for i, source in enumerate(ai_overview_analysis["current_sources"], 1):
            report_lines.append(f"  {i}. {source.get('title', 'N/A')} ({source.get('domain', 'N/A')})")
    else:
        report_lines.append("Brak zidentyfikowanych źródeł w AI Overview.")

    if ai_overview_analysis.get("opportunities_for_client"):
        report_lines.append("\n**Możliwości dla klienta w AI Overview:**")
        for opp in ai_overview_analysis["opportunities_for_client"]:
            report_lines.append(f"- {opp}")

    if ai_overview_analysis.get("potential_content_formats"):
        report_lines.append("\n**Sugerowane formaty treści:**")
        report_lines.append(", ".join(ai_overview_analysis["potential_content_formats"]))
    report_lines.append("\n")

    competitive_landscape = analysis_results.get("competitive_landscape", {})
    report_lines.append(f"## Krajobraz Konkurencji")
    if competitive_landscape.get("key_competitors_in_ai_overview"):
        report_lines.append("**Kluczowi konkurenci w AI Overview:**")
        report_lines.append(", ".join(competitive_landscape["key_competitors_in_ai_overview"]))
    if competitive_landscape.get("key_competitors_in_organic"):
        report_lines.append("\n**Kluczowi konkurenci w wynikach organicznych:**")
        report_lines.append(", ".join(competitive_landscape["key_competitors_in_organic"]))
    report_lines.append("\n")

    content_gap_analysis = analysis_results.get("content_gap_analysis", {})
    report_lines.append(f"## Analiza Luk w Treści")
    if content_gap_analysis.get("unanswered_paa_questions"):
        report_lines.append("**Pytania z PAA do zaadresowania:**")
        for q in content_gap_analysis["unanswered_paa_questions"]:
            report_lines.append(f"- {q}")
    if content_gap_analysis.get("related_search_opportunities"):
        report_lines.append("\n**Możliwości z powiązanych wyszukiwań:**")
        for rs in content_gap_analysis["related_search_opportunities"]:
            report_lines.append(f"- {rs}")
    report_lines.append("\n")

    actionable_recommendations = analysis_results.get("actionable_recommendations", {})
    report_lines.append(f"## Rekomendacje Działań")
    for priority in ["priority_1", "priority_2", "priority_3"]:
        if actionable_recommendations.get(priority):
            report_lines.append(f"**{priority.replace('_', ' ').capitalize()}:**")
            for rec in actionable_recommendations[priority]:
                report_lines.append(f"- {rec}")
    report_lines.append("\n")

    report_lines.append(f"## Ogólne Podsumowanie")
    report_lines.append(analysis_results.get("overall_summary", "Brak podsumowania."))
    report_lines.append("\n---\n")
    report_lines.append("Raport wygenerowany przez Analizator AI Overview.")

    return "\n".join(report_lines)


def main():
    st.set_page_config(page_title="Analizator AI Overview", layout="wide")
    st.title("🔍 Analizator AI Overview & SERP")
    st.markdown("Wprowadź dane, aby przeanalizować obecność w AI Overview i uzyskać rekomendacje.")

    # Inicjalizacja stanu sesji
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'last_keyword' not in st.session_state:
        st.session_state.last_keyword = ""
    if 'error_message' not in st.session_state:
        st.session_state.error_message = None
    if 'available_llm_models' not in st.session_state:
        st.session_state.available_llm_models = []
    if 'default_llm_model_id' not in st.session_state:
        st.session_state.default_llm_model_id = "anthropic/claude-3.5-sonnet" # Domyślny, jeśli pobieranie zawiedzie

    # Pobierz listę modeli LLM przy pierwszym ładowaniu (lub jeśli jest pusta)
    # Robimy to tutaj, aby uniknąć wielokrotnego pobierania przy każdym przeładowaniu UI
    if not st.session_state.available_llm_models:
        try:
            from app.llm_client import OpenRouterClient # Uniknięcie problemów z importem na górze pliku przed inicjalizacją .env
            llm_api_client = OpenRouterClient()
            models_data = llm_api_client.get_available_models()
            if models_data:
                # Tworzymy listę ID modeli, można też dodać bardziej przyjazne nazwy, jeśli są dostępne
                st.session_state.available_llm_models = sorted([m.get("id") for m in models_data if m.get("id")])
                # Ustaw domyślny model, jeśli jest na liście, w przeciwnym razie pierwszy z listy
                if st.session_state.default_llm_model_id not in st.session_state.available_llm_models and st.session_state.available_llm_models:
                    st.session_state.default_llm_model_id = st.session_state.available_llm_models[0]
            else:
                st.warning("Nie udało się pobrać listy modeli LLM z OpenRouter. Używany będzie model domyślny.")
        except Exception as e:
            st.error(f"Błąd podczas pobierania listy modeli LLM: {e}")
            # Zapewnij, że available_llm_models jest listą, nawet jeśli pusta
            if not isinstance(st.session_state.available_llm_models, list):
                 st.session_state.available_llm_models = []


    with st.sidebar:
        st.header("🛠️ Panel Sterowania Analizą")

        with st.expander("Podstawowe Dane Wejściowe", expanded=True):
            keyword = st.text_input("Słowo kluczowe do analizy", placeholder="np. najlepsze oprogramowanie CRM")
            client_domain = st.text_input("Domena klienta", placeholder="np. mojafirma.pl")
            client_industry = st.text_input("Branża klienta", placeholder="np. Oprogramowanie SaaS")

            col1, col2 = st.columns(2)
            with col1:
                search_lang = st.selectbox("Język wyszukiwania", ["pl", "en", "de", "es", "fr"], index=0, key="search_lang")
            with col2:
                search_country = st.selectbox("Kraj wyszukiwania", ["PL", "US", "DE", "ES", "FR", "GB"], index=0, key="search_country")

        with st.expander("⚙️ Konfiguracja Modelu LLM"):
            if st.session_state.available_llm_models:
                try:
                    # Sprawdź, czy domyślny model jest na liście, jeśli nie, ustaw pierwszy dostępny
                    current_default_index = st.session_state.available_llm_models.index(st.session_state.default_llm_model_id) \
                        if st.session_state.default_llm_model_id in st.session_state.available_llm_models \
                        else 0
                except ValueError: # Jeśli default_llm_model_id nie ma na liście
                    current_default_index = 0

                selected_llm_model = st.selectbox(
                    "Wybierz model LLM",
                    options=st.session_state.available_llm_models,
                    index=current_default_index,
                    key="llm_model_select",
                    help="Lista modeli pobierana z OpenRouter. Wybierz model do analizy."
                )
            else:
                st.info("Ładowanie listy modeli LLM lub błąd pobierania. Używany model domyślny.")
                selected_llm_model = st.text_input("ID Modelu LLM (jeśli lista niezaładowana)", value=st.session_state.default_llm_model_id, key="llm_model_manual")

            llm_temperature = st.slider(
                "Temperatura LLM",
                min_value=0.0, max_value=2.0,
                value=0.5, step=0.1,
                key="llm_temp",
                help="Kreatywność modelu. Niższe wartości = bardziej deterministyczne odpowiedzi."
            )
            llm_max_tokens = st.number_input(
                "Maks. tokenów LLM",
                min_value=512, max_value=16384, # Zakres może zależeć od modelu
                value=4096, step=256,
                key="llm_max_tokens",
                help="Maksymalna długość odpowiedzi modelu. Dostosuj w zależności od potrzeb i możliwości modelu."
            )

        analyze_button = st.button("🚀 Rozpocznij Analizę", type="primary", use_container_width=True)

        if analyze_button:
            if not keyword or not client_domain or not client_industry:
                st.error("Proszę wypełnić wszystkie pola: Słowo kluczowe, Domena klienta i Branża klienta.")
                st.session_state.error_message = "Proszę wypełnić wszystkie pola."
                st.session_state.analysis_results = None
            else:
                st.session_state.error_message = None
                st.session_state.last_keyword = keyword
                # Użyj wybranego modelu lub domyślnego, jeśli lista nie jest dostępna
                model_to_use = selected_llm_model if st.session_state.available_llm_models else st.session_state.default_llm_model_id

                spinner_message = f"Trwa analiza dla słowa kluczowego: '{keyword}' przy użyciu modelu: '{model_to_use}'... To może potrwać kilka minut."
                with st.spinner(spinner_message):
                    try:
                        results = run_full_analysis(
                            keyword=keyword,
                            client_domain=client_domain,
                            client_industry=client_industry,
                            lang=search_lang,
                            country_code=search_country,
                            llm_model_id=model_to_use,
                            llm_temperature=llm_temperature,
                            llm_max_tokens=llm_max_tokens
                        )
                        st.session_state.analysis_results = results
                        if results and results.get("error"):
                             st.session_state.error_message = f"Błąd analizy: {results.get('error')}"
                        elif not results:
                             st.session_state.error_message = "Analiza nie zwróciła żadnych wyników."

                    except Exception as e:
                        st.error(f"Wystąpił nieoczekiwany błąd: {e}")
                        st.session_state.analysis_results = {"error": "Unexpected Exception", "details": str(e)}
                        st.session_state.error_message = f"Nieoczekiwany błąd: {e}"

        st.markdown("---")
        st.caption("Upewnij się, że w pliku `.env` znajdują się poprawne klucze API dla `SERPDATA_API_KEY` oraz `OPENROUTER_API_KEY`.")


    if st.session_state.error_message and not st.session_state.analysis_results:
        st.error(st.session_state.error_message)

    if st.session_state.analysis_results:
        st.header(f"Wyniki Analizy dla: \"{st.session_state.last_keyword}\"")
        displayed_results = display_analysis_results(st.session_state.analysis_results) # display_analysis_results teraz zwraca wyniki

        if displayed_results and not displayed_results.get("error"): # Jeśli są wyniki i nie ma błędu
            st.markdown("---")
            st.subheader("📋 Wygeneruj Raport Tekstowy")
            if st.button("Generuj Raport do Skopiowania", key="generate_report_button"):
                report_text = generate_text_report(displayed_results)
                st.text_area("Raport (Markdown):", value=report_text, height=400)
                st.download_button(
                    label="Pobierz Raport jako .txt",
                    data=report_text,
                    file_name=f"raport_ai_overview_{st.session_state.last_keyword.replace(' ','_')}.txt",
                    mime="text/plain"
                )
    else:
        st.info("Wprowadź dane i kliknij 'Rozpocznij Analizę', aby zobaczyć wyniki.")

    # Opcjonalnie: Wyświetlanie historii poprzednich analiz dla danego słowa kluczowego
    # if st.session_state.last_keyword:
    #     with st.expander(f"Historia analiz dla '{st.session_state.last_keyword}'"):
    #         previous_serps = get_serp_results_by_keyword(st.session_state.last_keyword)
    #         if previous_serps:
    #             for i, serp_record in enumerate(previous_serps[:5]): # Pokaż ostatnie 5
    #                 st.write(f"Analiza z dnia: {serp_record['search_datetime']}")
    #                 # Można dodać przycisk do załadowania pełnej analizy LLM dla tego SERP
    #                 # st.json(json.loads(serp_record['raw_serp_data'])['results']['ai_overview']) # Przykład
    #         else:
    #             st.write("Brak wcześniejszych analiz dla tego słowa kluczowego.")


if __name__ == "__main__":
    main()
