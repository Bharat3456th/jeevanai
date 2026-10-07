import math
import re
from collections import Counter

STOP = set("""a an the and or but if then else of to in on at by for with from as is are was were be been being it this that
these those i you he she we they them his her our your their not no do does did have has had will would can could should may might
about into over under than so such also very just more most other some any each which who whom what when where why how""".split())


def sentences(text: str):
    parts = re.split(r"(?<=[.!?])\s+|\n{2,}", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 20]


def words(text: str):
    return [w for w in re.findall(r"[A-Za-z][A-Za-z\-']+", text.lower()) if w not in STOP and len(w) > 2]


def stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3 and not w.endswith("ss"):
            return w[: -len(suf)]
    return w


def extractive_summary(text: str, max_sentences: int = 5) -> str:
    sents = sentences(text)
    if len(sents) <= max_sentences:
        return " ".join(sents) or text.strip()[:500]
    freq = Counter(words(text))
    scored = []
    for i, s in enumerate(sents):
        ws = words(s)
        scored.append((sum(freq[w] for w in ws) / (len(ws) + 1), i, s))
    top = sorted(sorted(scored, reverse=True)[:max_sentences], key=lambda x: x[1])
    return " ".join(s for _, _, s in top)


def chunk_text(text: str, size: int = 900, overlap: int = 150):
    text = re.sub(r"\s+", " ", text).strip()
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i + size])
        i += size - overlap
    return chunks


def top_chunks(text: str, question: str, k: int = 3):
    """BM25 ranking of text chunks against the question."""
    chunks = chunk_text(text)
    q = {stem(w) for w in words(question)}
    if not chunks or not q:
        return []
    docs = [Counter(stem(w) for w in words(c)) for c in chunks]
    lens = [sum(d.values()) for d in docs]
    avg = (sum(lens) / len(lens)) or 1
    n_docs = len(chunks)
    scored = []
    for d, ln, c in zip(docs, lens, chunks):
        score = 0.0
        for t in q:
            f = d.get(t, 0)
            if not f:
                continue
            n = sum(1 for x in docs if t in x)
            idf = math.log(1 + (n_docs - n + 0.5) / (n + 0.5))
            score += idf * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * ln / avg))
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for s, c in scored[:k] if s > 0]
