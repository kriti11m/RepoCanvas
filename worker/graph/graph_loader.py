# backend/worker/graph/graph_loader.py
import networkx as nx
import json

def build_graph(nodes, edges):
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n['id'], **n)
    for e in edges:
        src, tgt = e['from'], e['to']
        G.add_edge(src, tgt, **{k:v for k,v in e.items() if k not in ['from','to']})
    return G

def save_graph_json(nodes, edges, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
