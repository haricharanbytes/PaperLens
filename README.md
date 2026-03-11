#  PaperLens

## Project Structure

```
arxiv-summarizer/
├── app/
│   ├── app.py                        ← Flask server + API routes
│   ├── templates/
│   │   ├── index.html                ← Landing page
│   │   └── summarizer.html           ← App page
│   └── static/
│       ├── css/
│       │   ├── landing.css           ← Landing styles
│       │   └── app.css               ← App styles
│       └── js/
│           ├── landing.js            ← Scroll animations
│           └── app.js                ← Pipeline UI logic
├── fetcher/
│   └── arxiv_fetcher.py              ← ArXiv API integration
├── utils/
│   └── helpers.py                    ← Text cleaning & chunking
├── summarizer/
│   └── summarize.py                  ← LangChain + Groq summarization
├── explainer/
│   └── concept_explainer.py          ← Jargon detection & explanation
├── outputs/
│   └── summaries/                    ← Saved summary outputs
├── web_screenshots/                  ← App screenshots
├── main.py                           ← CLI entry point
├── requirements.txt
├── Procfile
└── .gitignore
```

## Screenshots

<table>
  <tr>
    <td><img src="web_screenshots/1.jpg" alt="Screenshot 1" width="100%"/></td>
    <td><img src="web_screenshots/2.jpg" alt="Screenshot 2" width="100%"/></td>
  </tr>
  <tr>
    <td><img src="web_screenshots/3.jpg" alt="Screenshot 3" width="100%"/></td>
    <td><img src="web_screenshots/4.jpg" alt="Screenshot 4" width="100%"/></td>
  </tr>
  <tr>
    <td><img src="web_screenshots/5.jpg" alt="Screenshot 5" width="100%"/></td>
    <td><img src="web_screenshots/6.jpg" alt="Screenshot 6" width="100%"/></td>
  </tr>
  <tr>
    <td><img src="web_screenshots/7.jpg" alt="Screenshot 7" width="100%"/></td>
    <td><img src="web_screenshots/8.jpg" alt="Screenshot 8" width="100%"/></td>
  </tr>
</table>

<p align="center">
  <b>1. Home Page</b><br>
  <img src="web_screenshots/1.jpg" width="800"><br>
  <i>This shows the main landing page of PaperLens.</i>
</p>

<p align="center">
  <b>2. Pipeline</b><br>
  <img src="web_screenshots/2.jpg" width="800"><br>
  <i>This shows the steps in summarizing the paper.</i>
</p>

<p align="center">
  <b>3. Start</b><br>
  <img src="web_screenshots/3.jpg" width="800"><br>
  <i>Stop skimming and start summarizing.</i>
</p>

<p align="center">
  <b>4. Search Page</b><br>
  <img src="web_screenshots/4.jpg" width="800"><br>
  <i>Search by ID, URL, and Keyword of the paper.</i>
</p>

<p align="center">
  <b>5. Search Result</b><br>
  <img src="web_screenshots/5.jpg" width="800"><br>
  <i>Result of the fetched paper from arXiv API.</i>
</p>

<p align="center">
  <b>6. Summarize Process</b><br>
  <img src="web_screenshots/6.jpg" width="800"><br>
  <i>Shows the process of Fetching, Cleaning, Summarizing, and Explaining.</i>
</p>

<p align="center">
  <b>7. Summarized Text</b><br>
  <img src="web_screenshots/7.jpg" width="800"><br>
  <i>Displays the summarized text in a structured format.</i>
</p>

<p align="center">
  <b>8. Term Explaining</b><br>
  <img src="web_screenshots/8.jpg" width="800"><br>
  <i>Explanation of jargons with examples and context of the paper.</i>
</p>