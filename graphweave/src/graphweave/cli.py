import click
from pathlib import Path
from rich.console import Console
from rich import print as rprint

console = Console()


@click.group()
@click.version_option()
def main():
    """graphweave — Build knowledge graphs from any source, automatically."""
    pass


@main.command()
@click.argument("topics", nargs=-1, required=True)
@click.option("--arxiv", "-a", multiple=True, help="ArXiv search query")
@click.option("--url", "-u", multiple=True, help="URL to fetch")
@click.option("--pdf", "-p", multiple=True, type=click.Path(exists=True), help="PDF file path")
@click.option("--output", "-o", default=".graphweave", show_default=True, help="Output directory")
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "openai", "ollama"]), show_default=True)
@click.option("--model", default=None, help="Model override")
@click.option("--ollama-host", default="http://localhost:11434", show_default=True)
@click.option("--obsidian", is_flag=True, help="Export Obsidian-compatible vault")
@click.option("--no-browser", is_flag=True, help="Don't open browser after build")
@click.option("--arxiv-results", default=5, show_default=True, help="Max ArXiv results per query")
def build(topics, arxiv, url, pdf, output, provider, model, ollama_host, obsidian, no_browser, arxiv_results):
    """Build a knowledge graph from Wikipedia topics and other sources.

    \b
    Examples:
      graphweave build "CRISPR" "gene editing" --arxiv "CRISPR cancer therapy"
      graphweave build "transformer" "attention mechanism" --provider ollama --model llama3.2
      graphweave build "COVID-19" --url https://example.com/article.html --obsidian
    """
    from .engine import GraphWeave

    rprint(f"\n[bold cyan]⬡ graphweave[/bold cyan] — building knowledge graph\n")

    gw = GraphWeave(provider=provider, model=model, ollama_host=ollama_host)

    if topics:
        gw.add_wikipedia(list(topics))

    for q in arxiv:
        gw.add_arxiv(q, max_results=arxiv_results)

    for u in url:
        gw.add_url(u)

    for p in pdf:
        gw.add_pdf(p)

    html_path = gw.build(output_dir=output, open_browser=not no_browser, obsidian=obsidian)
    rprint(f"\n[bold green]Done![/bold green] Open [link=file://{html_path.absolute()}]{html_path}[/link]")


@main.command()
@click.argument("graph_path", type=click.Path(exists=True))
@click.option("--port", default=8000, show_default=True)
def serve(graph_path, port):
    """Serve an existing graph visualization."""
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    graph_dir = Path(graph_path).parent
    app = FastAPI()

    @app.get("/")
    def index():
        return FileResponse(str(graph_dir / "index.html"))

    @app.get("/graph.json")
    def graph():
        return JSONResponse(content=__import__("json").loads((graph_dir / "graph.json").read_text()))

    rprint(f"[bold green]Serving graph at[/bold green] http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")


@main.command()
@click.argument("graph_path", type=click.Path(exists=True))
def stats(graph_path):
    """Show statistics about a saved graph."""
    from .graph import KnowledgeGraph
    kg = KnowledgeGraph.load(Path(graph_path))
    s = kg.stats()
    rprint(f"[bold]Nodes:[/bold]     {s['nodes']}")
    rprint(f"[bold]Edges:[/bold]     {s['edges']}")
    rprint(f"[bold]Density:[/bold]   {s['density']}")
    rprint(f"[bold]Components:[/bold] {s['components']}")
