import json

def parse_serp_data_for_llm(serp_json_string):
    """
    Parses the raw SERP JSON string to extract key information relevant for LLM analysis.
    Focuses on AI Overview sources, organic results, PAA, and related searches.
    """
    try:
        serp_data = json.loads(serp_json_string)
    except json.JSONDecodeError:
        print("Error decoding SERP JSON string.")
        return {}

    results = serp_data.get("results", {})
    if not results: # Handle cases where 'results' key might be missing or null
        return {
            "query": serp_data.get("request", {}).get("query", "Unknown query"),
            "ai_overview_sources": [],
            "organic_results_titles": [],
            "people_also_ask_questions": [],
            "related_searches_queries": []
        }


    ai_overview = results.get("ai_overview", {})
    ai_overview_sources = []
    if ai_overview and isinstance(ai_overview, dict) and ai_overview.get("sources"):
        for source in ai_overview.get("sources", []):
            ai_overview_sources.append({
                "title": source.get("title"),
                "url": source.get("url"),
                "snippet": source.get("snippet")
            })

    organic_results = results.get("organic_results", [])
    organic_results_titles_urls = []
    if organic_results:
        for res in organic_results:
            organic_results_titles_urls.append({
                "title": res.get("title"),
                "url": res.get("url"),
                "domain": res.get("domain")
            })

    people_also_ask = results.get("people_also_ask", {})
    people_also_ask_questions = []
    if people_also_ask and isinstance(people_also_ask, dict) and people_also_ask.get("questions"):
        for q_data in people_also_ask.get("questions", []):
            if isinstance(q_data, dict): # Ensure q_data is a dictionary
                 people_also_ask_questions.append(q_data.get("text"))
            elif isinstance(q_data, str): # If it's just a list of strings (less common for PAA)
                 people_also_ask_questions.append(q_data)


    related_searches = results.get("related_searches", {})
    related_searches_queries = []
    if related_searches and isinstance(related_searches, dict) and related_searches.get("queries"):
        related_searches_queries = related_searches.get("queries", [])


    extracted_data = {
        "query": results.get("query", serp_data.get("request", {}).get("query", "Unknown query")),
        "ai_overview_sources": ai_overview_sources,
        "organic_results": organic_results_titles_urls,
        "people_also_ask_questions": people_also_ask_questions,
        "related_searches_queries": related_searches_queries
    }
    return extracted_data


def format_serp_for_llm_prompt(parsed_serp_data, client_domain):
    """
    Formats the parsed SERP data into a string suitable for an LLM prompt.
    """
    prompt_lines = [
        f"Analyzing SERP for query: \"{parsed_serp_data.get('query', 'N/A')}\"",
        f"Client's domain: {client_domain}\n"
    ]

    prompt_lines.append("AI Overview Sources:")
    if parsed_serp_data.get("ai_overview_sources"):
        for i, source in enumerate(parsed_serp_data["ai_overview_sources"], 1):
            prompt_lines.append(f"  {i}. Title: {source.get('title', 'N/A')}, URL: {source.get('url', 'N/A')}")
            if source.get('snippet'):
                 prompt_lines.append(f"     Snippet: {source.get('snippet')[:150]}...") # Truncate long snippets
    else:
        prompt_lines.append("  No AI Overview sources found or provided.")
    prompt_lines.append("\n")

    prompt_lines.append("Top Organic Results (excluding client domain if present in top 10):")
    client_domain_in_top_organic = False
    if parsed_serp_data.get("organic_results"):
        count = 0
        for i, res in enumerate(parsed_serp_data["organic_results"], 1):
            is_client = client_domain in res.get('domain', '')
            if is_client:
                client_domain_in_top_organic = True
            # Display competitors, or all if client is not in top results
            prompt_lines.append(f"  {i}. Title: {res.get('title', 'N/A')}, URL: {res.get('url', 'N/A')} {'(Client)' if is_client else ''}")
            count+=1
            if count >=10: # limit to top 10 for brevity in prompt
                break
    else:
        prompt_lines.append("  No organic results found or provided.")

    if client_domain_in_top_organic:
        prompt_lines.append(f"\nNote: Client domain ({client_domain}) IS present in the top organic results.")
    else:
        prompt_lines.append(f"\nNote: Client domain ({client_domain}) IS NOT present in the top organic results.")
    prompt_lines.append("\n")


    prompt_lines.append("People Also Ask:")
    if parsed_serp_data.get("people_also_ask_questions"):
        for i, q in enumerate(parsed_serp_data["people_also_ask_questions"], 1):
            prompt_lines.append(f"  - {q}")
    else:
        prompt_lines.append("  No People Also Ask questions found or provided.")
    prompt_lines.append("\n")

    prompt_lines.append("Related Searches:")
    if parsed_serp_data.get("related_searches_queries"):
        for i, q in enumerate(parsed_serp_data["related_searches_queries"], 1):
            prompt_lines.append(f"  - {q}")
    else:
        prompt_lines.append("  No related searches found or provided.")

    return "\n".join(prompt_lines)

# Example for testing
if __name__ == '__main__':
    # This is the example result from the initial prompt
    example_serp_json_string = """
    {
      "search_engine": "google",
      "location": "us",
      "language": "en",
      "timestamp": "2025-06-30T14:50:12.619931",
      "search_url": null,
      "total_results_count": null,
      "results": {
        "query": "real estate software companies",
        "snippets_found": [
          "people_also_ask",
          "related_searches",
          "ai_overview",
          "ads",
          "complementary_results"
        ],
        "organic_results": [
          {
            "domain": "builtin.com",
            "rank_absolute": 7,
            "rank_inner": 1,
            "title": "Real Estate Technology: Overview, Trends and 29 ...",
            "type": "standard",
            "url": "https://builtin.com/articles/real-estate-technology"
          },
          {
            "domain": "thefinancialtechnologyreport.com",
            "rank_absolute": 8,
            "rank_inner": 2,
            "title": "The Top 25 Real Estate Technology Companies of 2024",
            "type": "standard",
            "url": "https://thefinancialtechnologyreport.com/the-top-25-real-estate-technology-companies-of-2024/"
          },
          {
            "domain": "hicronsoftware.com",
            "rank_absolute": 15,
            "rank_inner": 8,
            "title": "50+ PropTech Software Companies Shaping the Industry",
            "type": "standard",
            "url": "https://hicronsoftware.com/blog/proptech-software-companies-shaping-real-estate/"
          }
        ],
        "snippets_data": {
          "ads": [],
          "ai_overview": {
            "has_listen_button": false,
            "rank_absolute": 1,
            "sources": [
              {
                "display_url": "The Financial Technology Report.",
                "rank_inner": 1,
                "snippet": "Apr 29, 2024 — Zillow is a real estate marketplace company that provides information and services related to selling, buying, renting...",
                "title": "The Top 25 Real Estate Technology Companies of 2024",
                "url": "https://thefinancialtechnologyreport.com/the-top-25-real-estate-technology-companies-of-2024/"
              },
              {
                "display_url": "Hicron Software",
                "rank_inner": 21,
                "snippet": "Jan 10, 2025 —  PropTech/ Real Estate Investment Platforms * Fundrise – Gives retail investors a chance to participate in real estate...",
                "title": "50+ PropTech Software Companies Shaping the Industry",
                "url": "https://hicronsoftware.com/blog/proptech-software-companies-shaping-real-estate/"
              }
            ],
            "status": "success",
            "text": "Real estate software companies provide a variety of tools to streamline various aspects of the industry..."
          },
          "people_also_ask": {
            "questions": [
              { "text": "What is the best software for real estate management?" },
              { "text": "What is the 7% rule in real estate?" }
            ],
            "rank_absolute": 9
          },
          "related_searches": {
            "queries": [
              "real estate software companies near laredo, tx",
              "Top real estate software companies"
            ],
            "rank_absolute": 21
          }
        }
      },
      "request": {
        "query": "real estate software companies"
      },
      "status": "success"
    }
    """

    parsed_data = parse_serp_data_for_llm(example_serp_json_string)
    print("--- Parsed SERP Data ---")
    print(json.dumps(parsed_data, indent=2))

    client_domain_example = "hicronsoftware.com"
    prompt_text = format_serp_for_llm_prompt(parsed_data, client_domain_example)
    print("\n--- Formatted LLM Prompt ---")
    print(prompt_text)

    client_domain_example_not_present = "someotherdomain.com"
    prompt_text_not_present = format_serp_for_llm_prompt(parsed_data, client_domain_example_not_present)
    print("\n--- Formatted LLM Prompt (Client Not Present) ---")
    print(prompt_text_not_present)

    # Test with minimal data (e.g. only query)
    minimal_serp_json_string = """
    {
        "request": {"query": "minimal query"},
        "results": null
    }
    """
    parsed_minimal_data = parse_serp_data_for_llm(minimal_serp_json_string)
    print("\n--- Parsed Minimal SERP Data ---")
    print(json.dumps(parsed_minimal_data, indent=2))
    prompt_text_minimal = format_serp_for_llm_prompt(parsed_minimal_data, "anydomain.com")
    print("\n--- Formatted LLM Prompt (Minimal Data) ---")
    print(prompt_text_minimal)

    # Test with empty results
    empty_results_serp_json_string = """
    {
        "request": {"query": "empty results query"},
        "results": {
            "query": "empty results query",
            "ai_overview": null,
            "organic_results": [],
            "people_also_ask": null,
            "related_searches": null
        }
    }
    """
    parsed_empty_results_data = parse_serp_data_for_llm(empty_results_serp_json_string)
    print("\n--- Parsed Empty Results SERP Data ---")
    print(json.dumps(parsed_empty_results_data, indent=2))
    prompt_text_empty_results = format_serp_for_llm_prompt(parsed_empty_results_data, "anydomain.com")
    print("\n--- Formatted LLM Prompt (Empty Results Data) ---")
    print(prompt_text_empty_results)
