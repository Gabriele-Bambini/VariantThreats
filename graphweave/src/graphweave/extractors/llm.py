from __future__ import annotations
import json
import re
from dataclasses import dataclass
from typing import Literal

EXTRACTION_PROMPT = """Extract all entities and relationships from the text below.

Return ONLY a JSON array of triples. Each triple must have:
- "subject": entity name (concise, 1-4 words)
- "predicate": relationship verb (concise, 1-3 words)
- "object": entity name (concise, 1-4 words)
- "subject_type": one of [person, organization, concept, place, event, technology, disease, drug, gene, other]
- "object_type": one of [person, organization, concept, place, event, technology, disease, drug, gene, other]

Rules:
- Extract 10-30 triples per chunk
- Prefer specific, meaningful relationships over generic ones
- Normalize entity names (use canonical form)
- No duplicates

Text:
\"\"\"
{text}
\"\"\"

JSON array:"""


@dataclass
class Triple:
    subject: str
    predicate: str
    object: str
    subject_type: str = "other"
    object_type: str = "other"
    source: str = ""

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object,
            "subject_type": self.subject_type,
            "object_type": self.object_type,
            "source": self.source,
        }


def _chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def _parse_triples(raw: str, source: str) -> list[Triple]:
    # extract JSON array from response
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group())
        triples = []
        for item in data:
            if all(k in item for k in ("subject", "predicate", "object")):
                triples.append(Triple(
                    subject=str(item["subject"]).strip(),
                    predicate=str(item["predicate"]).strip(),
                    object=str(item["object"]).strip(),
                    subject_type=item.get("subject_type", "other"),
                    object_type=item.get("object_type", "other"),
                    source=source,
                ))
        return triples
    except (json.JSONDecodeError, ValueError):
        return []


class LLMExtractor:
    def __init__(
        self,
        provider: Literal["anthropic", "openai", "ollama"] = "anthropic",
        model: str | None = None,
        api_key: str | None = None,
        ollama_host: str = "http://localhost:11434",
    ):
        self.provider = provider
        self.ollama_host = ollama_host

        if provider == "anthropic":
            from anthropic import Anthropic
            self._client = Anthropic(api_key=api_key)
            self._model = model or "claude-haiku-4-5-20251001"
        elif provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)
            self._model = model or "gpt-4o-mini"
        elif provider == "ollama":
            import ollama
            self._client = ollama.Client(host=ollama_host)
            self._model = model or "llama3.2"

    def _call_llm(self, text: str) -> str:
        prompt = EXTRACTION_PROMPT.format(text=text)

        if self.provider == "anthropic":
            msg = self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text

        elif self.provider == "openai":
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0,
            )
            return resp.choices[0].message.content

        elif self.provider == "ollama":
            resp = self._client.chat(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp["message"]["content"]

        return "[]"

    def extract(self, text: str, source: str = "", chunk_size: int = 2000) -> list[Triple]:
        chunks = _chunk_text(text, chunk_size=chunk_size)
        all_triples: list[Triple] = []
        seen = set()

        for chunk in chunks:
            raw = self._call_llm(chunk)
            triples = _parse_triples(raw, source)
            for t in triples:
                key = (t.subject.lower(), t.predicate.lower(), t.object.lower())
                if key not in seen:
                    seen.add(key)
                    all_triples.append(t)

        return all_triples
