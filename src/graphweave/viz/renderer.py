import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_html(graph_data: dict, title: str = "Knowledge Graph", output_path: Path | None = None) -> str:
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))
    template = env.get_template("graph.html")
    html = template.render(
        title=title,
        graph_json=json.dumps(graph_data),
        node_count=len(graph_data["nodes"]),
        edge_count=len(graph_data["links"]),
    )
    if output_path:
        output_path.write_text(html, encoding="utf-8")
    return html
