Dynamic Web Scraper & Summarizer

A Python-based desktop tool designed to automate the process of web research. It utilizes multi-threading to fetch search results, scrape content from targeted domains, and provide an interactive visual analysis of common themes.

Features
* **Targeted Search Scopes:** Pre-configured filters for Nigerian Academic (.edu.ng) and Government (.gov.ng) domains.
* **Multi-Threaded Scraping:** Uses `concurrent.futures` to process multiple URLs simultaneously for high performance.
* **Live Summaries:** Extracts and displays the first 300 characters of page content with clickable hyperlinks.
* **Data Visualization:** Automatically generates a bar chart of the top 10 most frequent keywords (excluding noise and stop-words).
* **Smart Filtering:** Automatically skips PDFs, connection timeouts, and low-quality (short) text responses.

 Prerequisites
Ensure you have Python 3.x installed. You will need the following libraries:

```bash
pip install requests beautifulsoup4 duckduckgo_search matplotlib
```

 Installation & Usage
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/web-scraper-summarizer.git
    cd web-scraper-summarizer
    ```
2.  **Run the application:**
    ```bash
    python main.py
    ```
3.  **Search:** Enter your query, select a scope (e.g., Academic), and hit **Start Search**.

 How It Works
* **Search Engine:** Leverages the DuckDuckGo API via DDGS for privacy-focused results.
* **Content Extraction:** Uses `BeautifulSoup` to parse paragraph text.
* **Analysis:** Filters words through a custom stop-word list and calculates frequency using `collections.Counter`.
* **GUI:** Built with `Tkinter` for a lightweight, cross-platform desktop experience.

 License
Distributed under the MIT License. See `LICENSE` for more information.
