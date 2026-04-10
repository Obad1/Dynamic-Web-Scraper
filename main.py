import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import concurrent.futures
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from collections import Counter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re
import webbrowser  # Added to make links clickable

# Basic stop-words list to filter out junk words without needing SpaCy
STOP_WORDS = {
    "this", "that", "with", "from", "your", "what", "have", "paper",
    "research", "study", "article", "journal", "abstract", "introduction",
    "were", "their", "they", "which", "will", "there", "would", "about", "these",
    "http", "https", "www", "com", "org"
}


class WebScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Web Scraper & Summarizer")
        self.root.geometry("1000x750")

        # --- UI SETUP ---
        input_frame = ttk.Frame(root, padding=10)
        input_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(input_frame, text="Search Query:").pack(side=tk.LEFT, padx=5)
        self.query_var = tk.StringVar(value="Crime reporting")
        self.query_entry = ttk.Entry(input_frame, textvariable=self.query_var, width=30)
        self.query_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(input_frame, text="Search In:").pack(side=tk.LEFT, padx=5)
        self.scope_var = tk.StringVar(value="Academic (edu.ng)")
        self.scope_combo = ttk.Combobox(input_frame, textvariable=self.scope_var, width=22, state="readonly")
        # Fixed the options to be more dynamic and localized
        self.scope_combo['values'] = ("Academic (edu.ng)", "Nigerian Gov (.gov.ng)", "News Sites", "General Web")
        self.scope_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(input_frame, text="Results:").pack(side=tk.LEFT, padx=5)
        self.num_results_var = tk.IntVar(value=13)
        self.num_results_spinbox = ttk.Spinbox(input_frame, from_=13, to=50, textvariable=self.num_results_var, width=5)
        self.num_results_spinbox.pack(side=tk.LEFT, padx=5)

        self.search_btn = ttk.Button(input_frame, text="Start Search", command=self.start_pipeline)
        self.search_btn.pack(side=tk.LEFT, padx=15)

        log_frame = ttk.Frame(root, padding=10)
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        ttk.Label(log_frame, text="Information Retrieved (Click URLs to open):").pack(anchor=tk.W)
        self.log_area = scrolledtext.ScrolledText(log_frame, height=15, state='disabled', wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        self.plot_frame = ttk.Frame(root, padding=10)
        self.plot_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.canvas_widget = None

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        self.root.update_idletasks()

    def log_link(self, url, summary):
        """Creates a clickable hyperlink in the Tkinter text widget."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, "\n[URL]: ")

        # Mark start and end of the URL for the tag
        start_index = self.log_area.index(tk.END + "-1c")
        self.log_area.insert(tk.END, url + "\n")
        end_index = self.log_area.index(tk.END + "-1c")

        # Apply hyperlink styling and bind the click event
        tag_name = f"link_{url}"
        self.log_area.tag_add(tag_name, start_index, end_index)
        self.log_area.tag_config(tag_name, foreground="blue", underline=1)
        self.log_area.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open_new(u))
        self.log_area.tag_bind(tag_name, "<Enter>", lambda e: self.log_area.config(cursor="hand2"))
        self.log_area.tag_bind(tag_name, "<Leave>", lambda e: self.log_area.config(cursor=""))

        self.log_area.insert(tk.END, f"[SUMMARY]: {summary}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        self.root.update_idletasks()

    def start_pipeline(self):
        query = self.query_var.get().strip()
        num_results = self.num_results_var.get()

        if not query:
            messagebox.showwarning("Input Error", "Please enter a search query.")
            return

        self.search_btn.config(state=tk.DISABLED)
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')

        if self.canvas_widget:
            self.canvas_widget.get_tk_widget().destroy()

        threading.Thread(target=self.run_search_and_scrape, args=(query, num_results), daemon=True).start()

    def run_search_and_scrape(self, query, num_results):
        try:
            scope = self.scope_var.get()
            search_query = query

            # Perfectly matching the combobox strings to ensure dynamic search works
            if scope == "Academic (edu.ng)":
                search_query = f"{query} site:edu.ng OR site:edu"
            elif scope == "Nigerian Gov (.gov.ng)":
                search_query = f"{query} site:gov.ng"
            elif scope == "News Sites":
                search_query = f"{query} news Nigeria"

            self.log(f"Searching DuckDuckGo for: '{search_query}'...")

            urls = []
            results = DDGS().text(search_query, max_results=num_results)

            if results:
                urls = [r.get('href') for r in results if r.get('href')]

            self.log(f"Found {len(urls)} initial URLs. Scraping and filtering out bad links...\n")
            if not urls:
                self.log("No results found.")
                return

            feature_counts, summaries = self.process_urls(urls)

            self.log("\n" + "=" * 50)
            self.log(f"INFORMATION RETRIEVED ({len(summaries)} successful links)")
            self.log("=" * 50)

            for url, summary in summaries.items():
                self.log_link(url, summary)  # Using the clickable link function

            top_features = feature_counts.most_common(10)
            if top_features:
                self.root.after(0, self.draw_plot, top_features)
            else:
                self.log("\n[!] No valid text extracted from any of the links.")

        except Exception as e:
            self.log(f"Pipeline Error: {e}")
        finally:
            self.root.after(0, lambda: self.search_btn.config(state=tk.NORMAL))

    def scrape_content(self, url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            response = requests.get(url, headers=headers, timeout=8)

            # FILTER: If it's a 403, 404, or any error, silently drop it by returning None
            if response.status_code != 200:
                return None, None, None

            # FILTER: Silently drop PDFs since we aren't parsing them right now
            if 'application/pdf' in response.headers.get('Content-Type', ''):
                return None, None, None

            soup = BeautifulSoup(response.text, "html.parser")
            paragraphs = soup.find_all("p")
            text = " ".join([p.get_text(strip=True) for p in paragraphs])

            clean_text = re.sub(r'\s+', ' ', text).strip()

            # FILTER: If the site returns less than 50 characters of useful text, drop it
            if len(clean_text) < 50:
                return None, None, None

            summary = clean_text[:300] + "..." if len(clean_text) > 300 else clean_text

            return url, text, summary

        except requests.exceptions.Timeout:
            return None, None, None  # Filter out timeouts completely
        except Exception:
            return None, None, None  # Filter out any other connection errors

    def extract_features(self, text):
        words = re.findall(r'\b[a-zA-Z]{5,}\b', text.lower())
        return [w for w in words if w not in STOP_WORDS]

    def process_urls(self, urls):
        feature_counts = Counter()
        summaries = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.scrape_content, url): url for url in urls}

            for future in concurrent.futures.as_completed(future_to_url):
                url, content, summary = future.result()

                # If the URL is None, it means our scrape_content function rejected it as a "low response"
                if url is None:
                    continue

                summaries[url] = summary
                if content.strip():
                    features = self.extract_features(content)
                    feature_counts.update(features)

        return feature_counts, summaries

    def draw_plot(self, top_features):
        features, counts = zip(*top_features)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(features, counts, color='mediumseagreen')
        ax.set_xticks(range(len(features)))
        ax.set_xticklabels(features, rotation=45, ha='right')
        ax.set_xlabel("Feature")
        ax.set_ylabel("Frequency")
        ax.set_title("Top 10 Extracted Features Across Successful Links")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.canvas_widget = canvas
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = WebScraperApp(root)
    root.mainloop()
