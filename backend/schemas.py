"""
Pydantic schemas for request/response models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class EdgeType(str, Enum):
    CALL = "call"
    IMPORT = "import"
    INHERIT = "inherit"
    AMBIGUOUS = "ambiguous"

# Graph Models
class GraphNode(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display name")
    file: str = Field(..., description="Source file path")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    code: str = Field(..., description="Code snippet")
    doc: Optional[str] = Field(None, description="Documentation string")
    node_type: Optional[str] = Field("function", description="Type of node (function, class, etc.)")

class GraphEdge(BaseModel):
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = Field(..., description="Type of relationship")

class Graph(BaseModel):
    nodes: List[GraphNode] = Field(..., description="List of graph nodes")
    edges: List[GraphEdge] = Field(..., description="List of graph edges")

# Search Models
class SearchHit(BaseModel):
    node_id: str = Field(..., description="Node identifier")
    score: float = Field(..., description="Relevance score")
    snippet: str = Field(..., description="Code snippet")
    file: str = Field(..., description="Source file")
    start_line: int = Field(..., description="Starting line number")

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    top_k: int = Field(10, description="Number of results to return", ge=1, le=50)

class SearchResponse(BaseModel):
    results: List[SearchHit] = Field(..., description="Search results")
    query: str = Field(..., description="Original query")
    total_results: int = Field(..., description="Total number of results")
    processing_time: float = Field(..., description="Processing time in seconds")

# Code snippet model
class CodeSnippet(BaseModel):
    node_id: str = Field(..., description="Node identifier")
    code: str = Field(..., description="Code content")
    file: str = Field(..., description="Source file")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    doc: Optional[str] = Field(None, description="Documentation")

# Summary Models
class NodeReference(BaseModel):
    node_id: str = Field(..., description="Node identifier")
    excerpt_line: str = Field(..., description="Key line or signature")

class Summary(BaseModel):
    one_liner: str = Field(..., description="Concise one-line explanation")
    steps: List[str] = Field(..., description="Step-by-step breakdown")
    inputs_outputs: List[str] = Field(default_factory=list, description="Input/output descriptions")
    caveats: List[str] = Field(default_factory=list, description="Important caveats or notes")
    node_refs: List[NodeReference] = Field(default_factory=list, description="Referenced nodes")

class SummarizeRequest(BaseModel):
    snippets: List[CodeSnippet] = Field(..., description="Code snippets to summarize")
    question: str = Field(..., description="User's question", min_length=1, max_length=500)
    max_tokens: int = Field(400, description="Maximum tokens for summary", ge=100, le=1000)

class SummarizeResponse(BaseModel):
    summary: Summary = Field(..., description="Generated summary")

# Parse Models
class ParseRequest(BaseModel):
    repo_url: str = Field(..., description="Repository URL to parse")
    branch: Optional[str] = Field("main", description="Branch to parse")
    include_tests: bool = Field(True, description="Whether to include test files")
    max_files: int = Field(1000, description="Maximum number of files to process", ge=1, le=5000)

class ParseResponse(BaseModel):
    success: bool = Field(..., description="Whether parsing succeeded")
    message: str = Field(..., description="Status message")
    graph_path: Optional[str] = Field(None, description="Path to generated graph.json")
    processing_time: float = Field(..., description="Processing time in seconds")
    stats: Optional[Dict[str, Any]] = Field(None, description="Parsing statistics")

# Analyze Models
class AnalyzeRequest(BaseModel):
    query: str = Field(..., description="Analysis query", min_length=1, max_length=500)
    top_k: int = Field(10, description="Number of search results to consider", ge=1, le=50)
    include_full_graph: bool = Field(False, description="Whether to include full graph in response")
    max_path_length: int = Field(20, description="Maximum path length", ge=1, le=50)

class AnalyzeResponse(BaseModel):
    answer_path: List[str] = Field(..., description="Ordered list of node IDs in the answer path")
    path_edges: List[GraphEdge] = Field(..., description="Edges connecting the path nodes")
    snippets: List[CodeSnippet] = Field(..., description="Code snippets for path nodes")
    summary: Optional[Summary] = Field(None, description="Generated summary")
    graph: Optional[Graph] = Field(None, description="Full graph (if requested)")
    processing_time: float = Field(..., description="Processing time in seconds")

# Health Models
class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall health status")
    timestamp: int = Field(..., description="Unix timestamp")
    services: Dict[str, bool] = Field(..., description="Service availability status")

# Error Models
class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: int = Field(..., description="Unix timestamp")