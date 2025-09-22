import React, { useState, useCallback, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  Position,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  FolderIcon, 
  FileIcon, 
  ChevronRightIcon, 
  ChevronDownIcon,
  CodeIcon,
  ZapIcon,
  BoxIcon
} from 'lucide-react';

// Custom Node Types
const FolderNode = ({ data, selected }: any) => {
  const { label, isExpanded, nodeType, fileCount, onToggle } = data;
  
  return (
    <div className={`
      px-4 py-3 rounded-lg border-2 transition-all duration-200 min-w-[160px]
      ${selected 
        ? 'border-blue-500 bg-blue-50 shadow-lg' 
        : 'border-gray-300 bg-white hover:border-gray-400 hover:shadow-md'
      }
    `}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-blue-100">
            <FolderIcon className="w-4 h-4 text-blue-600" />
          </div>
          <span className="font-medium text-sm text-gray-800 truncate max-w-[100px]">
            {label}
          </span>
        </div>
        <div className="flex items-center space-x-1">
          {fileCount > 0 && (
            <Badge variant="secondary" className="text-xs px-1">
              {fileCount}
            </Badge>
          )}
          <Button
            variant="ghost"
            size="sm"
            className="p-0 h-5 w-5"
            onClick={onToggle}
          >
            {isExpanded ? (
              <ChevronDownIcon className="w-3 h-3" />
            ) : (
              <ChevronRightIcon className="w-3 h-3" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

const FileNode = ({ data, selected }: any) => {
  const { label, nodeType, language, functionCount } = data;
  
  const getIcon = () => {
    switch (nodeType) {
      case 'function': return <ZapIcon className="w-4 h-4 text-green-600" />;
      case 'class': return <BoxIcon className="w-4 h-4 text-purple-600" />;
      default: return <FileIcon className="w-4 h-4 text-gray-600" />;
    }
  };
  
  const getBorderColor = () => {
    switch (language) {
      case 'typescript': return 'border-blue-400';
      case 'javascript': return 'border-yellow-400';
      case 'python': return 'border-green-400';
      case 'java': return 'border-orange-400';
      default: return 'border-gray-300';
    }
  };
  
  return (
    <div className={`
      px-3 py-2 rounded-lg border-2 transition-all duration-200 min-w-[140px]
      ${selected 
        ? `${getBorderColor()} bg-gray-50 shadow-lg` 
        : `${getBorderColor()} bg-white hover:shadow-md`
      }
    `}>
      <div className="flex items-center space-x-2">
        <div className="p-1 rounded bg-gray-100">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <span className="font-medium text-xs text-gray-800 truncate block max-w-[80px]">
            {label}
          </span>
          {functionCount > 0 && (
            <Badge variant="outline" className="text-xs mt-1">
              {functionCount} funcs
            </Badge>
          )}
        </div>
      </div>
    </div>
  );
};

const nodeTypes = {
  folder: FolderNode,
  file: FileNode,
};

// Layout algorithm using Dagre
const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ 
    rankdir: direction,
    nodesep: 100,
    ranksep: 150,
    marginx: 50,
    marginy: 50,
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 180, height: 80 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = Position.Top;
    node.sourcePosition = Position.Bottom;
    node.position = {
      x: nodeWithPosition.x - 90,
      y: nodeWithPosition.y - 40,
    };
  });

  return { nodes, edges };
};

interface HierarchicalRepoGraphProps {
  graphData?: {
    nodes: any[];
    edges: any[];
  };
}

const HierarchicalRepoGraph: React.FC<HierarchicalRepoGraphProps> = ({ graphData }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['root']));

  // Transform raw graph data into hierarchical structure
  const transformGraphData = useCallback(() => {
    if (!graphData?.nodes || !graphData?.edges) return;

    // Create a hierarchical structure from flat graph data
    const nodeMap = new Map();
    const folderNodes: Node[] = [];
    const fileNodes: Node[] = [];
    const visibleEdges: Edge[] = [];

    // Group nodes by directory
    const directories = new Map<string, any[]>();
    const rootFiles: any[] = [];

    graphData.nodes.forEach((node) => {
      const parts = node.file?.split('/') || ['root'];
      if (parts.length === 1) {
        rootFiles.push(node);
      } else {
        const dir = parts.slice(0, -1).join('/');
        if (!directories.has(dir)) {
          directories.set(dir, []);
        }
        directories.get(dir)!.push(node);
      }
    });

    // Create folder nodes
    const folderMap = new Map<string, string>();
    directories.forEach((files, dirPath) => {
      const parts = dirPath.split('/');
      const folderName = parts[parts.length - 1];
      const folderId = `folder-${dirPath}`;
      
      folderMap.set(dirPath, folderId);
      
      folderNodes.push({
        id: folderId,
        type: 'folder',
        position: { x: 0, y: 0 },
        data: {
          label: folderName,
          isExpanded: expandedNodes.has(folderId),
          nodeType: 'folder',
          fileCount: files.length,
          onToggle: () => toggleNode(folderId),
        },
      });

      // Add file nodes if folder is expanded
      if (expandedNodes.has(folderId)) {
        files.forEach((file, index) => {
          const fileId = `file-${file.id}`;
          fileNodes.push({
            id: fileId,
            type: 'file',
            position: { x: 0, y: 0 },
            data: {
              label: file.name || file.id.split(':').pop(),
              nodeType: file.type || 'file',
              language: file.language || 'unknown',
              functionCount: file.functions?.length || 0,
            },
          });

          // Add edge from folder to file
          visibleEdges.push({
            id: `edge-${folderId}-${fileId}`,
            source: folderId,
            target: fileId,
            type: 'smoothstep',
            style: { stroke: '#94a3b8', strokeWidth: 2 },
            animated: false,
          });
        });
      }
    });

    // Add root files
    rootFiles.forEach((file) => {
      const fileId = `file-${file.id}`;
      fileNodes.push({
        id: fileId,
        type: 'file',
        position: { x: 0, y: 0 },
        data: {
          label: file.name || file.id.split(':').pop(),
          nodeType: file.type || 'file',
          language: file.language || 'unknown',
          functionCount: file.functions?.length || 0,
        },
      });
    });

    // Create hierarchical folder connections
    const folderPaths = Array.from(directories.keys()).sort();
    folderPaths.forEach((path) => {
      const parentPath = path.split('/').slice(0, -1).join('/');
      if (parentPath && folderMap.has(parentPath)) {
        visibleEdges.push({
          id: `edge-${folderMap.get(parentPath)}-${folderMap.get(path)}`,
          source: folderMap.get(parentPath)!,
          target: folderMap.get(path)!,
          type: 'smoothstep',
          style: { stroke: '#64748b', strokeWidth: 3 },
          animated: false,
        });
      }
    });

    const allNodes = [...folderNodes, ...fileNodes];
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      allNodes,
      visibleEdges
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [graphData, expandedNodes]);

  const toggleNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  }, []);

  useEffect(() => {
    transformGraphData();
  }, [transformGraphData]);

  const collapseAll = useCallback(() => {
    setExpandedNodes(new Set());
  }, []);

  const expandAll = useCallback(() => {
    const allFolders = nodes
      .filter((node) => node.type === 'folder')
      .map((node) => node.id);
    setExpandedNodes(new Set(allFolders));
  }, [nodes]);

  return (
    <div className="w-full h-full relative">
      {/* Toolbar */}
      <div className="absolute top-4 left-4 z-10 flex space-x-2">
        <Button variant="outline" size="sm" onClick={expandAll}>
          Expand All
        </Button>
        <Button variant="outline" size="sm" onClick={collapseAll}>
          Collapse All
        </Button>
      </div>

      {/* Graph */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.2}
        maxZoom={2}
        className="bg-gray-50"
      >
        <Controls position="bottom-right" />
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#e2e8f0" />
      </ReactFlow>
    </div>
  );
};

export default HierarchicalRepoGraph;