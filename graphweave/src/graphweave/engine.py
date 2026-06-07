from __future__ import annotations
import os
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .fetchers import WikipediaFetcher, ArxivFetcher, URLFetcher, PDFFetcher
from .fetchers.wikipedia import FetchedDocument
from .extractors import LLMExtractor
from .graph import KnowledgeGraph
from .viz import render_html

console = Console()


class GraphWeave:
    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        api_key: str | None = None,
        ollama_host: str = "http://localhost:11434",
    ):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.extractor = LLMExtractor(
            provider=provider,
            model=model,
            api_key=api_key,
            ollama_host=ollama_host,
        )
        self.kg = KnowledgeGraph()

    def add_wikipedia(self, topics: list[str]) -> None:
        fetcher = WikipediaFetcher()
        with Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"), console=console) as p:
            task = p.add_task("Fetching Wikipedia…", total=len(topics))
            for topic in topics:
                p.update(task, description=f"Wikipedia: {topic}")
                doc = fetcher.fetch(topic)
                if doc:
                    self._process_doc(doc)
                p.advance(task)

    def add_arxiv(self, query: str, max_results: int = 5) -> None:
        fetcher = ArxivFetcher()
        with console.status(f"[bold blue]Fetching ArXiv: {query}…"):
            docs = fetcher.fetch(query, max_results=max_results)
        for doc in docs:
            self._process_doc(doc)

    def add_url(self, url: str) -> None:
        fetcher = URLFetcher()
        with console.status(f"[bold blue]Fetching URL: {url}…"):
            doc = fetcher.fetch(url)
        if doc:
            self._process_doc(doc)

    def add_pdf(self, path: str) -> None:
        fetcher = PDFFetcher()
        doc = fetcher.fetch(path)
        if doc:
            self._process_doc(doc)

    def _process_doc(self, doc: FetchedDocument) -> None:
        with console.status(f"[bold green]Extracting triples: {doc.title[:50]}…"):
            triples = self.extractor.extract(doc.content, source=doc.source)
        self.kg.add_triples(triples)
        console.print(f"  [green]✓[/green] {doc.title[:60]} — [dim]{len(triples)} triples[/dim]")

    def build(
        self,
        output_dir: str | Path = ".graphweave",
        open_browser: bool = True,
        obsidian: bool = False,
    ) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        stats = self.kg.stats()
        console.print(f"\n[bold]Graph built:[/bold] {stats['nodes']} nodes, {stats['edges']} edges")

        # Save graph JSON
        graph_json_path = output_dir / "graph.json"
        self.kg.save(graph_json_path)

        # Render HTML
        html_path = output_dir / "index.html"
        render_html(self.kg.to_d3(), title="Knowledge Graph", output_path=html_path)
        console.print(f"[bold green]✓[/bold green] Visualization → {html_path}")

        # Obsidian export
        if obsidian:
            self.kg.to_obsidian(output_dir)
            console.print(f"[bold green]✓[/bold green] Obsidian vault → {output_dir / 'notes'}")

        if open_browser:
            import webbrowser
            webbrowser.open(f"file://{html_path.absolute()}")

        return html_path
