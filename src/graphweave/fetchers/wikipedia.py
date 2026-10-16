from dataclasses import dataclass

import wikipediaapi


@dataclass
class FetchedDocument:
    title: str
    content: str
    source: str
    url: str = ""


class WikipediaFetcher:
    def __init__(self, language: str = "en"):
        self.wiki = wikipediaapi.Wikipedia(
            language=language,
            user_agent="graphweave/0.1.0 (https://github.com/gabriele-bambini/graphweave)"
        )

    def fetch(self, topic: str, max_sections: int = 10) -> FetchedDocument | None:
        page = self.wiki.page(topic)
        if not page.exists():
            # try search
            return None

        sections = list(page.sections)[:max_sections]
        content_parts = [page.summary]
        for section in sections:
            content_parts.append(f"\n## {section.title}\n{section.text}")

        return FetchedDocument(
            title=page.title,
            content="\n".join(content_parts),
            source="wikipedia",
            url=page.fullurl,
        )

    def fetch_many(self, topics: list[str]) -> list[FetchedDocument]:
        docs = []
        for topic in topics:
            doc = self.fetch(topic)
            if doc:
                docs.append(doc)
        return docs
