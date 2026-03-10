import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


# ── Model Setup ──────────────────────────────────────────────────────────────

def get_llm(model: str = "llama3-70b-8192", temperature: float = 0.3) -> ChatGroq:
    """
    Initialize the Groq LLM via LangChain.

    Args:
        model:       Groq model name (default: llama3-70b-8192)
        temperature: 0.0 = focused/deterministic, 1.0 = creative/random
                     0.3 is a sweet spot for factual summarization

    Returns: ChatGroq LLM instance
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found. "
            "Make sure it's set in your .env file."
        )

    return ChatGroq(
        api_key=api_key,
        model_name=model,
        temperature=temperature,
    )


# ── Prompts ──────────────────────────────────────────────────────────────────

# Used when paper fits in a single chunk (most abstracts)
SINGLE_CHUNK_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a research assistant who specializes in explaining "
        "complex academic papers in simple, clear language. "
        "Your summaries are structured, easy to follow, and avoid unnecessary jargon."
    ),
    (
        "human",
        """Summarize the following research paper content.

Structure your response exactly like this:

 WHAT IS THIS PAPER ABOUT?
(1-2 sentences, plain English, like you're explaining to a smart friend)

 KEY CONTRIBUTIONS
(3-5 bullet points of the most important findings or ideas)

 HOW DID THEY DO IT?
(2-3 sentences about the methodology / approach)

 RESULTS & IMPACT
(2-3 sentences about outcomes and why it matters)

---
Paper content:
{text}
"""
    )
])


# Used for each chunk when the paper is too long (map step)
MAP_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a precise research assistant. Extract only the most important "
        "information from this section of a research paper."
    ),
    (
        "human",
        """Extract the key points from this section of a research paper.
Be concise — 3 to 5 bullet points max.

Section:
{text}
"""
    )
])


# Used to combine chunk summaries into one final summary (reduce step)
REDUCE_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a research assistant who synthesizes information from multiple "
        "sections of a paper into one clear, unified summary."
    ),
    (
        "human",
        """Below are key points extracted from different sections of a research paper.
Combine them into one structured summary.

Structure your response exactly like this:

 WHAT IS THIS PAPER ABOUT?
(1-2 sentences, plain English)

 KEY CONTRIBUTIONS
(3-5 bullet points)

 HOW DID THEY DO IT?
(2-3 sentences)

 RESULTS & IMPACT
(2-3 sentences)

---
Extracted points:
{text}
"""
    )
])


# ── Core Summarization Logic ─────────────────────────────────────────────────

def summarize_single(text: str, llm: ChatGroq) -> str:
    """
    Summarize text that fits in one LLM call.
    Used when the paper abstract is short enough (most cases).

    Chain: prompt → llm → string parser
    """
    chain = SINGLE_CHUNK_PROMPT | llm | StrOutputParser()
    return chain.invoke({"text": text})


def summarize_chunks(chunks: list[str], llm: ChatGroq) -> str:
    """
    Map-Reduce summarization for long texts with multiple chunks.

    Step 1 — MAP:    Summarize each chunk independently
    Step 2 — REDUCE: Combine all chunk summaries into one final summary

    This mirrors how a human would read a long paper:
    take notes on each section, then write a unified summary.
    """
    print(f"\n   📄 Processing {len(chunks)} chunk(s) with Map-Reduce...")

    # ── MAP: summarize each chunk ─────────────────────────────────────────
    map_chain = MAP_PROMPT | llm | StrOutputParser()

    chunk_summaries = []
    for i, chunk in enumerate(chunks, 1):
        print(f"    Summarizing chunk {i}/{len(chunks)}...")
        summary = map_chain.invoke({"text": chunk})
        chunk_summaries.append(summary)

    # ── REDUCE: combine all chunk summaries ───────────────────────────────
    print("    Combining chunk summaries...")
    combined = "\n\n---\n\n".join(chunk_summaries)
    reduce_chain = REDUCE_PROMPT | llm | StrOutputParser()
    final_summary = reduce_chain.invoke({"text": combined})

    return final_summary


def summarize_paper(paper: dict, model: str = "llama-3.3-70b-versatile") -> str:
    """
    Main entry point for summarization.

    Automatically decides between single-call or map-reduce
    based on how many chunks the paper was split into.

    Args:
        paper: enriched dict from helpers.prepare_paper()
        model: Groq model to use

    Returns: final summary string
    """
    print(f"\n Starting summarization with {model}...")

    llm    = get_llm(model=model)
    chunks = paper.get("chunks", [])

    if not chunks:
        raise ValueError("Paper has no chunks. Did you run helpers.prepare_paper()?")

    # Single chunk → one direct LLM call
    if len(chunks) == 1:
        print("   ⚡ Single chunk detected — using direct summarization")
        return summarize_single(chunks[0], llm)

    # Multiple chunks → map-reduce pipeline
    print(f"     Multiple chunks detected — using Map-Reduce")
    return summarize_chunks(chunks, llm)


def save_summary(paper: dict, summary: str) -> str:
    """
    Save the summary to a .txt file in outputs/summaries/.

    Returns: the file path where it was saved
    """
    os.makedirs("outputs/summaries", exist_ok=True)

    # Sanitize title for use as filename
    safe_title = re.sub(r"[^\w\s-]", "", paper["title"])
    safe_title = safe_title.strip().replace(" ", "_")[:60]
    filename   = f"outputs/summaries/{safe_title}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"PAPER: {paper['title']}\n")
        f.write(f"AUTHORS: {', '.join(paper['authors'][:5])}\n")
        f.write(f"PUBLISHED: {paper['published']}\n")
        f.write(f"URL: {paper['url']}\n")
        f.write(f"{'=' * 60}\n\n")
        f.write(summary)

    return filename


# ── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import re

    # Simulate a prepared paper dict (as if helpers.prepare_paper() ran)
    mock_paper = {
        "title":    "Attention Is All You Need",
        "authors":  ["Vaswani", "Shazeer", "Parmar"],
        "published": "2017-06-12",
        "url":      "https://arxiv.org/abs/1706.03762",
        "chunks": [
            """The dominant sequence transduction models are based on complex recurrent 
            or convolutional neural networks. We propose a new architecture, the Transformer, 
            based solely on attention mechanisms, dispensing with recurrence and convolutions 
            entirely. The Transformer achieves state-of-the-art results on machine translation 
            tasks while being more parallelizable and requiring significantly less training time."""
        ],
        "token_count": 80
    }

    summary = summarize_paper(mock_paper, model="llama-3.3-70b-versatile")

    print("\n" + "=" * 60)
    print(" SUMMARY")
    print("=" * 60)
    print(summary)

    path = save_summary(mock_paper, summary)
    print(f"\n Saved to: {path}")