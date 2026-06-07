from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

import networkx as nx

from ..extractors.llm import Triple

NODE_COLORS = {
    "person": "#4A90D9",
    "organization": "#E67E22",
    "concept": "#27AE60",
    "place": "#8E44AD",
    "event": "#E74C3C",
    "technology": "#1ABC9C",
    "disease": "#C0392B",
    "drug": "#F39C12",
    "gene": "#2ECC71",
    "other": "#95A5A6",
}


class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self._triple_count: dict[tuple, int] = defaultdict(int)

    def add_triples(self, triples: list[Triple]) -> None:
        for t in triples:
            subj = t.subject.strip()
            obj = t.object.strip()
            if not subj or not obj or subj == obj:
                continue

            if subj not in self.graph:
                self.graph.add_node(subj, type=t.subject_type, sources=set())
            if obj not in self.graph:
                self.graph.add_node(obj, type=t.object_type, sources=set())

            if t.source:
                self.graph.nodes[subj]["sources"].add(t.source)
                self.graph.nodes[obj]["sources"].add(t.source)

            key = (subj, t.predicate.lower(), obj)
            self._triple_count[key] += 1
            self.graph.add_edge(subj, obj, label=t.predicate, weight=self._triple_count[key])

    def merge(self, other: "KnowledgeGraph") -> None:
        self.add_triples([
            Triple(
                subject=u,
                predicate=data["label"],
                object=v,
                subject_type=self.graph.nodes.get(u, {}).get("type", "other"),
                object_type=self.graph.nodes.get(v, {}).get("type", "other"),
            )
            for u, v, data in other.graph.edges(data=True)
        ])

    def prune(self, min_degree: int = 1) -> None:
        to_remove = [n for n, d in self.graph.degree() if d < min_degree]
        self.graph.remove_nodes_from(to_remove)

    def stats(self) -> dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": round(nx.density(self.graph), 4),
            "components": nx.number_weakly_connected_components(self.graph),
        }

    def to_d3(self) -> dict:
        """Serialize to D3.js force graph format."""
        node_index = {n: i for i, n in enumerate(self.graph.nodes())}
        nodes = []
        for node, data in self.graph.nodes(data=True):
            node_type = data.get("type", "other")
            nodes.append({
                "id": node,
                "index": node_index[node],
                "type": node_type,
                "color": NODE_COLORS.get(node_type, NODE_COLORS["other"]),
                "degree": self.graph.degree(node),
                "sources": list(data.get("sources", [])),
            })

        edges = []
        seen_edges: dict[tuple, dict] = {}
        for u, v, data in self.graph.edges(data=True):
            key = (u, v)
            if key in seen_edges:
                seen_edges[key]["labels"].append(data.get("label", ""))
            else:
                seen_edges[key] = {
                    "source": u,
                    "target": v,
                    "labels": [data.get("label", "")],
                    "weight": data.get("weight", 1),
                }
        edges = list(seen_edges.values())

        return {"nodes": nodes, "links": edges}

    def to_obsidian(self, output_dir: Path) -> None:
        """Export as Obsidian-compatible markdown vault."""
        notes_dir = output_dir / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)

        for node, data in self.graph.nodes(data=True):
            outgoing = [(v, d["label"]) for _, v, d in self.graph.out_edges(node, data=True)]
            incoming = [(u, d["label"]) for u, _, d in self.graph.in_edges(node, data=True)]

            lines = [
                f"# {node}",
                f"\n**Type:** {data.get('type', 'other')}",
                f"**Sources:** {', '.join(data.get('sources', []))}",
                "\n## Relationships\n",
            ]

            if outgoing:
                lines.append("### Outgoing")
                for target, label in outgoing:
                    safe = target.replace("/", "-").replace("\\", "-")
                    lines.append(f"- **{label}** → [[{safe}]]")

            if incoming:
                lines.append("\n### Incoming")
                for source, label in incoming:
                    safe = source.replace("/", "-").replace("\\", "-")
                    lines.append(f"- [[{safe}]] **{label}**")

            safe_node = node.replace("/", "-").replace("\\", "-").replace(":", "")
            (notes_dir / f"{safe_node}.md").write_text("\n".join(lines), encoding="utf-8")

    def save(self, path: Path) -> None:
        data = {
            "nodes": [
                {"id": n, "type": d.get("type", "other"), "sources": list(d.get("sources", []))}
                for n, d in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, "label": d.get("label", ""), "weight": d.get("weight", 1)}
                for u, v, d in self.graph.edges(data=True)
            ],
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "KnowledgeGraph":
        data = json.loads(path.read_text(encoding="utf-8"))
        kg = cls()
        for node in data["nodes"]:
            kg.graph.add_node(node["id"], type=node.get("type", "other"), sources=set(node.get("sources", [])))
        for edge in data["edges"]:
            kg.graph.add_edge(edge["source"], edge["target"], label=edge.get("label", ""), weight=edge.get("weight", 1))
        return kg
