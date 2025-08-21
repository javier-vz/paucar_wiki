# -*- coding: utf-8 -*-
"""
visualizar_grafo.py
-----------------------
Visualiza el grafo (JSON con 'nodes' y 'edges') quedándose por defecto
con la componente conexa maximal (LCC). Exporta PNG y SVG.

Uso:
    python visualizar_grafo_lcc.py --input data/grafo_unificado.json
    # (opcional) cambiar prefijo de salida:
    # python visualizar_grafo_lcc.py -i data/grafo_unificado.json -o data/grafo_unificado_viz
"""

import argparse
import json
from pathlib import Path
from math import sqrt
import warnings

import matplotlib.pyplot as plt
import networkx as nx


def load_property_graph(json_path: Path) -> nx.MultiDiGraph:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    G = nx.MultiDiGraph()
    for n in nodes:
        nid = n.get("id")
        if not nid:
            continue
        G.add_node(
            nid,
            label=n.get("label") or "",
            labels=n.get("labels") or []
        )
    for e in edges:
        src = e.get("source")
        dst = e.get("target")
        if not src or not dst:
            continue
        G.add_edge(
            src, dst,
            property_id=e.get("property_id"),
            property_label=e.get("property_label"),
            category=e.get("category")
        )
    return G


def to_simple_graph(Gmulti: nx.MultiDiGraph) -> nx.Graph:
    """Colapsa MultiDiGraph -> Graph sumando pesos por aristas paralelas."""
    Gsimple = nx.Graph()
    Gsimple.add_nodes_from(Gmulti.nodes(data=True))
    for u, v, _k in Gmulti.edges(keys=True):
        if Gsimple.has_edge(u, v):
            Gsimple[u][v]["weight"] += 1
        else:
            Gsimple.add_edge(u, v, weight=1)
    return Gsimple


def largest_connected_component(G: nx.Graph) -> nx.Graph:
    """Devuelve la componente conexa maximal (tratando el grafo como no dirigido)."""
    if G.number_of_nodes() == 0:
        return G
    H = nx.Graph(G)  # garantizar no dirigido para componentes
    comps = list(nx.connected_components(H))
    if not comps:
        return G
    giant = max(comps, key=len)
    return H.subgraph(giant).copy()


def score_node_size(deg, base=150, scale=55, exp=1.2, min_sz=80, max_sz=1800):
    val = base + scale * (deg ** exp)
    return max(min_sz, min(max_sz, int(val)))


def pick_labels(G: nx.Graph, top_k=25, keywords=None):
    """Etiquetas: top_k por grado + nodos cuyo label coincida con keywords."""
    keywords = keywords or []
    deg = dict(G.degree())
    top_nodes = {n for n, _ in sorted(deg.items(), key=lambda x: x[1], reverse=True)[:top_k]}

    kw_nodes = set()
    if keywords:
        lower_kw = [k.lower() for k in keywords]
        for n, d in G.nodes(data=True):
            label = (d.get("label") or "").lower()
            if any(k in label for k in lower_kw):
                kw_nodes.add(n)
    return top_nodes | kw_nodes


def truncate(s: str, maxlen=36):
    s = s or ""
    return (s[: maxlen - 1] + "…") if len(s) > maxlen else s


def draw_graph(G: nx.Graph,
               output_prefix: Path,
               top_labels=25,
               keywords=None,
               figsize=(14, 10),
               dpi=200,
               seed=42):
    if G.number_of_nodes() == 0:
        warnings.warn("Grafo vacío; no se generará imagen.")
        return

    # Layout spring con k ~ 1/sqrt(n) para evitar amontonamiento
    n = G.number_of_nodes()
    k = 1.2 / max(1.0, sqrt(n))
    pos = nx.spring_layout(G, k=k, seed=seed, iterations=200)

    deg = dict(G.degree())
    weights = [G[u][v].get("weight", 1) for u, v in G.edges()]
    max_w = max(weights) if weights else 1

    # Estéticas (sin colores específicos)
    node_sizes = [score_node_size(deg.get(n, 0)) for n in G.nodes()]
    edge_widths = [1 + 2.5 * (w / max_w) for w in weights]

    plt.figure(figsize=figsize, dpi=dpi)

    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.35)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, alpha=0.9, linewidths=0.8, edgecolors="black")

    label_nodes = pick_labels(G, top_k=top_labels, keywords=keywords or ["qoyllur", "paucartambo", "carmen"])
    labels = {}
    for n, d in G.nodes(data=True):
        if n in label_nodes:
            text = d.get("label") or n
            labels[n] = truncate(text, 34)

    nx.draw_networkx_labels(
        G, pos, labels=labels,
        font_size=9,
        font_weight="regular",
        verticalalignment="center",
        horizontalalignment="center",
        bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="black", alpha=0.65, lw=0.5)
    )

    title = f"Grafo (LCC) • nodos={G.number_of_nodes()} • aristas={G.number_of_edges()} • etiquetas={len(labels)}"
    plt.title(title, fontsize=12)
    plt.axis("off")

    png_path = output_prefix.with_suffix(".png")
    svg_path = output_prefix.with_suffix(".svg")
    plt.tight_layout(pad=0.5)
    plt.savefig(png_path, dpi=dpi)
    plt.savefig(svg_path)
    plt.close()
    print(f"Visualización exportada:\n  - {png_path}\n  - {svg_path}")


def main():
    ap = argparse.ArgumentParser(description="Visualizador (LCC por defecto) de grafos JSON (nodes/edges).")
    ap.add_argument("--input", "-i", required=True, help="Ruta al JSON (p.ej., data/grafo_unificado.json)")
    ap.add_argument("--output", "-o", default=None, help="Prefijo de salida (sin extensión). Por defecto: <input>_viz")
    ap.add_argument("--top-labels", type=int, default=25, help="Nº de nodos etiquetados por grado (default: 25)")
    ap.add_argument("--dpi", type=int, default=220, help="DPI para PNG (default: 220)")
    ap.add_argument("--figw", type=float, default=14.0, help="Ancho figura (pulgadas)")
    ap.add_argument("--figh", type=float, default=10.0, help="Alto figura (pulgadas)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {in_path}")

    out_prefix = Path(args.output) if args.output else in_path.with_suffix("").parent / (in_path.stem + "_viz")

    Gm = load_property_graph(in_path)
    G = to_simple_graph(Gm)

    # LCC por defecto
    G = largest_connected_component(G)

    draw_graph(
        G,
        output_prefix=out_prefix,
        top_labels=args.top_labels,
        figsize=(args.figw, args.figh),
        dpi=args.dpi,
    )


if __name__ == "__main__":
    main()
