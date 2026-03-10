import os
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()


# ── Prompts ──────────────────────────────────────────────────────────────────

JARGON_EXTRACTOR_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert at identifying technical and academic jargon "
        "in research papers. You extract terms that a general audience "
        "would find confusing or unfamiliar."
    ),
    (
        "human",
        """From the text below, extract all technical terms, acronyms, and 
academic jargon that a non-expert might not understand.

Rules:
- Return ONLY a comma-separated list of terms
- No explanations, no numbering, no bullet points
- Maximum 10 terms
- Prioritize the most important and confusing ones
- Include acronyms (e.g. BERT, RLHF, CNN)

Text:
{text}

Output (comma-separated terms only):"""
    )
])


CONCEPT_EXPLAINER_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are a brilliant teacher who explains complex concepts "
        "from research papers in simple, relatable language. "
        "You use analogies and real-world examples wherever possible."
    ),
    (
        "human",
        """Explain the following technical term from a research paper context.

Term: {term}
Paper context: {context}

Structure your explanation like this:

 SIMPLE DEFINITION
(1-2 sentences, no jargon, like explaining to a curious 16-year-old)

 REAL-WORLD ANALOGY
(1 relatable analogy or comparison)

 IN THIS PAPER
(1 sentence: why this term matters specifically in this paper's context)
"""
    )
])


# ── Jargon Extraction ────────────────────────────────────────────────────────

def extract_jargon(text: str, llm: ChatGroq) -> list[str]:
    """
    Ask the LLM to identify technical terms from the summary text.

    Returns: list of term strings e.g. ["Transformer", "BERT", "attention mechanism"]
    """
    print("\n🔍 Scanning for technical terms...")

    chain  = JARGON_EXTRACTOR_PROMPT | llm | StrOutputParser()
    result = chain.invoke({"text": text})

    # Parse the comma-separated response into a clean list
    terms = [term.strip() for term in result.split(",") if term.strip()]

    # Remove any empty strings or terms that are just punctuation
    terms = [t for t in terms if re.search(r"[a-zA-Z]", t)]

    print(f"   Found {len(terms)} technical term(s): {', '.join(terms)}")
    return terms


# ── Concept Explanation ───────────────────────────────────────────────────────

def explain_term(term: str, context: str, llm: ChatGroq) -> str:
    """
    Generate a plain-English explanation for a single technical term.

    Args:
        term:    The jargon term to explain e.g. "attention mechanism"
        context: The paper title/abstract — gives the LLM context
        llm:     The ChatGroq instance

    Returns: formatted explanation string
    """
    chain = CONCEPT_EXPLAINER_PROMPT | llm | StrOutputParser()
    return chain.invoke({"term": term, "context": context})


def explain_all_concepts(terms: list[str], paper: dict, llm: ChatGroq) -> dict[str, str]:
    """
    Explain every extracted jargon term one by one.

    Args:
        terms:  List of technical terms from extract_jargon()
        paper:  The paper dict (used for context)
        llm:    The ChatGroq instance

    Returns: dict mapping term → explanation
             e.g. {"Transformer": "...", "attention": "..."}
    """
    context = f"{paper['title']}. {paper.get('clean_abstract', paper.get('abstract', ''))[:300]}"

    explanations = {}
    for i, term in enumerate(terms, 1):
        print(f"   💡 Explaining term {i}/{len(terms)}: '{term}'...")
        explanation        = explain_term(term, context, llm)
        explanations[term] = explanation

    return explanations


# ── Display ───────────────────────────────────────────────────────────────────

def display_explanations(explanations: dict[str, str]):
    """Pretty print all concept explanations to the terminal."""
    print("\n" + "=" * 60)
    print(" CONCEPT EXPLAINER")
    print("=" * 60)

    for i, (term, explanation) in enumerate(explanations.items(), 1):
        print(f"\n{'─' * 60}")
        print(f"  [{i}] {term.upper()}")
        print(f"{'─' * 60}")
        print(explanation)

    print("\n" + "=" * 60)


# ── Main Entry Point ──────────────────────────────────────────────────────────

def explain_paper_concepts(paper: dict, summary: str, model: str = "llama-3.3-70b-versatile") -> dict[str, str]:
    """
    Full pipeline: given a paper and its summary,
    extract jargon and explain every term.

    Args:
        paper:   enriched paper dict from helpers.prepare_paper()
        summary: the summary string from summarize_paper()
        model:   Groq model to use

    Returns: dict of { term: explanation }
    """
    print(f"\n Running Concept Explainer with {model}...")

    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model_name=model,
        temperature=0.3,
    )

    # Step 1: Extract jargon from the summary
    terms = extract_jargon(summary, llm)

    if not terms:
        print("   ℹ️  No technical terms found — paper may already be written simply.")
        return {}

    # Step 2: Explain each term
    print(f"\n Generating explanations for {len(terms)} term(s)...")
    explanations = explain_all_concepts(terms, paper, llm)

    # Step 3: Display
    display_explanations(explanations)

    return explanations


def save_explanations(paper: dict, explanations: dict[str, str]) -> str:
    """
    Append concept explanations to the existing summary file.

    Returns: file path
    """
    os.makedirs("outputs/summaries", exist_ok=True)

    safe_title = re.sub(r"[^\w\s-]", "", paper["title"])
    safe_title = safe_title.strip().replace(" ", "_")[:60]
    filename   = f"outputs/summaries/{safe_title}.txt"

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"\n\n{'=' * 60}\n")
        f.write("💡 CONCEPT EXPLAINER\n")
        f.write(f"{'=' * 60}\n")

        for term, explanation in explanations.items():
            f.write(f"\n{'─' * 40}\n")
            f.write(f"  {term.upper()}\n")
            f.write(f"{'─' * 40}\n")
            f.write(explanation + "\n")

    return filename


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    mock_paper = {
        "title":   "Attention Is All You Need",
        "authors": ["Vaswani", "Shazeer"],
        "abstract": """The dominant sequence transduction models are based on complex 
        recurrent or convolutional neural networks that include an encoder and a decoder.
        We propose the Transformer, a model architecture based solely on attention mechanisms.
        The model achieves state-of-the-art BLEU scores on WMT translation benchmarks.""",
        "clean_abstract": """The dominant sequence transduction models are based on complex 
        recurrent or convolutional neural networks. We propose the Transformer, based solely 
        on attention mechanisms. Achieves state-of-the-art BLEU scores on WMT benchmarks.""",
        "published": "2017-06-12",
        "url": "https://arxiv.org/abs/1706.03762",
    }

    mock_summary = """
     WHAT IS THIS PAPER ABOUT?
    This paper introduces the Transformer architecture, replacing RNNs with self-attention.

     KEY CONTRIBUTIONS
    • Introduces multi-head self-attention mechanism
    • Eliminates recurrence — enables full parallelization
    • Achieves state-of-the-art BLEU score on WMT translation tasks
    • Positional encodings replace sequential processing

     HOW DID THEY DO IT?
    The model uses stacked encoder-decoder blocks with multi-head attention layers,
    feed-forward networks, and residual connections with layer normalization.

     RESULTS & IMPACT
    Achieved 28.4 BLEU on WMT English-to-German. Became the foundation for BERT, GPT,
    and virtually every modern LLM.
    """

    explanations = explain_paper_concepts(mock_paper, mock_summary, model="llama-3.3-70b-versatile")
    path = save_explanations(mock_paper, explanations)
    print(f"\n💾 Explanations appended to: {path}")