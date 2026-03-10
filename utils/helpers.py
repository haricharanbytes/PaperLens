import re
import tiktoken


# ── Constants ────────────────────────────────────────────────────────────────

CHUNK_SIZE   = 1500   # Max tokens per chunk sent to the LLM
CHUNK_OVERLAP = 150   # Tokens shared between chunks to preserve context


# ── Text Cleaning ────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Clean raw text from ArXiv abstracts.

    Removes:
      - LaTeX commands      e.g. \\textbf{word} → word
      - Inline math         e.g. $x^2$ → [MATH]
      - Excessive whitespace / newlines
      - Unicode artifacts   e.g. \xa0 (non-breaking space)

    Returns: clean, readable plain text
    """
    if not text or not text.strip():
        raise ValueError("Text is empty or None — nothing to clean.")

    # 1. Replace non-breaking spaces and unicode artifacts
    text = text.replace("\xa0", " ").replace("\u2019", "'")

    # 2. Remove LaTeX commands like \textbf{...}, \emph{...}, \cite{...}
    #    Pattern: backslash + word + optional {content}
    text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)  # keep inner content
    text = re.sub(r"\\[a-zA-Z]+", "", text)                 # remove bare commands

    # 3. Replace inline math $...$ or $$...$$ with placeholder
    text = re.sub(r"\$\$.*?\$\$", "[MATH]", text, flags=re.DOTALL)
    text = re.sub(r"\$.*?\$",     "[MATH]", text)

    # 4. Remove leftover LaTeX braces
    text = text.replace("{", "").replace("}", "")

    # 5. Collapse multiple newlines into one
    text = re.sub(r"\n{2,}", "\n\n", text)

    # 6. Collapse multiple spaces into one
    text = re.sub(r" {2,}", " ", text)

    # 7. Strip leading/trailing whitespace
    text = text.strip()

    return text


# ── Token Counting ───────────────────────────────────────────────────────────

def count_tokens(text: str, model: str = "gpt2") -> int:
    """
    Count how many tokens a string contains.

    We use tiktoken (OpenAI's tokenizer) — it's a good approximation
    for LLaMA/Mixtral token counts too, close enough for chunking purposes.

    Args:
        text:  The string to count
        model: Tokenizer model to use (gpt2 is fast and available offline)

    Returns: integer token count
    """
    encoder = tiktoken.get_encoding(model)
    return len(encoder.encode(text))


# ── Text Chunking ────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split a long text into overlapping token-aware chunks.

    Why chunking?
      LLMs have a context window limit (e.g. 8192 tokens for llama3-8b).
      A full research paper can be 10,000–50,000 tokens.
      We split it into chunks so each fits inside the model's limit.

    Why overlap?
      If a key sentence falls right at the boundary of two chunks,
      overlap ensures it's included in at least one chunk fully.

    Args:
        text:       The full cleaned text
        chunk_size: Max tokens per chunk
        overlap:    How many tokens to repeat between chunks

    Returns: list of text strings (chunks)
    """
    encoder  = tiktoken.get_encoding("gpt2")
    tokens   = encoder.encode(text)
    chunks   = []

    start = 0
    while start < len(tokens):
        end        = start + chunk_size
        chunk_toks = tokens[start:end]
        chunk_text = encoder.decode(chunk_toks)
        chunks.append(chunk_text)

        # Move forward by (chunk_size - overlap) to create the overlap window
        start += chunk_size - overlap

        # Stop if the remaining tokens are too small to be useful
        if start >= len(tokens):
            break

    return chunks


# ── Paper Preparation ────────────────────────────────────────────────────────

def prepare_paper(paper: dict) -> dict:
    """
    Full pipeline: take a raw paper dict from the fetcher,
    clean it and chunk the abstract, return enriched dict.

    For ArXiv papers, we only have the abstract (not full text) via API.
    The abstract is usually short enough to fit in one chunk,
    but we chunk anyway so this function works for any text length.

    Args:
        paper: dict from arxiv_fetcher.get_paper_from_user()

    Returns: same dict + added keys: "clean_abstract", "chunks", "token_count"
    """
    print("\n  Preparing paper for summarization...")

    # Clean the abstract
    clean = clean_text(paper["abstract"])

    # Count tokens
    token_count = count_tokens(clean)

    # Chunk the text
    chunks = chunk_text(clean)

    print(f"    Cleaned text  : {len(clean)} characters")
    print(f"    Token count   : {token_count} tokens")
    print(f"    Chunks created: {len(chunks)} chunk(s)")

    return {
        **paper,                       # Keep all original fields
        "clean_abstract": clean,
        "chunks": chunks,
        "token_count": token_count,
    }


# ── Quick test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample_text = """
    We present \\textbf{GPT-4}, a large multimodal model trained on $10^{25}$ FLOPS of compute.
    The model achieves state-of-the-art results on numerous benchmarks, including  
    \\emph{MMLU} and \\textit{HumanEval}.\n\n\n   Extra   spaces   here.
    """

    print("── Raw text ──────────────────────────────")
    print(repr(sample_text))

    cleaned = clean_text(sample_text)
    print("\n── Cleaned text ──────────────────────────")
    print(cleaned)

    tokens = count_tokens(cleaned)
    print(f"\n── Token count: {tokens} tokens ──────────")

    chunks = chunk_text(cleaned, chunk_size=20, overlap=5)
    print(f"\n── Chunks (size=20, overlap=5): {len(chunks)} chunk(s) ──")
    for i, c in enumerate(chunks, 1):
        print(f"\n  Chunk {i}: {repr(c)}")