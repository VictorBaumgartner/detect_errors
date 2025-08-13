# Social Media Link Checker

This Python script is designed to verify and suggest social media links for a business based on structured data and web searches. It extracts URLs from a JSON file, validates them against specific social media platforms, and suggests additional links if necessary.

## Features
- **URL Extraction**: Extracts URLs from a JSON input file.
- **Social Media Validation**: Checks if URLs belong to supported social media platforms (Facebook, Instagram, Twitter, LinkedIn, Google, Google Maps, TripAdvisor).
- **Structured Data Analysis**: Uses `extruct` to parse structured data (JSON-LD, microdata, OpenGraph) and validate relevance based on business name, city, and activities.
- **Web Search**: Uses `duckduckgo_search` to suggest missing social media links.
- **Output**: Saves results to a JSON file, including validated URLs, suggested links, and error details.

## Prerequisites
- Python 3.8+
- Required libraries:
  - `duckduckgo_search`
  - `requests`
  - `tldextract`
  - `bs4` (BeautifulSoup)
  - `extruct`
  - `w3lib`
- Install dependencies using:
  ```bash
  pip install duckduckgo_search requests tldextract beautifulsoup4 extruct w3lib
  ```

## Usage
1. **Prepare Input**:
   - Create a JSON file (e.g., `topkite-fr.json`) with business details, including:
     - `info.name`: Business name
     - `info.addresses[0].city`: City
     - `info.tags`: List of activities/tags
   - Example JSON structure:
     ```json
     {
       "info": {
         "name": "Example Business",
         "addresses": [{"city": "Paris"}],
         "tags": ["kitesurfing", "sports"]
       }
     }
     ```

2. **Run the Script**:
   - Update the file path in the script to point to your JSON file:
     ```python
     with open(r"path/to/your/topkite-fr.json", "r", encoding="utf-8") as f:
     ```
   - Execute the script:
     ```bash
     python script.py
     ```

3. **Output**:
   - Results are saved to `output_links_check.json` in the specified directory.
   - The output includes:
     - Validated URLs with their final resolved URL, platform, HTTP status, and relevance.
     - Suggested URLs for missing social media platforms.
     - Error details for failed checks.

## Example Output
```json
[
  {
    "initial_url": "https://facebook.com/example",
    "final_url": "https://www.facebook.com/example",
    "reseau": "Facebook",
    "http_status": 200,
    "pertinent": true,
    "erreur": null,
    "url_corrigee": null
  },
  {
    "initial_url": null,
    "final_url": null,
    "reseau": "Instagram",
    "http_status": null,
    "pertinent": true,
    "erreur": null,
    "url_corrigee": "https://instagram.com/example"
  }
]
```

## Notes
- The script assumes the input JSON file is correctly formatted and contains the required fields.
- Supported platforms are defined in the `RESEAUX_VALIDES` dictionary.
- The script uses DuckDuckGo for web searches, which may have rate limits.
- Ensure a stable internet connection for URL validation and web searches.

## License
This project is licensed under the MIT License.
