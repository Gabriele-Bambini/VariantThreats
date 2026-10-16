
import arxiv

from .wikipedia import FetchedDocument


class ArxivFetcher:
    def __init__(self):
        self.client = arxiv.Client()

    def fetch(self, query: str, max_results: int = 5) -> list[FetchedDocument]:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        docs = []
        for result in self.client.results(search):
            content = f"Title: {result.title}\n\nAuthors: {', '.join(a.name for a in result.authors)}\n\nAbstract: {result.summary}"
            docs.append(FetchedDocument(
                title=result.title,
                content=content,
                source="arxiv",
                url=result.entry_id,
            ))
        return docs
