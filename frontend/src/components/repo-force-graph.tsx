import React, { useState, useCallback, useEffect, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  FolderIcon, 
  FileIcon, 
  ChevronRightIcon, 
  ChevronDownIcon,
  CodeIcon,
  Package,
  Layers3,
  GitBranch,
  Eye,
  EyeOff,
  RotateCcw,
  ZoomIn,
  ZoomOut
} from 'lucide-react';

interface GraphNode {
  id: string;
  name: string;
  type: 'root' | 'folder' | 'file' | 'function' | 'class';
  val?: number; // Node size
  color?: string;
  group?: number;
  parent?: string;
  children?: string[];
  isExpanded?: boolean;
  level?: number;
  language?: string;
  path?: string;
}

interface GraphLink {
  source: string;
  target: string;
  value?: number;
  color?: string;
}

interface RepoForceGraphProps {
  graphData?: {
    nodes: any[];
    edges: any[];
  };
  repoName?: string;
}

const RepoForceGraph: React.FC<RepoForceGraphProps> = ({ graphData, repoName }) => {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['root']));
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [view3D, setView3D] = useState(false);

  // Color scheme for different node types (updated for dark theme)
  const getNodeColor = (node: GraphNode) => {
    if (selectedNode === node.id) return '#ff6b35';
    
    switch (node.type) {
      case 'root': return '#a855f7';
      case 'folder': return '#3b82f6';
      case 'file': return '#10b981';
      case 'function': return '#f59e0b';
      case 'class': return '#ef4444';
      default: return '#9ca3af';
    }
  };

  // Node size based on type and importance (made smaller)
  const getNodeSize = (node: GraphNode) => {
    switch (node.type) {
      case 'root': return 12;
      case 'folder': return expandedNodes.has(node.id) ? 10 : 8;
      case 'file': return 6;
      case 'function': return 4;
      case 'class': return 5;
      default: return 3;
    }
  };

  // Transform raw graph data into hierarchical structure
  const transformGraphData = useCallback(() => {
    if (!graphData?.nodes || !graphData?.edges) {
      // Create a sample repository structure for demonstration
      const sampleNodes: GraphNode[] = [
        { id: 'root', name: repoName || 'RepoCanvas', type: 'root', level: 0 },
        { id: 'frontend', name: 'frontend', type: 'folder', parent: 'root', level: 1 },
        { id: 'backend', name: 'backend', type: 'folder', parent: 'root', level: 1 },
        { id: 'worker', name: 'worker', type: 'folder', parent: 'root', level: 1 },
        { id: 'summarizer', name: 'summarizer', type: 'folder', parent: 'root', level: 1 },
        // Frontend files
        { id: 'frontend/src', name: 'src', type: 'folder', parent: 'frontend', level: 2 },
        { id: 'frontend/src/App.tsx', name: 'App.tsx', type: 'file', parent: 'frontend/src', level: 3, language: 'typescript' },
        { id: 'frontend/src/main.tsx', name: 'main.tsx', type: 'file', parent: 'frontend/src', level: 3, language: 'typescript' },
        // Backend files
        { id: 'backend/app.py', name: 'app.py', type: 'file', parent: 'backend', level: 2, language: 'python' },
        { id: 'backend/config.py', name: 'config.py', type: 'file', parent: 'backend', level: 2, language: 'python' },
        // Worker files
        { id: 'worker/app.py', name: 'app.py', type: 'file', parent: 'worker', level: 2, language: 'python' },
        { id: 'worker/parse_repo.py', name: 'parse_repo.py', type: 'file', parent: 'worker', level: 2, language: 'python' },
      ];

      const sampleLinks: GraphLink[] = [
        { source: 'root', target: 'frontend' },
        { source: 'root', target: 'backend' },
        { source: 'root', target: 'worker' },
        { source: 'root', target: 'summarizer' },
        { source: 'frontend', target: 'frontend/src' },
        { source: 'frontend/src', target: 'frontend/src/App.tsx' },
        { source: 'frontend/src', target: 'frontend/src/main.tsx' },
        { source: 'backend', target: 'backend/app.py' },
        { source: 'backend', target: 'backend/config.py' },
        { source: 'worker', target: 'worker/app.py' },
        { source: 'worker', target: 'worker/parse_repo.py' },
      ];

      setNodes(sampleNodes);
      setLinks(sampleLinks);
      // Reset expanded nodes for sample data
      setExpandedNodes(new Set(['root']));
      return;
    }

    console.log('Processing real repository data:', { 
      nodeCount: graphData.nodes.length, 
      edgeCount: graphData.edges.length,
      firstNode: graphData.nodes[0]
    });

    // Transform actual graph data into hierarchical structure
    const transformedNodes: GraphNode[] = [];
    const transformedLinks: GraphLink[] = [];
    const folderMap = new Map<string, GraphNode>();

    // First pass: Create folder structure
    graphData.nodes.forEach((rawNode) => {
      const filePath = rawNode.file || rawNode.file_path || '';
      const pathParts = filePath.split('/').filter(Boolean);
      
      // Create folder nodes for each path segment
      for (let i = 0; i < pathParts.length - 1; i++) {
        const folderPath = pathParts.slice(0, i + 1).join('/');
        const folderName = pathParts[i];
        const parentPath = i > 0 ? pathParts.slice(0, i).join('/') : '';
        
        if (!folderMap.has(folderPath)) {
          const folderNode: GraphNode = {
            id: `folder:${folderPath}`,
            name: folderName,
            type: 'folder',
            level: i + 1,
            path: folderPath,
            parent: i > 0 ? `folder:${parentPath}` : 'root',
          };
          folderMap.set(folderPath, folderNode);
        }
      }
    });

    // Add root node
    transformedNodes.push({
      id: 'root',
      name: repoName || 'Repository',
      type: 'root',
      level: 0,
    });

    // Add folder nodes
    transformedNodes.push(...Array.from(folderMap.values()));

    // Second pass: Create file nodes
    graphData.nodes.forEach((rawNode) => {
      const filePath = rawNode.file || rawNode.file_path || '';
      const pathParts = filePath.split('/').filter(Boolean);
      const fileName = pathParts[pathParts.length - 1] || rawNode.name || rawNode.label || rawNode.id || 'unknown';
      
      // Determine node type from the raw data
      let nodeType: GraphNode['type'] = 'file';
      if (rawNode.type === 'FUNCTION' || (rawNode.id && rawNode.id.includes('function:'))) {
        nodeType = 'function';
      } else if (rawNode.type === 'CLASS' || (rawNode.id && rawNode.id.includes('class:'))) {
        nodeType = 'class';
      } else if (rawNode.type === 'FILE' || (rawNode.id && rawNode.id.includes('file:'))) {
        nodeType = 'file';
      }

      const parentPath = pathParts.length > 1 ? pathParts.slice(0, -1).join('/') : '';
      const parent = parentPath ? `folder:${parentPath}` : 'root';

      const fileNode: GraphNode = {
        id: rawNode.id || `node_${Math.random().toString(36).substr(2, 9)}`,
        name: fileName,
        type: nodeType,
        level: pathParts.length,
        language: rawNode.language || 'unknown',
        path: filePath,
        parent: parent,
      };

      transformedNodes.push(fileNode);
    });

    // Create folder hierarchy links
    folderMap.forEach((folder) => {
      if (folder.parent) {
        transformedLinks.push({
          source: folder.parent,
          target: folder.id,
        });
      }
    });

    // Create file to folder links
    transformedNodes.forEach((node) => {
      if (node.type !== 'root' && node.type !== 'folder' && node.parent) {
        transformedLinks.push({
          source: node.parent,
          target: node.id,
        });
      }
    });

    // Add original edges between nodes
    graphData.edges.forEach((rawEdge) => {
      // Only add edges between nodes that exist in our transformed data
      const sourceExists = transformedNodes.some(n => n.id === rawEdge.source);
      const targetExists = transformedNodes.some(n => n.id === rawEdge.target);
      
      if (sourceExists && targetExists) {
        transformedLinks.push({
          source: rawEdge.source,
          target: rawEdge.target,
        });
      }
    });

    console.log('Transformed repository data:', { 
      nodes: transformedNodes.length, 
      links: transformedLinks.length,
      folders: folderMap.size 
    });

    setNodes(transformedNodes);
    setLinks(transformedLinks);

    // Reset and set up initial expanded nodes for real repository data
    const topLevelFolders = transformedNodes
      .filter(node => node.type === 'folder' && node.level === 1)
      .map(node => node.id);
    
    const initialExpanded = new Set(['root', ...topLevelFolders.slice(0, 3)]); // Expand root and first 3 top-level folders
    console.log('Setting initial expanded nodes:', Array.from(initialExpanded));
    setExpandedNodes(initialExpanded);
  }, [graphData, repoName]);

  // Filter nodes and links based on expanded state
  const { visibleNodes, visibleLinks } = useMemo(() => {
    console.log('Computing visible nodes from:', nodes.length, 'total nodes');
    console.log('Expanded nodes:', Array.from(expandedNodes));
    
    if (nodes.length === 0) {
      return { visibleNodes: [], visibleLinks: [] };
    }

    const visible = new Set<string>();
    
    // Always include root
    visible.add('root');
    
    // BFS to find all visible nodes
    const queue = ['root'];
    
    while (queue.length > 0) {
      const nodeId = queue.shift()!;
      
      // If node is expanded, add its children
      if (expandedNodes.has(nodeId)) {
        const children = nodes.filter(n => n.parent === nodeId);
        children.forEach(child => {
          if (!visible.has(child.id)) {
            visible.add(child.id);
            queue.push(child.id);
          }
        });
      }
    }

    const visibleNodes = nodes.filter(n => visible.has(n.id)).map(node => ({
      ...node,
      val: getNodeSize(node),
      color: getNodeColor(node),
      isExpanded: expandedNodes.has(node.id),
    }));

    const visibleLinks = links.filter(l => 
      visible.has(l.source as string) && visible.has(l.target as string)
    ).map(link => ({
      ...link,
      color: selectedNode && (link.source === selectedNode || link.target === selectedNode) 
        ? '#ff6b35' : '#94a3b8',
      value: selectedNode && (link.source === selectedNode || link.target === selectedNode) 
        ? 3 : 1,
    }));

    console.log('Visible nodes:', visibleNodes.length, 'Visible links:', visibleLinks.length);
    return { visibleNodes, visibleLinks };
  }, [nodes, links, expandedNodes, selectedNode]);

  // Toggle node expansion
  const handleNodeClick = useCallback((node: any) => {
    const nodeId = node.id;
    setSelectedNode(nodeId);
    
    // Only toggle expansion for folders
    if (node.type === 'folder' || node.type === 'root') {
      setExpandedNodes(prev => {
        const newSet = new Set(prev);
        if (newSet.has(nodeId)) {
          newSet.delete(nodeId);
          // Also collapse all children
          const childrenToCollapse = nodes.filter(n => n.id.startsWith(nodeId + '/'));
          childrenToCollapse.forEach(child => newSet.delete(child.id));
        } else {
          newSet.add(nodeId);
        }
        return newSet;
      });
    }
  }, [nodes]);

  // Custom node rendering (optimized for dark theme and small size)
  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.name;
    const fontSize = Math.max(10 / globalScale, 2);
    const iconSize = Math.max(12 / globalScale, 3);
    
    ctx.font = `${fontSize}px Arial`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.val, 0, 2 * Math.PI, false);
    ctx.fillStyle = node.color;
    ctx.fill();
    
    // Add border for selected node
    if (selectedNode === node.id) {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
    
    // Draw expand/collapse indicator for folders (smaller)
    if ((node.type === 'folder' || node.type === 'root') && globalScale > 0.3) {
      ctx.fillStyle = '#ffffff';
      ctx.font = `${iconSize}px Arial`;
      const indicator = node.isExpanded ? '−' : '+';
      ctx.fillText(indicator, node.x, node.y);
    }
    
    // Draw label (only show for larger scales to avoid clutter)
    if (globalScale > 0.6) {
      ctx.fillStyle = '#e5e7eb';
      ctx.font = `${fontSize}px Arial`;
      const maxLength = 12;
      const displayLabel = label.length > maxLength ? label.substring(0, maxLength) + '...' : label;
      ctx.fillText(displayLabel, node.x, node.y + node.val + fontSize + 1);
    }
  }, [selectedNode]);

  useEffect(() => {
    transformGraphData();
  }, [transformGraphData]);

  // Control functions
  const expandAll = () => {
    const allFolders = nodes
      .filter(n => n.type === 'folder' || n.type === 'root')
      .map(n => n.id);
    setExpandedNodes(new Set(allFolders));
  };

  const collapseAll = () => {
    setExpandedNodes(new Set(['root']));
  };

  const reset = () => {
    setSelectedNode(null);
    setExpandedNodes(new Set(['root']));
  };

  return (
    <div className="w-full h-full relative bg-transparent overflow-hidden max-w-full max-h-full">
      {/* Loading State */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-black/50 backdrop-blur-sm">
          <div className="text-center">
            <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-3"></div>
            <div className="text-gray-300 text-sm">
              {graphData ? 'Building graph...' : 'No data yet'}
            </div>
          </div>
        </div>
      )}

      {/* Controls - Made smaller and more compact */}
      <div className="absolute top-2 left-2 z-10 flex flex-col gap-1">
        <div className="flex gap-1">
          <Button variant="outline" size="sm" onClick={expandAll} disabled={nodes.length === 0} className="text-xs px-2 py-1 h-6 bg-black/50 border-gray-600 text-gray-300 hover:bg-gray-700">
            <Eye className="w-3 h-3 mr-1" />
            Expand
          </Button>
          <Button variant="outline" size="sm" onClick={collapseAll} disabled={nodes.length === 0} className="text-xs px-2 py-1 h-6 bg-black/50 border-gray-600 text-gray-300 hover:bg-gray-700">
            <EyeOff className="w-3 h-3 mr-1" />
            Collapse
          </Button>
          <Button variant="outline" size="sm" onClick={reset} disabled={nodes.length === 0} className="text-xs px-2 py-1 h-6 bg-black/50 border-gray-600 text-gray-300 hover:bg-gray-700">
            <RotateCcw className="w-3 h-3" />
          </Button>
        </div>
        
        {/* Node info - Made smaller */}
        {selectedNode && (
          <div className="bg-black/80 border border-gray-600 p-2 rounded-md shadow-lg max-w-xs text-xs">
            <div className="font-semibold text-gray-200">
              {visibleNodes.find(n => n.id === selectedNode)?.name}
            </div>
            <div className="text-gray-400 text-xs mt-1">
              {visibleNodes.find(n => n.id === selectedNode)?.type}
            </div>
            {visibleNodes.find(n => n.id === selectedNode)?.language && (
              <div className="text-gray-500 text-xs">
                {visibleNodes.find(n => n.id === selectedNode)?.language}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Stats - Made smaller */}
      <div className="absolute top-2 right-2 z-10">
        <div className="bg-black/80 border border-gray-600 px-2 py-1 rounded-md shadow text-xs">
          <div className="flex items-center gap-3 text-gray-300">
            <div className="flex items-center gap-1">
              <GitBranch className="w-3 h-3 text-blue-400" />
              <span>{visibleNodes.length}</span>
            </div>
            <div className="flex items-center gap-1">
              <Package className="w-3 h-3 text-green-400" />
              <span>{visibleLinks.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Force Graph */}
      {visibleNodes.length > 0 && (
        <ForceGraph2D
          graphData={{ nodes: visibleNodes, links: visibleLinks }}
          nodeLabel="name"
          nodeCanvasObject={nodeCanvasObject}
          onNodeClick={handleNodeClick}
          linkWidth={(link: any) => link.value || 1}
          linkColor={(link: any) => link.color || '#6b7280'}
          backgroundColor="transparent"
          cooldownTicks={100}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          enableNodeDrag={true}
          nodeRelSize={4}
          linkDirectionalArrowLength={2}
          linkDirectionalArrowRelPos={1}
          width={720}
          height={480}
        />
      )}
    </div>
  );
};

export default RepoForceGraph;