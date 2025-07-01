# Dokumentacja Użytkownika i Techniczna: Analizator AI Overview & SERP

## 1. Wprowadzenie i Cel Projektu

### 1.1. Co to jest Analizator AI Overview & SERP?

Analizator AI Overview & SERP to specjalistyczna aplikacja stworzona, aby pomóc w zrozumieniu i optymalizacji widoczności stron internetowych w wynikach wyszukiwania Google, ze szczególnym naciskiem na nową funkcję "AI Overview" (Przegląd AI). Narzędzie to automatyzuje proces zbierania danych z wyników wyszukiwania (SERP), analizuje je przy użyciu zaawansowanych modeli językowych (LLM) i dostarcza konkretnych, praktycznych rekomendacji.

Głównym celem aplikacji jest umożliwienie użytkownikom, nawet tym bez głębokiej wiedzy technicznej z zakresu SEO, efektywnego konkurowania o czołowe pozycje w AI Overview oraz tradycyjnych wynikach organicznych.

### 1.2. Dla kogo jest ta aplikacja?

Aplikacja jest przeznaczona dla:
*   **Specjalistów SEO i marketerów**: Do głębszej analizy SERP, identyfikacji możliwości i tworzenia strategii contentowych.
*   **Właścicieli stron internetowych i blogerów**: Do samodzielnego monitorowania swojej widoczności i podejmowania działań optymalizacyjnych.
*   **Agencji marketingowych**: Jako narzędzie wspierające pracę z klientami i dostarczające wartościowych analiz.
*   **Każdego, kto chce zrozumieć, jak AI zmienia wyniki wyszukiwania** i jak się do tych zmian dostosować.

### 1.3. Główne cele analizy wykonywanej przez aplikację:

Analiza przeprowadzana przez aplikację ma na celu:

1.  **Zidentyfikowanie obecności w AI Overview**: Sprawdzenie, czy analizowana domena (lub jej konkurenci) pojawia się w sekcji AI Overview dla danego słowa kluczowego.
2.  **Analiza źródeł AI Overview**: Zrozumienie, jakie strony i jakie treści są wykorzystywane przez Google do generowania AI Overview.
3.  **Wykrywanie luk konkurencyjnych**: Wskazanie, gdzie konkurenci mają przewagę i jakie tematy lub typy treści są przez nich wykorzystywane do zdobywania widoczności w AI Overview.
4.  **Identyfikacja możliwości treściowych**: Sugerowanie tematów, pytań (np. z sekcji "People Also Ask" - PAA) i formatów treści, które mogą pomóc w zdobyciu lub poprawie pozycji w AI Overview.
5.  **Analiza krajobrazu konkurencji**: Określenie kluczowych konkurentów zarówno w AI Overview, jak i w tradycyjnych wynikach organicznych.
6.  **Dostarczenie konkretnych rekomendacji**: Podanie listy działań (z priorytetami), które użytkownik może podjąć, aby poprawić swoją widoczność.
7.  **Ocena ogólnej sytuacji**: Krótkie podsumowanie najważniejszych wniosków.

### 1.4. Jakie problemy rozwiązuje aplikacja?

*   **Brak widoczności w AI Overview**: Pomaga zrozumieć, dlaczego strona nie pojawia się w AI Overview i co można zrobić, aby to zmienić.
*   **Trudność w analizie SERP**: Automatyzuje zbieranie i wstępną interpretację złożonych danych z wyników wyszukiwania.
*   **Niepewność co do strategii contentowej**: Dostarcza pomysłów na nowe treści i optymalizację istniejących w kontekście AI Overview.
*   **Oszczędność czasu**: Znacząco skraca czas potrzebny na ręczną analizę wyników wyszukiwania i konkurencji.
*   **Dostosowanie do zmian w Google**: Pomaga reagować na ewolucję algorytmów wyszukiwarki, zwłaszcza w kontekście rosnącej roli AI.

## 2. Architektura i Sposób Działania Aplikacji

### 2.1. Główne komponenty aplikacji:

Aplikacja składa się z kilku kluczowych modułów, które współpracują ze sobą:

1.  **Interfejs Użytkownika (Streamlit)**: Plik `app/main.py`. Jest to główny punkt interakcji użytkownika z aplikacją. Pozwala na wprowadzanie danych, inicjowanie analizy i przeglądanie wyników.
2.  **Klient API SerpData (`app/serp_client.py`)**: Odpowiada za komunikację z zewnętrznym serwisem `serpdata.io` w celu pobrania aktualnych danych z wyników wyszukiwania Google (SERP) dla zadanego słowa kluczowego, języka i kraju.
3.  **Klient API OpenRouter (`app/llm_client.py`)**: Zarządza komunikacją z platformą `OpenRouter.ai`, która umożliwia dostęp do różnych modeli językowych (LLM) od różnych dostawców (np. OpenAI GPT, Anthropic Claude). Ten klient pobiera listę dostępnych modeli i wysyła do wybranego modelu przetworzone dane SERP w celu uzyskania analizy.
4.  **Silnik Analizy (`app/analysis_engine.py`)**: Centralny moduł orkiestrujący cały proces. Koordynuje pracę pozostałych komponentów: pobiera dane przez `SerpDataClient`, przetwarza je, przygotowuje specjalny "prompt" (instrukcję) dla modelu LLM, wysyła go przez `OpenRouterClient`, odbiera odpowiedź LLM, a następnie zapisuje wyniki.
5.  **Obsługa Bazy Danych (`app/db_handler.py`)**: Zarządza lokalną bazą danych SQLite (`ai_overview_analysis.db`). Przechowuje historię wyszukiwanych słów kluczowych, surowe dane SERP oraz wyniki analiz LLM. Pozwala to na późniejszy wgląd w historię i potencjalne śledzenie zmian w czasie.
6.  **Narzędzia Pomocnicze (`app/utils.py`)**: Zawiera funkcje do parsowania (przetwarzania) surowych danych SERP na format bardziej zrozumiały dla modeli LLM oraz do formatowania tych danych w ramach promptu.
7.  **Szablony Promptów LLM (`app/llm_prompts.py`)**: Przechowuje predefiniowane szablony instrukcji (promptów), które są wysyłane do modeli LLM. Te szablony kierują modelem, jakich informacji oczekujemy w analizie i w jakim formacie.

### 2.2. Przepływ danych i proces analizy (krok po kroku):

1.  **Użytkownik wprowadza dane**: W interfejsie Streamlit użytkownik podaje:
    *   Słowo kluczowe do analizy.
    *   Domenę swojej strony internetowej.
    *   Ogólną branżę, w której działa.
    *   Język i kraj dla wyników wyszukiwania.
    *   Wybiera model LLM z listy dostępnych modeli na OpenRouter.
    *   Ustawia parametry modelu LLM (temperatura, maksymalna liczba tokenów).
2.  **Inicjacja Analizy**: Użytkownik klika przycisk "Rozpocznij Analizę".
3.  **Pobieranie Danych SERP**:
    *   Silnik Analizy (`analysis_engine.py`) zleca `SerpDataClient` pobranie danych SERP dla zadanego słowa kluczowego, języka i kraju.
    *   `SerpDataClient` wysyła zapytanie do API `serpdata.io` i odbiera surowe dane w formacie JSON.
4.  **Zapis Danych SERP**:
    *   Silnik Analizy zapisuje pobrane surowe dane SERP oraz powiązane słowo kluczowe do lokalnej bazy danych SQLite za pomocą `db_handler.py`.
5.  **Przetwarzanie Danych SERP dla LLM**:
    *   Silnik Analizy używa funkcji z `utils.py` do przetworzenia surowych danych SERP. Ekstrahowane są kluczowe informacje, takie jak:
        *   Źródła użyte w AI Overview (jeśli istnieje).
        *   Lista wyników organicznych.
        *   Pytania z sekcji "People Also Ask" (PAA).
        *   Powiązane wyszukiwania.
    *   Te przetworzone dane są następnie formatowane w czytelny tekst, który będzie częścią promptu dla LLM.
6.  **Generowanie Promptu dla LLM**:
    *   Silnik Analizy, korzystając ze szablonu z `llm_prompts.py` oraz przetworzonych danych SERP, konstruuje szczegółowy prompt. Prompt zawiera również informacje o domenie klienta i jego branży. Instrukcja prosi model LLM o przeprowadzenie analizy i zwrócenie wyników w określonym formacie JSON.
7.  **Wysłanie Promptu do Modelu LLM**:
    *   Silnik Analizy przekazuje skonstruowany prompt oraz wybrane przez użytkownika ID modelu LLM (i jego parametry) do `OpenRouterClient`.
    *   `OpenRouterClient` wysyła zapytanie do API `OpenRouter.ai`.
8.  **Odbiór i Przetwarzanie Odpowiedzi LLM**:
    *   `OpenRouterClient` odbiera odpowiedź od modelu LLM (oczekiwany format to JSON).
    *   Odpowiedź jest przekazywana z powrotem do Silnika Analizy.
9.  **Zapis Wyników Analizy LLM**:
    *   Silnik Analizy zapisuje odpowiedź LLM (wyniki analizy) do bazy danych SQLite, powiązując ją z odpowiednim rekordem SERP. Zapisywane jest również ID użytego modelu.
10. **Wyświetlanie Wyników Użytkownikowi**:
    *   Wyniki analizy są przekazywane do interfejsu użytkownika (`main.py`).
    *   Streamlit dynamicznie aktualizuje stronę, prezentując użytkownikowi przetworzone wyniki w czytelnych sekcjach (np. Podsumowanie, Analiza AI Overview, Rekomendacje).
11. **Generowanie Raportu (opcjonalnie)**:
    *   Użytkownik może kliknąć przycisk, aby wygenerować raport tekstowy (w formacie Markdown) zawierający wszystkie kluczowe informacje z analizy. Raport ten można skopiować lub pobrać jako plik `.txt`.

Ten cykl powtarza się dla każdego nowego słowa kluczowego lub gdy użytkownik zdecyduje się ponownie przeanalizować to samo słowo kluczowe (np. po pewnym czasie, aby zobaczyć zmiany).

## 3. Instalacja i Konfiguracja Aplikacji

Aby uruchomić Analizator AI Overview & SERP lokalnie na swoim komputerze, postępuj zgodnie z poniższymi krokami.

### 3.1. Wymagania Wstępne:

*   **Python**: Upewnij się, że masz zainstalowanego Pythona w wersji 3.9 lub nowszej. Możesz go pobrać z [oficjalnej strony Python.org](https://www.python.org/downloads/). Podczas instalacji Pythona na Windows, zaznacz opcję "Add Python to PATH".
*   **PIP**: Narzędzie do zarządzania pakietami Pythona, zazwyczaj instalowane razem z Pythonem.
*   **Przeglądarka internetowa**: Do wyświetlania interfejsu aplikacji (np. Chrome, Firefox, Edge).
*   **Konto na serpdata.io**: Będziesz potrzebować klucza API z [serpdata.io](https://serpdata.io/) do pobierania danych SERP. Zarejestruj się i znajdź swój klucz API w panelu użytkownika.
*   **Konto na OpenRouter.ai**: Będziesz potrzebować klucza API z [OpenRouter.ai](https://openrouter.ai/) do korzystania z modeli LLM. Zarejestruj się, doładuj konto (niektóre modele są płatne) i skopiuj swój klucz API.

### 3.2. Pobieranie Plików Aplikacji:

Wszystkie pliki aplikacji powinny zostać dostarczone w jednym archiwum (np. `.zip`) lub pobrane z repozytorium kodu (np. GitHub). Struktura plików powinna wyglądać następująco:

```
ANALIZATOR_AI_OVERVIEW/
│
├── app/
│   ├── __init__.py
│   ├── main.py               # Główny plik aplikacji Streamlit
│   ├── analysis_engine.py    # Logika analizy
│   ├── serp_client.py        # Klient API serpdata.io
│   ├── llm_client.py         # Klient API OpenRouter.ai
│   ├── db_handler.py         # Obsługa bazy danych
│   ├── utils.py              # Funkcje pomocnicze
│   └── llm_prompts.py        # Szablony promptów
│
├── requirements.txt          # Lista zależności Pythona
├── .env.template             # Szablon pliku konfiguracyjnego dla kluczy API
└── (ewentualnie inne pliki, np. ta dokumentacja)
```

1.  **Utwórz folder**: Na swoim komputerze utwórz nowy folder, w którym będziesz przechowywać aplikację, np. `C:\Analizator_AI_Overview` (Windows) lub `/home/uzytkownik/Analizator_AI_Overview` (Linux/macOS).
2.  **Skopiuj pliki**: Rozpakuj archiwum lub skopiuj wszystkie pliki i foldery aplikacji (całą strukturę pokazaną powyżej) do tego nowo utworzonego folderu.

### 3.3. Konfiguracja Kluczy API:

Aplikacja do działania potrzebuje dostępu do zewnętrznych usług API, co wymaga podania tzw. kluczy API. Klucze te są poufne i nie powinny być udostępniane publicznie.

1.  **Znajdź plik `.env.template`**: W głównym folderze aplikacji (`ANALIZATOR_AI_OVERVIEW/`) znajduje się plik o nazwie `.env.template`.
2.  **Stwórz kopię**: Skopiuj ten plik i zmień nazwę kopii na `.env` (usuń rozszerzenie `.template`). Plik `.env` jest specjalnym plikiem, który aplikacja będzie automatycznie odczytywać w poszukiwaniu konfiguracji.
3.  **Edytuj plik `.env`**: Otwórz plik `.env` w dowolnym edytorze tekstu (np. Notatnik, Notepad++, VS Code). Zobaczysz następującą zawartość:

    ```
    # Zmień nazwę tego pliku na .env i uzupełnij klucze API
    # Klucz API dla serpdata.io
    SERPDATA_API_KEY="TWÓJ_KLUCZ_SERPDATA_API"

    # Klucz API dla OpenRouter (lub bezpośrednio OpenAI jeśli zdecydujesz się zmienić)
    OPENROUTER_API_KEY="TWÓJ_KLUCZ_OPENROUTER_API"
    ```
4.  **Wklej swoje klucze API**:
    *   W miejsce `"TWÓJ_KLUCZ_SERPDATA_API"` wklej swój rzeczywisty klucz API skopiowany z panelu `serpdata.io`.
    *   W miejsce `"TWÓJ_KLUCZ_OPENROUTER_API"` wklej swój rzeczywisty klucz API skopiowany z panelu `OpenRouter.ai`.
    *   **Ważne**: Upewnij się, że klucze są wklejone dokładnie między cudzysłowami.
5.  **Zapisz plik `.env`**.

Przykład poprawnie wypełnionego pliku `.env` (z fikcyjnymi kluczami):
```
SERPDATA_API_KEY="abcdef1234567890serpdata"
OPENROUTER_API_KEY="sk-or-v1-abcdef1234567890openrouter"
```

### 3.4. Instalacja Zależności Pythona:

Aplikacja korzysta z kilku zewnętrznych bibliotek Pythona, które muszą zostać zainstalowane.

1.  **Otwórz terminal (wiersz poleceń)**:
    *   **Windows**: Naciśnij klawisz `Win`, wpisz `cmd` lub `PowerShell` i naciśnij Enter.
    *   **Linux/macOS**: Otwórz aplikację Terminal.
2.  **Przejdź do folderu aplikacji**: W terminalu użyj komendy `cd` (change directory), aby przejść do folderu, w którym zapisałeś pliki aplikacji.
    *   Przykład dla Windows: `cd C:\Analizator_AI_Overview`
    *   Przykład dla Linux/macOS: `cd /home/uzytkownik/Analizator_AI_Overview`
3.  **(Opcjonalnie, ale zalecane) Utwórz środowisko wirtualne**: Środowisko wirtualne izoluje zależności tej aplikacji od innych projektów Pythona na Twoim komputerze.
    *   Wpisz w terminalu: `python -m venv venv`
    *   Aktywuj środowisko wirtualne:
        *   Windows (cmd): `venv\Scripts\activate`
        *   Windows (PowerShell): `venv\Scripts\Activate.ps1` (może być konieczne zezwolenie na uruchamianie skryptów: `Set-ExecutionPolicy Unrestricted -Scope Process`)
        *   Linux/macOS: `source venv/bin/activate`
    *   Po aktywacji, nazwa środowiska (`venv`) powinna pojawić się na początku linii w terminalu.
4.  **Zainstaluj zależności**: Będąc w głównym folderze aplikacji (i z aktywnym środowiskiem wirtualnym, jeśli je utworzyłeś), wpisz w terminalu:
    ```bash
    pip install -r requirements.txt
    ```
    Ta komenda odczyta plik `requirements.txt` i automatycznie pobierze oraz zainstaluje wszystkie potrzebne biblioteki. Proces ten może chwilę potrwać, w zależności od szybkości Twojego internetu.

Po zakończeniu instalacji zależności, aplikacja jest prawie gotowa do uruchomienia.

## 4. Uruchamianie Aplikacji

### 4.1. Uruchamianie Lokalnie (zalecane na początek):

1.  **Upewnij się, że jesteś w folderze aplikacji w terminalu**: Jeśli zamknąłeś terminal, otwórz go ponownie i przejdź do folderu aplikacji komendą `cd`.
2.  **(Jeśli używasz) Aktywuj środowisko wirtualne**: `venv\Scripts\activate` (Windows cmd), `source venv/bin/activate` (Linux/macOS).
3.  **Uruchom aplikację Streamlit**: Wpisz w terminalu następującą komendę:
    ```bash
    streamlit run app/main.py
    ```
4.  **Otwórz aplikację w przeglądarce**: Po chwili w terminalu powinny pojawić się informacje, a Twoja domyślna przeglądarka internetowa powinna automatycznie otworzyć nową kartę z działającą aplikacją. Adres URL będzie prawdopodobnie wyglądał tak: `http://localhost:8501`.
    *   Jeśli przeglądarka nie otworzy się automatycznie, skopiuj adres URL (np. `Local URL: http://localhost:8501`) wyświetlony w terminalu i wklej go ręcznie do paska adresu przeglądarki.

Aplikacja jest teraz uruchomiona! Możesz zacząć z niej korzystać. Aby zatrzymać aplikację, wróć do okna terminala i naciśnij `Ctrl+C`.

### 4.2. Ułatwione Uruchamianie na Windows (plik .BAT - opcjonalnie):

Aby ułatwić uruchamianie aplikacji na Windows bez każdorazowego wpisywania komend w terminalu, możesz stworzyć prosty plik wsadowy (`.bat`).

1.  **Otwórz Notatnik**.
2.  **Wklej poniższy kod**:

    ```batch
    @echo off
    echo Uruchamianie Analizatora AI Overview & SERP...

    REM Przejdz do folderu, w ktorym znajduje sie ten plik .bat
    cd /d "%~dp0"

    REM Sprawdz, czy istnieje folder srodowiska wirtualnego 'venv'
    IF EXIST venv\Scripts\activate.bat (
        echo Aktywowanie srodowiska wirtualnego...
        call venv\Scripts\activate.bat
    ) ELSE (
        echo Ostrzezenie: Srodowisko wirtualne 'venv' nie znalezione. Uruchamiam z globalnymi pakietami Python.
    )

    echo Uruchamianie aplikacji Streamlit...
    streamlit run app/main.py

    REM Deaktywacja srodowiska wirtualnego po zamknieciu aplikacji (opcjonalne)
    IF EXIST venv\Scripts\deactivate.bat (
        call venv\Scripts\deactivate.bat
    )

    pause
    ```
3.  **Zapisz plik**:
    *   W Notatniku wybierz `Plik > Zapisz jako...`.
    *   W polu "Nazwa pliku" wpisz `uruchom_analizator.bat`.
    *   W polu "Zapisz jako typ" wybierz `Wszystkie pliki (*.*)`.
    *   **Zapisz ten plik w głównym folderze aplikacji** (tam, gdzie jest folder `app` i plik `requirements.txt`).
4.  **Uruchamianie**: Teraz możesz uruchomić aplikację, klikając dwukrotnie plik `uruchom_analizator.bat`. Otworzy się okno terminala, a następnie aplikacja w przeglądarce. Po zamknięciu aplikacji (Ctrl+C w terminalu lub zamknięcie okna terminala), możesz nacisnąć dowolny klawisz w oknie terminala, aby je zamknąć.

**Uwaga dla pliku .BAT**: Ten skrypt zakłada, że komenda `streamlit` jest dostępna globalnie lub w środowisku wirtualnym. Jeśli Python i Streamlit były instalowane tylko w środowisku wirtualnym i nie dodano Pythona do PATH, może być konieczne podanie pełnej ścieżki do `streamlit.exe` wewnątrz folderu `venv\Scripts`.

### 4.3. Uruchamianie Online (np. Streamlit Community Cloud):

Aplikacja jest przygotowana do wdrożenia na platformach takich jak Streamlit Community Cloud. Wymaga to:

1.  **Umieszczenia kodu w repozytorium Git**: Najlepiej na GitHub. Plik `.env` z kluczami API **nie powinien** być umieszczany w publicznym repozytorium.
2.  **Konta na Streamlit Community Cloud**: Zarejestruj się na [share.streamlit.io](https://share.streamlit.io/).
3.  **Wdrożenia aplikacji**: W panelu Streamlit Cloud wybierz "New app", połącz swoje konto GitHub, wybierz repozytorium i gałąź oraz wskaż główny plik aplikacji (`app/main.py`).
4.  **Konfiguracji Sekretów**: W zaawansowanych ustawieniach aplikacji w Streamlit Cloud dodaj swoje klucze API (`SERPDATA_API_KEY` i `OPENROUTER_API_KEY`) jako "Secrets". Aplikacja automatycznie je odczyta jako zmienne środowiskowe.

Streamlit Community Cloud oferuje darmowy plan, który jest wystarczający do hostowania tej aplikacji dla celów demonstracyjnych lub małego użytku.

## 5. Korzystanie z Aplikacji - Panel Sterowania

Po uruchomieniu aplikacji zobaczysz interfejs użytkownika podzielony na dwie główne części: panel boczny (po lewej) do wprowadzania danych i konfiguracji, oraz główny obszar (po prawej) do wyświetlania wyników.

### 5.1. Panel Boczny ("Panel Sterowania Analizą"):

Panel boczny zawiera wszystkie opcje potrzebne do przeprowadzenia analizy.

1.  **Sekcja "Podstawowe Dane Wejściowe"**:
    *   **Słowo kluczowe do analizy**: Wpisz frazę kluczową, dla której chcesz przeprowadzić analizę SERP i AI Overview (np. `najlepsze restauracje w Krakowie`, `jak naprawić kran`).
    *   **Domena klienta**: Podaj pełną domenę Twojej strony internetowej, którą analizujesz (np. `mojadomena.pl`, `blogkulinarny.com`). Bez `http://` czy `https://`.
    *   **Branża klienta**: Krótko opisz branżę lub tematykę Twojej strony (np. `Restauracje włoskie`, `Poradniki DIY`, `Marketing internetowy`). Pomoże to modelowi LLM lepiej zrozumieć kontekst.
    *   **Język wyszukiwania**: Wybierz z listy język, w którym ma być przeprowadzone wyszukiwanie (np. `pl` dla polskiego, `en` dla angielskiego).
    *   **Kraj wyszukiwania**: Wybierz z listy kraj, dla którego mają być symulowane wyniki wyszukiwania (np. `PL` dla Polski, `US` dla Stanów Zjednoczonych).

2.  **Sekcja "Konfiguracja Modelu LLM"**:
    *   **Wybierz model LLM**: Z rozwijanej listy wybierz model językowy, który ma być użyty do analizy. Lista modeli jest dynamicznie pobierana z OpenRouter. Różne modele mogą dawać różne wyniki, mieć różne ceny i ograniczenia. Przykładowe popularne modele to:
        *   `anthropic/claude-3.5-sonnet` (dobra jakość, często zalecany jako domyślny)
        *   `anthropic/claude-3-haiku` (szybszy i tańszy, dobra opcja na start)
        *   `openai/gpt-4o` (bardzo zaawansowany model od OpenAI)
        *   `google/gemini-pro`
        *   Jeśli lista nie załaduje się poprawnie, pojawi się pole do ręcznego wpisania ID modelu.
    *   **Temperatura LLM**: Suwak pozwalający ustawić "kreatywność" modelu.
        *   Wartości bliższe `0.0` (np. `0.1` - `0.3`): Odpowiedzi będą bardziej deterministyczne, spójne i oparte na faktach. Zalecane do zadań analitycznych.
        *   Wartości bliższe `1.0` (np. `0.7` - `1.0`): Odpowiedzi będą bardziej kreatywne, zróżnicowane, ale mogą być mniej precyzyjne.
        *   Domyślna wartość to `0.5`, co jest dobrym kompromisem.
    *   **Maks. tokenów LLM**: Liczba określająca maksymalną długość odpowiedzi, jaką może wygenerować model (zarówno prompt, jak i odpowiedź wliczają się w ogólny limit tokenów kontekstu modelu).
        *   Większa wartość pozwala na bardziej rozbudowane analizy, ale może zwiększyć koszt (jeśli model jest płatny za tokeny) i czas odpowiedzi.
        *   Mniejsza wartość może uciąć odpowiedź, jeśli analiza jest obszerna.
        *   Domyślna wartość `4096` jest zazwyczaj wystarczająca dla tego typu analizy. Sprawdź limity konkretnych modeli na stronie OpenRouter.

3.  **Przycisk "Rozpocznij Analizę"**: Po wypełnieniu wszystkich pól i ustawieniu parametrów, kliknij ten przycisk, aby rozpocząć proces analizy.

4.  **Informacja o Kluczach API**: Przypomnienie o konieczności skonfigurowania kluczy API w pliku `.env`.

### 5.2. Główny Obszar Wyświetlania Wyników:

Po kliknięciu "Rozpocznij Analizę", w głównym obszarze strony pojawi się informacja o trwającym procesie ("spinner"). Po zakończeniu analizy (co może potrwać od kilkunastu sekund do kilku minut, w zależności od szybkości API i modelu LLM), wyświetlone zostaną wyniki.

**Struktura Wyświetlanych Wyników:**

1.  **Nagłówek**: "Wyniki Analizy dla: '[Twoje Słowo Kluczowe]'"

2.  **Sekcja "Podsumowanie Zapytania"**:
    *   **Zapytanie**: Powtórzenie analizowanego słowa kluczowego.
    *   **Domena Klienta**: Twoja domena.
    *   **Branża Klienta**: Twoja branża.
    *   **Model LLM**: ID modelu LLM użytego do tej konkretnej analizy.
    *   **Temperatura**: Wartość temperatury użyta dla LLM.
    *   **Maks. tokenów**: Maksymalna liczba tokenów ustawiona dla LLM.
    *   **Klient w AI Overview**: "Tak" lub "Nie" – czy Twoja domena została znaleziona w źródłach AI Overview.
    *   **Klient w Top 10 Organicznych**: "Tak" lub "Nie" – czy Twoja domena została znaleziona w pierwszych 10 organicznych wynikach wyszukiwania.

3.  **Sekcja "Analiza AI Overview"**:
    *   **Aktualne źródła w AI Overview**: Lista stron (tytuł i domena), które Google wykorzystało do wygenerowania odpowiedzi AI Overview. To Twoi bezpośredni konkurenci o miejsce w tym boksie.
    *   **Możliwości dla klienta w AI Overview**: Konkretne sugestie od LLM, co możesz zrobić, aby Twoja strona pojawiła się w AI Overview (np. "Stwórz artykuł odpowiadający na pytanie X", "Dodaj sekcję FAQ na stronie Y").
    *   **Sugerowane formaty treści**: Propozycje typów treści, które mogą być skuteczne w kontekście AI Overview (np. "Blog post", "FAQ page", "Infografika").

4.  **Sekcja "Krajobraz Konkurencji"**:
    *   **Kluczowi konkurenci w AI Overview**: Domeny konkurentów, którzy pojawiają się w AI Overview.
    *   **Kluczowi konkurenci w wynikach organicznych**: Domeny konkurentów, którzy są wysoko w standardowych wynikach wyszukiwania.

5.  **Sekcja "Analiza Luk w Treści"**:
    *   **Pytania z PAA do zaadresowania**: Lista pytań z sekcji "People Also Ask" (Ludzie również pytają), na które Twoja strona mogłaby dostarczyć odpowiedzi, potencjalnie zwiększając szansę na pojawienie się w AI Overview lub jako "featured snippet".
    *   **Możliwości z powiązanych wyszukiwań**: Lista tematów z sekcji "Related Searches" (Powiązane wyszukiwania), które wskazują na dodatkowe zainteresowania użytkowników i mogą być inspiracją dla nowych treści.

6.  **Sekcja "Rekomendacje Działań"**:
    *   Lista konkretnych, praktycznych rekomendacji podzielonych na priorytety (Priorytet 1, 2, 3). Są to działania, które powinieneś rozważyć w pierwszej kolejności.

7.  **Sekcja "Ogólne Podsumowanie"**:
    *   Krótkie, 2-3 zdaniowe podsumowanie całej analizy przygotowane przez LLM, wskazujące na najważniejsze wnioski i sugestie.

8.  **Sekcja "Wygeneruj Raport Tekstowy"**:
    *   **Przycisk "Generuj Raport do Skopiowania"**: Po kliknięciu, poniżej pojawi się pole tekstowe z całym raportem w formacie Markdown, gotowym do skopiowania.
    *   **Przycisk "Pobierz Raport jako .txt"**: Umożliwia pobranie tego samego raportu jako pliku tekstowego na Twój komputer.

## 6. Interpretacja Wyników Analizy

Zrozumienie wyników analizy jest kluczowe do podjęcia skutecznych działań. Oto wskazówki, jak interpretować poszczególne sekcje:

*   **Obecność Klienta (AI Overview, Top 10 Organiczne)**: To szybki wskaźnik Twojej aktualnej pozycji. Jeśli odpowiedź brzmi "Nie", szczególnie w AI Overview, to głównym celem będzie znalezienie sposobu, aby się tam pojawić.
*   **Aktualne źródła w AI Overview**: Dokładnie przeanalizuj te strony. Jakie treści publikują? Jaki jest ich format? Jak odpowiadają na zapytanie użytkownika? Staraj się tworzyć treści lepsze, bardziej wyczerpujące lub prezentujące unikalną perspektywę.
*   **Możliwości dla klienta w AI Overview**: To bezpośrednie sugestie od AI. Traktuj je jako punkt wyjścia do burzy mózgów nad nowymi treściami lub optymalizacją istniejących.
*   **Konkurenci**: Zidentyfikuj, kto jest Twoim głównym konkurentem w walce o widoczność. Odwiedź ich strony, zobacz, co robią dobrze.
*   **Luki w Treści (PAA, Powiązane wyszukiwania)**: To kopalnia pomysłów na content. Odpowiadanie na pytania użytkowników (PAA) i pokrywanie tematów z powiązanych wyszukiwań to świetny sposób na zwiększenie relewancji Twojej strony.
*   **Rekomendacje Działań**: Potraktuj je jako listę zadań. Zacznij od tych z najwyższym priorytetem. Nie wszystkie rekomendacje muszą być idealne – użyj własnego osądu i wiedzy o swojej branży.
*   **Ogólne Podsumowanie**: Daje szybki przegląd sytuacji. Jeśli masz mało czasu, zacznij od tej sekcji.

**Ważne uwagi:**

*   **AI Overview jest dynamiczne**: To, co jest dziś źródłem AI Overview, jutro może nim nie być. Regularne analizy są kluczowe.
*   **Jakość treści jest najważniejsza**: Google dąży do dostarczania najlepszych odpowiedzi. Twoje treści muszą być wartościowe, dokładne i dobrze napisane.
*   **E-E-A-T**: (Experience, Expertise, Authoritativeness, Trustworthiness - Doświadczenie, Ekspertyza, Autorytet, Wiarygodność) – to czynniki, które Google bierze pod uwagę. Dbaj o te aspekty na swojej stronie.
*   **Eksperymentuj z modelami LLM**: Różne modele mogą dawać nieco inne sugestie. Jeśli masz możliwość, przetestuj kilka modeli dla tego samego zapytania, aby uzyskać szerszą perspektywę. Pamiętaj jednak, że częste zapytania do wielu modeli mogą generować koszty na platformie OpenRouter.

## 7. Rozwiązywanie Problemów (Troubleshooting)

*   **Aplikacja nie uruchamia się**:
    *   Sprawdź, czy poprawnie zainstalowałeś wszystkie zależności z `requirements.txt`.
    *   Upewnij się, że komenda `streamlit run app/main.py` jest wpisywana w terminalu, będąc w głównym folderze aplikacji.
    *   Jeśli używasz środowiska wirtualnego, upewnij się, że jest aktywowane.
*   **Błąd dotyczący kluczy API**:
    *   Sprawdź, czy plik `.env` istnieje w głównym folderze aplikacji i czy ma poprawną nazwę (bez `.template`).
    *   Upewnij się, że klucze `SERPDATA_API_KEY` i `OPENROUTER_API_KEY` w pliku `.env` są poprawnie wklejone i nie zawierają dodatkowych spacji czy znaków.
    *   Sprawdź, czy Twoje klucze API są aktywne na platformach `serpdata.io` i `OpenRouter.ai` (np. czy masz wystarczające środki na koncie OpenRouter).
*   **Brak wyników analizy lub błędy podczas analizy**:
    *   Sprawdź połączenie internetowe.
    *   Komunikaty o błędach w aplikacji lub w terminalu mogą wskazać przyczynę (np. błąd API SerpData, błąd API OpenRouter, przekroczony limit zapytań).
    *   Spróbuj użyć innego, mniej wymagającego modelu LLM (np. Claude Haiku zamiast GPT-4o), jeśli podejrzewasz problemy z wydajnością lub kosztami.
    *   Upewnij się, że słowo kluczowe i domena są wpisane poprawnie.
*   **Lista modeli LLM nie ładuje się**:
    *   Sprawdź klucz `OPENROUTER_API_KEY`.
    *   OpenRouter API może być chwilowo niedostępne. Spróbuj ponownie później lub wpisz ID znanego Ci modelu ręcznie.
*   **Długi czas oczekiwania na wyniki**:
    *   Analiza, zwłaszcza zapytania do modeli LLM, może zająć trochę czasu. Bądź cierpliwy.
    *   Szybsze modele LLM (np. Claude Haiku) będą generalnie odpowiadać szybciej niż bardziej złożone (np. Claude Sonnet, GPT-4o).

## 8. Możliwości Rozwoju i Personalizacji (Dla Zaawansowanych)

*   **Dodawanie nowych szablonów promptów LLM**: Możesz modyfikować istniejące prompty w `app/llm_prompts.py` lub dodawać nowe, aby dostosować analizę do specyficznych potrzeb.
*   **Zmiana domyślnych parametrów**: Wartości domyślne dla modelu LLM, temperatury, itp. są zdefiniowane w `app/analysis_engine.py` i `app/main.py` – można je zmienić.
*   **Rozbudowa bazy danych**: Można dodać więcej pól do tabel w `app/db_handler.py`, np. do śledzenia konkretnych parametrów LLM użytych do analizy.
*   **Bardziej zaawansowane raportowanie**: Zamiast raportu tekstowego, można zaimplementować generowanie PDF (np. używając bibliotek `FPDF` lub `ReportLab`).
*   **Integracja z innymi narzędziami**: Można rozważyć integrację z Google Search Console, Google Analytics lub innymi narzędziami SEO.

---
*Dokumentacja została przygotowana z myślą o jak największej przejrzystości. W razie dalszych pytań lub problemów, zaleca się kontakt z osobą, która dostarczyła aplikację, lub poszukiwanie rozwiązań w dokumentacji poszczególnych narzędzi (Streamlit, OpenRouter, SerpData).*
