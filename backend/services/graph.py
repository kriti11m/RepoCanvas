"""
Graph service for loading and manipulating repository dependency graphs
"""

import json
import networkx as nx
from typing import List, Dict, Any, Tuple, Optional, Set
from pathlib import Path
import logging

from schemas import Graph, GraphNode, GraphEdge, CodeSnippet

logger = logging.getLogger(__name__)

class GraphService:
    """Service for managing repository dependency graphs"""
    
    def __init__(self):
        self.graph: Optional[nx.DiGraph] = None
        self.graph_data: Optional[Dict[str, Any]] = None
        self.node_map: Dict[str, GraphNode] = {}
        
    def is_loaded(self) -> bool:
        """Check if a graph is currently loaded"""
        return self.graph is not None and len(self.graph.nodes) > 0
    
    def load_graph(self, graph_path: str) -> None:
        """
        Load graph from JSON file
        
        Args:
            graph_path: Path to graph.json file
        """
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                self.graph_data = json.load(f)
            
            # Create NetworkX graph
            self.graph = nx.DiGraph()
            self.node_map = {}
            
            # Add nodes
            for node_data in self.graph_data.get('nodes', []):
                node = GraphNode(**node_data)
                self.node_map[node.id] = node
                
                # Add to NetworkX graph with attributes
                self.graph.add_node(
                    node.id,
                    label=node.label,
                    file=node.file,
                    start_line=node.start_line,
                    end_line=node.end_line,
                    code=node.code,
                    doc=node.doc,
                    node_type=getattr(node, 'node_type', 'function')
                )
            
            # Add edges
            for edge_data in self.graph_data.get('edges', []):
                edge = GraphEdge(**edge_data)
                if edge.source in self.node_map and edge.target in self.node_map:
                    self.graph.add_edge(
                        edge.source,
                        edge.target,
                        type=edge.type.value
                    )
            
            logger.info(f"Loaded graph with {len(self.graph.nodes)} nodes and {len(self.graph.edges)} edges")
            
        except Exception as e:
            logger.error(f"Failed to load graph from {graph_path}: {e}")
            raise
    
    def get_graph_json(self) -> Dict[str, Any]:
        """Get the loaded graph as JSON"""
        if not self.graph_data:
            raise ValueError("No graph loaded")
        return self.graph_data
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a specific node by ID"""
        return self.node_map.get(node_id)
    
    def get_neighbors(self, node_id: str, direction: str = "both") -> List[str]:
        """
        Get neighbors of a node
        
        Args:
            node_id: Node identifier
            direction: "in", "out", or "both"
        """
        if not self.graph or node_id not in self.graph:
            return []
        
        if direction == "in":
            return list(self.graph.predecessors(node_id))
        elif direction == "out":
            return list(self.graph.successors(node_id))
        else:  # both
            return list(set(self.graph.predecessors(node_id)) | set(self.graph.successors(node_id)))
    
    def compute_answer_path(self, node_ids: List[str]) -> Tuple[List[str], List[GraphEdge]]:
        """
        Compute a minimal path connecting the given nodes
        
        Args:
            node_ids: List of node IDs to connect
            
        Returns:
            Tuple of (ordered_path_nodes, path_edges)
        """
        if not self.graph or not node_ids:
            return [], []
        
        # Filter to nodes that exist in graph
        valid_nodes = [nid for nid in node_ids if nid in self.graph]
        if not valid_nodes:
            return [], []
        
        if len(valid_nodes) == 1:
            return valid_nodes, []
        
        try:
            # Strategy: Use the highest scored node as seed, find shortest paths to others
            seed_node = valid_nodes[0]
            all_path_nodes = set([seed_node])
            all_path_edges = []
            
            for target_node in valid_nodes[1:]:
                try:
                    # Try to find shortest path
                    path = nx.shortest_path(self.graph, seed_node, target_node)
                    all_path_nodes.update(path)
                    
                    # Add edges for this path
                    for i in range(len(path) - 1):
                        source, target = path[i], path[i + 1]
                        edge_data = self.graph.get_edge_data(source, target)
                        if edge_data:
                            all_path_edges.append(GraphEdge(
                                source=source,
                                target=target,
                                type=edge_data.get('type', 'call')
                            ))
                    
                except nx.NetworkXNoPath:
                    # No path exists, include the isolated node anyway
                    all_path_nodes.add(target_node)
                    logger.warning(f"No path from {seed_node} to {target_node}")
                    continue
            
            # Order nodes by their appearance in original node_ids list
            ordered_path = []
            for nid in node_ids:
                if nid in all_path_nodes:
                    ordered_path.append(nid)
            
            # Add any remaining nodes from paths
            for nid in all_path_nodes:
                if nid not in ordered_path:
                    ordered_path.append(nid)
            
            return ordered_path, all_path_edges
            
        except Exception as e:
            logger.error(f"Error computing answer path: {e}")
            # Fallback: return original nodes without path
            return valid_nodes, []
    
    def get_code_snippets(self, node_ids: List[str]) -> List[CodeSnippet]:
        """
        Get code snippets for the given node IDs
        
        Args:
            node_ids: List of node identifiers
            
        Returns:
            List of code snippets
        """
        snippets = []
        
        for node_id in node_ids:
            node = self.get_node(node_id)
            if node:
                snippets.append(CodeSnippet(
                    node_id=node_id,
                    code=node.code,
                    file=node.file,
                    start_line=node.start_line,
                    end_line=node.end_line,
                    doc=node.doc
                ))
        
        return snippets
    
    def find_nodes_by_file(self, file_path: str) -> List[str]:
        """Find all nodes in a specific file"""
        return [
            node_id for node_id, node in self.node_map.items()
            if node.file == file_path
        ]
    
    def find_nodes_by_pattern(self, pattern: str) -> List[str]:
        """Find nodes whose labels contain the pattern"""
        pattern_lower = pattern.lower()
        return [
            node_id for node_id, node in self.node_map.items()
            if pattern_lower in node.label.lower()
        ]
    
    def get_subgraph(self, node_ids: List[str], expand_neighbors: bool = True) -> Dict[str, Any]:
        """
        Extract a subgraph containing the specified nodes
        
        Args:
            node_ids: List of node IDs to include
            expand_neighbors: Whether to include immediate neighbors
            
        Returns:
            Subgraph as JSON
        """
        if not self.graph:
            return {"nodes": [], "edges": []}
        
        subgraph_nodes = set(node_ids)
        
        # Optionally expand to include neighbors
        if expand_neighbors:
            for node_id in node_ids:
                if node_id in self.graph:
                    subgraph_nodes.update(self.graph.neighbors(node_id))
        
        # Build subgraph JSON
        nodes = []
        edges = []
        
        for node_id in subgraph_nodes:
            if node_id in self.node_map:
                node = self.node_map[node_id]
                nodes.append({
                    "id": node.id,
                    "label": node.label,
                    "file": node.file,
                    "start_line": node.start_line,
                    "end_line": node.end_line,
                    "code": node.code,
                    "doc": node.doc,
                    "node_type": getattr(node, 'node_type', 'function')
                })
        
        # Add edges within the subgraph
        for source in subgraph_nodes:
            if source in self.graph:
                for target in self.graph.successors(source):
                    if target in subgraph_nodes:
                        edge_data = self.graph.get_edge_data(source, target)
                        edges.append({
                            "source": source,
                            "target": target,
                            "type": edge_data.get('type', 'call')
                        })
        
        return {"nodes": nodes, "edges": edges}
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded graph"""
        if not self.graph:
            return {}
        
        stats = {
            "total_nodes": len(self.graph.nodes),
            "total_edges": len(self.graph.edges),
            "connected_components": nx.number_connected_components(self.graph.to_undirected()),
            "average_degree": sum(dict(self.graph.degree()).values()) / len(self.graph.nodes) if self.graph.nodes else 0
        }
        
        # Node type distribution
        node_types = {}
        for node_id in self.graph.nodes:
            node_type = self.graph.nodes[node_id].get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        stats["node_types"] = node_types
        
        # Edge type distribution
        edge_types = {}
        for source, target, data in self.graph.edges(data=True):
            edge_type = data.get('type', 'unknown')
            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        stats["edge_types"] = edge_types
        
        return stats