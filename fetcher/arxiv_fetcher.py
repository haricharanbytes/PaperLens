import arxiv
import re


def detect_input_type(user_input: str) -> str:
    """
    Detect whether the user entered a URL, paper ID, or title keyword.

    Returns: "url", "id", or "title"
    """
    user_input = user_input.strip()

    # URL pattern: contains arxiv.org
    if "arxiv.org" in user_input:
        return "url"

    # ID pattern: digits, dot, digits — e.g. 2303.08774 or arxiv:2303.08774
    if re.match(r"^(arxiv:)?(\d{4}\.\d{4,5})(v\d+)?$", user_input, re.IGNORECASE):
        return "id"

    # Everything else is treated as a title/keyword search
    return "title"


def extract_id_from_url(url: str) -> str:
    """
    Pull the paper ID out of an ArXiv URL.

    Handles formats like:
      https://arxiv.org/abs/2303.08774
      https://arxiv.org/pdf/2303.08774v2
    """
    match = re.search(r"arxiv\.org/(abs|pdf)/(\d{4}\.\d{4,5})(v\d+)?", url)
    if not match:
        raise ValueError(f"Could not extract paper ID from URL: {url}")
    return match.group(2)


def fetch_by_id(paper_id: str) -> dict:
    """Fetch a single paper by its exact ArXiv ID."""
    client = arxiv.Client()
    search = arxiv.Search(id_list=[paper_id])
    results = list(client.results(search))

    if not results:
        raise ValueError(f"No paper found for ID: {paper_id}")

    return _build_paper_dict(results[0])


def fetch_by_title(query: str, max_results: int = 5) -> list[dict]:
    """
    Search ArXiv by title/keyword and return top matches.
    User will then pick which one they want.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    results = list(client.results(search))

    if not results:
        raise ValueError(f"No papers found for query: '{query}'")

    return [_build_paper_dict(paper) for paper in results]


def _build_paper_dict(paper) -> dict:
    """Internal helper — converts an arxiv.Result object into a clean dict."""
    return {
        "id": paper.entry_id.split("/")[-1],   # e.g. "2303.08774v1" → "2303.08774v1"
        "title": paper.title,
        "authors": [str(a) for a in paper.authors],
        "abstract": paper.summary,
        "url": paper.entry_id,
        "pdf_url": paper.pdf_url,
        "published": str(paper.published.date()),
        "categories": paper.categories,
    }


def display_paper_info(paper: dict):
    """Pretty print paper info to terminal."""
    print(f"\n📄 Title     : {paper['title']}")
    print(f"👤 Authors   : {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
    print(f"📅 Published : {paper['published']}")
    print(f"🏷️  Categories: {', '.join(paper['categories'])}")
    print(f"🔗 URL       : {paper['url']}")
    print(f"\n📝 Abstract Preview:\n{paper['abstract'][:300]}...")


def get_paper_from_user() -> dict:
    """
    Interactive prompt — asks the user how they want to search,
    handles all three input types, and returns a single paper dict.
    """
    print("\n🔍 How would you like to find your paper?")
    print("   You can enter any of the following:")
    print("   • ArXiv URL  → https://arxiv.org/abs/2303.08774")
    print("   • Paper ID   → 2303.08774")
    print("   • Title/keywords → attention is all you need")

    user_input = input("\n➤ Enter URL, ID, or title: ").strip()

    if not user_input:
        raise ValueError("No input provided.")

    input_type = detect_input_type(user_input)

    #URL
    if input_type == "url":
        print("\n🔗 Detected: ArXiv URL")
        paper_id = extract_id_from_url(user_input)
        print(f"   Extracted ID: {paper_id}")
        print("   Fetching paper...")
        paper = fetch_by_id(paper_id)
        display_paper_info(paper)
        return paper

    #ID 
    elif input_type == "id":
        print("\n🔢 Detected: Paper ID")
        # Strip "arxiv:" prefix if present
        clean_id = re.sub(r"^arxiv:", "", user_input, flags=re.IGNORECASE)
        print("   Fetching paper...")
        paper = fetch_by_id(clean_id)
        display_paper_info(paper)
        return paper

    #Title / keyword 
    else:
        print(f"\n🔤 Detected: Title/keyword search → '{user_input}'")
        print("   Searching ArXiv...")
        papers = fetch_by_title(user_input)

        print(f"\n📚 Found {len(papers)} results. Pick one:\n")
        for i, p in enumerate(papers, 1):
            print(f"  [{i}] {p['title']}")
            print(f"      {', '.join(p['authors'][:2])} — {p['published']}\n")

        while True:
            choice = input(f"➤ Enter number (1–{len(papers)}): ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(papers):
                selected = papers[int(choice) - 1]
                print("\n✅ Selected:")
                display_paper_info(selected)
                return selected
            print(f"   ⚠️  Please enter a number between 1 and {len(papers)}.")


#Quick test 
if __name__ == "__main__":
    paper = get_paper_from_user()
    print(f"\n✅ Paper ready for summarization: {paper['title']}")