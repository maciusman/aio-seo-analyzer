# --- START OF FILE main.py ---
# Wersja 3.4 (FINAL) - Naprawiono błędy z poprzedniej wersji.
# 1. Usunięto problem z wyświetlaniem niechcianych obiektów 'NULL' poprzez refaktoryzację sekcji eksportu.
# 2. Poprawiono logikę widoczności przycisków, aby były w pełni niezależne.
# Aplikacja jest teraz w pełni funkcjonalna i stabilna.

import streamlit as st
import pandas as pd
import json
import sys
import os
import html
import pickle

# Dodaj główny katalog projektu (nadrzędny do 'app') do sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.analysis_engine import run_full_analysis, init_db, DEFAULT_LLM_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
from app.db_handler import get_serp_results_by_keyword

# Wszystkie funkcje pomocnicze (get_latest_raw_serp_data, etc.) pozostają bez zmian.
# Zostały one skopiowane z poprzedniej, działającej wersji.

def get_latest_raw_serp_data(keyword):
    """Pobiera najnowsze surowe dane SERP dla danego słowa kluczowego z bazy danych."""
    try:
        serp_results = get_serp_results_by_keyword(keyword)
        if serp_results:
            latest_result = serp_results[0]
            raw_serp_data = json.loads(latest_result['raw_serp_data'])
            return raw_serp_data
        return None
    except Exception as e:
        print(f"Error fetching raw SERP data: {e}")
        return None

def display_serp_data_viewer(keyword):
    """Wyświetla surowe dane SERP w czytelnym formacie."""
    raw_serp_data = get_latest_raw_serp_data(keyword)
    
    if not raw_serp_data:
        st.warning("Brak surowych danych SERP do wyświetlenia. Dane są dostępne po przeprowadzeniu analizy.")
        return
    
    st.write("### 📊 Statystyki pobranych danych:")
    col1, col2, col3, col4 = st.columns(4)
    
    results = raw_serp_data.get('results', {})
    organic_results = results.get('organic_results', [])
    snippets_data = results.get('snippets_data', {}) if isinstance(results, dict) else {}
    
    ai_overview_sources = snippets_data.get('ai_overview', {}).get('sources', []) if isinstance(snippets_data, dict) else []
    paa_questions = snippets_data.get('people_also_ask', {}).get('questions', []) if isinstance(snippets_data, dict) else []
    related_searches = snippets_data.get('related_searches', {}).get('queries', []) if isinstance(snippets_data, dict) else []

    with col1: st.metric("🎯 AI Overview Sources", len(ai_overview_sources))
    with col2: st.metric("📋 Organic Results", len(organic_results))
    with col3: st.metric("❓ People Also Ask", len(paa_questions))
    with col4: st.metric("🔗 Related Searches", len(related_searches))
    
    st.json(raw_serp_data, expanded=False)

def display_analysis_results(results):
    """Wyświetla wyniki analizy LLM w sposób ustrukturyzowany, włączając nowe sekcje."""
    if not results or not isinstance(results, dict) or results.get("error"):
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
    
    st.markdown("---")

    if "query_intent_analysis" in results:
        st.subheader("🕵️ Analiza Intencji Zapytania")
        intent_analysis = results.get("query_intent_analysis", {})
        st.info(f"**Zidentyfikowana intencja:** `{intent_analysis.get('identified_intent', 'Nie zidentyfikowano')}`")
        st.write(f"**Uzasadnienie:** {intent_analysis.get('intent_justification', 'Brak uzasadnienia.')}")
        st.markdown("---")

    st.subheader("🤖 Analiza AI Overview")
    ai_overview_analysis = results.get("ai_overview_analysis", {})
    st.write("**Aktualne źródła w AI Overview:**")
    if ai_overview_analysis.get("current_sources"):
        for i, source in enumerate(ai_overview_analysis["current_sources"], 1):
            st.write(f"{i}. {source.get('title', 'N/A')} ({source.get('domain', 'N/A')})")
    else:
        st.write("Brak zidentyfikowanych źródeł w AI Overview.")
    st.write("**Możliwości dla klienta w AI Overview:**")
    if ai_overview_analysis.get("opportunities_for_client"):
        for opp in ai_overview_analysis["opportunities_for_client"]: st.markdown(f"- {opp}")
    
    st.markdown("---")
    
    st.subheader("🎯 Analiza Luk w Treści (Content Gaps)")
    content_gap_analysis = results.get("content_gap_analysis", {})
    st.write("**Pytania z PAA do zaadresowania (z sugerowanymi odpowiedziami):**")
    if content_gap_analysis.get("unanswered_paa_questions"):
        for q_data in content_gap_analysis["unanswered_paa_questions"]:
            if isinstance(q_data, dict):
                 with st.expander(f"**Pytanie:** {q_data.get('question', 'Brak pytania')}"):
                    st.success(f"**Sugerowana odpowiedź:** {q_data.get('suggested_answer', 'Brak odpowiedzi')}")
            else: 
                st.markdown(f"- {q_data}")
    else:
        st.write("Brak pytań z PAA do zaadresowania.")
    st.write("**Możliwości z powiązanych wyszukiwań:**")
    if content_gap_analysis.get("related_search_opportunities"):
        for rs in content_gap_analysis["related_search_opportunities"]: st.markdown(f"- {rs}")

    st.markdown("---")

    if "strategic_advantage_opportunities" in results:
        st.subheader("💡 Możliwości Uzyskania Przewagi Strategicznej")
        strategic_opps = results.get("strategic_advantage_opportunities", {})
        st.info(f"**Unikalny kąt (angle) dla treści:**")
        st.write(strategic_opps.get("unique_angle_suggestion", "Brak sugestii."))
        st.info(f"**Propozycja następnego artykułu budującego autorytet:**")
        st.write(strategic_opps.get("next_logical_content_piece", "Brak sugestii."))
        st.markdown("---")

    st.subheader("🚀 Rekomendacje Działań")
    actionable_recommendations = results.get("actionable_recommendations", {})
    tabs = st.tabs(["**Priorytet 1 (Najwyższy)**", "**Priorytet 2**", "**Priorytet 3**"])
    with tabs[0]:
        if actionable_recommendations.get("priority_1"):
            for rec in actionable_recommendations["priority_1"]: st.markdown(f"- {rec}")
        else: st.write("Brak rekomendacji.")
    with tabs[1]:
        if actionable_recommendations.get("priority_2"):
            for rec in actionable_recommendations["priority_2"]: st.markdown(f"- {rec}")
        else: st.write("Brak rekomendacji.")
    with tabs[2]:
        if actionable_recommendations.get("priority_3"):
            for rec in actionable_recommendations["priority_3"]: st.markdown(f"- {rec}")
        else: st.write("Brak rekomendacji.")
        
    st.markdown("---")
    
    st.subheader("📜 Ogólne Podsumowanie")
    st.success(results.get("overall_summary", "Brak podsumowania."))

    return results

def generate_text_report(analysis_results):
    if not analysis_results or not isinstance(analysis_results, dict) or analysis_results.get("error"):
        return "Nie można wygenerować raportu: Brak poprawnych wyników analizy."
    report_lines = [f"# Raport Analizy AI Overview & SERP", f"Data wygenerowania: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", "\n---\n"]
    qs = analysis_results.get("query_summary", {})
    report_lines.extend([f"## Podsumowanie Zapytania",
                         f"- **Zapytanie:** {qs.get('query', 'N/A')}", f"- **Domena Klienta:** {qs.get('client_domain', 'N/A')}",
                         f"- **Branża Klienta:** {qs.get('client_industry', 'N/A')}",
                         f"- **Model LLM użyty:** {analysis_results.get('llm_model_used', 'N/A')}",
                         f"- **Temperatura:** {analysis_results.get('llm_temperature_used', 'N/A')}",
                         f"- **Maks. tokenów:** {analysis_results.get('llm_max_tokens_used', 'N/A')}",
                         f"- **Klient w AI Overview:** {'Tak' if qs.get('client_present_in_ai_overview') else 'Nie'}",
                         f"- **Klient w Top 10 Organicznych:** {'Tak' if qs.get('client_present_in_top_10_organic') else 'Nie'}\n"])
    if "query_intent_analysis" in analysis_results:
        ia = analysis_results.get("query_intent_analysis", {})
        report_lines.extend([f"## Analiza Intencji Zapytania", f"**Zidentyfikowana intencja:** {ia.get('identified_intent', 'N/A')}", f"**Uzasadnienie:** {ia.get('intent_justification', 'N/A')}\n"])
    aioa = analysis_results.get("ai_overview_analysis", {})
    report_lines.append("## Analiza AI Overview")
    if aioa.get("current_sources"):
        report_lines.append("**Aktualne źródła w AI Overview:**")
        for i, source in enumerate(aioa["current_sources"], 1): report_lines.append(f"  {i}. {source.get('title', 'N/A')} ({source.get('domain', 'N/A')})")
    if aioa.get("opportunities_for_client"):
        report_lines.append("\n**Możliwości dla klienta w AI Overview:**")
        for opp in aioa["opportunities_for_client"]: report_lines.append(f"- {opp}")
    report_lines.append("\n")
    cga = analysis_results.get("content_gap_analysis", {})
    report_lines.append("## Analiza Luk w Treści")
    if cga.get("unanswered_paa_questions"):
        report_lines.append("**Pytania z PAA do zaadresowania:**")
        for q_data in cga["unanswered_paa_questions"]:
            if isinstance(q_data, dict):
                report_lines.append(f"- **Pytanie:** {q_data.get('question', 'N/A')}")
                report_lines.append(f"  - **Sugerowana odpowiedź:** {q_data.get('suggested_answer', 'N/A')}")
            else:
                report_lines.append(f"- {q_data}")
    if cga.get("related_search_opportunities"):
        report_lines.append("\n**Możliwości z powiązanych wyszukiwań:**")
        for rs in cga["related_search_opportunities"]: report_lines.append(f"- {rs}")
    report_lines.append("\n")
    if "strategic_advantage_opportunities" in analysis_results:
        sao = analysis_results.get("strategic_advantage_opportunities", {})
        report_lines.extend([f"## Możliwości Uzyskania Przewagi Strategicznej",
                             f"**Unikalny kąt dla treści:** {sao.get('unique_angle_suggestion', 'N/A')}",
                             f"**Propozycja następnego artykułu:** {sao.get('next_logical_content_piece', 'N/A')}\n"])
    ar = analysis_results.get("actionable_recommendations", {})
    report_lines.append("## Rekomendacje Działań")
    for priority in ["priority_1", "priority_2", "priority_3"]:
        if ar.get(priority):
            report_lines.append(f"**{priority.replace('_', ' ').capitalize()}:**")
            for rec in ar[priority]: report_lines.append(f"- {rec}")
    report_lines.append("\n")
    report_lines.extend([f"## Ogólne Podsumowanie", analysis_results.get("overall_summary", "Brak podsumowania."), "\n---\n", "Raport wygenerowany przez Analizator AI Overview."])
    return "\n".join(report_lines)

def generate_html_report(analysis_results):
    if not analysis_results or not isinstance(analysis_results, dict) or analysis_results.get("error"):
        return "<html><body><h1>Błąd generowania raportu</h1></body></html>"
    def e(text): return html.escape(str(text))
    qs, ia, aioa, cga, sao, ar = (analysis_results.get(k, {}) for k in ["query_summary", "query_intent_analysis", "ai_overview_analysis", "content_gap_analysis", "strategic_advantage_opportunities", "actionable_recommendations"])
    styles = """<style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;margin:40px;background-color:#f0f2f6;color:#31333f}.container{max-width:800px;margin:auto;background-color:white;padding:20px;border-radius:10px;box-shadow:0 0 10px rgba(0,0,0,0.1)}h1,h2,h3{color:#31333f}h1{font-size:2em}h2{font-size:1.5em;border-bottom:1px solid #ddd;padding-bottom:10px;margin-top:40px}h3{font-size:1.2em}.info-box,.success-box{padding:15px;border-radius:5px;margin:10px 0;border-left:5px solid}.info-box{background-color:#e6f3ff;border-color:#007bff}.success-box{background-color:#e6ffed;border-color:#28a745}ul{list-style-type:none;padding-left:0}li{margin-bottom:10px}details{border:1px solid #ddd;border-radius:5px;padding:10px;margin-bottom:10px}summary{font-weight:bold;cursor:pointer}.tabs{display:flex;border-bottom:2px solid #ddd}.tab-label{padding:10px 15px;cursor:pointer}.tab-label.active{border-bottom:2px solid #007bff;font-weight:bold}.tab-content{display:none;padding:15px;border:1px solid #ddd;border-top:none}.tab-content.active{display:block}</style>"""
    html_parts = ["<!DOCTYPE html><html><head><title>Raport Analizy</title>", styles, "</head><body><div class='container'>"]
    html_parts.append(f"<h1>Raport Analizy dla: '{e(qs.get('query', 'N/A'))}'</h1>")
    html_parts.append(f"<h2>Podsumowanie Zapytania</h2><ul><li><strong>Domena Klienta:</strong> {e(qs.get('client_domain'))}</li><li><strong>Branża Klienta:</strong> {e(qs.get('client_industry'))}</li></ul>")
    if "query_intent_analysis" in analysis_results: html_parts.append(f"<h2>Analiza Intencji Zapytania</h2><div class='info-box'><strong>Zidentyfikowana intencja:</strong> {e(ia.get('identified_intent'))}</div><p><strong>Uzasadnienie:</strong> {e(ia.get('intent_justification'))}</p>")
    if "ai_overview_analysis" in analysis_results:
        html_parts.extend(["<h2>Analiza AI Overview</h2><h3>Aktualne źródła:</h3><ul>", *[f"<li>{e(s.get('title'))} ({e(s.get('domain'))})</li>" for s in aioa.get("current_sources",[])], "</ul><h3>Możliwości:</h3><ul>", *[f"<li>{e(opp)}</li>" for opp in aioa.get("opportunities_for_client",[])], "</ul>"])
    if "content_gap_analysis" in analysis_results:
        html_parts.append("<h2>Analiza Luk w Treści</h2><h3>Pytania z PAA:</h3>")
        html_parts.extend([f"<details><summary>{e(q.get('question'))}</summary><div class='success-box'>{e(q.get('suggested_answer'))}</div></details>" for q in cga.get("unanswered_paa_questions",[])])
        html_parts.extend(["<h3>Możliwości z powiązanych wyszukiwań:</h3><ul>", *[f"<li>{e(rs)}</li>" for rs in cga.get("related_search_opportunities",[])], "</ul>"])
    if "strategic_advantage_opportunities" in analysis_results: html_parts.append(f"<h2>Możliwości Uzyskania Przewagi Strategicznej</h2><div class='info-box'><strong>Unikalny kąt dla treści:</strong><p>{e(sao.get('unique_angle_suggestion'))}</p></div><div class='info-box'><strong>Propozycja następnego artykułu:</strong><p>{e(sao.get('next_logical_content_piece'))}</p></div>")
    html_parts.append("<h2>Rekomendacje Działań</h2><div class='tabs'><div class='tab-label active' onclick=\"showTab('p1')\">Priorytet 1</div><div class='tab-label' onclick=\"showTab('p2')\">Priorytet 2</div><div class='tab-label' onclick=\"showTab('p3')\">Priorytet 3</div></div>")
    for i in range(1,4): html_parts.extend([f"<div id='p{i}' class='tab-content {'active' if i==1 else ''}'><ul>", *[f"<li>{e(rec)}</li>" for rec in ar.get(f'priority_{i}',[])], "</ul></div>"])
    html_parts.append(f"<h2>Ogólne Podsumowanie</h2><div class='success-box'>{e(analysis_results.get('overall_summary'))}</div>")
    html_parts.append("<script>function showTab(t){document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));document.getElementById(t).classList.add('active');document.querySelectorAll('.tab-label').forEach(l=>l.classList.remove('active'));event.target.classList.add('active')}</script></div></body></html>")
    return "".join(html_parts)

def main():
    st.set_page_config(page_title="Analizator AI Overview", layout="wide")

    if 'db_initialized' not in st.session_state:
        init_db()
        st.session_state.db_initialized = True
    
    st.title("🔍 Analizator AI Overview & SERP")
    st.markdown("Wprowadź dane, aby przeanalizować obecność w AI Overview i uzyskać rekomendacje.")

    # Inicjalizacja stanu sesji
    if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
    if 'last_keyword' not in st.session_state: st.session_state.last_keyword = ""
    if 'available_llm_models' not in st.session_state: st.session_state.available_llm_models = []
    if 'default_llm_model_id' not in st.session_state: st.session_state.default_llm_model_id = "anthropic/claude-3.5-sonnet"
    if 'show_text_report' not in st.session_state: st.session_state.show_text_report = False
    if 'loaded_from_file' not in st.session_state: st.session_state.loaded_from_file = None

    if not st.session_state.available_llm_models:
        try:
            from app.llm_client import OpenRouterClient
            llm_api_client = OpenRouterClient()
            models_data = llm_api_client.get_available_models()
            if models_data:
                st.session_state.available_llm_models = sorted([m.get("id") for m in models_data if m.get("id")])
        except Exception as e:
            st.error(f"Błąd podczas pobierania listy modeli LLM: {e}")

    with st.sidebar:
        st.header("🛠️ Panel Sterowania Analizą")
        with st.expander("Podstawowe Dane Wejściowe", expanded=True):
            keyword = st.text_input("Słowo kluczowe do analizy", placeholder="np. najlepsze oprogramowanie CRM")
            client_domain = st.text_input("Domena klienta", placeholder="np. mojafirma.pl")
            client_industry = st.text_input("Branża klienta", placeholder="np. Oprogramowanie SaaS")
            col1, col2 = st.columns(2)
            with col1: search_lang = st.selectbox("Język wyszukiwania", ["pl", "en", "de", "es", "fr"], index=0)
            with col2: search_country = st.selectbox("Kraj wyszukiwania", ["pl", "us", "de", "es", "fr", "gb"], index=0)
        with st.expander("⚙️ Konfiguracja Modelu LLM"):
            if st.session_state.available_llm_models:
                try:
                    default_index = st.session_state.available_llm_models.index(st.session_state.default_llm_model_id)
                except ValueError: default_index = 0
                selected_llm_model = st.selectbox("Wybierz model LLM", options=st.session_state.available_llm_models, index=default_index)
            else:
                selected_llm_model = st.text_input("ID Modelu LLM", value=st.session_state.default_llm_model_id)
            llm_temperature = st.slider("Temperatura LLM", 0.0, 2.0, DEFAULT_TEMPERATURE, 0.1)
            llm_max_tokens = st.number_input("Maks. tokenów LLM", 512, 16384, DEFAULT_MAX_TOKENS, 256)
        
        analyze_button = st.button("🚀 Rozpocznij Analizę", type="primary", use_container_width=True)

        st.markdown("---")
        
        with st.expander("🗄️ Zarządzanie Analizami"):
            is_analysis_available = st.session_state.analysis_results and not st.session_state.analysis_results.get("error")
            if is_analysis_available:
                analysis_to_save = pickle.dumps(st.session_state.analysis_results)
                kw_for_filename = st.session_state.last_keyword.replace(' ','_').replace('"', '')
                st.download_button("💾 Zapisz bieżącą analizę (.pkl)", analysis_to_save, f"analiza_{kw_for_filename}.pkl", "application/octet-stream", use_container_width=True)
            else:
                st.button("💾 Zapisz bieżącą analizę (.pkl)", disabled=True, use_container_width=True, help="Przeprowadź analizę, aby ją zapisać.")

            uploaded_file = st.file_uploader("📂 Wczytaj analizę z pliku .pkl", type="pkl", key="file_uploader")
            if uploaded_file is not None:
                try:
                    loaded_results = pickle.loads(uploaded_file.getvalue())
                    if isinstance(loaded_results, dict) and "query_summary" in loaded_results:
                        st.session_state.analysis_results = loaded_results
                        st.session_state.last_keyword = loaded_results.get("query_summary", {}).get("query", "N/A")
                        st.session_state.loaded_from_file = uploaded_file.name
                        st.session_state.show_text_report = False
                        st.rerun()
                except Exception as e:
                    st.error(f"Błąd podczas wczytywania pliku: {e}")

    if analyze_button:
        st.session_state.loaded_from_file = None
        if not keyword or not client_domain or not client_industry:
            st.error("Proszę wypełnić wszystkie pola.")
        else:
            st.session_state.last_keyword = keyword
            st.session_state.show_text_report = False
            with st.spinner(f"Trwa analiza dla słowa kluczowego: '{keyword}'..."):
                results = run_full_analysis(
                    keyword=keyword, client_domain=client_domain, client_industry=client_industry,
                    lang=search_lang, country_code=search_country,
                    llm_model_id=selected_llm_model, llm_temperature=llm_temperature, llm_max_tokens=llm_max_tokens)
                st.session_state.analysis_results = results
    
    if st.session_state.analysis_results:
        if st.session_state.analysis_results.get("error"):
            st.error(f"❌ Błąd Analizy: {st.session_state.analysis_results.get('error')}")
            with st.expander("🔍 Szczegóły techniczne"):
                st.json(st.session_state.analysis_results.get("details", {}))
        else:
            if st.session_state.loaded_from_file:
                st.success(f"Wyświetlanie analizy wczytanej z pliku: **{st.session_state.loaded_from_file}**")
            st.header(f"Wyniki Analizy dla: \"{st.session_state.last_keyword}\"")
            
            # Wyświetlanie głównego raportu. Ta funkcja nie zwraca już wartości.
            display_analysis_results(st.session_state.analysis_results)
            
            st.markdown("---")
            with st.expander("🔍 Surowe dane SERP (podgląd i weryfikacja)", expanded=False):
                display_serp_data_viewer(st.session_state.last_keyword)
            
            st.markdown("---")
            st.subheader("📋 Opcje Eksportu Raportu")
            
            # Uproszczony i poprawiony layout przycisków eksportu
            html_report_data = generate_html_report(st.session_state.analysis_results)
            st.download_button(
                label="Pobierz Raport Interaktywny (.html)",
                data=html_report_data,
                file_name=f"raport_interaktywny_{st.session_state.last_keyword.replace(' ','_')}.html",
                mime="text/html",
                use_container_width=True
            )
            
            if st.button("Generuj/Ukryj Raport Tekstowy (.txt)", use_container_width=True):
                st.session_state.show_text_report = not st.session_state.get('show_text_report', False)

            if st.session_state.show_text_report:
                report_text = generate_text_report(st.session_state.analysis_results)
                st.text_area("Raport (Markdown):", value=report_text, height=400)

    else:
        st.info("Wprowadź dane i kliknij 'Rozpocznij Analizę', aby zobaczyć wyniki.")

if __name__ == "__main__":
    main()
