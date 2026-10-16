# ⬡ graphweave

**Automatically build and visualize knowledge graphs from any source.**

Give graphweave a topic. It crawls Wikipedia, ArXiv, your PDFs and URLs, extracts entities and relationships using an LLM, and generates an interactive knowledge graph — plus an Obsidian-compatible vault.

```bash
pip install graphweave
graphweave build "CRISPR" "gene therapy" --arxiv "CRISPR cancer 2024" --obsidian
```

> *An auto-generated Obsidian vault. No manual note-taking.*

**Install from source** (always works, no PyPI needed):

```bash
git clone https://github.com/Gabriele-Bambini/graphweave   # repository name after rename
cd graphweave
pip install -e ".[dev]"
pytest
```

---

## Features

- **Multi-source ingestion** — Wikipedia, ArXiv, any URL, local PDFs
- **LLM-powered extraction** — entities + relationships via Claude, GPT-4o, or local Ollama
- **Interactive D3.js visualization** — filter by node type, search, zoom, click to explore
- **Obsidian export** — generates a `.md` per node with `[[wikilinks]]`, ready to open
- **Save & share** — outputs `graph.json` + standalone `index.html`
- **Zero infrastructure** — runs entirely local, no database needed

---

## Quickstart

```bash
pip install graphweave
export ANTHROPIC_API_KEY=sk-...   # or OPENAI_API_KEY, or use --provider ollama
```

### From Wikipedia topics

```bash
graphweave build "transformer architecture" "attention mechanism" "BERT"
```

### Add ArXiv papers

```bash
graphweave build "CRISPR" --arxiv "CRISPR cancer therapy 2024" --arxiv-results 10
```

### From URLs and PDFs

```bash
graphweave build "climate change" \
  --url https://en.wikipedia.org/wiki/Climate_change \
  --pdf /path/to/report.pdf
```

### Export as Obsidian vault

```bash
graphweave build "quantum computing" --obsidian
# → .graphweave/notes/*.md with [[wikilinks]]
```

### Use local models (no API key)

```bash
ollama pull llama3.2
graphweave build "neural networks" --provider ollama --model llama3.2
```

---

## Python API

```python
from graphweave import GraphWeave

gw = GraphWeave(provider="anthropic")  # or "openai", "ollama"

gw.add_wikipedia(["CRISPR", "Gene therapy", "Cas9"])
gw.add_arxiv("CRISPR cancer therapy", max_results=8)
gw.add_pdf("/path/to/paper.pdf")
gw.add_url("https://example.com/article")

html_path = gw.build(output_dir="./my-graph", obsidian=True)
```

Access the underlying graph directly:

```python
import networkx as nx

kg = gw.kg
print(kg.stats())
# {'nodes': 147, 'edges': 312, 'density': 0.0145, 'components': 3}

# It's a standard NetworkX MultiDiGraph
central = nx.degree_centrality(kg.graph)
top_nodes = sorted(central, key=central.get, reverse=True)[:10]
```

---

## Output structure

```
.graphweave/
├── index.html      # standalone interactive visualization
├── graph.json      # full graph data (nodes + edges)
└── notes/          # Obsidian vault (with --obsidian)
    ├── CRISPR.md
    ├── Jennifer Doudna.md
    ├── gene editing.md
    └── ...
```

Open `index.html` directly in any browser — no server needed.

---

## CLI reference

```
graphweave build TOPICS...

  TOPICS              Wikipedia topics to fetch
  --arxiv, -a TEXT    ArXiv search query (repeatable)
  --url, -u TEXT      URL to fetch (repeatable)
  --pdf, -p PATH      PDF file (repeatable)
  --output, -o DIR    Output directory [default: .graphweave]
  --provider          anthropic | openai | ollama [default: anthropic]
  --model TEXT        Model override
  --ollama-host TEXT  Ollama host [default: http://localhost:11434]
  --obsidian          Export Obsidian-compatible vault
  --no-browser        Don't open browser after build
  --arxiv-results N   Max ArXiv results per query [default: 5]

graphweave serve GRAPH_PATH   Serve graph via local web server
graphweave stats  GRAPH_PATH  Show graph statistics
```

---

## How it works

```
Sources (Wikipedia / ArXiv / URL / PDF)
        ↓
   Text chunking
        ↓
  LLM extraction → (subject, predicate, object) triples
        ↓
  NetworkX graph
        ↓
  D3.js visualization + Obsidian vault
```

The LLM receives chunks of ~2000 words and returns structured JSON triples. Duplicates are deduplicated across chunks.

---

## Supported providers

| Provider | Default model | Notes |
|----------|--------------|-------|
| `anthropic` | `claude-haiku-4-5-20251001` | Fast, cheap, accurate |
| `openai` | `gpt-4o-mini` | Good alternative |
| `ollama` | `llama3.2` | Fully offline, no API key |

---

## Contributing

Contributions welcome. Open an issue or PR.

```bash
git clone https://github.com/gabriele-bambini/graphweave
cd graphweave
pip install -e ".[dev]"
pytest tests/
```

---

## License

MIT
