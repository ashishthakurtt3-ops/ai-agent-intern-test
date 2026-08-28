from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-–][A-Za-z0-9]+)*")


@dataclass(frozen=True)
class Passage:
    filename: str
    heading: str
    text: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class RetrievedPassage:
    passage: Passage
    score: float


def _tokens(text: str) -> list[str]:
    return [x.lower() for x in TOKEN_RE.findall(text)]


def _parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---"):
        return {}, raw
    parts = raw.split("---", 2)
    if len(parts) != 3:
        return {}, raw
    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            metadata[k.strip()] = v.strip().strip("\"'")
    return metadata, parts[2].lstrip()


def load_passages(knowledge_dir: str | Path) -> list[Passage]:
    root = Path(knowledge_dir)
    passages: list[Passage] = []
    for path in sorted(root.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        metadata, body = _parse_frontmatter(raw)
        current_heading = metadata.get("title", path.stem)
        chunk: list[str] = []
        def flush() -> None:
            nonlocal chunk
            text = "\n".join(chunk).strip()
            if text:
                passages.append(Passage(path.name, current_heading, text, metadata.copy()))
            chunk = []
        for line in body.splitlines():
            if line.startswith("## ") or line.startswith("# "):
                flush()
                current_heading = line.lstrip("#").strip()
            elif line.startswith("---"):
                continue
            else:
                chunk.append(line)
        flush()
    return passages


class Retriever:
    """Small deterministic TF-IDF retriever with explicit document precedence."""

    def __init__(self, passages: list[Passage]) -> None:
        self.passages = passages
        self.doc_freq = Counter()
        self.vectors: list[dict[str, float]] = []
        for p in passages:
            terms = set(_tokens(f"{p.filename} {p.heading} {p.text}"))
            self.doc_freq.update(terms)
        n = max(1, len(passages))
        for p in passages:
            counts = Counter(_tokens(f"{p.filename} {p.heading} {p.text}"))
            total = max(1, sum(counts.values()))
            vec: dict[str, float] = {}
            for term, count in counts.items():
                idf = math.log((1 + n) / (1 + self.doc_freq[term])) + 1
                vec[term] = (count / total) * idf
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.vectors.append({k: v / norm for k, v in vec.items()})

    @staticmethod
    def _precedence(p: Passage) -> float:
        status = p.metadata.get("status", "active").lower()
        authority = p.metadata.get("policy_authority", "").lower()
        audience = p.metadata.get("audience", "").lower()
        score = 0.0
        if status == "active": score += 1.0
        if status in {"superseded", "legacy", "archived"}: score -= 2.0
        if authority == "official": score += 1.4
        elif authority in {"internal", "unofficial"}: score -= 0.8
        if audience == "customer": score += 0.4
        if "internal" in p.filename.lower() or "migration" in p.filename.lower(): score -= 1.8
        return score

    def search(self, query: str, top_k: int = 6) -> list[RetrievedPassage]:
        q_counts = Counter(_tokens(query))
        q_vec: dict[str, float] = {}
        total = max(1, sum(q_counts.values()))
        n = max(1, len(self.passages))
        for term, count in q_counts.items():
            idf = math.log((1 + n) / (1 + self.doc_freq.get(term, 0))) + 1
            q_vec[term] = (count / total) * idf
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0
        q_vec = {k: v / q_norm for k, v in q_vec.items()}

        scored: list[RetrievedPassage] = []
        for p, vec in zip(self.passages, self.vectors):
            lexical = sum(q_vec.get(k, 0.0) * v for k, v in vec.items())
            heading_bonus = 0.25 if any(t in _tokens(p.heading) for t in q_counts) else 0.0
            score = lexical + heading_bonus + 0.20 * self._precedence(p)
            scored.append(RetrievedPassage(p, score))
        return sorted(scored, key=lambda x: x.score, reverse=True)[:top_k]
