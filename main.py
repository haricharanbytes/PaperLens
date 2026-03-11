import os
import sys
from dotenv import load_dotenv

from fetcher.arxiv_fetcher import get_paper_from_user
from utils.helpers import prepare_paper
from summarizer.summarize import summarize_paper, save_summary
from explainer.concept_explainer import explain_paper_concepts, save_explanations

load_dotenv()


#Banner

def print_banner():
    print("""
╔══════════════════════════════════════════════════════╗
║                                                      ║
║         ArXiv Research Paper Summarizer              ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
    """)


#Ask user 

def ask_options() -> dict:
    """
    Ask the user which features they want to run.
    Returns a dict of boolean flags.
    """
    print("\n  What would you like to do?")
    print("   [1] Summarize paper only")
    print("   [2] Summarize + Explain concepts")

    while True:
        choice = input("\n➤ Enter choice (1 or 2): ").strip()
        if choice in ("1", "2"):
            return {"explain_concepts": choice == "2"}
        print("     Please enter 1 or 2.")


def ask_model() -> str:
    """Let the user pick a Groq model."""
    print("\n Choose a model:")
    print("   [1] llama-3.3-70b-versatile  (best quality — recommended)")
    print("   [2] llama-3.1-8b-instant     (faster, lightweight)")
    print("   [3] llama-3.3-70b-specdec    (faster decoding, same quality)")
    print("   [4] openai/gpt-oss-120b    ")

    models = {
        "1": "llama-3.3-70b-versatile",
        "2": "llama-3.1-8b-instant",
        "3": "llama-3.3-70b-specdec",
        "4": "openai/gpt-oss-120b"
    }

    while True:
        choice = input("\n➤ Enter choice (1/2/3/4) or press Enter for default: ").strip()
        if choice == "":
            return "llama-3.3-70b-versatile"
        if choice in models:
            return models[choice]
        print("     Please enter 1, 2, 3 or 4.")


#Validation 

def check_api_key():
    """Check GROQ_API_KEY is set before doing anything."""
    if not os.getenv("GROQ_API_KEY"):
        print("\n ERROR: GROQ_API_KEY is not set.")
        print("   1. Go to https://console.groq.com/keys")
        print("   2. Create a free API key")
        print("   3. Add it to your .env file:")
        print("      GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx\n")
        sys.exit(1)


#Result Display

def print_summary(paper: dict, summary: str):
    print("\n" + "═" * 60)
    print(f"   {paper['title']}")
    print(f"   {', '.join(paper['authors'][:3])}")
    print(f"   {paper['published']}")
    print("═" * 60)
    print(summary)
    print("═" * 60)


def print_done(summary_path: str):
    print(f"\n All done!")
    print(f" Full output saved to: {summary_path}")
    print(f"\n   You can open it with:")
    print(f"   cat {summary_path}\n")


#Main

def main():
    print_banner()

    check_api_key()

    options = ask_options()
    model   = ask_model()

    print("\n" + "─" * 60)
    print("  STEP 1 — Fetch Paper")
    print("─" * 60)
    paper = get_paper_from_user()

    print("\n" + "─" * 60)
    print("  STEP 2 — Prepare Text")
    print("─" * 60)
    paper = prepare_paper(paper)

    print("\n" + "─" * 60)
    print("  STEP 3 — Summarize")
    print("─" * 60)
    summary = summarize_paper(paper, model=model)
    print_summary(paper, summary)

    summary_path = save_summary(paper, summary)

    if options["explain_concepts"]:
        print("\n" + "─" * 60)
        print("  STEP 4 — Explain Concepts")
        print("─" * 60)
        explanations = explain_paper_concepts(paper, summary, model=model)
        if explanations:
            save_explanations(paper, explanations)

    print_done(summary_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n Unexpected error: {e}")
        print("   Check your API key and internet connection.")
        sys.exit(1)